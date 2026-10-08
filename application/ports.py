from abc import ABC, abstractmethod
from typing import Any, Optional

from domain.farm_inventory import FarmInventory
from domain.produce_order import ProduceOrder


class OrderRepository(ABC):
    @abstractmethod
    def get(self, order_id: str) -> Optional[ProduceOrder]:
        raise NotImplementedError

    @abstractmethod
    def save(self, order: ProduceOrder) -> None:
        raise NotImplementedError


class InventoryRepository(ABC):
    @abstractmethod
    def get(self) -> Optional[FarmInventory]:
        raise NotImplementedError

    @abstractmethod
    def save(self, inventory: FarmInventory) -> None:
        raise NotImplementedError


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: Any) -> list:
        raise NotImplementedError
