import os
import json

from kafka import KafkaProducer


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
# KAFKA PRODUCER
# ============================================================

producer = KafkaProducer(

    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,

    # Convert Python dictionary → JSON bytes
    value_serializer=lambda value: json.dumps(
        value
    ).encode("utf-8")
)


# ============================================================
# PUBLISH EVENT
# ============================================================

def publish_event(event):

    """
    Publish an event to Kafka.
    """

    producer.send(

        # Kafka Topic
        "chat-events",

        # Event data
        value=event
    )


    # Ensure event is sent
    producer.flush()


    print(
        f"Kafka Event Published: {event}"
    )