from application.dtos import (
    OUTCOME_AWAITING_STOCK,
    OUTCOME_FULFILLED,
    PlaceOrderInput,
    PlaceOrderOutput,
)
from application.errors import InventoryNotFound, ProduceNotStocked
from application.ports import EventPublisher, InventoryRepository, OrderRepository
from domain.produce import Produce
from domain.produce_order import ProduceOrder
from domain.value_objects import ProduceQuantity


class PlaceOrderService:
    """Main use case: place and confirm a produce order.

    Coordinates lookup, domain operations, event publication and save.
    Business rules live in the domain, not here.
    Repositories and the event publisher are injected (dependency injection).
    """

    def __init__(
        self,
        orders: OrderRepository,
        inventories: InventoryRepository,
        events: EventPublisher,
    ) -> None:
        self._orders = orders
        self._inventories = inventories
        self._events = events

    def execute(self, data: PlaceOrderInput) -> PlaceOrderOutput:
        inventory = self._inventories.get()
        if inventory is None:
            raise InventoryNotFound("farm inventory was not found")

        order = ProduceOrder(data.order_id, data.buyer)
        for line in data.items:
            try:
                produce = Produce.from_name(line.produce_name)
            except KeyError as exc:
                raise ProduceNotStocked(line.produce_name) from exc
            if not inventory.stocks(produce):
                raise ProduceNotStocked(line.produce_name)
            quantity = ProduceQuantity(line.amount, produce.unit)
            order.add_item(produce, quantity)

        order.confirm()

        results = []
        for event in order.pull_events():
            results.extend(self._events.publish(event))

        reserved = any(getattr(result, "reserved", False) for result in results)
        allocations = ()
        if reserved:
            order.fulfil()
            for result in results:
                if getattr(result, "reserved", False):
                    allocations = result.allocations
                    break

        self._orders.save(order)
        return PlaceOrderOutput(
            order_id=order.id,
            status=order.status.value,
            outcome=OUTCOME_FULFILLED if reserved else OUTCOME_AWAITING_STOCK,
            allocations=allocations,
        )
