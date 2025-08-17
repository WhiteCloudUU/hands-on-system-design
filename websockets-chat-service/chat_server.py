import asyncio
import websockets
from redis_client import RedisPubSub

connected_users = {}  # user_id -> websocket
redis_pubsub = RedisPubSub()


async def handler(websocket, path):
    # Extracting user_id from websocket client
    user_id = path.strip("/")  # e.g., "/alice" in "ws://localhost:6789/alice"
    print(f"[Connected] {user_id}")

    # Save connection
    connected_users[user_id] = websocket

    # Subscribe to Redis channel
    async def on_message_from_redis(message):
        if user_id in connected_users:
            await connected_users[user_id].send(message)

    await redis_pubsub.subscribe(user_id, on_message_from_redis)

    try:
        async for message in websocket:
            print(f"[{user_id}] → {message}")
            # Simulate message format: "TO:recipient_id|Hello!"
            if message.startswith("TO:"):
                try:
                    meta, content = message.split("|", 1)
                    recipient_id = meta[3:]
                    await redis_pubsub.publish(
                        recipient_id, f"FROM:{user_id}|{content}"
                    )
                except ValueError:
                    await websocket.send("Invalid message format.")
    except websockets.exceptions.ConnectionClosed:
        print(f"[Disconnected] {user_id}")
    finally:
        connected_users.pop(user_id, None)


async def main():
    print("Chat server started on ws://localhost:6789")
    async with websockets.serve(handler, "localhost", 6789):
        await asyncio.Future()


asyncio.run(main())
