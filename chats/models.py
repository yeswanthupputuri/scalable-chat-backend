from django.conf import settings
from django.db import models


class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id}"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='members'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['conversation', 'user'],
                name='unique_conversation_member'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - Conversation {self.conversation.id}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} by {self.sender.username}"


class MessageStatus(models.Model):
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='status'
    )

    delivered_at = models.DateTimeField(null=True, blank=True)

    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Status for Message {self.message.id}"