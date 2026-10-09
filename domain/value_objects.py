from dataclasses import dataclass

from domain.errors import InvalidQuantity


@dataclass(frozen=True)
class ProduceQuantity:
    """BR1 Value Object. Compared by value; has no identity of its own.

    100 kg is 100 kg wherever it appears, so two instances with the same
    amount and unit are equal. Validation lives here so an invalid quantity
    never enters the domain.
    """

    amount: float
    unit: str

    MAX_AMOUNT = 5000
    SUPPORTED_UNITS = ("kg", "litre", "tray")

    def __post_init__(self) -> None:
        pass