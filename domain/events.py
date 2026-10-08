from dataclasses import dataclass
from typing import Tuple

from domain.produce import Produce
from domain.value_objects import ProduceQuantity


@dataclass(frozen=True)
class ProduceOrderConfirmed:
    """BR5 Domain Event: a past-tense fact that an order was confirmed.

    Immutable. Carries only what FarmInventory needs to attempt reservation.
    """

    order_id: str
    items: Tuple[Tuple[Produce, ProduceQuantity], ...]
