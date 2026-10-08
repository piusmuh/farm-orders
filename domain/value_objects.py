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
        if not (0 < self.amount <= self.MAX_AMOUNT):
            raise InvalidQuantity(
                f"quantity must be above 0 and at most {self.MAX_AMOUNT}, got {self.amount}"
            )
        if self.unit not in self.SUPPORTED_UNITS:
            raise InvalidQuantity(
                f"unit must be one of {self.SUPPORTED_UNITS}, got {self.unit!r}"
            )
