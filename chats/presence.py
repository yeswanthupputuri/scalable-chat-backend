import uuid

from .redis_client import redis_client


def get_presence_key(user_id):
    return f"user:{user_id}:connections"


def add_connection(user_id):
    connection_id = str(uuid.uuid4())
    presence_key = get_presence_key(user_id)
    was_offline = redis_client.scard(presence_key) == 0
    redis_client.sadd(
        presence_key,
        connection_id
    )

    return {
        "connection_id": connection_id,
        "was_offline": was_offline,
    }


def remove_connection(user_id, connection_id):
    presence_key = get_presence_key(user_id)

    redis_client.srem(
        presence_key,
        connection_id
    )

    remaining_connections = redis_client.scard(
        presence_key
    )

    if remaining_connections == 0:
        redis_client.delete(presence_key)

    return remaining_connections


def is_user_online(user_id):
    presence_key = get_presence_key(user_id)

    return redis_client.scard(presence_key) > 0


def get_connection_count(user_id):
    presence_key = get_presence_key(user_id)

    return redis_client.scard(presence_key)