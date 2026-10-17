# NexusMart Datathon: Raw Data Profiling Summary Report

**Generated Automatically by Non-Destructive Profiler**
**Zero Data Loss Rule Enforced**: Raw source files in `data/raw/` untouched.

## 1. Dataset Overview

| Table Name | File Name | Rows | Columns | File Size (KB) |
| :--- | :--- | :--- | :--- | :--- |
| **customers** | `customers.csv` | 45,000 | 8 | 3,552.3 |
| **locations** | `locations.csv` | 650 | 7 | 33.2 |
| **order_items** | `order_items.csv` | 315,143 | 7 | 13,078.0 |
| **orders** | `orders.csv` | 163,200 | 8 | 8,846.0 |
| **payments** | `payments.csv` | 168,111 | 6 | 8,236.2 |
| **products** | `products.csv` | 3,200 | 9 | 271.7 |
| **returns** | `returns.csv` | 16,048 | 6 | 884.6 |
| **sellers** | `sellers.csv` | 420 | 6 | 19.6 |
| **shipping** | `shipping.csv` | 151,228 | 7 | 8,969.9 |

## 2. Duplicate Complete Rows Analysis

| Table Name | Total Rows | Exact Duplicate Rows | Duplicate % |
| :--- | :--- | :--- | :--- |
| customers | 45,000 | 0 | 0.0% |
| locations | 650 | 0 | 0.0% |
| order_items | 315,143 | 0 | 0.0% |
| orders | 163,200 | 3,200 | 1.9608% |
| payments | 168,111 | 3,296 | 1.9606% |
| products | 3,200 | 0 | 0.0% |
| returns | 16,048 | 0 | 0.0% |
| sellers | 420 | 0 | 0.0% |
| shipping | 151,228 | 0 | 0.0% |

## 3. High Missing or Placeholder Values (Columns with >0% missing)

| Table Name | Column Name | Total Rows | Exact Empty | Whitespace | Placeholders | Missing % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| orders | `discount_code` | 163,200 | 112,059 | 0 | 0 | **68.66%** |
| products | `sub_category` | 3,200 | 485 | 0 | 0 | **15.16%** |
| returns | `return_reason` | 16,048 | 2,390 | 0 | 0 | **14.89%** |
| shipping | `delivered_date` | 151,228 | 18,841 | 0 | 0 | **12.46%** |
| products | `brand` | 3,200 | 392 | 0 | 0 | **12.25%** |
| customers | `birth_year` | 45,000 | 4,600 | 0 | 0 | **10.22%** |
| order_items | `discount_amount` | 315,143 | 31,567 | 0 | 0 | **10.02%** |
| products | `weight_kg` | 3,200 | 296 | 0 | 0 | **9.25%** |
| sellers | `join_date` | 420 | 34 | 0 | 0 | **8.1%** |
| customers | `phone` | 45,000 | 3,599 | 0 | 0 | **8.0%** |
| sellers | `rating` | 420 | 33 | 0 | 0 | **7.86%** |
| shipping | `shipping_fee` | 151,228 | 9,145 | 0 | 0 | **6.05%** |
| products | `cost_price` | 3,200 | 170 | 0 | 0 | **5.31%** |
| sellers | `seller_tier` | 420 | 22 | 0 | 0 | **5.24%** |
| locations | `latitude` | 650 | 33 | 0 | 0 | **5.08%** |
| customers | `city_id` | 45,000 | 2,233 | 0 | 0 | **4.96%** |
| customers | `gender` | 45,000 | 2,199 | 0 | 0 | **4.89%** |
| locations | `longitude` | 650 | 31 | 0 | 0 | **4.77%** |
| orders | `ship_city_id` | 163,200 | 6,516 | 0 | 0 | **3.99%** |
| shipping | `shipped_date` | 151,228 | 5,943 | 0 | 0 | **3.93%** |
| locations | `province` | 650 | 25 | 0 | 0 | **3.85%** |
| customers | `email` | 45,000 | 1,698 | 0 | 0 | **3.77%** |
| payments | `payment_date` | 168,111 | 5,017 | 0 | 0 | **2.98%** |

## 4. Key Findings & Data Quality Highlights

### Casing & Formatting Variations
Columns with inconsistent casing detected (e.g. 'DELIVERD' vs 'Delivered', 'Refunded' vs 'REFUNDED'):
- **customers.gender** (Distinct variants: 9)
- **locations.province** (Distinct variants: 22)
- **orders.order_status** (Distinct variants: 20)
- **orders.discount_code** (Distinct variants: 33)
- **orders.channel** (Distinct variants: 12)
- **payments.payment_method** (Distinct variants: 22)
- **payments.payment_status** (Distinct variants: 17)
- **returns.return_reason** (Distinct variants: 38)
- **returns.return_status** (Distinct variants: 10)
- **sellers.seller_tier** (Distinct variants: 11)
- **shipping.courier** (Distinct variants: 22)
- **shipping.delivery_status** (Distinct variants: 15)

### Whitespace & Formatting Trailing Issues
- **customers.full_name**: 2,275 rows with leading/trailing whitespace.
- **locations.city**: 12 rows with leading/trailing whitespace.
- **locations.province**: 3 rows with leading/trailing whitespace.
- **orders.order_status**: 924 rows with leading/trailing whitespace.
- **orders.discount_code**: 2,099 rows with leading/trailing whitespace.
- **payments.payment_method**: 5,355 rows with leading/trailing whitespace.
- **payments.payment_status**: 757 rows with leading/trailing whitespace.
- **products.product_name**: 123 rows with leading/trailing whitespace.
- **products.category**: 641 rows with leading/trailing whitespace.
- **sellers.seller_name**: 15 rows with leading/trailing whitespace.
- **sellers.seller_tier**: 5 rows with leading/trailing whitespace.

### Currency Formatting in Numeric Columns
Columns with dirty currency strings (such as 'Rs. 2,290') requiring normalization:
- **order_items.quantity**: 965 rows contain non-standard numeric tokens.

## 5. Candidate Primary Keys Verification

| Table Name | Column Name | Total Rows | Unique Values | Duplicate Count | Is 100% Unique PK Candidate? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| customers | `customer_id` | 45,000 | 45,000 | 0 | ✅ YES |
| customers | `city_id` | 45,000 | 651 | 44,349 | ❌ NO (Duplicates or Nulls) |
| locations | `city_id` | 650 | 650 | 0 | ✅ YES |
| locations | `city` | 650 | 650 | 0 | ✅ YES |
| order_items | `order_item_id` | 315,143 | 315,143 | 0 | ✅ YES |
| order_items | `order_id` | 315,143 | 160,000 | 155,143 | ❌ NO (Duplicates or Nulls) |
| order_items | `product_id` | 315,143 | 4,086 | 311,057 | ❌ NO (Duplicates or Nulls) |
| order_items | `seller_id` | 315,143 | 407 | 314,736 | ❌ NO (Duplicates or Nulls) |
| orders | `order_id` | 163,200 | 160,000 | 3,200 | ❌ NO (Duplicates or Nulls) |
| orders | `customer_id` | 163,200 | 33,756 | 129,444 | ❌ NO (Duplicates or Nulls) |
| orders | `ship_city_id` | 163,200 | 651 | 162,549 | ❌ NO (Duplicates or Nulls) |
| payments | `payment_id` | 168,111 | 164,815 | 3,296 | ❌ NO (Duplicates or Nulls) |
| payments | `order_id` | 168,111 | 160,000 | 8,111 | ❌ NO (Duplicates or Nulls) |
| products | `product_id` | 3,200 | 3,200 | 0 | ✅ YES |
| products | `seller_id` | 3,200 | 407 | 2,793 | ❌ NO (Duplicates or Nulls) |
| returns | `return_id` | 16,048 | 16,048 | 0 | ✅ YES |
| returns | `order_item_id` | 16,048 | 16,048 | 0 | ✅ YES |
| sellers | `seller_id` | 420 | 420 | 0 | ✅ YES |
| sellers | `city_id` | 420 | 106 | 314 | ❌ NO (Duplicates or Nulls) |
| shipping | `shipment_id` | 151,228 | 151,228 | 0 | ✅ YES |
| shipping | `order_id` | 151,228 | 151,228 | 0 | ✅ YES |

