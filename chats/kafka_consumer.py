import os
import sys
import json

import django
from kafka import KafkaConsumer


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from chats.models import (
    ConversationMember,
    Notification
)

from chats.redis_client import redis_client
from chats.tasks import send_notification

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)


consumer = KafkaConsumer(
    "chat-events",
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="notification-group",
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    ),
    auto_offset_reset="earliest"
)

print( "Notification Kafka Consumer Started..." )

print(
    f"Connected to Kafka: "
    f"{KAFKA_BOOTSTRAP_SERVERS}"
)


for kafka_message in consumer:
    event = kafka_message.value
    print( "\nKafka Event Received:" )

    print(event)

    if event.get("event") != "MESSAGE_SENT":
        continue

    conversation_id = event.get( "conversation_id" )
    sender_id = event.get( "sender_id" )
    message_id = event.get( "message_id" )

    members = ConversationMember.objects.filter(
        conversation_id=conversation_id
    ).exclude(
        user_id=sender_id
    )

    for member in members:
        receiver_id = member.user_id
        presence_key = (
            f"user:{receiver_id}:connections"
        )
        connection_count = redis_client.scard(presence_key)
        print(
            f"User {receiver_id} "
            f"connection count: "
            f"{connection_count}"
        )

        if connection_count > 0:
            print( f"User {receiver_id} is online." )
            print( "Persistent notification not required." )
            continue

        print( f"User {receiver_id} is offline." )

        try:
            notification, created = (
                Notification.objects.get_or_create(
                    user_id=receiver_id,
                    message_id=message_id,
                    notification_type="MESSAGE"
                )
            )

            if not created:
                print( "Notification already exists." )
                continue

            print(
                f"Notification created: "
                f"{notification.id}"
            )

            send_notification.delay(
                user_id=receiver_id, message_id=message_id
            )

            print(
                f"Celery notification task "
                f"created for User {receiver_id}"
            )

        except Exception as error:
            print(
                f"Notification creation failed: "
                f"{error}"
            )