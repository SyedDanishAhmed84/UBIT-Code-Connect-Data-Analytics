# NexusMart Datathon: Relationship & Referential Integrity Validation

**Safety Rule**: Zero Data Loss Enforced. All records preserved.

## 1. Summary of Relationship Integrity Checks

| Relationship | Expected | Child Rows | Null Keys | Orphan Records | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `orders.customer_id -> customers.customer_id` | 1:N | 163,200 | 0 | 330 | ⚠️ ORPHAN_KEYS_DETECTED |
| `order_items.order_id -> orders.order_id` | 1:N | 315,143 | 0 | 0 | ✅ PASS |
| `order_items.product_id -> products.product_id` | 1:N | 315,143 | 0 | 932 | ⚠️ ORPHAN_KEYS_DETECTED |
| `order_items.seller_id -> sellers.seller_id` | 1:N | 315,143 | 0 | 0 | ✅ PASS |
| `products.seller_id -> sellers.seller_id` | 1:N | 3,200 | 0 | 0 | ✅ PASS |
| `orders.ship_city_id -> locations.city_id` | 1:N | 163,200 | 6,516 | 0 | ✅ PASS |
| `customers.city_id -> locations.city_id` | 1:N | 45,000 | 2,233 | 0 | ✅ PASS |
| `sellers.city_id -> locations.city_id` | 1:N | 420 | 0 | 0 | ✅ PASS |
| `payments.order_id -> orders.order_id` | 1:N (Multiple payments) | 168,111 | 0 | 0 | ✅ PASS |
| `shipping.order_id -> orders.order_id` | 1:1 | 151,228 | 0 | 0 | ✅ PASS |
| `returns.order_item_id -> order_items.order_item_id` | 1:1 | 16,048 | 0 | 139 | ⚠️ ORPHAN_KEYS_DETECTED |

## 2. In-Depth Referential Integrity Findings

### A. Orphan Records (Crucial Data Preservation Alert)
- **orders.customer_id -> customers.customer_id**: **330 orphan records** referencing 315 non-existent parent IDs.
  - *Action Plan*: Under the Zero Data Loss Rule, these records **MUST NOT be dropped**. They must be retained and tagged with audit flags (e.g., `is_orphan_reference=True`) and quarantined for review.
- **order_items.product_id -> products.product_id**: **932 orphan records** referencing 888 non-existent parent IDs.
  - *Action Plan*: Under the Zero Data Loss Rule, these records **MUST NOT be dropped**. They must be retained and tagged with audit flags (e.g., `is_orphan_reference=True`) and quarantined for review.
- **returns.order_item_id -> order_items.order_item_id**: **139 orphan records** referencing 139 non-existent parent IDs.
  - *Action Plan*: Under the Zero Data Loss Rule, these records **MUST NOT be dropped**. They must be retained and tagged with audit flags (e.g., `is_orphan_reference=True`) and quarantined for review.

### B. Orders without Shipping (8,772 Orders)
Investigation confirms that all 8,772 orders without a corresponding record in `shipping.csv` are **Cancelled** orders (variants: 'Cancelled', 'cancelled', 'Canceled', 'CANCELLED').
- *Business Meaning*: When an order is cancelled prior to dispatch, no shipment is created. This is completely consistent with real e-commerce operations.

### C. Cardinality Analysis: Payments per Order
Unlike a simple 1:1 model, `payments` has a **1:Many** relationship with `orders`:
- Single payment: 152,108 orders
- Split/Multiple payments (2 payments): 7,675 orders
- 3 or more payments: 217 orders
- *Data Engineering Notice*: Joining orders directly to payments without aggregation would produce accidental row duplication (fan-out).

### D. Returns Line-Level Grain
- Returns link directly to `order_item_id` (1:1 candidate), NOT just `order_id`.
- Exactly 139 return records reference `order_item_id` values not present in `order_items.csv`.
- Only returns where `return_status` is not 'Rejected' count as real returns per Datathon business rules.

