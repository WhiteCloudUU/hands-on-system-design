import threading


class OCCDatabase:
    def __init__(self):
        self._data = {}
        self._versions = {}
        self._lock = threading.Lock()

    def read(self, key):
        with self._lock:
            value = self._data.get(key)
            version = self._versions.get(key, 0)
            return value, version

    def write(self, key, new_value, expected_version):
        with self._lock:
            current_version = self._versions.get(key, 0)
            if current_version != expected_version:
                # Retry

                raise Exception(
                    f"Concurrency conflict: expected version {expected_version}, but found {current_version}"
                )

            self._data[key] = new_value
            self._versions[key] = current_version + 1

    def get_all(self):
        with self._lock:
            return dict(self._data)


db = OCCDatabase()
db.write("item1", "value1", 0)  # Initial write


# Simulated transaction
def transaction():
    thread = threading.current_thread()

    try:
        value, version = db.read("item1")
        print(f"[{thread.name}] Read value: {value} at version: {version}")

        updated_value = value + "_updated"  # Simulate some computation
        db.write("item1", updated_value, version)  # Try writing back
        print(f"[{thread.name}] Write successful")
    except Exception as e:
        print(f"[{thread.name}] Transaction failed:", e)


# Simulate concurrent transactions
t1 = threading.Thread(target=transaction)
t2 = threading.Thread(target=transaction)

t1.start()
t2.start()

t1.join()
t2.join()

thread = threading.current_thread()
print(f"[{thread.name}] Final DB state:", db.get_all())
