"""Application-level lookup failures (BR6)."""


class InventoryNotFound(Exception):
    """BR6: the farm inventory aggregate was not in the repository."""


class ProduceNotStocked(Exception):
    """BR6: an ordered produce has no lot in the loaded inventory."""
