import json
import os

from kafka import KafkaConsumer
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)

MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://localhost:27017/"
)

mongo_client = MongoClient(MONGO_URI)
mongo_database = mongo_client["chat_audit"]
events_collection = mongo_database["events"]
events_collection.create_index(
    [("event_id", ASCENDING)], unique=True
)


consumer = KafkaConsumer(
    "chat-events",
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="audit-group",
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    ),
    auto_offset_reset="earliest"
)

print("Audit Kafka Consumer Started...")
print(f"Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")


for kafka_message in consumer:
    event = kafka_message.value
    print("\nKafka Event Received:")
    print(event)

    event_id = event.get("event_id")

    if not event_id:
        print("Event does not contain event_id. Skipping.")
        continue
    try:
        result = events_collection.insert_one(event)
        print("Event stored in MongoDB")
        print(f"MongoDB Document ID: {result.inserted_id}")
        
    except DuplicateKeyError:
        print(f"Duplicate event ignored: {event_id}")