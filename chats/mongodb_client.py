import os
from pymongo import MongoClient

# ============================================================
# MONGODB URI
#
# Windows:
# mongodb://localhost:27017/
#
# Docker:
# mongodb://mongodb:27017/
# ============================================================
MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://localhost:27017/"
)

# ============================================================
# MONGODB CONNECTION
# ============================================================
mongo_client = MongoClient( MONGO_URI )

# ============================================================
# DATABASE
# ============================================================
db = mongo_client[ "chat_backend" ]

# ============================================================
# COLLECTION
# ============================================================
audit_events = db[ "audit_events" ]