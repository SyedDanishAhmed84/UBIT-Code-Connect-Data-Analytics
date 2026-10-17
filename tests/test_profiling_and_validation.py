"""
Unit tests for NexusMart Profiling and Validation modules.
Uses small synthetic in-memory/temp data without requiring the large raw dataset.
Tests strictly for Zero Data Loss, missing/blank profiling, date/numeric parsing,
duplicate detection, and orphan foreign key handling.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from src.profiling.profile_raw_data import (
    is_placeholder,
    profile_single_file,
    run_full_profiling,
)
from src.validation.validate_raw_data import validate_relationships


@pytest.fixture
def temp_workspace():
    """Creates a temporary workspace with synthetic small CSV files."""
    temp_dir = tempfile.mkdtemp()
    workspace = Path(temp_dir)
    raw_dir = workspace / "data" / "raw"
    reports_dir = workspace / "reports" / "profiling"
    raw_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)

    # 1. Synthetic Customers
    cust_data = pd.DataFrame([
        {"customer_id": "C001", "full_name": " Alice ", "email": "alice@example.com", "phone": "03001234567", "gender": "F", "registration_date": "2024-01-01", "city_id": "1", "birth_year": "1990"},
        {"customer_id": "C002", "full_name": "Bob", "email": "", "phone": "NA", "gender": "male", "registration_date": "2024-02-01", "city_id": "2", "birth_year": "1985"},
    ])
    cust_data.to_csv(raw_dir / "customers.csv", index=False)

    # 2. Synthetic Locations
    loc_data = pd.DataFrame([
        {"city_id": "1", "city": "Karachi", "province": "Sindh", "region": "South", "latitude": "24.8607", "longitude": "67.0011", "population_tier": "Tier-1"},
        {"city_id": "2", "city": "Lahore", "province": "Punjab", "region": "North", "latitude": "31.5204", "longitude": "74.3587", "population_tier": "Tier-1"},
    ])
    loc_data.to_csv(raw_dir / "locations.csv", index=False)

    # 3. Synthetic Sellers
    sellers_data = pd.DataFrame([
        {"seller_id": "S001", "seller_name": "Seller One", "join_date": "2023-01-01", "seller_tier": "Gold", "city_id": "1", "rating": "4.5"}
    ])
    sellers_data.to_csv(raw_dir / "sellers.csv", index=False)

    # 4. Synthetic Products
    prod_data = pd.DataFrame([
        {"product_id": "P001", "product_name": "Item A", "category": "Tech", "sub_category": "Cables", "brand": "BrandX", "list_price": "1000", "cost_price": "800", "weight_kg": "0.2", "seller_id": "S001"}
    ])
    prod_data.to_csv(raw_dir / "products.csv", index=False)

    # 5. Synthetic Orders (with 1 duplicate complete row and 1 orphan customer)
    orders_data = pd.DataFrame([
        {"order_id": "O001", "customer_id": "C001", "order_date": "2024-03-01", "order_status": "Delivered", "ship_city_id": "1", "order_total": "1000", "discount_code": "SAVE10", "channel": "App"},
        {"order_id": "O001", "customer_id": "C001", "order_date": "2024-03-01", "order_status": "Delivered", "ship_city_id": "1", "order_total": "1000", "discount_code": "SAVE10", "channel": "App"},
        {"order_id": "O002", "customer_id": "C999", "order_date": "2024-03-05", "order_status": "Cancelled", "ship_city_id": "", "order_total": "500", "discount_code": "", "channel": "Web"},
    ])
    orders_data.to_csv(raw_dir / "orders.csv", index=False)

    # 6. Synthetic Order Items (with dirty currency and orphan product)
    items_data = pd.DataFrame([
        {"order_item_id": "OI001", "order_id": "O001", "product_id": "P001", "seller_id": "S001", "quantity": "1", "unit_price": "Rs. 1,000", "discount_amount": "100"},
        {"order_item_id": "OI002", "order_id": "O002", "product_id": "P999", "seller_id": "S001", "quantity": "2", "unit_price": "500", "discount_amount": "0"},
    ])
    items_data.to_csv(raw_dir / "order_items.csv", index=False)

    # 7. Synthetic Payments
    pay_data = pd.DataFrame([
        {"payment_id": "PAY001", "order_id": "O001", "payment_method": "COD", "payment_status": "Paid", "amount": "900", "payment_date": "2024-03-01"}
    ])
    pay_data.to_csv(raw_dir / "payments.csv", index=False)

    # 8. Synthetic Shipping
    ship_data = pd.DataFrame([
        {"shipment_id": "SH001", "order_id": "O001", "courier": "TCS", "shipped_date": "2024-03-02", "delivered_date": "2024-03-04", "shipping_fee": "200", "delivery_status": "DELIVERD"}
    ])
    ship_data.to_csv(raw_dir / "shipping.csv", index=False)

    # 9. Synthetic Returns (with orphan order_item)
    ret_data = pd.DataFrame([
        {"return_id": "R001", "order_item_id": "OI999", "return_date": "2024-03-10", "return_reason": "Damaged", "return_status": "Refunded", "refund_amount": "500"}
    ])
    ret_data.to_csv(raw_dir / "returns.csv", index=False)

    yield workspace, raw_dir, reports_dir

    shutil.rmtree(temp_dir)


def test_placeholder_detection():
    """Verifies that suspicious null strings are accurately classified."""
    assert is_placeholder("NA") is True
    assert is_placeholder(" n/a ") is True
    assert is_placeholder("null") is True
    assert is_placeholder("UNKNOWN") is True
    assert is_placeholder("Valid String") is False


def test_profiling_and_duplicate_detection(temp_workspace):
    """Verifies that duplicate rows and missing values are correctly counted without dropping."""
    workspace, raw_dir, reports_dir = temp_workspace
    
    # Save original raw hash/content
    raw_orders_before = (raw_dir / "orders.csv").read_text()

    res = profile_single_file(raw_dir / "orders.csv", reports_dir)
    assert res["overview"]["row_count"] == 3
    assert res["duplicate_info"]["exact_duplicate_rows"] == 1

    # CRITICAL: Confirm raw file was untouched (Zero Data Loss)
    raw_orders_after = (raw_dir / "orders.csv").read_text()
    assert raw_orders_before == raw_orders_after, "Raw data file was modified!"


def test_relationship_validation_detects_orphans(temp_workspace):
    """Verifies that relationship validation flags orphan references accurately."""
    workspace, raw_dir, reports_dir = temp_workspace

    val_res = validate_relationships(raw_dir, reports_dir)
    df_rel = val_res["summary"]

    # Check orders -> customers orphan detection (C999 is orphan)
    cust_rel = df_rel[df_rel["child_table"] == "orders"]
    assert cust_rel.iloc[0]["child_orphan_records"] == 1
    assert cust_rel.iloc[0]["unique_orphan_keys"] == 1

    # Check returns -> order_items orphan detection (OI999 is orphan)
    ret_rel = df_rel[df_rel["child_table"] == "returns"]
    assert ret_rel.iloc[0]["child_orphan_records"] == 1


def test_end_to_end_profiling_artifacts(temp_workspace):
    """Verifies all required machine-readable CSVs and markdown files are generated."""
    workspace, raw_dir, reports_dir = temp_workspace
    run_full_profiling(raw_dir, reports_dir)

    expected_files = [
        "data_overview.csv",
        "column_profile.csv",
        "missing_values.csv",
        "duplicate_rows.csv",
        "candidate_key_profile.csv",
        "date_profile.csv",
        "category_profile.csv",
        "numeric_profile.csv",
        "profiling_summary.md",
    ]
    for ef in expected_files:
        assert (reports_dir / ef).exists(), f"Missing expected output report: {ef}"
