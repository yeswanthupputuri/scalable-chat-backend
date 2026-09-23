from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from .models import (
    ConversationMember,
    MessageStatus,
)

from .presence import (
    add_connection,
    remove_connection,
)

from .services import create_chat_message
from .kafka_producer import publish_event


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"][
            "conversation_id"
        ]

        self.user = self.scope.get("user")
        if (
            self.user is None
            or isinstance(self.user, AnonymousUser)
            or not self.user.is_authenticated
        ):
            await self.close(code=4001)
            return

        self.user_id = self.user.id

        is_member = await self.check_conversation_membership(
            self.conversation_id,
            self.user_id
        )

        if not is_member:
            await self.close(code=4003)
            return

        connection_data = await self.register_connection()

        self.connection_id = connection_data["connection_id"]
        was_offline = connection_data["was_offline"]

        self.conversation_group = (
            f"conversation_{self.conversation_id}"
        )

        self.user_group = (
            f"user_{self.user_id}"
        )

        await self.channel_layer.group_add(
            self.conversation_group,
            self.channel_name
        )

        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        await self.accept()

        if was_offline:
            await self.broadcast_user_online()

        print(
            f"User {self.user_id} connected "
            f"to conversation {self.conversation_id}"
        )

    async def disconnect(self, close_code):

        if hasattr(self, "conversation_group"):

            await self.channel_layer.group_discard(
                self.conversation_group,
                self.channel_name
            )

        if hasattr(self, "user_group"):

            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

        if hasattr(self, "user_id") and hasattr(
            self, "connection_id"
        ):

            remaining_connections = await self.unregister_connection()

            if remaining_connections == 0:
                await self.broadcast_user_offline()

        print(
            f"User {getattr(self, 'user_id', None)} disconnected"
        )

    async def receive_json(self, content):

        event_type = content.get("type")

        if event_type == "message":

            await self.handle_message(
                content.get("content")
            )

        elif event_type == "delivered":

            await self.handle_delivered(
                content.get("message_id")
            )

        elif event_type == "read":

            await self.handle_read(
                content.get("message_id")
            )

    async def handle_message(self, content):

        if not isinstance(content, str) or not content.strip():
            return

        message_data = await self.create_message(
            content.strip()
        )

        if message_data is None:
            return

        await self.channel_layer.group_send(
            self.conversation_group,
            {
                "type": "chat_message",
                "message_id": message_data["message_id"],
                "conversation_id": message_data[
                    "conversation_id"
                ],
                "sender_id": message_data["sender_id"],
                "content": message_data["content"],
                "created_at": message_data["created_at"],
            }
        )

    async def handle_delivered(self, message_id):

        if not message_id:
            return

        event_data = await self.mark_message_delivered(
            message_id
        )

        if event_data is None:
            return

        publish_event(event_data)

        sender_user_group = (
            f"user_{event_data['sender_id']}"
        )

        await self.channel_layer.group_send(
            sender_user_group,
            {
                "type": "delivery_event",
                "event": "MESSAGE_DELIVERED",
                "message_id": event_data["message_id"],
                "user_id": event_data["user_id"],
                "conversation_id": event_data[
                    "conversation_id"
                ],
                "delivered_at": event_data[
                    "delivered_at"
                ],
            }
        )

    async def handle_read(self, message_id):

        if not message_id:
            return

        event_data = await self.mark_message_read(
            message_id
        )

        if event_data is None:
            return

        publish_event(event_data)

        sender_user_group = (
            f"user_{event_data['sender_id']}"
        )

        await self.channel_layer.group_send(
            sender_user_group,
            {
                "type": "read_event",
                "event": "MESSAGE_READ",
                "message_id": event_data["message_id"],
                "reader_id": event_data["reader_id"],
                "conversation_id": event_data[
                    "conversation_id"
                ],
                "read_at": event_data["read_at"],
            }
        )

    async def chat_message(self, event):

        await self.send_json(
            {
                "type": "message",
                "message_id": event["message_id"],
                "conversation_id": event[
                    "conversation_id"
                ],
                "sender_id": event["sender_id"],
                "content": event["content"],
                "created_at": event["created_at"],
            }
        )

    async def delivery_event(self, event):

        await self.send_json(
            {
                "type": "delivered",
                "message_id": event["message_id"],
                "user_id": event["user_id"],
                "conversation_id": event[
                    "conversation_id"
                ],
                "delivered_at": event[
                    "delivered_at"
                ],
            }
        )

    async def read_event(self, event):

        await self.send_json(
            {
                "type": "read",
                "message_id": event["message_id"],
                "reader_id": event["reader_id"],
                "conversation_id": event[
                    "conversation_id"
                ],
                "read_at": event["read_at"],
            }
        )

    async def presence_event(self, event):
        await self.send_json(
            {
                "type": "presence",
                "event": event["event"],
                "user_id": event["user_id"]
            }
        )

    @database_sync_to_async
    def check_conversation_membership(
        self, conversation_id, user_id
    ):
        return ConversationMember.objects.filter(
            conversation_id=conversation_id, user_id=user_id
        ).exists()

    @database_sync_to_async
    def create_message(self, content):

        try:
            message = create_chat_message(
                conversation_id=self.conversation_id,
                sender=self.user,
                content=content
            )

            return {
                "message_id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }

        except Exception as error:
            print(
                f"Message creation failed: {error}"
            )
            return None

    @database_sync_to_async
    def mark_message_delivered(self, message_id):

        try:
            status = MessageStatus.objects.select_related(
                "message"
            ).get(
                message_id=message_id,
                user_id=self.user_id,
                message__conversation_id=self.conversation_id
            )
            if status.delivered_at is not None:
                return None

            status.delivered_at = timezone.now()
            status.save(
                update_fields=[
                    "delivered_at"
                ]
            )

            delivered_at = (
                status.delivered_at.isoformat()
            )

            return {
                "event": "MESSAGE_DELIVERED",
                "message_id": status.message_id,
                "conversation_id": (
                    status.message.conversation_id
                ),
                "sender_id": (
                    status.message.sender_id
                ),
                "user_id": self.user_id,
                "delivered_at": delivered_at
            }

        except MessageStatus.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id):

        try:
            status = MessageStatus.objects.select_related(
                "message"
            ).get(
                message_id=message_id,
                user_id=self.user_id,
                message__conversation_id=self.conversation_id
            )

            if status.read_at is not None:
                return None

            now = timezone.now()

            status.delivered_at = (
                status.delivered_at or now
            )

            status.read_at = now
            status.save(
                update_fields=[
                    "delivered_at",
                    "read_at"
                ]
            )

            read_at = status.read_at.isoformat()

            return {
                "event": "MESSAGE_READ",
                "message_id": status.message_id,
                "conversation_id": (
                    status.message.conversation_id
                ),
                "sender_id": (
                    status.message.sender_id
                ),
                "reader_id": self.user_id,
                "read_at": read_at
            }

        except MessageStatus.DoesNotExist:
            return None

    @database_sync_to_async
    def register_connection(self):
        return add_connection(self.user_id)

    @database_sync_to_async
    def unregister_connection(self):
        return remove_connection(
            self.user_id, self.connection_id
        )

    async def broadcast_user_online(self):
        await self.channel_layer.group_send(
            self.conversation_group,
            {
                "type": "presence_event",
                "event": "USER_ONLINE",
                "user_id": self.user_id
            }
        )

    async def broadcast_user_offline(self):
        await self.channel_layer.group_send(
            self.conversation_group,
            {
                "type": "presence_event",
                "event": "USER_OFFLINE",
                "user_id": self.user_id
            }
        )