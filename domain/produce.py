from enum import Enum


class Produce(Enum):
    """Reference data for marketable farm produce.

    Each member value includes the name so members with the same unit and
    shelf life (Maize and Beans) do not become Enum aliases of each other.
    """

    MAIZE = ("MAIZE", "kg", 180)
    BEANS = ("BEANS", "kg", 180)
    TOMATOES = ("TOMATOES", "kg", 7)
    MILK = ("MILK", "litre", 2)
    EGGS = ("EGGS", "tray", 21)

    @property
    def catalog_name(self) -> str:
        return self.value[0]

    @property
    def unit(self) -> str:
        return self.value[1]

    @property
    def shelf_life_days(self) -> int:
        return self.value[2]

    @classmethod
    def from_name(cls, name: str) -> "Produce":
        key = name.strip().upper()
        try:
            return cls[key]
        except KeyError as exc:
            raise KeyError(f"unknown produce {name!r}") from exc
