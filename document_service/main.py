from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from hashlib import sha256
from typing import Dict, List
import uvicorn
from collections import defaultdict

# Simulated list of server addresses (normally IP:port)
SERVER_ADDRESSES = ["server1", "server2", "server3"]


class HashRing:
    def __init__(self, servers: List[str]):
        self.servers = sorted(servers)

    def get_server(self, doc_id: str) -> str:
        doc_hash = int(sha256(doc_id.encode()).hexdigest(), 16)
        index = doc_hash % len(self.servers)
        print(
            f"[HashRing] Doc '{doc_id}' should be mapped to server '{self.servers[index]}'."
        )
        return self.servers[index]


class DocumentServer:
    def __init__(self, server: str, hash_ring: HashRing):
        self._server = server
        self._hash_ring = hash_ring
        self._app = FastAPI()

        self.doc_sockets: Dict[str, List[WebSocket]] = defaultdict(
            list
        )  # doc_id -> websocket
        self.loaded_docs: Dict[str, bool] = {}  # track which docs are loaded

        self._app.get("/connect/{doc_id}")(self.http_connect)
        self._app.websocket("/ws/{doc_id}")(self.ws_connect)

    async def http_connect(self, doc_id: str):
        target_server = self._hash_ring.get_server(doc_id)
        if target_server != self._server:
            print(f"[{self._server}] Redirecting doc {doc_id} to {target_server}")
            return RedirectResponse(url=f"http://{target_server}:8000/connect/{doc_id}")

        print(f"[{self._server}] Handling doc {doc_id} locally")
        return {"message": f"Connect to websocket at /ws/{doc_id}"}

    async def ws_connect(self, websocket: WebSocket, doc_id: str):
        await websocket.accept()
        self.doc_sockets[doc_id].append(websocket)
        print(f"[{self._server}] WebSocket connected for doc {doc_id}")

        if doc_id not in self.loaded_docs:
            self.load_document_operations(doc_id)

        try:
            while True:
                data = await websocket.receive_text()
                print(f"[{self._server}] Received op for doc {doc_id}: {data}")

                await self.broadcast_to_others(doc_id, sender=websocket, message=data)
        except WebSocketDisconnect:
            print(f"[{self.address}] WebSocket disconnected for doc {doc_id}")
            self.doc_connections[doc_id].remove(websocket)

    def load_document_operations(self, doc_id: str):
        print(f"[{self._server}] Loading stored ops for doc {doc_id}...")
        # Simulate DB load delay
        self.loaded_docs[doc_id] = True

    async def broadcast_to_others(self, doc_id: str, sender: WebSocket, message: str):
        for connection in self.doc_sockets[doc_id]:
            if connection != sender:
                try:
                    await connection.send_text(message)
                except:
                    pass  # optionally log or handle closed connection


# Simulate running on server2
if __name__ == "__main__":
    hash_ring = HashRing(SERVER_ADDRESSES)
    server = DocumentServer("server2", hash_ring)

    uvicorn.run(server._app, host="0.0.0.0", port=8000)
