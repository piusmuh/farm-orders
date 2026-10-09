# Farm Produce Order & Fulfilment (CSC 3115 coursework)

Small DDD / TDD / Clean Architecture project. Two connected use cases, in-memory persistence, no web interface and no database:

1. **Place and confirm a produce order** (`PlaceOrderService` -> Aggregate A `ProduceOrder`)
2. **Reserve fresh stock** (`ReserveStockHandler` -> Aggregate B `FarmInventory`)

They are linked by one domain event, **`ProduceOrderConfirmed`**.

AI use: Cursor (Grok 4.6) helped implement the code from the group's design guide; Claude (Anthropic) helped draft that guide and the report. The group can explain every rule, class and test.

## How to run

Python 3.10 or later is required.

```text
python -m pip install -r requirements.txt
python -m pytest -v
python check_layers.py
python -m interface.main
```

- `python -m pytest -v` runs the eight tests T1-T8.
- `python check_layers.py` checks that imports only point inward.
- `python -m interface.main` runs a demonstration of both use cases.

On Windows, `run_tests.bat`, `run_layers.bat` and `run_demo.bat` run the same commands, and `make_evidence.bat` saves their output to `evidence/`.

## The six business rules

| Rule | Statement | Enforced by | If broken |
|------|-----------|-------------|-----------|
| BR1 | A produce quantity must be above 0 and at most 5,000, in a supported unit (`kg`, `litre` or `tray`). | `ProduceQuantity` | `InvalidQuantity`. No object is created. |
| BR2 | An order moves PENDING -> CONFIRMED -> FULFILLED. It cannot be confirmed twice, when it has no items, or after cancellation, and it cannot be fulfilled before it is confirmed. | `ProduceOrder.confirm()` and `fulfil()` | `InvalidOrderState`. Status unchanged. |
| BR3 | An order has at most 3 lines, the same produce cannot appear on two lines, and each line uses its produce's own unit. | `ProduceOrder.add_item()` | `InvalidOrderLine`. The order is unchanged. |
| BR4 | A stock lot can be used for a produce only if its age since harvest is within that produce's shelf life. The last day still counts. | `FreshnessPolicy.is_fresh()` | The lot is skipped. If too little fresh stock remains, Aggregate B rejects. |
| BR5 | When an order is confirmed, the inventory must be asked to reserve the ordered stock. | `ProduceOrderConfirmed` + `ReserveStockHandler` | If the inventory rejects, the order stays CONFIRMED and the outcome is `AWAITING_STOCK`. |
| BR6 | Before an order is confirmed, the farm inventory must exist and every ordered produce must be stocked there. | `InventoryRepository` + `PlaceOrderService` | `InventoryNotFound` or `ProduceNotStocked`. Nothing is saved. |

FULFILLED means all ordered stock has been reserved. Delivery is out of scope. AWAITING_STOCK means the confirmation was valid but Aggregate B refused the reservation; the order is not rolled back to PENDING.

## Tests T1-T8

| Test | Checks |
|------|--------|
| T1 | 100 kg valid; 5,000 accepted; 0, 5,000.01 and unit `bag` rejected |
| T2 | Pending order with an item confirms; confirming twice, an empty order, a cancelled order, and fulfilling before confirming are rejected |
| T3 | Three lines allowed; a fourth produce, the same produce twice, and a wrong unit are rejected |
| T4 | Tomatoes 7 days fresh, 8 stale; milk 2 days fresh, 3 stale |
| T5 | Confirming raises exactly one `ProduceOrderConfirmed`, then the list is empty |
| T6 | Unstocked produce and missing inventory are rejected; nothing is saved |
| T7 | 120 kg maize + 10 litre milk: event handled, oldest lots first, order FULFILLED |
| T8 | Only stale tomatoes: inventory rejects, order stays CONFIRMED, lot unchanged |

Tests use the fixed date 10 October 2026, so freshness never depends on the real clock.

## Structure

```text
domain/           entities, value object, domain service, domain event, rules
application/      PlaceOrderService, DTOs, repository abstractions, event handler
infrastructure/   in-memory repositories and in-process event bus
interface/        main.py (composition root: builds objects and injects them)
tests/            test_rules.py (T1-T8)
evidence/         saved test output (TDD red and green, final run, layer check, demo)
```

Dependency rule: Domain imports nothing outside Domain. Application imports Domain. Infrastructure imports Application and Domain. Interface imports all three. No Factory and no Layer Supertype are used (reasons are in the report).

## Evidence files

| File | What it shows |
|------|---------------|
| `tdd_red.txt` | T1 failing before quantity validation existed |
| `tdd_green.txt` | T1 passing after validation was added to `ProduceQuantity.__post_init__` |
| `final_run.txt` | All 8 tests passing |
| `layers_check.txt` | Dependencies point inward |
| `demo_run.txt` | O1 fulfilled; O2 awaiting stock |
