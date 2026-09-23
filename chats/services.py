# finds conversation and checks wether sender belongs to it , and saves the message.
# create messagestatus for every recipient, and publishes a MESSAGE_SENT event to kafka, and return created message.

import json
import os
import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from kafka import KafkaProducer

from .models import (
    Conversation,
    ConversationMember,
    Message,
    MessageStatus,
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
)


@transaction.atomic
def create_chat_message(
    *,
    conversation_id,
    sender,
    content,
):
    if not isinstance(content, str):
        raise ValidationError(
            "Message content must be a string."
        )

    content = content.strip()

    if not content:
        raise ValidationError(
            "Message content cannot be empty."
        )

    conversation = Conversation.objects.get(
        id=conversation_id
    )

    is_member = ConversationMember.objects.filter(
        conversation=conversation,
        user=sender
    ).exists()

    if not is_member:
        raise PermissionError(
            "You are not a member of this conversation."
        )

    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=content,
    )

    recipients = ConversationMember.objects.filter(
        conversation=conversation
    ).exclude(
        user=sender
    )

    for recipient in recipients:
        MessageStatus.objects.create(
            message=message,
            user=recipient.user,
        )

    event = {
        "event_id": str(uuid.uuid4()),
        "event": "MESSAGE_SENT",
        "message_id": message.id,
        "conversation_id": conversation.id,
        "sender_id": sender.id,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }

    producer.send(
        "chat-events",
        value=event
    )

    producer.flush()

    return message