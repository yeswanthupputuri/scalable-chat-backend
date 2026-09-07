import json

from urllib.parse import parse_qs

from asgiref.sync import sync_to_async

from django.utils import timezone

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import (
    Message,
    Conversation,
    MessageStatus
)

from .redis_client import redis_client
from .kafka_producer import publish_event


class ChatConsumer(AsyncWebsocketConsumer):

    # ============================================================
    # CONNECT
    # ============================================================

    async def connect(self):

        # Get conversation ID from URL
        self.conversation_id = self.scope[
            "url_route"
        ]["kwargs"]["conversation_id"]

        # Get user_id from query parameters
        #
        # Example:
        # ws://127.0.0.1:8000/ws/chat/1/?user_id=1

        query_string = self.scope["query_string"].decode()

        query_params = parse_qs(query_string)

        user_id = query_params.get("user_id")

        # Close connection if user_id is missing
        if not user_id:

            await self.close()

            return

        self.user_id = user_id[0]

        # Conversation group
        self.room_group_name = (
            f"conversation_{self.conversation_id}"
        )

        # Add WebSocket connection to conversation group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Mark user as online in Redis
        await self.set_user_online()

        # Accept WebSocket connection
        await self.accept()

        # Notify users in conversation
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_event",
                "user_id": self.user_id,
                "status": "online",
            }
        )

        print(
            f"User {self.user_id} connected to "
            f"conversation {self.conversation_id}"
        )

    # ============================================================
    # DISCONNECT
    # ============================================================

    async def disconnect(self, close_code):

        # Connection may be rejected before initialization
        if not hasattr(self, "room_group_name"):
            return

        # Remove WebSocket connection from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Only continue if user_id was initialized
        if hasattr(self, "user_id"):

            # Mark user offline
            await self.set_user_offline()

            # Notify remaining users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "presence_event",
                    "user_id": self.user_id,
                    "status": "offline",
                }
            )

            print(
                f"User {self.user_id} disconnected from "
                f"conversation {self.conversation_id}"
            )

    # ============================================================
    # RECEIVE EVENTS FROM CLIENT
    # ============================================================

    async def receive(self, text_data):

        data = json.loads(text_data)

        message_type = data.get("type")

        # MESSAGE EVENT
        if message_type == "message":

            await self.handle_message(data)

        # TYPING EVENT
        elif message_type == "typing":

            await self.handle_typing(data)

        # DELIVERED EVENT
        elif message_type == "delivered":

            await self.handle_delivered(data)

        # READ EVENT
        elif message_type == "read":

            await self.handle_read(data)

        # UNKNOWN EVENT
        else:

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "Unknown event type"
                    }
                )
            )

    # ============================================================
    # HANDLE MESSAGE
    # ============================================================

    async def handle_message(self, data):

        content = data.get("content")

        if not content:

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "content is required"
                    }
                )
            )

            return

        # Save message permanently in PostgreSQL
        message = await self.create_message(
            content,
            self.user_id
        )

        # Publish MESSAGE_SENT event to Kafka
        event = {
            "event": "MESSAGE_SENT",
            "message_id": message["id"],
            "conversation_id": int(
                self.conversation_id
            ),
            "sender_id": message["sender_id"],
            "timestamp": message["created_at"],
        }

        await sync_to_async(
            publish_event
        )(event)

        # Broadcast message through Django Channels
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message["id"],
                "content": message["content"],
                "sender_id": message["sender_id"],
                "created_at": message["created_at"],
            }
        )

    # ============================================================
    # HANDLE TYPING
    # ============================================================

    async def handle_typing(self, data):

        is_typing = data.get(
            "is_typing",
            False
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_event",
                "user_id": self.user_id,
                "is_typing": is_typing,
            }
        )

    # ============================================================
    # HANDLE DELIVERED
    # ============================================================

    async def handle_delivered(self, data):

        message_id = data.get("message_id")

        if not message_id:

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "message_id is required"
                    }
                )
            )

            return

        message = await self.mark_message_delivered(
            message_id
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "delivery_event",
                "message_id": message["id"],
                "delivered_at": message["delivered_at"],
            }
        )

    # ============================================================
    # HANDLE READ
    # ============================================================

    async def handle_read(self, data):

        message_id = data.get("message_id")

        if not message_id:

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "message_id is required"
                    }
                )
            )

            return

        message = await self.mark_message_read(
            message_id
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "read_event",
                "message_id": message["id"],
                "reader_id": self.user_id,
                "read_at": message["read_at"],
            }
        )

    # ============================================================
    # CHANNEL EVENTS
    # ============================================================

    async def chat_message(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message_id": event["message_id"],
                    "content": event["content"],
                    "sender_id": event["sender_id"],
                    "created_at": event["created_at"],
                }
            )
        )

    async def typing_event(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user_id": event["user_id"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    async def presence_event(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "presence",
                    "user_id": event["user_id"],
                    "status": event["status"],
                }
            )
        )

    async def delivery_event(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "delivered",
                    "message_id": event["message_id"],
                    "delivered_at": event["delivered_at"],
                }
            )
        )

    async def read_event(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "read",
                    "message_id": event["message_id"],
                    "reader_id": event["reader_id"],
                    "read_at": event["read_at"],
                }
            )
        )

    # ============================================================
    # DATABASE OPERATIONS
    # ============================================================

    @database_sync_to_async
    def create_message(self, content, sender_id):

        conversation = Conversation.objects.get(
            id=self.conversation_id
        )

        message = Message.objects.create(
            conversation=conversation,
            sender_id=sender_id,
            content=content
        )

        MessageStatus.objects.create(
            message=message
        )

        return {
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "created_at": message.created_at.isoformat(),
        }

    # ============================================================
    # MARK MESSAGE DELIVERED
    # ============================================================

    @database_sync_to_async
    def mark_message_delivered(self, message_id):

        status = MessageStatus.objects.get(
            message_id=message_id
        )

        if status.delivered_at is None:

            status.delivered_at = timezone.now()

            status.save()

        return {
            "id": message_id,
            "delivered_at": status.delivered_at.isoformat(),
        }

    # ============================================================
    # MARK MESSAGE READ
    # ============================================================

    @database_sync_to_async
    def mark_message_read(self, message_id):

        status = MessageStatus.objects.get(
            message_id=message_id
        )

        if status.read_at is None:

            status.read_at = timezone.now()

            status.save()

        return {
            "id": message_id,
            "read_at": status.read_at.isoformat(),
        }

    # ============================================================
    # REDIS PRESENCE
    # ============================================================

    @sync_to_async
    def set_user_online(self):

        redis_client.set(
            f"user:{self.user_id}:presence",
            "online"
        )

    @sync_to_async
    def set_user_offline(self):

        redis_client.set(
            f"user:{self.user_id}:presence",
            "offline"
        )