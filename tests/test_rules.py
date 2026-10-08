"""T1-T8: one automated test per required identifier."""

from datetime import date, timedelta

import pytest

from application.dtos import OrderLineInput, PlaceOrderInput
from application.errors import InventoryNotFound, ProduceNotStocked
from application.handlers import ReserveStockHandler
from application.services import PlaceOrderService
from domain.errors import InvalidOrderLine, InvalidOrderState, InvalidQuantity
from domain.events import ProduceOrderConfirmed
from domain.farm_inventory import FarmInventory, StockLot
from domain.freshness import FreshnessPolicy
from domain.produce import Produce
from domain.produce_order import OrderStatus, ProduceOrder
from domain.value_objects import ProduceQuantity
from infrastructure.in_memory import (
    InMemoryInventoryRepository,
    InMemoryOrderRepository,
    InProcessEventBus,
)

FIXED_TODAY = date(2026, 10, 10)


def test_T1_produce_quantity_accepts_valid_values_and_rejects_invalid_ones():
    # boundary: exactly 5,000 is accepted
    valid = ProduceQuantity(100, "kg")
    boundary = ProduceQuantity(5000, "kg")
    assert valid.amount == 100
    assert valid.unit == "kg"
    assert boundary.amount == 5000
    assert ProduceQuantity(100, "kg") == ProduceQuantity(100, "kg")

    # three rejections
    with pytest.raises(InvalidQuantity):
        ProduceQuantity(0, "kg")
    with pytest.raises(InvalidQuantity):
        ProduceQuantity(5000.01, "kg")
    with pytest.raises(InvalidQuantity):
        ProduceQuantity(10, "bag")


def test_T2_order_confirms_from_pending_and_rejects_illegal_transitions():
    order = ProduceOrder("O1", "B001")
    order.add_item(Produce.MAIZE, ProduceQuantity(100, "kg"))
    order.confirm()
    assert order.status is OrderStatus.CONFIRMED

    with pytest.raises(InvalidOrderState):
        order.confirm()
    assert order.status is OrderStatus.CONFIRMED

    empty = ProduceOrder("O2", "B001")
    with pytest.raises(InvalidOrderState):
        empty.confirm()
    assert empty.status is OrderStatus.PENDING


def test_T3_order_allows_three_lines_and_rejects_fourth_or_duplicate_produce():
    order = ProduceOrder("O1", "B001")
    order.add_item(Produce.MAIZE, ProduceQuantity(10, "kg"))
    order.add_item(Produce.BEANS, ProduceQuantity(10, "kg"))
    order.add_item(Produce.EGGS, ProduceQuantity(1, "tray"))
    assert len(order.items) == 3

    with pytest.raises(InvalidOrderLine):
        order.add_item(Produce.MILK, ProduceQuantity(1, "litre"))
    assert len(order.items) == 3

    duplicate = ProduceOrder("O2", "B001")
    duplicate.add_item(Produce.MAIZE, ProduceQuantity(10, "kg"))
    with pytest.raises(InvalidOrderLine):
        duplicate.add_item(Produce.MAIZE, ProduceQuantity(5, "kg"))
    assert len(duplicate.items) == 1


def test_T4_freshness_is_inclusive_on_the_last_day():
    policy = FreshnessPolicy()
    harvest = FIXED_TODAY

    assert policy.is_fresh(Produce.TOMATOES, harvest - timedelta(days=7), FIXED_TODAY) is True
    assert policy.is_fresh(Produce.TOMATOES, harvest - timedelta(days=8), FIXED_TODAY) is False
    assert policy.is_fresh(Produce.MILK, harvest - timedelta(days=2), FIXED_TODAY) is True
    assert policy.is_fresh(Produce.MILK, harvest - timedelta(days=3), FIXED_TODAY) is False


def test_T5_confirming_raises_exactly_one_produce_order_confirmed_event():
    order = ProduceOrder("O1", "B001")
    qty = ProduceQuantity(120, "kg")
    order.add_item(Produce.MAIZE, qty)
    order.confirm()

    events = order.pull_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, ProduceOrderConfirmed)
    assert event.order_id == "O1"
    assert event.items == ((Produce.MAIZE, qty),)
    assert order.pull_events() == ()


def _wired_service(inventory: FarmInventory | None):
    orders = InMemoryOrderRepository()
    inventories = InMemoryInventoryRepository()
    if inventory is not None:
        inventories.save(inventory)
    events = InProcessEventBus()
    handler = ReserveStockHandler(
        inventories,
        FreshnessPolicy(),
        clock=lambda: FIXED_TODAY,
    )
    events.subscribe(handler.handle)
    service = PlaceOrderService(orders, inventories, events)
    return service, orders, inventories


def test_T6_unknown_produce_or_missing_inventory_is_rejected_and_nothing_is_saved():
    inventory = FarmInventory("FARM-1")
    inventory.add_lot(StockLot("A", Produce.MAIZE, 50, date(2026, 4, 13)))
    service, orders, _inventories = _wired_service(inventory)

    with pytest.raises(ProduceNotStocked):
        service.execute(
            PlaceOrderInput(
                order_id="O9",
                buyer="B001",
                items=(OrderLineInput("TOMATOES", 1),),
            )
        )
    assert orders.get("O9") is None

    service_missing, orders_missing, _ = _wired_service(None)
    with pytest.raises(InventoryNotFound):
        service_missing.execute(
            PlaceOrderInput(
                order_id="O10",
                buyer="B001",
                items=(OrderLineInput("MAIZE", 1),),
            )
        )
    assert orders_missing.get("O10") is None


def test_T7_confirmed_order_is_fulfilled_and_oldest_fresh_lots_are_used_first():
    inventory = FarmInventory("FARM-1")
    # 13 Apr 2026 is exactly 180 days before 10 Oct 2026 (maize last fresh day).
    inventory.add_lot(StockLot("A", Produce.MAIZE, 100, date(2026, 4, 13)))
    inventory.add_lot(StockLot("B", Produce.MAIZE, 100, date(2026, 9, 1)))
    inventory.add_lot(StockLot("M", Produce.MILK, 20, date(2026, 10, 9)))
    service, orders, inventories = _wired_service(inventory)

    output = service.execute(
        PlaceOrderInput(
            order_id="O1",
            buyer="B001",
            items=(
                OrderLineInput("MAIZE", 120),
                OrderLineInput("MILK", 10),
            ),
        )
    )

    assert output.status == "FULFILLED"
    assert output.outcome == "FULFILLED"
    assert [(a.lot_id, a.amount) for a in output.allocations] == [
        ("A", 100),
        ("B", 20),
        ("M", 10),
    ]
    stored = orders.get("O1")
    assert stored.status is OrderStatus.FULFILLED
    remaining = inventories.get()
    assert remaining.lot("A").available == 0
    assert remaining.lot("B").available == 80
    assert remaining.lot("M").available == 10


def test_T8_stale_stock_is_rejected_order_stays_confirmed_and_lots_are_unchanged():
    inventory = FarmInventory("FARM-1")
    inventory.add_lot(StockLot("T", Produce.TOMATOES, 30, date(2026, 9, 1)))
    service, orders, inventories = _wired_service(inventory)

    output = service.execute(
        PlaceOrderInput(
            order_id="O2",
            buyer="B002",
            items=(OrderLineInput("TOMATOES", 10),),
        )
    )

    assert output.status == "CONFIRMED"
    assert output.outcome == "AWAITING_STOCK"
    assert output.allocations == ()
    assert orders.get("O2").status is OrderStatus.CONFIRMED
    assert inventories.get().lot("T").available == 30
