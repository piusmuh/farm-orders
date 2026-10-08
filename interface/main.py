"""Composition root: builds in-memory stores, injects them, runs the two connected use cases."""

from datetime import date

from application.dtos import OrderLineInput, PlaceOrderInput
from application.handlers import ReserveStockHandler
from application.services import PlaceOrderService
from domain.farm_inventory import FarmInventory, StockLot
from domain.freshness import FreshnessPolicy
from domain.produce import Produce
from infrastructure.in_memory import (
    InMemoryInventoryRepository,
    InMemoryOrderRepository,
    InProcessEventBus,
)

DEMO_DATE = date(2026, 10, 10)


def seed_inventory() -> FarmInventory:
    inventory = FarmInventory("FARM-1")
    inventory.add_lot(StockLot("A", Produce.MAIZE, 100, date(2026, 4, 13)))
    inventory.add_lot(StockLot("B", Produce.MAIZE, 100, date(2026, 9, 1)))
    inventory.add_lot(StockLot("M", Produce.MILK, 20, date(2026, 10, 9)))
    inventory.add_lot(StockLot("T", Produce.TOMATOES, 30, date(2026, 9, 1)))
    return inventory


def build_app(inventory: FarmInventory | None = None):
    orders = InMemoryOrderRepository()
    inventories = InMemoryInventoryRepository()
    if inventory is not None:
        inventories.save(inventory)
    policy = FreshnessPolicy()
    events = InProcessEventBus()
    handler = ReserveStockHandler(inventories, policy, clock=lambda: DEMO_DATE)
    events.subscribe(handler.handle)
    service = PlaceOrderService(orders, inventories, events)
    return service, orders, inventories


def main() -> None:
    service, _orders, inventories = build_app(seed_inventory())

    print("=== Use case 1 + 2 (connected by ProduceOrderConfirmed) ===")
    print("Place/confirm order O1: 120 kg maize and 10 litre milk")
    success = service.execute(
        PlaceOrderInput(
            order_id="O1",
            buyer="B001",
            items=(
                OrderLineInput("MAIZE", 120),
                OrderLineInput("MILK", 10),
            ),
        )
    )
    print(
        f"  status={success.status} outcome={success.outcome} "
        f"allocations={[(a.lot_id, a.amount) for a in success.allocations]}"
    )
    inventory = inventories.get()
    print(
        "  remaining lots:",
        [(lot.id, lot.produce.catalog_name, lot.available) for lot in inventory.lots],
    )

    print()
    print("Order O2: 10 kg tomatoes (only stale lot T exists)")
    waiting = service.execute(
        PlaceOrderInput(
            order_id="O2",
            buyer="B002",
            items=(OrderLineInput("TOMATOES", 10),),
        )
    )
    print(f"  status={waiting.status} outcome={waiting.outcome}")
    print(f"  tomato lot T still {inventory.lot('T').available} kg")


if __name__ == "__main__":
    main()
