# NexusMart Datathon: Team Data Handoff Guide

Welcome team! This guide explains how to use our cleaned, audit-annotated datasets for **SQL Staging, Star Schema Modeling, Airflow Integration, and Power BI Reporting**.

---

## 1. Where the Cleaned Datasets are Located
All 9 cleaned datasets are stored in:
```
data/processed/cleaned/
├── customers.csv      (45,000 rows)
├── locations.csv      (650 rows)
├── products.csv       (3,200 rows)
├── sellers.csv        (420 rows)
├── orders.csv         (163,200 rows)
├── order_items.csv    (315,143 rows)
├── payments.csv       (168,111 rows)
├── shipping.csv       (151,228 rows)
└── returns.csv        (16,048 rows)
```
**Total Row Count**: Exactly **863,000 rows** across all 9 tables.  
**Preservation Standard**: 100% Zero Data Loss. Every original raw row and value is preserved.

---

## 2. How to Verify Row Counts & Integrity
You can verify the exact row counts and reconciliation status anytime using Windows PowerShell or Python:

```powershell
# In Windows PowerShell:
python -c "
import pandas as pd
from pathlib import Path

clean_dir = Path('data/processed/cleaned')
for p in sorted(clean_dir.glob('*.csv')):
    df = pd.read_csv(p, dtype=str)
    print(f'{p.name:<16}: {len(df):,} rows')
"
```

The detailed reconciliation audit log is located at:
`reports/profiling/cleaning_reconciliation.csv`

---

## 3. Critical Guidelines for SQL Staging & Star Schema Developers

### A. Deduplication Guidelines (Orders & Payments)
- `orders.csv` contains **6,400 exact duplicate rows** (3,200 unique order pairs repeated). They are tagged with `is_exact_duplicate = True`.
  - When computing the **Cancellation Rate** or net sales metrics, filter using `WHERE is_exact_duplicate = FALSE` (or take `DISTINCT` / `ROW_NUMBER() OVER (PARTITION BY order_id)`).
- `payments.csv` contains **6,592 exact duplicate rows** (3,296 repeated pairs). They are tagged with `is_exact_duplicate = True`.

### B. Prevent Row Multiplication (Fan-out) in Joins
Do **NOT** perform naive joins between tables without accounting for differing grains:
1. **Payments to Orders (1-to-Many)**:
   - Over 7,800 orders have multiple payments (split payments, deposits, installment plans).
   - If joining `orders` to `payments`, first aggregate payments at the order level:
     ```sql
     SELECT order_id, SUM(amount_pkr) AS total_paid_pkr
     FROM payments
     WHERE is_exact_duplicate = FALSE
     GROUP BY order_id;
     ```
2. **Shipping to Order Items**:
   - `shipping.shipping_fee` is billed **once per order**, paid by NexusMart (customers receive free shipping).
   - If joining `shipping` to `order_items`, **never SUM `shipping_fee` directly**, or it will be multiplied by the number of line items in the order! Keep shipping calculations at the order grain or allocate proportionally.
3. **Returns to Orders**:
   - Returns link at the **line-item level** via `order_item_id`, NOT the order level.
   - Join `returns` to `order_items` on `order_item_id`.

### C. Handling Orphan References in SQL Dim/Fact Modeling
We preserved orphan records rather than dropping them:
- **330 orders** reference non-existent customer IDs (`has_orphan_customer = True`).
- **932 order items** reference non-existent product IDs (`has_orphan_product = True`).
- *SQL Staging Best Practice*: Create **Unknown Member records** in your dimension tables:
  - In `dim_customer`: Insert `customer_id = 'C_UNKNOWN'`, `full_name = 'Unknown Customer'`.
  - In `dim_product`: Insert `product_id = 'P_UNKNOWN'`, `product_name = 'Unknown Product'`.
  - Use `COALESCE(c.customer_id, 'C_UNKNOWN')` in your fact table ETL so no transaction revenue is lost!

### D. Return Validity Rule
- Per competition guidelines: **Only returns with `return_status` other than 'Rejected' count as real returns**.
- Use the provided column:
  ```sql
  WHERE is_valid_return = TRUE
  ```
  Exactly 1,322 rejected/declined returns are retained for auditing with `is_valid_return = FALSE`.

---

## 4. How Contributors Can Pull the Latest Changes
Run these commands in Windows PowerShell:
```powershell
# 1. Fetch all remote branches
git fetch origin

# 2. Check out the handoff branch
git checkout data/cleaned-datasets-handoff

# 3. Pull latest changes
git pull origin data/cleaned-datasets-handoff

# 4. Verify test suite
pytest tests -v
```
