from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class OrderLineInput:
    produce_name: str
    amount: float


@dataclass(frozen=True)
class PlaceOrderInput:
    order_id: str
    buyer: str
    items: Tuple[OrderLineInput, ...]


@dataclass(frozen=True)
class AllocationOutput:
    lot_id: str
    amount: float


@dataclass(frozen=True)
class PlaceOrderOutput:
    order_id: str
    status: str
    outcome: str
    allocations: Tuple[AllocationOutput, ...]


OUTCOME_FULFILLED = "FULFILLED"
OUTCOME_AWAITING_STOCK = "AWAITING_STOCK"
