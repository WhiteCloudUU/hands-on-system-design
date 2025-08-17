import asyncio
import redis.asyncio as redis


class RedisPubSub:
    def __init__(self):
        self.redis = redis.Redis()
        self.subscribers = {}

    async def subscribe(self, user_id, message_handler):
        channel = f"user:{user_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        self.subscribers[user_id] = (pubsub, message_handler)

        async def reader():
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    await message_handler(msg["data"].decode())

        asyncio.create_task(reader())

    async def publish(self, user_id, message):
        channel = f"user:{user_id}"
        await self.redis.publish(channel, message)
