from datetime import date
from typing import Callable, Tuple

from application.dtos import AllocationOutput
from application.ports import InventoryRepository
from domain.errors import StockRejected
from domain.events import ProduceOrderConfirmed
from domain.freshness import FreshnessPolicy


class ReservationResult:
    def __init__(
        self,
        reserved: bool,
        allocations: Tuple[AllocationOutput, ...] = (),
        reason: str = "",
    ) -> None:
        self.reserved = reserved
        self.allocations = allocations
        self.reason = reason


class ReserveStockHandler:
    """Reacts to ProduceOrderConfirmed. Asks Aggregate B to reserve stock.

    Does not edit lot fields. Calls FarmInventory.reserve() only.
    """

    def __init__(
        self,
        inventories: InventoryRepository,
        policy: FreshnessPolicy,
        clock: Callable[[], date],
    ) -> None:
        self._inventories = inventories
        self._policy = policy
        self._clock = clock

    def handle(self, event: ProduceOrderConfirmed) -> ReservationResult:
        inventory = self._inventories.get()
        if inventory is None:
            return ReservationResult(False, reason="inventory missing at reservation time")
        try:
            raw = inventory.reserve(
                event.order_id,
                event.items,
                self._clock(),
                self._policy,
            )
        except StockRejected as error:
            return ReservationResult(False, reason=str(error))
        self._inventories.save(inventory)
        allocations = tuple(
            AllocationOutput(lot_id, amount) for lot_id, amount in raw
        )
        return ReservationResult(True, allocations=allocations)
