# NexusMart Datathon: Final Cleaning Findings & Proposed Rules

**Document Type**: Pre-Cleaning Investigation and Proposal for Student & Mentor Alignment  
**Safety Protocol**: **Zero Data Loss Rule** strictly enforced. No raw files modified. All proposals are deterministic, rule-based, and auditable.

---

## 1. Category, Geography & Courier Spelling Variants & Proposed Canonical Mappings

Across the raw tables, inconsistent casing, typos, and trailing whitespaces exist across categorical columns. We inspected each unique value across the full 863,000 records.

### A. Gender (`customers.gender` - 45,000 rows)
- **Observed Counts**:
  - `'M'`: 16,672 | `'Male'`: 2,328 | `'male'`: 2,382 | `'m'`: 2,327  $\rightarrow$ **Total M**: 23,709 (52.69%)
  - `'F'`: 13,344 | `'Female'`: 1,909 | `'female'`: 1,890 | `'f'`: 1,949 $\rightarrow$ **Total F**: 19,092 (42.43%)
  - `Empty / Missing`: 2,199 (4.89%)
- **Proposed Canonical Values**: `'M'`, `'F'`, `'UNKNOWN'`.
- **Action**: Map all male variants to `'M'`, female variants to `'F'`, and missing to `'UNKNOWN'`. Retain original string in `raw_gender`.

### B. Courier (`shipping.courier` - 151,228 rows)
- **Observed Counts**:
  - TCS variants (`'TCS'`: 36,319, `'tcs'`: 3,090, `'TCS Express'`: 3,001, `'T.C.S'`: 2,992) $\rightarrow$ **45,402**
  - Leopards variants (`'Leopards'`: 26,570, `'leopards'`: 2,267, `'Leopard Courier'`: 2,264, `'LEOPARDS'`: 2,251) $\rightarrow$ **33,352**
  - M&P variants (`'M&P'`: 18,256, `'M & P'`: 1,537, `'m&p'`: 1,494, `'MnP'`: 1,452) $\rightarrow$ **22,739**
  - Trax variants (`'Trax'`: 15,652, `'TRAX'`: 1,969, `'trax'`: 1,963) $\rightarrow$ **19,584**
  - PostEx variants (`'PostEx'`: 14,401, `'POSTEX'`: 1,836, `'Postex'`: 1,833) $\rightarrow$ **18,070**
  - BlueEx variants (`'BlueEx'`: 9,662, `'Blue EX'`: 825, `'Blue-Ex'`: 798, `'blueex'`: 796) $\rightarrow$ **12,081**
- **Proposed Canonical Set**: `['TCS', 'LEOPARDS', 'M&P', 'TRAX', 'POSTEX', 'BLUEEX']`.

### C. Payment Method (`payments.payment_method` - 168,111 rows)
- **Observed Counts**:
  - Cash on Delivery (`'COD'`, `'Cash on Delivery'`, `'Cash On Delivery'`, `'cod'`) $\rightarrow$ **86,309** (51.34%)
  - Card (`'Card'`, `'Credit/Debit Card'`, `'CARD'`, `'card'`, `'Debit Card'`) $\rightarrow$ **29,145** (17.34%)
  - JazzCash (`'JazzCash'`, `'Jazzcash'`, `'Jazz Cash'`, `'JAZZCASH'`) $\rightarrow$ **21,362** (12.71%)
  - EasyPaisa (`'EasyPaisa'`, `'Easypaisa'`, `'Easy Paisa'`, `'EASYPAISA'`) $\rightarrow$ **19,981** (11.89%)
  - Bank Transfer (`'Bank Transfer'`, `'Bank Trf'`, `'bank transfer'`, `'BANK TRANSFER'`) $\rightarrow$ **11,314** (6.73%)
- **Proposed Canonical Set**: `['COD', 'CARD', 'JAZZCASH', 'EASYPAISA', 'BANK_TRANSFER']`.

### D. Province & Region (`locations.province`, `locations.region` - 650 rows)
- **Observed Counts**:
  - Punjab (`'Punjab'`, `'Panjab'`, `'PUNJAB'`, `'punjab'`) $\rightarrow$ **300**
  - Sindh (`'Sindh'`, `'sindh'`, `'SINDH'`) $\rightarrow$ **150**
  - Khyber Pakhtunkhwa (`'Khyber Pakhtunkhwa'`, `'KPK'`, `'kpk'`) $\rightarrow$ **100**
  - Balochistan (`'Balochistan'`, `'balochistan'`) $\rightarrow$ **55**
  - Islamabad Capital Territory (`'Islamabad'`, `'ICT'`) $\rightarrow$ **20**
  - Missing: 25 rows
- **Proposed Canonical Set**: `['PUNJAB', 'SINDH', 'KHYBER_PAKHTUNKHWA', 'BALOCHISTAN', 'ISLAMABAD_CAPITAL_TERRITORY', 'UNKNOWN']`.

### E. Seller Tier (`sellers.seller_tier` - 420 rows)
- **Observed Counts**: Bronze variants: 259 | Silver variants: 99 | Gold variants: 40 | Missing: 22.
- **Proposed Canonical Set**: `['BRONZE', 'SILVER', 'GOLD', 'UNKNOWN']`.

---

## 2. Status Label Variants & Proposed Canonical Values

### A. Order Status (`orders.order_status` - 163,200 rows)
- **Observed Counts**:
  - Delivered variants (`'Delivered'`, `'DELIVERD'`, `'Complete'`, `'Completed'`, `'DELIVERED'`, `'delivered'`): **143,938** (88.20%)
  - Cancelled variants (`'Cancelled'`, `'cancelled'`, `'Canceled'`, `'CANCELLED'`): **14,972** (9.17%)
  - Returned variants (`'Returned'`, `'returned'`, `'RETURNED'`, `'Return'`): **2,911** (1.78%)
  - In Transit variants (`'In Transit'`, `'In-Transit'`, `'in transit'`, `'IN TRANSIT'`): **1,303** (0.80%)
  - Shipped: **76** (0.05%)
- **Proposed Canonical Values**: `['DELIVERED', 'COMPLETED', 'CANCELLED', 'RETURNED', 'IN_TRANSIT', 'SHIPPED']`.
  - *Note on Delivered vs Completed*: Real data treats 'Complete' and 'Delivered' interchangeably for final fulfillment; we will normalize to `'DELIVERED'` for standardized delivery rate reporting while keeping the original string.

### B. Payment Status (`payments.payment_status` - 168,111 rows)
- **Observed Counts**:
  - Paid variants (`'Paid'`, `'PAID'`, `'paid'`, `'Complete'`, `'Success'`): **151,986** (90.41%)
  - Cancelled variants (`'Cancelled'`, `'cancelled'`, `'Canceled'`, `'CANCELLED'`): **12,235** (7.28%)
  - Refunded variants (`'Refunded'`, `'refunded'`, `'REFUNDED'`, `'Refund'`): **3,185** (1.89%)
  - Pending variants (`'Pending'`, `'PENDING'`, `'pending'`): **705** (0.42%)
- **Proposed Canonical Values**: `['PAID', 'CANCELLED', 'REFUNDED', 'PENDING']`.

### C. Shipping Delivery Status (`shipping.delivery_status` - 151,228 rows)
- **Observed Counts**:
  - Delivered variants (`'Delivered'`, `'DELIVERD'`, `'Completed'`, `'Complete'`, `'DELIVERED'`, `'delivered'`): **143,887** (95.15%)
  - Returned to Seller variants (`'Returned to Seller'`, `'Return to Seller'`, `'RTO'`, `'returned to seller'`): **5,890** (3.90%)
  - In Transit variants: **1,279** (0.85%)
  - Shipped: **74** (0.05%)
- **Proposed Canonical Values**: `['DELIVERED', 'RETURNED_TO_SELLER', 'IN_TRANSIT', 'SHIPPED']`.

### D. Return Status (`returns.return_status` - 16,048 rows)
- **Observed Counts**:
  - Refunded variants (`'Refunded'`, `'Refund'`, `'REFUNDED'`, `'refunded'`): **11,549** (71.97%)
  - Approved variants (`'Approved'`, `'APPROVED'`, `'approved'`): **3,177** (19.80%)
  - Rejected variants (`'Rejected'`, `'rejected'`, `'Declined'`): **1,322** (8.24%)
- **Proposed Canonical Values**: `['REFUNDED', 'APPROVED', 'REJECTED']`.
- **Business Rule Enforcement**: Per competition guidelines, **only returns with status other than Rejected count as valid returns**. A dedicated boolean column `is_valid_return` (`return_status != 'REJECTED'`) will be created. Exactly 1,322 records are Rejected and will have `is_valid_return=False`. They will NOT be dropped.

---

## 3. Exact Duplicate Records in Orders and Payments

- **Orders**: 
  - Exactly 6,400 rows are exact duplicate rows across all 8 columns, representing **3,200 unique orders repeated twice**.
  - Example: `O0018251` appearing at row index 10 and row index 51,170 with identical customer, date, total, discount, and channel.
  - *Proposed Action*: For the **Final Clean Layer**, remove the duplicate occurrences keeping the first occurrence (`keep='first'`), resulting in **160,000 unique orders**. The 3,200 removed duplicate records will be archived to `data/processed/rejects_final/reject_duplicate_orders.csv` with reason code `EXACT_DUPLICATE_ORDER`.
- **Payments**:
  - Exactly 6,592 rows are exact duplicate rows across all 6 columns, representing **3,296 unique payments repeated twice**.
  - *Proposed Action*: Keep first occurrence, yielding **164,815 payment records**. The 3,296 duplicate records will be archived to `data/processed/rejects_final/reject_duplicate_payments.csv` with reason code `EXACT_DUPLICATE_PAYMENT`.

---

## 4. Entity Deduplication Candidates (Customers & Products)

*Rule: Never merge customers or products by name alone.*

### A. Customers (45,000 records)
We performed multi-attribute linkage analysis without using names alone:
- **Shared Normalized Phone**: 4,394 candidate records across 2,197 phone groups.
- **Shared Normalized Email**: 3,935 candidate records across 1,964 email groups.
- **Shared BOTH Exact Email AND Cleaned Phone**: **3,222 customer records across 1,611 duplicate groups**.
  - Strongest evidence: Same email and same phone number, registered at different times or with casing differences.
  - *Proposed Rule*: Create a deterministic mapping table `customer_id_map.csv` mapping `customer_id -> master_customer_id` using the **lowest/earliest `customer_id`** in the group.
  - In `customers.csv` (final layer): Do NOT delete the physical rows; assign the `master_customer_id` column so analysts can aggregate by true entity without losing registration history.

### B. Products (3,200 records)
- Shared Product Name alone: 52 products in 26 groups (could be different sellers selling the same item name).
- Shared Product Name AND Seller ID: **4 products in 2 groups**.
- Shared ALL Attributes (name, category, brand, list_price, cost_price, seller_id): **0 records**.
- *Proposed Rule*: Because products with the same name have different prices or distinct sellers, **do NOT merge products**. Create a 1:1 `product_id_map.csv` leaving original identities intact.

---

## 5. Date Problems & Proposed Resolution Rules

*Stated Rule: Slash dates are strictly DAY/MONTH/YEAR. Valid order range: 1 Jan 2024 to 30 Jun 2025.*

### A. Format & Parsing Real Numbers
Using our strict DAY/MONTH/YEAR parser:
- **orders.order_date** (163,200 rows):
  - Valid parseable dates: 162,050 rows.
  - Impossible dash dates (e.g. `2024-13-05`, `2024-02-30`, `2024-04-31`): **909 rows**.
  - Impossible slash dates (e.g. `00/00/2024`, month > 12): **241 rows**.
  - Total unparseable dates: **1,150 rows** (0.70%).
- **Out of Bounds Order Dates**:
  - Of the 160,000 unique orders, **481 orders** have dates outside 1 Jan 2024 – 30 Jun 2025 (all are future dates in 2026–2027, e.g. `2026-08-21`, `2027-04-17`).

### B. Chronological Sequence Violations
- **Shipment before Order (`shipped_date < order_date`)**: **436 shipments**.
- **Delivered before Shipped (`delivered_date < shipped_date`)**: **1,269 shipments**.
- **Return before Order (`return_date < order_date`)**: **171 returns**.

### C. Proposed Date Action Plan
1. **Unparseable / Corrupt Order Dates (1,150 rows)**: Cannot be guessed or repaired reliably.
   - *Proposal*: Move to `rejects_final/reject_orders.csv` with reason `INVALID_ORDER_DATE`. These orders cannot be accurately placed in monthly/quarterly financial periods.
2. **Out-of-Bounds Order Dates (481 rows in 2026-2027)**:
   - *Proposal*: Quarantine to `rejects_final/reject_orders.csv` with reason `ORDER_DATE_OUT_OF_BOUNDS_2026_2027`.
3. **Chronological Sequence Inconsistencies (shipped < order, delivered < shipped)**:
   - *Proposal*: Retain the order and shipment records in the clean layer, but nullify the logically impossible dependent date and set audit flag `has_chronological_sequence_error=True`. Do NOT drop the entire order/shipment.

---

## 6. Numeric Problems & Statistical Outlier Thresholds

### A. Unit Price (`order_items.unit_price`)
- **Dirty Strings**: 7,998 rows formatted with `"Rs. 2,290"` or commas. Successfully stripped to numeric floats.
- **Negative Unit Prices**: **316 rows** with negative prices (e.g. `-840.0`, `-4174.0`).
- **Placeholder Extreme Prices**: **305 rows** with price exactly equal to `9,999,999.0 PKR`.
- **Distribution** (Excluding negatives and 9,999,999):
  - 1st percentile: 256 PKR | 50th percentile (median): 1,619 PKR | 99th percentile: 22,978 PKR.
- *Proposed Action*:
  - Lines with negative price (316 rows) or `9,999,999` (305 rows): Move to `rejects_final/reject_order_items.csv` with reason `INVALID_UNIT_PRICE_NEGATIVE` or `INVALID_UNIT_PRICE_PLACEHOLDER`.

### B. Quantity (`order_items.quantity`)
- **Word/Float Conversions**: Text words (`'one'` to `'ten'`) and floats (`'1.0'` to `'6.0'`) converted to clean integers.
- **Negative Quantities**: **307 rows** with negative quantity (`-1` to `-6`).
- **Bulk Outlier Quantities**: **641 rows** with quantity equal to exactly `500`.
- *Proposed Action*:
  - Negative quantity lines (307 rows): Quarantine to `rejects_final/reject_order_items.csv` with reason `NEGATIVE_QUANTITY`.
  - Bulk quantity `500`: Retain in cleaned dataset with flag `is_bulk_quantity_outlier=True` (could represent B2B wholesale orders).

### C. Refund Amount (`returns.refund_amount`)
- Max refund is 250,592 PKR. Over 99% of refunds are $\le 28,655\text{ PKR}$. Zero refunds are negative.

---

## 7. Business Consistency & Financial Reconciliation Checks

### A. Order Total vs Order Lines
We calculated for every order:
$$\text{Calculated Net Line Total} = \sum (\text{normalized\_quantity} \times \text{unit\_price\_pkr} - \text{discount\_amount\_pkr})$$
- **143,390 out of 160,000 orders (89.62%) match $\text{order\_total}$ exactly**.
- In the remaining 10.38%, the difference matches the order-level `discount_code` percentage (e.g. `SAVE15` applied on the header rather than item lines).
- *Finding*: `order_total` represents the true final invoice amount paid by the customer. We will retain `order_total` as the master merchandise measure and compute `line_reconciliation_variance_pkr`.

### B. Payments vs Order Total
- **147,508 out of 160,000 orders (92.19%) match $\sum \text{payments.amount} == \text{order\_total}$ exactly**.
- The remaining orders reflect uncompleted payments, cancellations, or partial payments.

### C. Refund vs Line Item Value
- 10,641 returns (66.3%) match the exact net line item value. Partial refunds account for the rest (restocking fee deductions or partial return of bundle).

---

## 8. Broken Referential Integrity & Handling Proposal

| Relationship | Issue Found | Real Count | Proposed Clean Layer Rule |
| :--- | :--- | :--- | :--- |
| **orders $\rightarrow$ customers** | Orphan customer IDs | **330 orders** (315 unique missing IDs) | Create an **Unknown Customer record** (`customer_id = 'C_UNKNOWN'`) in the cleaned customer dimension. Map orphan orders to `'C_UNKNOWN'` and set `is_orphan_customer=True`. **Zero lost orders/revenue.** |
| **order_items $\rightarrow$ products**| Orphan product IDs | **932 line items** (888 unique missing IDs) | Create an **Unknown Product record** (`product_id = 'P_UNKNOWN'`) in products dimension. Map orphan items to `'P_UNKNOWN'` with `is_orphan_product=True`. **Zero lost line sales.** |
| **returns $\rightarrow$ order_items** | Orphan line item IDs | **139 return records** | Quarantine to `rejects_final/reject_returns.csv` with reason `ORPHAN_ORDER_ITEM_ID` (cannot link to product or seller). |
| **orders $\rightarrow$ locations** | Missing `ship_city_id` | **6,516 orders** (empty string) | Create an **Unknown Location record** (`city_id = 9999`, City='Unknown', Province='UNKNOWN'). Map missing city IDs to 9999. |
| **customers $\rightarrow$ locations** | Missing `city_id` | **2,233 customers** (empty string) | Map to Unknown Location (`city_id = 9999`). |
| **orders $\rightarrow$ shipping** | Orders without shipment | **8,772 orders** | Valid business state (all 8,772 are Cancelled orders). Keep orders intact. |

---

## 9. Missing Values by Column & Recommendation Summary

| Table | Column | Missing Count | % Missing | Recommendation | Business Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **orders** | `discount_code` | 112,059 | 68.66% | Impute with `'NONE'`, discount rate `0.0` | Brief states empty means no discount applied. |
| **orders** | `ship_city_id` | 6,516 | 3.99% | Map to `9999` (`'UNKNOWN_LOCATION'`) | Retains order without dropping sales records. |
| **customers**| `gender` | 2,199 | 4.89% | Impute with `'UNKNOWN'` | Demographics missing; preserve customer row. |
| **customers**| `birth_year` | 4,600 | 10.22% | Retain `NULL` (nullable integer) | Do NOT impute arbitrary birth year like 1900 or 0. |
| **customers**| `phone` / `email` | 3,599 / 1,698| 8.0% / 3.8%| Retain empty string / `NULL` | Many customers register with email only or phone only. |
| **products** | `brand` / `sub_category`| 392 / 485 | 12.2% / 15.2%| Impute with `'Generic'` / `'Uncategorized'` | Categorical grouping needed for BI aggregation. |
| **shipping** | `delivered_date` | 18,841 | 12.46% | Retain `NULL` | In-transit, cancelled, or returned packages have no delivery date. |
| **shipping** | `shipping_fee` | 9,145 | 6.05% | Impute with median courier fee by courier tier | Or retain `NULL` with flag; shipping fee is courier expense. |
| **order_items**| `discount_amount`| 31,567 | 10.02% | Impute with `0.0` | No discount amount given means zero discount. |
| **returns** | `return_reason` | 2,390 | 14.89% | Impute with `'Not Specified'` | Standard customer service default. |
| **sellers** | `join_date` / `rating` | 34 / 33 | 8.1% / 7.9% | Retain `NULL` | Preserves unbiased seller performance metrics. |
