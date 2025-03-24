import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn


app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])


async def data_generator():
    statuses = ["PENDING", "IN TRANSIT", "FINISHED"]

    while True:
        for status in statuses:
            yield {"data": {"status": status}}
            await asyncio.sleep(10)  # Wait 10 seconds before sending the next update


@app.get("/")
async def server_events():
    return EventSourceResponse(data_generator())


if __name__ == "__main__":
    server = uvicorn.Server(uvicorn.Config(app))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())
