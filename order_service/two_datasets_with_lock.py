import threading
from dataclasses import dataclass, field
from typing import Dict, List
import uuid


@dataclass
class Item:
    name: str
    item_id: str
    quantity: int


@dataclass
class Inventory:
    # item_id -> quantity
    items: Dict[str, int] = field(default_factory=dict)
    # item_id -> Lock
    locks: Dict[str, threading.Lock] = field(default_factory=dict)

    def add_item(self, item_id: str, quantity: int):
        if item_id not in self.items:
            self.items[item_id] = 0
            self.locks[item_id] = threading.Lock()
        self.items[item_id] += quantity


@dataclass
class Order:
    id: int
    items: List[Item]


class OrderService:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory
        self.orders: List[Order] = []
        self.global_lock = threading.Lock()

    def place_order(self, items: List[Item]) -> Order:
        # Sort to avoid deadlocks
        item_ids = sorted(set(item.item_id for item in items))
        acquired_locks = []

        thread_name = threading.current_thread().name
        try:
            # Acquire locks in consistent order
            for item_id in item_ids:
                print(f"[{thread_name}] Trying to lock {item_id}")
                lock = self.inventory.locks[item_id]
                lock.acquire()
                acquired_locks.append(lock)
                print(f"[{thread_name}] Locked {item_id}")

            # Check stock
            for item in items:
                available = self.inventory.items.get(item.item_id, 0)
                if available < item.quantity:
                    print(
                        f"[{thread_name}] Insufficient stock for {item.item_id} (needed {item.quantity}, available {available})"
                    )
                    raise ValueError(f"Insufficient stock for item: {item.item_id}")

            # Record order
            with self.global_lock:
                order = Order(id=uuid.uuid4(), items=items)
                self.orders.append(order)
                print(f"[{thread_name}] Order {order.id} created")

            # Update inventory
            for item in items:
                self.inventory.items[item.item_id] -= item.quantity
                print(
                    f"[{thread_name}] Deducted {item.quantity} from {item.item_id} (new stock: {self.inventory.items[item.item_id]})"
                )

            return order

        finally:
            # Always release acquired locks
            for lock in reversed(acquired_locks):
                lock.release()


if __name__ == "__main__":
    import threading

    inventory = Inventory()
    inventory.add_item("fruit101", 10)
    inventory.add_item("fruit202", 5)

    service = OrderService(inventory)

    def worker():
        try:
            order = service.place_order([Item("apple", "fruit101", 5)])
            print(f"Order placed: {order}")
        except ValueError as e:
            print(f"Failed: {e}")

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("Final inventory:", inventory.items)
