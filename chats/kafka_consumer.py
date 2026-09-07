import os
import sys
import json

import django

from kafka import KafkaConsumer


# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)


# ============================================================
# DJANGO SETUP
# ============================================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()


# ============================================================
# DJANGO IMPORTS
#
# Import Django models AFTER django.setup()
# ============================================================

from chats.models import ConversationMember
from chats.redis_client import redis_client
from chats.tasks import send_notification


# ============================================================
# KAFKA BOOTSTRAP SERVER
#
# Windows:
# localhost:9092
#
# Docker:
# kafka:9092
# ============================================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)


# ============================================================
# KAFKA CONSUMER
# ============================================================

consumer = KafkaConsumer(

    # Kafka Topic
    "chat-events",

    # Kafka Server
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,

    # Consumer Group
    group_id="notification-group",

    # Convert Kafka bytes → Python dictionary
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    ),

    # Read old messages if consumer group is new
    auto_offset_reset="earliest"
)


print(
    "Notification Kafka Consumer Started..."
)


# ============================================================
# PROCESS EVENTS
# ============================================================

for kafka_message in consumer:

    event = kafka_message.value


    # ========================================================
    # DISPLAY EVENT
    # ========================================================

    print("\nKafka Event Received:")

    print(event)


    # ========================================================
    # ONLY HANDLE MESSAGE_SENT
    # ========================================================

    if event.get("event") != "MESSAGE_SENT":

        continue


    # ========================================================
    # GET EVENT DATA
    # ========================================================

    conversation_id = event.get(
        "conversation_id"
    )

    sender_id = event.get(
        "sender_id"
    )

    message_id = event.get(
        "message_id"
    )


    # ========================================================
    # FIND CONVERSATION MEMBERS
    # ========================================================

    members = ConversationMember.objects.filter(

        conversation_id=conversation_id

    ).exclude(

        user_id=sender_id

    )


    # ========================================================
    # CHECK EACH RECEIVER
    # ========================================================

    for member in members:

        receiver_id = member.user_id


        # ====================================================
        # CHECK REDIS PRESENCE
        # ====================================================

        presence = redis_client.get(

            f"user:{receiver_id}:presence"

        )


        print(

            f"User {receiver_id} presence: {presence}"

        )


        # ====================================================
        # USER IS OFFLINE
        # ====================================================

        if presence != "online":

            print(

                f"User {receiver_id} is offline."

            )

            print(

                "Creating Celery notification task..."

            )


            # =================================================
            # CREATE CELERY TASK
            # =================================================

            send_notification.delay(

                user_id=receiver_id,

                message_id=message_id

            )


        # ====================================================
        # USER IS ONLINE
        # ====================================================

        else:

            print(

                f"User {receiver_id} is online."

            )

            print(

                "Notification not required."

            )