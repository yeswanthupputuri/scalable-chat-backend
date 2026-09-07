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
# MONGODB IMPORT
# ============================================================

from chats.mongodb_client import audit_events


# ============================================================
# KAFKA CONFIGURATION
#
# Local development:
#
# localhost:9092
#
# Later, when this consumer runs inside Docker:
#
# kafka:9092
#
# The environment variable allows us to switch between
# these without modifying the Python code.
# ============================================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)


# ============================================================
# KAFKA CONSUMER
#
# IMPORTANT:
#
# This consumer uses a DIFFERENT consumer group from the
# notification consumer.
#
# notification-group
#       |
#       └── Notification processing
#
# audit-group
#       |
#       └── MongoDB audit storage
#
# Because they use different consumer groups, BOTH consumers
# independently receive the same Kafka event.
# ============================================================

consumer = KafkaConsumer(

    # Kafka topic
    "chat-events",

    # Kafka server
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,

    # Separate consumer group
    group_id="audit-group",

    # Convert Kafka bytes → Python dictionary
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    ),

    # Read existing events when this consumer group is new
    auto_offset_reset="earliest"
)


print(
    "Audit Kafka Consumer Started..."
)

print(
    f"Connected to Kafka: "
    f"{KAFKA_BOOTSTRAP_SERVERS}"
)


# ============================================================
# PROCESS KAFKA EVENTS
# ============================================================

for kafka_message in consumer:
    event = kafka_message.value

    # DISPLAY EVENT
    print("\nKafka Event Received:")
    print(event)
    # STORE EVENT IN MONGODB : MongoDB stores the complete event dictionary.
    
    result = audit_events.insert_one( event )

    # ========================================================
    # CONFIRM STORAGE
    # ========================================================
    print( "Event stored in MongoDB" )
    print( f"MongoDB Document ID: " f"{result.inserted_id}" )