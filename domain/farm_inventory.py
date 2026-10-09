from datetime import date
from typing import Dict, List, Tuple

from domain.errors import StockRejected
from domain.freshness import FreshnessPolicy
from domain.produce import Produce
from domain.value_objects import ProduceQuantity


class StockLot:
    """Entity inside FarmInventory. Identity is lot_id; available amount changes.

    The amount can only be lowered through reduce(), so a lot can never go below zero.
    """

    def __init__(
        self,
        lot_id: str,
        produce: Produce,
        available: float,
        harvest_date: date,
    ) -> None:
        if available < 0:
            raise ValueError("a stock lot cannot start with a negative amount")
        self.id = lot_id
        self.produce = produce
        self._available = available
        self.harvest_date = harvest_date

    @property
    def available(self) -> float:
        return self._available

    def reduce(self, amount: float) -> None:
        if amount < 0 or amount > self._available:
            raise StockRejected(f"lot {self.id} cannot give {amount}")
        self._available -= amount


class FarmInventory:
    """Aggregate B / root. Identity is inventory_id.

    Invariant: a lot never goes below zero; only fresh stock is reserved;
    reservation is all-or-nothing across every ordered line.
    """

    def __init__(self, inventory_id: str = "FARM-1") -> None:
        self.id = inventory_id
        self._lots: Dict[str, StockLot] = {}

    @property
    def lots(self) -> Tuple[StockLot, ...]:
        return tuple(self._lots.values())

    def lot(self, lot_id: str) -> StockLot:
        return self._lots[lot_id]

    def add_lot(self, lot: StockLot) -> None:
        self._lots[lot.id] = lot

    def stocks(self, produce: Produce) -> bool:
        """True when the inventory has at least one lot of this produce (any age)."""
        return any(lot.produce is produce for lot in self._lots.values())

    def reserve(
        self,
        order_id: str,
        items: Tuple[Tuple[Produce, ProduceQuantity], ...],
        on_date: date,
        policy: FreshnessPolicy,
    ) -> Tuple[Tuple[str, float], ...]:
        """Plan every line first. Change lots only if every line can be met."""
        plan: List[Tuple[StockLot, float]] = []
        for produce, quantity in items:
            still_needed = quantity.amount
            fresh_lots = sorted(
                (
                    lot
                    for lot in self._lots.values()
                    if lot.produce is produce
                    and lot.available > 0
                    and policy.is_fresh(produce, lot.harvest_date, on_date)
                ),
                key=lambda lot: lot.harvest_date,
            )
            for lot in fresh_lots:
                if still_needed <= 0:
                    break
                take = min(lot.available, still_needed)
                plan.append((lot, take))
                still_needed -= take
            if still_needed > 0:
                raise StockRejected(
                    f"not enough fresh {produce.catalog_name} for order {order_id}"
                )

        allocations = []
        for lot, take in plan:
            lot.reduce(take)
            allocations.append((lot.id, take))
        return tuple(allocations)
