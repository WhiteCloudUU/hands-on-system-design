import hashlib
import bisect


class ConsistentHashing:
    def __init__(self, num_points=100):
        self.num_points = num_points
        self.ring = []
        self.nodes = {}

    def _hash(self, key):
        """Hashes a key using SHA-256 and maps it onto the ring."""
        return int(hashlib.sha256(key.encode()).hexdigest(), 16) % self.num_points

    def add_node(self, node, node_name):
        """Add a node (e.g. DB instance) to the hash ring."""
        """ node is just a value/point in the hash ring """
        bisect.insort(
            self.ring, node
        )  # inserts an element into a sorted list, O(nlogn)
        self.nodes[node] = node_name

    def remove_node(self, node):
        """Removes a node from the hash ring."""
        if node in self.nodes:
            self.ring.remove(node)
            del self.nodes[node]

    def get_node(self, key):
        """Finds the node responsible for a given key."""
        hash_value = self._hash(str(key))
        print(f"Key '{key}' is hashed to {hash_value}. ")

        # Find the insertion index -> 给 hash_value 找插入位置
        # e.g. ring = [10, 25, 50, 75], hash_value = 30, idx 将返回 2，表示 30 将会顺时针map到 处于50位置上 的node

        # The % operator ensures that if hash_value > max(self.ring), idx will be 0
        idx = bisect.bisect(self.ring, hash_value) % len(self.ring)

        node = self.ring[idx]

        return self.nodes[node]


# Example Usage
ch = ConsistentHashing()
databases = ["DB1", "DB2", "DB3", "DB4"]

# Put 4 DB instances at position 0, 25, 50, and 75 of the ring.
for i, db in enumerate(databases):
    ch.add_node(i * 25, db)

print("Hash ring: ", ch.ring)
print("Nodes map: ", ch.nodes)

# Get the node for a given event
event_id = "event123"
assigned_db = ch.get_node(event_id)
print(f"Event '{event_id}' is assigned to database at position {assigned_db}")
