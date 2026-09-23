from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from config.asgi import application

from .models import (
    Conversation,
    ConversationMember,
    Message,
)


User = get_user_model()


class ChatAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="testuser1",
            password="TestPassword123"
        )

        self.user2 = User.objects.create_user(
            username="testuser2",
            password="TestPassword123"
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_conversation_list_is_rejected(self):
        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_create_conversation(self):
        self.authenticate(self.user1)

        response = self.client.post(
            "/api/conversations/",
            {},
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        conversation = Conversation.objects.get(
            id=response.data["id"]
        )

        self.assertTrue(
            ConversationMember.objects.filter(
                conversation=conversation,
                user=self.user1
            ).exists()
        )

    def test_user_sees_only_their_conversations(self):
        conversation1 = Conversation.objects.create()
        conversation2 = Conversation.objects.create()

        ConversationMember.objects.create(
            conversation=conversation1,
            user=self.user1
        )

        ConversationMember.objects.create(
            conversation=conversation2,
            user=self.user2
        )

        self.authenticate(self.user1)

        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(response.status_code, 200)

        if isinstance(response.data, dict):
            conversations = response.data["results"]
        else:
            conversations = response.data

        returned_ids = [
            item["id"]
            for item in conversations
        ]

        self.assertIn(
            conversation1.id,
            returned_ids
        )

        self.assertNotIn(
            conversation2.id,
            returned_ids
        )

    def test_conversation_member_can_send_message(self):
        conversation = Conversation.objects.create()

        ConversationMember.objects.create(
            conversation=conversation,
            user=self.user1
        )

        self.authenticate(self.user1)

        response = self.client.post(
            f"/api/conversations/{conversation.id}/messages/send/",
            {
                "content": "Hello from automated test"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            Message.objects.filter(
                conversation=conversation,
                sender=self.user1,
                content="Hello from automated test"
            ).exists()
        )

    def test_empty_message_is_rejected(self):
        conversation = Conversation.objects.create()

        ConversationMember.objects.create(
            conversation=conversation,
            user=self.user1
        )

        self.authenticate(self.user1)

        response = self.client.post(
            f"/api/conversations/{conversation.id}/messages/send/",
            {
                "content": "   "
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_non_member_cannot_send_message(self):
        conversation = Conversation.objects.create()

        ConversationMember.objects.create(
            conversation=conversation,
            user=self.user1
        )

        self.authenticate(self.user2)

        response = self.client.post(
            f"/api/conversations/{conversation.id}/messages/send/",
            {
                "content": "Unauthorized message"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)


class ChatWebSocketTests(TransactionTestCase):

    reset_sequences = True

    async def test_authenticated_user_can_connect_to_conversation(self):
        user = await self.create_user()

        conversation = await self.create_conversation(user)

        access_token = await self.create_access_token(user)

        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{conversation.id}/?token={access_token}"
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.disconnect()

    @staticmethod
    @database_sync_to_async
    def create_user():
        return User.objects.create_user(
            username="websocketuser",
            password="TestPassword123"
        )

    @staticmethod
    @database_sync_to_async
    def create_conversation(user):
        conversation = Conversation.objects.create()

        ConversationMember.objects.create(
            conversation=conversation,
            user=user
        )

        return conversation

    @staticmethod
    @database_sync_to_async
    def create_access_token(user):
        refresh_token = RefreshToken.for_user(user)
        return str(refresh_token.access_token)