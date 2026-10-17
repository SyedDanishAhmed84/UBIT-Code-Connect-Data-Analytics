# NexusMart Datathon: Conservative Data Cleaning & Preparation Plan

**Status**: Proposed Plan for Mentor & Judge Review  
**Safety Core**: **Zero Data Loss Rule** strictly enforced. No raw files will be changed, no records silently dropped, and all transformations reversible with audit flags.

---

## 1. Principles of Data Preservation
1. **Never mutate raw files**: All incoming files in `data/raw/` remain bit-for-bit identical.
2. **Never delete records**:
   - Duplicate records are flagged (`is_duplicate_record=True`) and tracked in `data/processed/rejects/`.
   - Orphan records (records referencing non-existent foreign keys) are flagged (`is_orphan_foreign_key=True`) rather than removed with inner joins.
   - Missing attributes will retain explicit audit columns and default standardized placeholders only where businesses require it.
3. **Reconcile row counts**: Every cleaning transformation must record:
   - `input_row_count`
   - `output_row_count`
   - `rows_flagged`
   - `rows_modified`
   - `quarantine_count`
   - Explanation of differences (which must sum to zero).

---

## 2. Table-by-Table Evidence & Action Plan

| Table | Column(s) | Observed Evidence | Proposed Action | Risk | Manual Review Required? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **orders** | Full Row | 3,200 exact duplicate complete rows (e.g. `O0018251`). | Keep original raw data. In cleaned dataset, preserve all records but add boolean flag `is_exact_duplicate`. Produce audit file in `rejects/duplicate_orders.csv`. | Low. No data dropped. | Yes (Confirm business deduplication preference) |
| **payments** | Full Row | 3,296 exact duplicate complete rows. | Same as orders: preserve all records, add `is_exact_duplicate` flag, and log to `rejects/duplicate_payments.csv`. | Low. | Yes |
| **orders** | `order_status` | Casing and spelling variants: `'Delivered'`, `'DELIVERD'`, `'Complete'`, `'Completed'`, `'Cancelled'`, `'Canceled'`. | Normalize to standard uppercase/titlecase enum (e.g., `'DELIVERED'`, `'COMPLETED'`, `'CANCELLED'`). Retain original string in `raw_order_status`. | Low. Reversible. | No |
| **orders** | `discount_code` | 68.66% null (no discount). Leading/trailing whitespace in 2,099 rows. Casing variants. | Strip whitespace, uppercase codes. Parse discount percentage (e.g. `SAVE20` -> 0.20) into new column `discount_rate_pct`. Preserve original in `raw_discount_code`. | Low. | No |
| **order_items** | `unit_price` | Formatted with strings like `'Rs. 2,290'`, commas, and whitespace. | Extract numeric value into float `unit_price_pkr`. Preserve original string in `raw_unit_price`. | Low. Reversible. | No |
| **order_items** | `quantity` | String numbers with words (`'one'`, `'two'`), floats (`'1.0'`), and negative quantities (`'-4'`). | Map text words to integers, cast floats to ints. For negative quantities, retain them, create flag `is_negative_quantity=True`. Never drop. | Medium. Negative quantities indicate reversals or returns. | Yes (Verify with business rules) |
| **order_items** | `product_id` | 932 line items reference 888 `product_id`s not in `products.csv`. | Do NOT drop line items! Retain records, flag with `is_orphan_product=True`, quarantine copies in `rejects/orphan_order_items.csv`. | High if inner-joined; Zero if preserved with flags. | Yes |
| **orders** | `customer_id` | 330 orders reference 315 `customer_id`s not in `customers.csv`. | Retain records with `is_orphan_customer=True`. Use LEFT JOIN in analytical marts. | High if inner-joined; Zero if preserved with flags. | Yes |
| **returns** | `order_item_id` | 139 return records reference `order_item_id`s not in `order_items.csv`. | Retain records with `is_orphan_order_item=True`. Quarantine to `rejects/orphan_returns.csv`. | High if inner-joined; Zero if preserved with flags. | Yes |
| **shipping** | `delivery_status`, `courier` | Whitespace and casing variants (`'TCS'` vs `'tcs'`, `'DELIVERD'` vs `'Delivered'`). | Standardize to uppercase / canonical names. Strip whitespace. Preserve originals. | Low. | No |
| **customers** | `gender` | Variants: `'M'`, `'m'`, `'Male'`, `'male'`, `'F'`, `'f'`, `'Female'`, `'female'`, and blank (2,199). | Map to canonical values `'M'`, `'F'`, and `'UNKNOWN'`. Preserve raw string in `raw_gender`. | Low. | No |
| **customers** | `phone` | 3,599 nulls. Inconsistent country codes and formats. | Preserve original string. Standardize valid Pakistani numbers to `+923xxxxxxxxx` in `normalized_phone`. | Low. | No |

---

## 3. Shipping & Payment Allocation Strategy
- **Shipping Fee**: Courier charges billed to NexusMart are charged once per order (`shipping_fee`).
  - *Rule*: When joining at the `order_items` grain, **never sum `shipping_fee` directly**, as that multiplies the fee by the number of line items.
  - *Recommendation*: Calculate shipping metrics strictly at the `orders` / `shipping` level, or allocate fee proportionally to line item value with explicit allocation columns.
- **Order Total & Discounts**:
  - `order_total` represents merchandise value after discounts.
  - Line-level items will reconcile: $\sum (\text{quantity} \times \text{unit\_price} - \text{discount\_amount})$ vs `order_total`.
  - Discrepancies will be captured in a reconciliation column `order_total_discrepancy_pkr`.

---

## 4. Reversible Output Locations
- Cleaned Datasets: `data/processed/cleaned/*.csv` (with audit and flag columns included).
- Quarantine / Reject Reports: `data/processed/rejects/*.csv` (complete original rows + rejection/warning reason).
- Audit Manifest: `reports/cleaning/row_count_reconciliation.csv`.
