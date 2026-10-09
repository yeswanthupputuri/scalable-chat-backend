import os
import json
from kafka import KafkaProducer

# KAFKA BOOTSTRAP SERVER
# Windows: localhost:9092
# Docker: kafka:9092

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)

# KAFKA PRODUCER
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(
        value
    ).encode("utf-8")
)

def publish_event(event):
    producer.send(
        # Kafka Topic
        "chat-events", value=event
    )
    producer.flush()
    print(
        f"Kafka Event Published: {event}"
    )