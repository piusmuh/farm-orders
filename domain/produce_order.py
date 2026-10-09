from enum import Enum
from typing import List, Tuple

from domain.errors import InvalidOrderLine, InvalidOrderState
from domain.events import ProduceOrderConfirmed
from domain.produce import Produce
from domain.value_objects import ProduceQuantity


class OrderStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class ProduceOrder:
    """Aggregate A / root. Identity is order_id (BR2).

    Invariant (BR3): at most MAX_LINES lines, the same produce cannot appear
    on two lines, and each line uses its produce's own unit. Callers add
    lines only through add_item().
    """

    MAX_LINES = 3

    def __init__(self, order_id: str, buyer: str) -> None:
        if not order_id:
            raise InvalidOrderState("order_id is required")
        self.id = order_id
        self.buyer = buyer
        self.status = OrderStatus.PENDING
        self._items: List[Tuple[Produce, ProduceQuantity]] = []
        self._events: List[ProduceOrderConfirmed] = []

    @property
    def items(self) -> Tuple[Tuple[Produce, ProduceQuantity], ...]:
        return tuple(self._items)

    def add_item(self, produce: Produce, quantity: ProduceQuantity) -> None:
        if self.status is not OrderStatus.PENDING:
            raise InvalidOrderState("items can only be added while the order is PENDING")
        if quantity.unit != produce.unit:
            raise InvalidOrderLine(
                f"{produce.catalog_name} must be ordered in {produce.unit}, got {quantity.unit}"
            )
        if len(self._items) >= self.MAX_LINES:
            raise InvalidOrderLine(
                f"an order may have at most {self.MAX_LINES} lines"
            )
        if any(existing is produce for existing, _ in self._items):
            raise InvalidOrderLine(
                f"{produce.catalog_name} is already on this order"
            )
        self._items.append((produce, quantity))

    def confirm(self) -> None:
        """BR2: PENDING -> CONFIRMED. Records ProduceOrderConfirmed (BR5)."""
        if self.status is not OrderStatus.PENDING:
            raise InvalidOrderState(
                f"only a PENDING order can be confirmed, current status is {self.status.value}"
            )
        if not self._items:
            raise InvalidOrderState("an order with no items cannot be confirmed")
        self.status = OrderStatus.CONFIRMED
        self._events.append(ProduceOrderConfirmed(self.id, self.items))

    def fulfil(self) -> None:
        """PENDING is never fulfilled directly; stock reservation must succeed first."""
        if self.status is not OrderStatus.CONFIRMED:
            raise InvalidOrderState(
                f"only a CONFIRMED order can be fulfilled, current status is {self.status.value}"
            )
        self.status = OrderStatus.FULFILLED

    def cancel(self) -> None:
        if self.status is OrderStatus.FULFILLED:
            raise InvalidOrderState("a fulfilled order cannot be cancelled")
        self.status = OrderStatus.CANCELLED

    def pull_events(self) -> Tuple[ProduceOrderConfirmed, ...]:
        events = tuple(self._events)
        self._events.clear()
        return events
