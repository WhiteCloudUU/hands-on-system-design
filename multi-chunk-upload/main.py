import hashlib
from flask import Flask, request, jsonify
from threading import Thread
import time

app = Flask(__name__)

"""
file metadata 举例
{
  '(fileId) 26fa...': {
    'status': 'uploaded',
    'chunks': {
        '1f4d...': 'uploaded', // chunkID: upload状态
        'a460...': 'uploaded'
    }
  }
}
"""
file_metadata_db = {}

"""
s3 storage 举例


{
    // chunkId: chunk内容
    '1f4d...': b'AAAAA....',  # 7MB of "A" 
    'a46...': b'BBBBB....'   # 6MB of "B"
}

"""
s3_storage = {}


def sha256(data: bytes) -> str:
    """
    Hash a file or a chunk into 64 bits hex string
    -) hashlib.sha256(data) creates a SHA-256 hash object.
    -) .hexdigest() returns the hash as a string of hexadecimal digits
        SHA-256, 256 bits = 32 bytes = 64 hex characters,
    """
    return hashlib.sha256(data).hexdigest()


def chunk_file(data: bytes, chunk_size=5 * 1024 * 1024):
    """
    把一个bytes object，按照 5MB 的大小进行chunk
    """
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


# ============================
# ==== Flask Backend API =====
# ============================


@app.route("/files/<file_id>", methods=["GET"])
def get_file_metadata(file_id):
    metadata = file_metadata_db.get(file_id)
    if metadata:
        return jsonify(metadata)
    else:
        return jsonify({"error": "not found"}), 404


@app.route("/files/presigned-url", methods=["POST"])
def get_presigned_url():
    """
    当client尝试upload 一个全新file时，返回一个S3 presigned_url
    client拿着这个presigned_url自助做upload

    POST
    {
        "fileId": ".."
        "chunkHashes": [..]
    }
    ->
    presigned_url
    """
    data = request.json
    file_id = data["fileId"]
    chunk_hashes = data["chunkHashes"]

    file_metadata_db[file_id] = {
        "status": "uploading",
        "chunks": {h: "not-uploaded" for h in chunk_hashes},
    }

    # Simulated presigned URL
    return jsonify({"uploadUrl": f"/s3-upload/{file_id}"})


@app.route("/s3-upload/<file_id>", methods=["POST"])
def upload_chunk(file_id):
    """
    Upload a single chunk to an existing file

    POST
    {
        chunk
    }
    """
    chunk = request.data
    chunk_hash = sha256(chunk)

    # Store chunk to "S3"
    s3_storage[chunk_hash] = chunk

    # Simulate S3 event notification
    Thread(target=s3_event_notification, args=(file_id, chunk_hash)).start()

    return jsonify({"message": "Chunk received"})


def s3_event_notification(file_id, chunk_hash):
    time.sleep(0.1)  # simulate the upload delay
    metadata = file_metadata_db.get(file_id)
    if metadata and chunk_hash in metadata["chunks"]:
        metadata["chunks"][chunk_hash] = "uploaded"

        if all(status == "uploaded" for status in metadata["chunks"].values()):
            metadata["status"] = "uploaded"
        print(f"[Backend] Chunk {chunk_hash} uploaded for file {file_id}")


# ============================
# ==== Client Simulation =====
# ============================
def simulate_client_upload():
    # 13MB bytes object; 模拟user的file
    file_content = b"A" * 7_000_000 + b"B" * 6_000_000
    file_id = sha256(file_content)
    print(f"[Client] File ID: {file_id}")

    chunks = chunk_file(
        file_content
    )  # 13MB object 将分成 5MB + 5MB + 3MB, 一共3个chunk
    chunk_hashes = [sha256(c) for c in chunks]
    print(f"[Client] Chunked the original file into {len(chunk_hashes)} chunks.")

    print("[Client] Checking if file exists...")
    resp = app.test_client().get(f"/files/{file_id}")
    if resp.status_code == 404:
        print("[Client] File not found. Requesting presigned URL...")
        # Request presigned URL
        presigned = (
            app.test_client()
            .post(
                "/files/presigned-url",
                json={"fileId": file_id, "chunkHashes": chunk_hashes},
            )
            .get_json()
        )
    else:
        print("[Client] File found. Resuming upload...")
        presigned = {"uploadUrl": f"/s3-upload/{file_id}"}

    # Upload chunks
    for i, chunk in enumerate(chunks):
        print(f"[Client] Uploading chunk {i + 1}/{len(chunks)}")
        app.test_client().post(presigned["uploadUrl"], data=chunk)

    # Wait here until all chunks are uploaded
    while True:
        time.sleep(0.2)
        final_meta = file_metadata_db[file_id]
        if final_meta["status"] == "uploaded":
            print("[Client] Upload complete!")
            break


# ============================
# ==== Run the simulation ====
# ============================
if __name__ == "__main__":
    # Run Flask in a thread
    thread = Thread(target=lambda: app.run(port=5000, use_reloader=False))
    thread.daemon = True
    thread.start()

    time.sleep(1)
    simulate_client_upload()
