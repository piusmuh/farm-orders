"""Domain errors raised when a business rule is violated."""


class DomainError(Exception):
    """Base type for domain rule violations."""


class InvalidQuantity(DomainError):
    """BR1: ProduceQuantity rejected an invalid amount or unit."""


class InvalidOrderState(DomainError):
    """BR2: ProduceOrder refused an illegal status change."""


class InvalidOrderLine(DomainError):
    """BR3: adding a line would break the ProduceOrder invariant."""


class StockRejected(DomainError):
    """Aggregate B refused to reserve stock (freshness / available quantity)."""
