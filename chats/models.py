from django.conf import settings
from django.db import models


class Conversation(models.Model):

    created_at = models.DateTimeField(
        auto_now_add=True
    )

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

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'conversation',
                    'user'
                ],
                name='unique_conversation_member'
            )
        ]

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"Conversation {self.conversation.id}"
        )


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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"Message {self.id} "
            f"by {self.sender.username}"
        )


class MessageStatus(models.Model):

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='statuses'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_statuses'
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'message',
                    'user'
                ],
                name='unique_message_user_status'
            )
        ]

    def __str__(self):

        return (
            f"Message {self.message.id} - "
            f"User {self.user.id}"
        )
        
class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=50,
        default='MESSAGE'
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'user',
                    'message',
                    'notification_type'
                ],
                name='unique_user_message_notification'
            )
        ]

    def __str__(self):

        return (
            f"Notification for "
            f"{self.user.username} - "
            f"Message {self.message.id}"
        )