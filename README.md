# Farm Produce Orders (CSC 3115 coursework)

Small DDD / TDD / Clean Architecture project for **Farm Produce Order & Fulfilment**.

Two connected use cases, in-memory persistence, no web UI and no database:

1. **Place and confirm a produce order** (`PlaceOrderService` → Aggregate A `ProduceOrder`)
2. **Reserve fresh stock** (`ReserveStockHandler` → Aggregate B `FarmInventory`)

They are linked by the domain event **`ProduceOrderConfirmed`**.

AI use: Cursor Grok 4.6 helped implement the farm-orders code from the CSC 3115 farm team guide; the group must still be able to explain every rule, class and test.

---

## How to open the project

1. Open **Cursor** or **VS Code**.
2. File → **Open Folder**.
3. Choose this folder:
   `C:\Users\hp\Desktop\advanced programming\farm_orders`
4. Open a terminal in that folder (Terminal → New Terminal).

Do **not** open the old `farm.mgt` Flask/MySQL app. This coursework is a new, small in-memory project.

Python **3.10+** is required. This machine already has Python 3.13.

---

## Install once

```text
cd "C:\Users\hp\Desktop\advanced programming\farm_orders"
python -m pip install -r requirements.txt
```

Or double-click `run_tests.bat` after install (see below).

---

## Commands the lecturer asked for

Run the eight tests (T1–T8):

```text
python -m pytest -v
```

Check that Clean Architecture imports only point inward:

```text
python check_layers.py
```

Run the command-line demo (composition root):

```text
python -m interface.main
```

On Windows you can also double-click:

- `run_tests.bat` — tests
- `run_layers.bat` — layer checker
- `run_demo.bat` — demo of both use cases

Saved evidence lives in `evidence/`:

| File | What it proves |
|------|----------------|
| `tdd_red.txt` | T1 failed before quantity validation existed |
| `tdd_green.txt` | T1 passed after `ProduceQuantity.__post_init__` |
| `final_run.txt` | All 8 tests passing |
| `layers_check.txt` | Dependencies point inward |
| `demo_run.txt` | Successful O1 fulfilment and O2 awaiting stock |

---

## Names used everywhere (slides, code, tests)

Keep these names identical on the 15 slides.

| Concept | Name |
|---------|------|
| Domain | Farm Produce Order & Fulfilment |
| Aggregate A / root | `ProduceOrder` |
| Aggregate B / root | `FarmInventory` |
| Value Object (BR1) | `ProduceQuantity` |
| Entity (BR2) | `ProduceOrder` (identity = `order_id`) |
| Child entity | `StockLot` (identity = `lot_id`) |
| Domain Service (BR4) | `FreshnessPolicy` |
| Domain Event (BR5) | `ProduceOrderConfirmed` |
| Application Service | `PlaceOrderService` |
| Event handler | `ReserveStockHandler` |
| Input DTO | `PlaceOrderInput` |
| Output DTO | `PlaceOrderOutput` |
| Repositories | `OrderRepository`, `InventoryRepository` |
| In-memory implementations | `InMemoryOrderRepository`, `InMemoryInventoryRepository` |
| Event bus | `InProcessEventBus` |

**Factory:** not used. Creating an order needs no complex construction rules; the constructor is enough.

**Layer Supertype:** not implemented. A Layer Supertype is a shared base class for objects in one layer (for example a base Entity with id and equality). We only have two entities, so a base class would add code without removing duplication.

---

## The six business rules

| Rule | Statement | Enforced by | If broken |
|------|-----------|-------------|-----------|
| BR1 | A produce quantity must be above 0 and at most 5,000, in a supported unit (`kg`, `litre` or `tray`). | `ProduceQuantity` | `InvalidQuantity`. No object is created. |
| BR2 | An order moves PENDING → CONFIRMED → FULFILLED. It cannot be confirmed twice, or when it has no items, or after cancellation. | `ProduceOrder.confirm()` | `InvalidOrderState`. Status unchanged. |
| BR3 | An order has at most 3 lines, and the same produce cannot appear on two lines. | `ProduceOrder.add_item()` | `InvalidOrderLine`. The order is unchanged. |
| BR4 | A stock lot can be used for a produce only if its age since harvest is within that produce's shelf life. The last day still counts. | `FreshnessPolicy.is_fresh()` | Lot is skipped. If too little fresh stock remains, Aggregate B rejects. |
| BR5 | When an order is confirmed, the inventory must be asked to reserve the ordered stock. | `ProduceOrderConfirmed` + `ReserveStockHandler` | If inventory rejects, order stays CONFIRMED and outcome is `AWAITING_STOCK`. |
| BR6 | Before an order is confirmed, the farm inventory must exist and every ordered produce must be stocked there. | `InventoryRepository` + `PlaceOrderService` | `InventoryNotFound` or `ProduceNotStocked`. Nothing is saved. |

**FULFILLED** means all ordered stock has been reserved. Delivery is out of scope.

**AWAITING_STOCK** means confirmation was valid but Aggregate B refused reservation. The order is not rolled back to PENDING (eventual consistency between two aggregates).

---

## Event flow (Slide 10)

```text
Request (PlaceOrderInput)
  → PlaceOrderService
  → ProduceOrder.confirm()          Aggregate A
  → ProduceOrderConfirmed           Domain Event
  → ReserveStockHandler             in-process
  → FarmInventory.reserve()         Aggregate B
```

- Event name: `ProduceOrderConfirmed`
- Before it is raised: a PENDING order with at least one valid line passed BR2 and became CONFIRMED
- Handler: loads inventory through `InventoryRepository` and calls `reserve()` (never edits lot fields)
- Rule B checks: never below zero, fresh stock only (BR4), all-or-nothing across lines
- If B rejects (T8): order stays CONFIRMED, outcome `AWAITING_STOCK`, lots unchanged

---

## Tests T1–T8

| Test | Checks | Kind |
|------|--------|------|
| T1 | 100 kg valid; 5,000 accepted; 0, 5,000.01 and unit `bag` rejected | boundary + rejections |
| T2 | Pending order with an item confirms; confirm again and empty order rejected | 2 rejections |
| T3 | Three lines allowed; fourth produce rejected; same produce twice rejected | boundary + 2 rejections |
| T4 | Tomatoes 7 days fresh, 8 stale; milk 2 days fresh, 3 stale | boundary |
| T5 | Confirming raises exactly one `ProduceOrderConfirmed`, then the list empties | positive |
| T6 | Unstocked produce and missing inventory rejected; nothing saved | 2 rejections |
| T7 | 120 kg maize + 10 litre milk: event handled, oldest lots first, order FULFILLED | success |
| T8 | Only stale tomatoes: inventory rejects, order CONFIRMED, lot unchanged | B rejects |

Tests use a **fixed date** 10 October 2026 so freshness never depends on the real clock.

---

## Clean Architecture folders

```text
farm_orders/
  domain/            entities, value objects, domain service, domain event, rules
  application/       PlaceOrderService, DTOs, repository abstractions, handler
  infrastructure/    in-memory repositories and in-process event bus
  interface/         main.py (composition root: builds objects and injects them)
  tests/             test_rules.py (T1–T8)
  evidence/          real pytest and checker output
```

Dependency rule: Domain imports nothing outside Domain. Application may import Domain. Infrastructure may import Application and Domain. Interface may import all four.

---

## Produce reference data (teaching values, not farming advice)

| Produce | Unit | Shelf life (days) |
|---------|------|-------------------|
| Maize | kg | 180 |
| Beans | kg | 180 |
| Tomatoes | kg | 7 |
| Milk | litre | 2 |
| Eggs | tray | 21 |
