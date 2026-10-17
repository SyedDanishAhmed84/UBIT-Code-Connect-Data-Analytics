# NexusMart Datathon: Data Dictionary (Cleaned Layer)

**Storage Location**: `data/processed/cleaned/`  
**Dataset Grain**: 9 Normalized Tables representing Pakistan e-commerce operations (Jan 2024 – Jun 2025).  
**Preservation Standard**: **Zero Data Loss Rule** enforced. All 863,000 source rows are preserved 1:1. Original raw values and columns are intact, supplemented by non-conflicting normalized fields and explicit audit flags.

---

## 1. Table Overview & Primary Identifiers

| Table | File Name | Rows | Columns | Primary Identifier / Natural Key | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **customers** | `customers.csv` | 45,000 | 18 | `customer_id` | Customer master with normalized demographics and audit flags. |
| **locations** | `locations.csv` | 650 | 14 | `city_id` | Geographic dimension covering Pakistani cities, provinces, and tiers. |
| **products** | `products.csv` | 3,200 | 14 | `product_id` | Catalog dimension containing pricing, weight, and seller link. |
| **sellers** | `sellers.csv` | 420 | 16 | `seller_id` | Marketplace merchants with ratings, tiers, and join dates. |
| **orders** | `orders.csv` | 163,200 | 23 | `order_id` (contains 3,200 dups) | Order header with order totals (PKR), discount codes, and channel. |
| **order_items**| `order_items.csv`| 315,143 | 22 | `order_item_id` | Line-item transaction grain linking orders to products and sellers. |
| **payments** | `payments.csv` | 168,111 | 19 | `payment_id` (contains 3,296 dups)| Payment transactions. Note: 1-to-many relationship with orders. |
| **shipping** | `shipping.csv` | 151,228 | 20 | `shipment_id` | Fulfillment and courier tracking (1 shipment per shipped order). |
| **returns** | `returns.csv` | 16,048 | 17 | `return_id` | Line-level product returns linking to `order_item_id`. |

---

## 2. Detailed Column Specifications

### A. `customers.csv` (45,000 rows)
- **Original Columns**:
  - `customer_id`: Unique string identifier (`C000001` to `C045000`).
  - `full_name`: Customer full name string (unmodified).
  - `email`: Customer email address.
  - `phone`: Contact number as originally recorded.
  - `gender`: Raw gender string (`M`, `F`, `Male`, `female`, etc.).
  - `registration_date`: Raw registration date string.
  - `city_id`: Foreign key referencing `locations.city_id`.
  - `birth_year`: Year of birth string.
- **Supplemental Normalized & Audit Columns**:
  - `is_exact_duplicate`: Boolean (`False`).
  - `has_missing_required_value`: Boolean flag if required attributes are missing.
  - `raw_gender`: Preserves exact raw string.
  - `normalized_gender`: Canonical gender (`'M'`, `'F'`, or `NaN`).
  - `has_unknown_category`: Boolean flag for non-standard gender entries.
  - `parsed_registration_date`: Standardized ISO date (`YYYY-MM-DD`).
  - `has_invalid_date`: Boolean flag for unparseable registration dates.
  - `has_invalid_numeric_value`: Boolean flag for out-of-range birth years.
  - `has_orphan_reference`: Boolean flag if `city_id` is not found in `locations`.
  - `audit_issue_codes`: Semicolon-delimited issue codes for quick indexing.

---

### B. `locations.csv` (650 rows)
- **Original Columns**:
  - `city_id`: City identifier (`1` to `650`).
  - `city`: City name string in Pakistan.
  - `province`: Province name string (Sindh, Punjab, KPK, Balochistan).
  - `region`: Geographic zone (South, North, Central).
  - `latitude`, `longitude`: Coordinate strings.
  - `population_tier`: Market classification (`Tier-1`, `Tier-2`, `Tier-3`).
- **Supplemental Columns**:
  - `latitude_val`, `longitude_val`: Float parsed coordinates.
  - `has_invalid_numeric_value`: Flag for unparseable coordinates.
  - `is_exact_duplicate`, `has_missing_required_value`, `has_orphan_reference`, `audit_issue_codes`.

---

### C. `products.csv` (3,200 rows)
- **Original Columns**:
  - `product_id`: Unique product catalog identifier (`P00001` to `P03200`).
  - `product_name`: Title and model string.
  - `category`, `sub_category`: Taxonomy strings.
  - `brand`: Brand name string.
  - `list_price`, `cost_price`: Price strings in PKR.
  - `weight_kg`: Weight string in kilograms.
  - `seller_id`: Foreign key referencing `sellers.seller_id`.
- **Supplemental Columns**:
  - `has_invalid_numeric_value`: Flag for malformed price/weight.
  - `has_orphan_reference`: Flag if `seller_id` does not match `sellers`.
  - `is_exact_duplicate`, `has_missing_required_value`, `audit_issue_codes`.

---

### D. `sellers.csv` (420 rows)
- **Original Columns**:
  - `seller_id`: Merchant identifier (`S0001` to `S0420`).
  - `seller_name`: Business or store title.
  - `join_date`: Onboarding date string.
  - `seller_tier`: Raw tier string (`Gold`, `Silver`, `Bronze`).
  - `city_id`: Seller's base city (`locations.city_id`).
  - `rating`: Seller review score (0.0 to 5.0).
- **Supplemental Columns**:
  - `raw_seller_tier`: Preserved original tier string.
  - `normalized_seller_tier`: Standardized title-case (`'Gold'`, `'Silver'`, `'Bronze'`).
  - `parsed_join_date`: Standardized ISO join date.
  - `has_invalid_date`, `has_invalid_numeric_value`, `has_unknown_category`, `audit_issue_codes`.

---

### E. `orders.csv` (163,200 rows)
- **Original Columns**:
  - `order_id`: Order identifier (`O0000001` to `O0160000`). Contains 3,200 repeated orders.
  - `customer_id`: Foreign key referencing `customers.customer_id`.
  - `order_date`: Date order was placed.
  - `order_status`: Fulfillment status string.
  - `ship_city_id`: Destination city key (`locations.city_id`).
  - `order_total`: Total merchandise value in PKR after discounts.
  - `discount_code`: Order-level promo code (e.g. `SAVE20`).
  - `channel`: Origin platform (`App`, `Web`, `Mobile Web`).
- **Supplemental Columns**:
  - `is_exact_duplicate`: **True for 6,400 rows** (3,200 unique order pairs repeated).
  - `raw_order_status`: Preserved status string.
  - `normalized_order_status`: Canonical status (`'DELIVERED'`, `'CANCELLED'`, `'COMPLETED'`, `'RETURNED'`, `'IN_TRANSIT'`, `'SHIPPED'`).
  - `parsed_order_date`: Standardized ISO date.
  - `order_total_pkr`: Numeric float total in PKR.
  - `raw_discount_code`: Original promo code string.
  - `discount_rate`: Numeric discount percentage (e.g. `0.20` for `SAVE20`, `0.0` for none).
  - `has_orphan_customer`: **True for 330 orders** where `customer_id` is not in `customers.csv`.
  - `has_orphan_city`: **True for 6,516 orders** where `ship_city_id` is missing.
  - `has_orphan_reference`: `has_orphan_customer | has_orphan_city`.
  - `has_invalid_date`, `has_invalid_numeric_value`, `has_unknown_category`, `audit_issue_codes`.

---

### F. `order_items.csv` (315,143 rows)
- **Original Columns**:
  - `order_item_id`: Unique line item key (`OI00000001` to `OI00315143`).
  - `order_id`: Parent order reference.
  - `product_id`: Purchased product reference.
  - `seller_id`: Fulfilling merchant reference.
  - `quantity`: Raw quantity (contains `'one'`, `'2.0'`, `'-4'`).
  - `unit_price`: Item unit price in PKR (contains `'Rs. 2,290'`).
  - `discount_amount`: Line item discount deduction.
- **Supplemental Columns**:
  - `raw_unit_price`: Preserved original string.
  - `unit_price_pkr`: Clean numeric price float in PKR.
  - `raw_quantity`: Preserved original string.
  - `normalized_quantity`: Clean integer quantity.
  - `has_negative_quantity`: **True for 307 rows** with negative quantity.
  - `discount_amount_pkr`: Clean numeric discount deduction float in PKR.
  - `has_orphan_product`: **True for 932 rows** referencing non-existent product IDs.
  - `has_orphan_order`, `has_orphan_seller`, `has_orphan_reference`, `audit_issue_codes`.

---

### G. `payments.csv` (168,111 rows)
- **Original Columns**:
  - `payment_id`: Payment key (`PAY00000001` to `PAY00164815`). Contains 3,296 repeated rows.
  - `order_id`: Referenced order. **Note: 1 order can have multiple payment rows.**
  - `payment_method`: Method string (`COD`, `Card`, `JazzCash`, etc.).
  - `payment_status`: Status string (`Paid`, `Cancelled`, `Refunded`, etc.).
  - `amount`: Payment amount in PKR.
  - `payment_date`: Date payment was settled.
- **Supplemental Columns**:
  - `is_exact_duplicate`: **True for 6,592 rows** (3,296 repeated pairs).
  - `raw_payment_status`: Preserved status string.
  - `normalized_payment_status`: Canonical status (`'PAID'`, `'CANCELLED'`, `'REFUNDED'`, `'PENDING'`).
  - `raw_payment_method`: Preserved method string.
  - `normalized_payment_method`: Canonical method (`'COD'`, `'CARD'`, `'JAZZCASH'`, `'EASYPAISA'`, `'BANK_TRANSFER'`).
  - `amount_pkr`: Clean numeric float in PKR.
  - `parsed_payment_date`: Standardized ISO date.
  - `has_invalid_date`, `has_invalid_numeric_value`, `has_orphan_reference`, `audit_issue_codes`.

---

### H. `shipping.csv` (151,228 rows)
- **Original Columns**:
  - `shipment_id`: Courier tracking identifier (`SH00000001` to `SH00151228`).
  - `order_id`: Shipped order reference.
  - `courier`: Courier partner name string.
  - `shipped_date`, `delivered_date`: Dispatch and delivery date strings.
  - `shipping_fee`: Courier charge billed to NexusMart (free shipping to customer).
  - `delivery_status`: Package milestone status.
- **Supplemental Columns**:
  - `raw_courier`: Preserved courier string.
  - `normalized_courier`: Canonical partner (`'TCS'`, `'LEOPARDS'`, `'M&P'`, `'TRAX'`, `'POSTEX'`, `'BLUEEX'`).
  - `raw_delivery_status`: Preserved delivery status string.
  - `normalized_delivery_status`: Canonical milestone (`'DELIVERED'`, `'RETURNED_TO_SELLER'`, `'IN_TRANSIT'`, `'SHIPPED'`).
  - `parsed_shipped_date`, `parsed_delivered_date`: Standardized ISO dates.
  - `shipping_fee_pkr`: Clean numeric float of courier charge.
  - `has_invalid_date`, `has_invalid_numeric_value`, `has_orphan_reference`, `audit_issue_codes`.

---

### I. `returns.csv` (16,048 rows)
- **Original Columns**:
  - `return_id`: RMA tracking identifier (`R000001` to `R016048`).
  - `order_item_id`: Returned item key (`order_items.order_item_id`).
  - `return_date`: Request date string.
  - `return_reason`: Return justification string.
  - `return_status`: Processing status (`Refunded`, `Approved`, `Rejected`).
  - `refund_amount`: Credit issued in PKR.
- **Supplemental Columns**:
  - `raw_return_status`: Preserved status string.
  - `normalized_return_status`: Canonical status (`'REFUNDED'`, `'APPROVED'`, `'REJECTED'`).
  - `is_valid_return`: **Boolean flag** (`True` if non-rejected, `False` for 1,322 rejected returns).
  - `parsed_return_date`: Standardized ISO date.
  - `refund_amount_pkr`: Clean numeric float in PKR.
  - `has_orphan_reference`: **True for 139 return rows** referencing non-existent line item IDs.
  - `has_invalid_date`, `has_invalid_numeric_value`, `audit_issue_codes`.
