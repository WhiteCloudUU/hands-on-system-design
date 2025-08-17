from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import uuid


@dataclass
class Item:
    id: str
    name: str
    quantity: int


@dataclass
class Inventory:
    items: Dict[Tuple[str, str], int] = field(
        default_factory=dict
    )  # item name, id -> quantity


@dataclass
class Order:
    id: int
    items: List[Item]


class OrderService:
    def __init__(self, inventory: Inventory):
        self._inventory = inventory
        self._orders: List[Order] = []

    def in_stock(self, item: Item) -> bool:
        return self._inventory.items.get((item.id, item.name), 0) >= item.quantity

    def update_stock(self, item: Item):
        if not self.in_stock(item):
            raise ValueError(f"Insufficient stock for item: {item.name}")

        self._inventory.items[(item.id, item.name)] -= item.quantity

    def place_order(self, items: List[Item]) -> Order:
        for item in items:
            if not self.in_stock(item):
                raise ValueError(f"Insufficient stock for item: {item.name}")

        order = Order(id=uuid.uuid4(), items=items)
        self._orders.append(order)

        # Update inventory
        for item in items:
            self.update_stock(item)

        return order


if __name__ == "__main__":
    inventory = Inventory()
    inventory.items[("fruit1", "apple")] = 10
    inventory.items[("fruit2", "banana")] = 5

    order_service = OrderService(inventory)

    order = order_service.place_order(
        [Item("fruit1", "apple", 3), Item("fruit2", "banana", 2)]
    )

    print(order)
    print(inventory)
