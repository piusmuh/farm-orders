from typing import Any, Callable, Dict, List, Optional

from application.ports import EventPublisher, InventoryRepository, OrderRepository
from domain.farm_inventory import FarmInventory
from domain.produce_order import ProduceOrder


class InMemoryOrderRepository(OrderRepository):
    """Stores ProduceOrder aggregates keyed by order id."""

    def __init__(self) -> None:
        self._orders: Dict[str, ProduceOrder] = {}

    def get(self, order_id: str) -> Optional[ProduceOrder]:
        return self._orders.get(order_id)

    def save(self, order: ProduceOrder) -> None:
        self._orders[order.id] = order


class InMemoryInventoryRepository(InventoryRepository):
    """Stores the single FarmInventory aggregate used by this small domain."""

    def __init__(self) -> None:
        self._inventory: Optional[FarmInventory] = None

    def get(self) -> Optional[FarmInventory]:
        return self._inventory

    def save(self, inventory: FarmInventory) -> None:
        self._inventory = inventory


class InProcessEventBus(EventPublisher):
    """Simple in-process bus. No message broker."""

    def __init__(self) -> None:
        self._handlers: List[Callable[[Any], Any]] = []

    def subscribe(self, handler: Callable[[Any], Any]) -> None:
        self._handlers.append(handler)

    def publish(self, event: Any) -> list:
        return [handler(event) for handler in self._handlers]
