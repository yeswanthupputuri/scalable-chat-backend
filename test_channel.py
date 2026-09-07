import asyncio

from channels_redis.core import RedisChannelLayer


async def test():
    layer = RedisChannelLayer(
        hosts=[
            ("127.0.0.1", 6379)
        ]
    )

    await layer.send(
        "test_channel",
        {
            "type": "test.message",
            "message": "hello"
        }
    )

    print("Message sent successfully")

    message = await layer.receive("test_channel")

    print("Message received:")
    print(message)

asyncio.run(test())