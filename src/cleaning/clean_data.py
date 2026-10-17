"""
Zero-Data-Loss Cleaning and Normalization Pipeline for NexusMart Datathon.

Rules strictly enforced:
- ZERO DATA LOSS: Every input row is preserved in the cleaned output (input row count == cleaned row count).
- NEVER delete or overwrite raw files in data/raw/.
- NEVER drop duplicates, orphan keys, missing values, or invalid records.
- Idempotent and deterministic: writing to temp files first and atomically replacing targets.
- Preserves all original raw column values (either untouched or alongside clean variants).
- Computes SHA-256 hashes of raw files before and after cleaning to prove immutability.
- Adds comprehensive boolean audit flags and rejection/quarantine tracking in data/processed/rejects/.
"""

import hashlib
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
import numpy as np

from src.utils.logging_config import setup_logger

logger = setup_logger("cleaner")

# Recognized date formats
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%b %d %Y",
    "%B %d %Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y/%m/%d"
]

SUSPICIOUS_PLACEHOLDERS = {
    "na", "n/a", "null", "none", "unknown", "nil", "?", "-", "--", "undefined", "empty"
}

# English word mapping for quantities
WORD_TO_QUANTITY = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def parse_date_safe(val: str) -> Tuple[str | None, bool]:
    """
    Parses date string without losing data.
    Returns: (parsed_iso_str_or_None, is_invalid_date_flag)
    """
    if not val or not str(val).strip():
        return None, False
    s = str(val).strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            # Basic sanity check on year
            if 1900 <= dt.year <= 2100:
                return dt.strftime("%Y-%m-%d"), False
            else:
                return None, True
        except ValueError:
            pass
    return None, True


def parse_currency_amount_safe(val: str) -> Tuple[float | None, bool]:
    """
    Safely parses currency amounts (e.g. 'Rs. 2,290', '1400', ' 50.5 ')
    Returns: (numeric_val_or_None, is_invalid_numeric_flag)
    """
    if not val or not str(val).strip():
        return None, False
    s = str(val).strip()
    cleaned = re.sub(r"[Rs\.,\s]", "", s) if "Rs" in s or "," in s else s
    try:
        num = float(cleaned)
        return num, False
    except ValueError:
        return None, True


def normalize_quantity_safe(val: str) -> Tuple[int | None, bool, bool]:
    """
    Parses quantity string ('1', '1.0', 'two', '-4')
    Returns: (integer_val_or_None, is_negative, is_invalid)
    """
    if not val or not str(val).strip():
        return None, False, False
    s = str(val).strip().lower()
    if s in WORD_TO_QUANTITY:
        return WORD_TO_QUANTITY[s], False, False
    try:
        f = float(s)
        i = int(f)
        if f == i:
            return i, (i < 0), False
        else:
            return None, False, True
    except ValueError:
        return None, False, True


def safe_atomic_write(df: pd.DataFrame, target_path: Path) -> None:
    """Writes dataframe to temp file first, then atomically renames to target."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = target_path.parent / ".tmp_atomic"
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8", newline="") as tf:
        temp_name = tf.name
        df.to_csv(tf, index=False)
    shutil.move(temp_name, target_path)
    try:
        temp_dir.rmdir()
    except OSError:
        pass


class NexusMartCleaningPipeline:
    """
    Executes the comprehensive, zero-data-loss cleaning pipeline across all 9 raw files.
    """

    def __init__(self, raw_dir: Path, cleaned_dir: Path, rejects_dir: Path, reports_dir: Path):
        self.raw_dir = raw_dir
        self.cleaned_dir = cleaned_dir
        self.rejects_dir = rejects_dir
        self.reports_dir = reports_dir

        self.reconciliation_records = []
        self.initial_hashes = {}
        self.final_hashes = {}

    def capture_raw_hashes(self) -> Dict[str, str]:
        """Calculates and stores initial SHA-256 hashes of all raw CSV files."""
        hashes = {}
        for p in sorted(self.raw_dir.glob("*.csv")):
            hashes[p.name] = compute_file_sha256(p)
        return hashes

    def verify_raw_immutability(self) -> bool:
        """Verifies that no raw file has been changed in any way."""
        current_hashes = self.capture_raw_hashes()
        for name, initial_hash in self.initial_hashes.items():
            if current_hashes.get(name) != initial_hash:
                logger.error(f"FATAL: Raw file {name} was modified! Hash mismatch!")
                return False
        return True

    def run(self) -> pd.DataFrame:
        """Runs the complete cleaning pipeline."""
        logger.info("Initializing Zero-Data-Loss Cleaning Pipeline...")
        self.initial_hashes = self.capture_raw_hashes()

        # Step 1: Load all raw data as strings with keep_default_na=False to prevent silent nullification
        logger.info("Loading all 9 raw files as raw strings...")
        raw_tables = {
            p.stem: pd.read_csv(p, dtype=str, keep_default_na=False)
            for p in sorted(self.raw_dir.glob("*.csv"))
        }

        # Step 2: Clean each table conservatively and append audit flags
        cleaned_tables = self.clean_all_tables(raw_tables)

        # Step 3: Write cleaned outputs atomically
        for table_name, df_clean in cleaned_tables.items():
            out_file = self.cleaned_dir / f"{table_name}.csv"
            logger.info(f"Writing cleaned {table_name} ({len(df_clean):,} rows) to {out_file}...")
            safe_atomic_write(df_clean, out_file)

        # Step 4: Write reject / quarantine copies (copies of records with issues, never removed from cleaned)
        self.export_quarantine_reports(cleaned_tables)

        # Step 5: Verify immutability of raw files
        assert self.verify_raw_immutability(), "Raw files were altered during cleaning!"

        # Step 6: Generate reconciliation dataframe and CSV
        df_reconciliation = pd.DataFrame(self.reconciliation_records)
        reconcil_csv = self.reports_dir / "cleaning_reconciliation.csv"
        safe_atomic_write(df_reconciliation, reconcil_csv)
        logger.info(f"Reconciliation report generated at {reconcil_csv}")

        return df_reconciliation

    def clean_all_tables(self, raw_tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Cleans and annotates each table with explicit audit columns."""
        cleaned = {}

        # Pre-extract primary key sets for foreign-key validation
        valid_cust_ids = set(raw_tables["customers"]["customer_id"].unique())
        valid_loc_city_ids = set(raw_tables["locations"]["city_id"].unique())
        valid_seller_ids = set(raw_tables["sellers"]["seller_id"].unique())
        valid_prod_ids = set(raw_tables["products"]["product_id"].unique())
        valid_order_ids = set(raw_tables["orders"]["order_id"].unique())
        valid_item_ids = set(raw_tables["order_items"]["order_item_id"].unique())

        # 1. CLEAN LOCATIONS
        logger.info("Processing locations.csv...")
        df_loc = raw_tables["locations"].copy()
        input_count = len(df_loc)
        df_loc["is_exact_duplicate"] = df_loc.duplicated(keep=False)
        df_loc["has_missing_required_value"] = df_loc["city"].eq("") | df_loc["city_id"].eq("")
        
        # Numeric lat/long
        df_loc["latitude_val"] = pd.to_numeric(df_loc["latitude"], errors="coerce")
        df_loc["longitude_val"] = pd.to_numeric(df_loc["longitude"], errors="coerce")
        df_loc["has_invalid_numeric_value"] = (df_loc["latitude"].ne("") & df_loc["latitude_val"].isna()) | \
                                              (df_loc["longitude"].ne("") & df_loc["longitude_val"].isna())
        df_loc["has_orphan_reference"] = False
        df_loc["audit_issue_codes"] = ""
        df_loc.loc[df_loc["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_loc.loc[df_loc["has_missing_required_value"], "audit_issue_codes"] += "MISSING_REQUIRED;"
        df_loc.loc[df_loc["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_COORDINATES;"
        
        cleaned["locations"] = df_loc
        self._record_reconciliation("locations.csv", input_count, df_loc)

        # 2. CLEAN CUSTOMERS
        logger.info("Processing customers.csv...")
        df_cust = raw_tables["customers"].copy()
        input_count = len(df_cust)
        df_cust["is_exact_duplicate"] = df_cust.duplicated(keep=False)
        df_cust["has_missing_required_value"] = df_cust["customer_id"].eq("") | df_cust["full_name"].eq("")
        
        # Gender normalization (retaining raw in raw_gender)
        df_cust["raw_gender"] = df_cust["gender"]
        gender_map = {
            "m": "M", "male": "M",
            "f": "F", "female": "F"
        }
        df_cust["normalized_gender"] = df_cust["raw_gender"].str.strip().str.lower().map(gender_map)
        df_cust.loc[df_cust["raw_gender"].str.strip().isin(["M", "F"]), "normalized_gender"] = df_cust["raw_gender"].str.strip()
        df_cust["has_unknown_category"] = df_cust["raw_gender"].ne("") & df_cust["normalized_gender"].isna()

        # Date parsing
        dates_parsed = [parse_date_safe(x) for x in df_cust["registration_date"]]
        df_cust["parsed_registration_date"] = [p[0] for p in dates_parsed]
        df_cust["has_invalid_date"] = [p[1] for p in dates_parsed]

        # Birth year numeric
        birth_year_num = pd.to_numeric(df_cust["birth_year"], errors="coerce")
        df_cust["has_invalid_numeric_value"] = df_cust["birth_year"].ne("") & (birth_year_num.isna() | (birth_year_num < 1920) | (birth_year_num > 2025))

        # Orphan city_id
        df_cust["has_orphan_reference"] = df_cust["city_id"].ne("") & ~df_cust["city_id"].isin(valid_loc_city_ids)

        df_cust["audit_issue_codes"] = ""
        df_cust.loc[df_cust["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_cust.loc[df_cust["has_missing_required_value"], "audit_issue_codes"] += "MISSING_REQUIRED;"
        df_cust.loc[df_cust["has_invalid_date"], "audit_issue_codes"] += "INVALID_DATE;"
        df_cust.loc[df_cust["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_BIRTH_YEAR;"
        df_cust.loc[df_cust["has_orphan_reference"], "audit_issue_codes"] += "ORPHAN_CITY_ID;"
        df_cust.loc[df_cust["has_unknown_category"], "audit_issue_codes"] += "UNKNOWN_GENDER;"

        cleaned["customers"] = df_cust
        self._record_reconciliation("customers.csv", input_count, df_cust)

        # 3. CLEAN SELLERS
        logger.info("Processing sellers.csv...")
        df_sell = raw_tables["sellers"].copy()
        input_count = len(df_sell)
        df_sell["is_exact_duplicate"] = df_sell.duplicated(keep=False)
        df_sell["has_missing_required_value"] = df_sell["seller_id"].eq("") | df_sell["seller_name"].eq("")
        
        # Tier normalization
        df_sell["raw_seller_tier"] = df_sell["seller_tier"]
        tier_map = {
            "bronze": "Bronze", "silver": "Silver", "gold": "Gold"
        }
        df_sell["normalized_seller_tier"] = df_sell["raw_seller_tier"].str.strip().str.lower().map(tier_map)
        df_sell["has_unknown_category"] = df_sell["raw_seller_tier"].ne("") & df_sell["normalized_seller_tier"].isna()

        # Date parsing
        dates_parsed = [parse_date_safe(x) for x in df_sell["join_date"]]
        df_sell["parsed_join_date"] = [p[0] for p in dates_parsed]
        df_sell["has_invalid_date"] = [p[1] for p in dates_parsed]

        # Rating numeric
        rating_num = pd.to_numeric(df_sell["rating"], errors="coerce")
        df_sell["has_invalid_numeric_value"] = df_sell["rating"].ne("") & (rating_num.isna() | (rating_num < 0) | (rating_num > 5.0))

        # Orphan city_id
        df_sell["has_orphan_reference"] = df_sell["city_id"].ne("") & ~df_sell["city_id"].isin(valid_loc_city_ids)

        df_sell["audit_issue_codes"] = ""
        df_sell.loc[df_sell["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_sell.loc[df_sell["has_invalid_date"], "audit_issue_codes"] += "INVALID_JOIN_DATE;"
        df_sell.loc[df_sell["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_RATING;"
        df_sell.loc[df_sell["has_orphan_reference"], "audit_issue_codes"] += "ORPHAN_CITY_ID;"

        cleaned["sellers"] = df_sell
        self._record_reconciliation("sellers.csv", input_count, df_sell)

        # 4. CLEAN PRODUCTS
        logger.info("Processing products.csv...")
        df_prod = raw_tables["products"].copy()
        input_count = len(df_prod)
        df_prod["is_exact_duplicate"] = df_prod.duplicated(keep=False)
        df_prod["has_missing_required_value"] = df_prod["product_id"].eq("") | df_prod["product_name"].eq("")

        # Numeric price & weight
        lp_num = pd.to_numeric(df_prod["list_price"], errors="coerce")
        cp_num = pd.to_numeric(df_prod["cost_price"], errors="coerce")
        wt_num = pd.to_numeric(df_prod["weight_kg"], errors="coerce")
        df_prod["has_invalid_numeric_value"] = (df_prod["list_price"].ne("") & lp_num.isna()) | \
                                               (df_prod["cost_price"].ne("") & cp_num.isna()) | \
                                               (df_prod["weight_kg"].ne("") & wt_num.isna())
        
        # Orphan seller_id
        df_prod["has_orphan_reference"] = df_prod["seller_id"].ne("") & ~df_prod["seller_id"].isin(valid_seller_ids)

        df_prod["audit_issue_codes"] = ""
        df_prod.loc[df_prod["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_prod.loc[df_prod["has_missing_required_value"], "audit_issue_codes"] += "MISSING_REQUIRED;"
        df_prod.loc[df_prod["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_PRICE_OR_WEIGHT;"
        df_prod.loc[df_prod["has_orphan_reference"], "audit_issue_codes"] += "ORPHAN_SELLER_ID;"

        cleaned["products"] = df_prod
        self._record_reconciliation("products.csv", input_count, df_prod)

        # 5. CLEAN ORDERS
        logger.info("Processing orders.csv...")
        df_ord = raw_tables["orders"].copy()
        input_count = len(df_ord)
        df_ord["is_exact_duplicate"] = df_ord.duplicated(keep=False)
        df_ord["has_missing_required_value"] = df_ord["order_id"].eq("") | df_ord["customer_id"].eq("")

        # Order status normalization (retain raw in raw_order_status)
        df_ord["raw_order_status"] = df_ord["order_status"]
        status_map = {
            "delivered": "DELIVERED", "deliverd": "DELIVERED",
            "complete": "COMPLETED", "completed": "COMPLETED",
            "cancelled": "CANCELLED", "canceled": "CANCELLED",
            "returned": "RETURNED", "return": "RETURNED",
            "in transit": "IN_TRANSIT", "in-transit": "IN_TRANSIT",
            "shipped": "SHIPPED"
        }
        df_ord["normalized_order_status"] = df_ord["raw_order_status"].str.strip().str.lower().map(status_map)
        df_ord["has_unknown_category"] = df_ord["raw_order_status"].ne("") & df_ord["normalized_order_status"].isna()

        # Date parsing
        dates_parsed = [parse_date_safe(x) for x in df_ord["order_date"]]
        df_ord["parsed_order_date"] = [p[0] for p in dates_parsed]
        df_ord["has_invalid_date"] = [p[1] for p in dates_parsed]

        # Numeric order_total
        tot_num = pd.to_numeric(df_ord["order_total"], errors="coerce")
        df_ord["order_total_pkr"] = tot_num
        df_ord["has_invalid_numeric_value"] = df_ord["order_total"].ne("") & (tot_num.isna() | (tot_num < 0))

        # Discount rate parsing
        df_ord["raw_discount_code"] = df_ord["discount_code"]
        discount_rates = []
        for code in df_ord["raw_discount_code"]:
            c = code.strip().upper()
            if not c:
                discount_rates.append(0.0)
            elif c.startswith("SAVE"):
                digits = re.findall(r"\d+", c)
                discount_rates.append(float(digits[0])/100.0 if digits else None)
            else:
                discount_rates.append(None)
        df_ord["discount_rate"] = discount_rates

        # Orphan references (customer_id & ship_city_id)
        df_ord["has_orphan_customer"] = df_ord["customer_id"].ne("") & ~df_ord["customer_id"].isin(valid_cust_ids)
        df_ord["has_orphan_city"] = df_ord["ship_city_id"].ne("") & ~df_ord["ship_city_id"].isin(valid_loc_city_ids)
        df_ord["has_orphan_reference"] = df_ord["has_orphan_customer"] | df_ord["has_orphan_city"]

        df_ord["audit_issue_codes"] = ""
        df_ord.loc[df_ord["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_ord.loc[df_ord["has_invalid_date"], "audit_issue_codes"] += "INVALID_ORDER_DATE;"
        df_ord.loc[df_ord["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_ORDER_TOTAL;"
        df_ord.loc[df_ord["has_orphan_customer"], "audit_issue_codes"] += "ORPHAN_CUSTOMER_ID;"
        df_ord.loc[df_ord["has_orphan_city"], "audit_issue_codes"] += "ORPHAN_SHIP_CITY_ID;"

        cleaned["orders"] = df_ord
        self._record_reconciliation("orders.csv", input_count, df_ord)

        # 6. CLEAN ORDER_ITEMS
        logger.info("Processing order_items.csv...")
        df_items = raw_tables["order_items"].copy()
        input_count = len(df_items)
        df_items["is_exact_duplicate"] = df_items.duplicated(keep=False)
        df_items["has_missing_required_value"] = df_items["order_item_id"].eq("") | df_items["order_id"].eq("") | df_items["product_id"].eq("")

        # Safe parsing of unit_price (e.g. 'Rs. 2,290')
        df_items["raw_unit_price"] = df_items["unit_price"]
        parsed_prices = [parse_currency_amount_safe(x) for x in df_items["raw_unit_price"]]
        df_items["unit_price_pkr"] = [p[0] for p in parsed_prices]
        invalid_price_flags = [p[1] for p in parsed_prices]

        # Safe parsing of quantity (words like 'two', '1.0', '-4')
        df_items["raw_quantity"] = df_items["quantity"]
        parsed_quantities = [normalize_quantity_safe(x) for x in df_items["raw_quantity"]]
        df_items["normalized_quantity"] = [q[0] for q in parsed_quantities]
        df_items["has_negative_quantity"] = [q[1] for q in parsed_quantities]
        invalid_qty_flags = [q[2] for q in parsed_quantities]

        # Discount amount
        df_items["raw_discount_amount"] = df_items["discount_amount"]
        disc_num = pd.to_numeric(df_items["raw_discount_amount"], errors="coerce")
        df_items["discount_amount_pkr"] = disc_num
        invalid_disc_flags = df_items["raw_discount_amount"].ne("") & disc_num.isna()

        # Convert to boolean series for bitwise OR
        s_inv_price = pd.Series(invalid_price_flags, index=df_items.index)
        s_inv_qty = pd.Series(invalid_qty_flags, index=df_items.index)
        s_inv_disc = pd.Series(invalid_disc_flags, index=df_items.index)
        df_items["has_invalid_numeric_value"] = s_inv_price | s_inv_qty | s_inv_disc

        # Orphan references (orders, products, sellers)
        df_items["has_orphan_order"] = df_items["order_id"].ne("") & ~df_items["order_id"].isin(valid_order_ids)
        df_items["has_orphan_product"] = df_items["product_id"].ne("") & ~df_items["product_id"].isin(valid_prod_ids)
        df_items["has_orphan_seller"] = df_items["seller_id"].ne("") & ~df_items["seller_id"].isin(valid_seller_ids)
        df_items["has_orphan_reference"] = df_items["has_orphan_order"] | df_items["has_orphan_product"] | df_items["has_orphan_seller"]

        df_items["audit_issue_codes"] = ""
        df_items.loc[df_items["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_items.loc[df_items["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_NUMERIC;"
        df_items.loc[df_items["has_negative_quantity"], "audit_issue_codes"] += "NEGATIVE_QUANTITY;"
        df_items.loc[df_items["has_orphan_product"], "audit_issue_codes"] += "ORPHAN_PRODUCT_ID;"
        df_items.loc[df_items["has_orphan_order"], "audit_issue_codes"] += "ORPHAN_ORDER_ID;"
        df_items.loc[df_items["has_orphan_seller"], "audit_issue_codes"] += "ORPHAN_SELLER_ID;"

        cleaned["order_items"] = df_items
        self._record_reconciliation("order_items.csv", input_count, df_items)

        # 7. CLEAN PAYMENTS
        logger.info("Processing payments.csv...")
        df_pay = raw_tables["payments"].copy()
        input_count = len(df_pay)
        df_pay["is_exact_duplicate"] = df_pay.duplicated(keep=False)
        df_pay["has_missing_required_value"] = df_pay["payment_id"].eq("") | df_pay["order_id"].eq("")

        # Payment status normalization
        df_pay["raw_payment_status"] = df_pay["payment_status"]
        pay_status_map = {
            "paid": "PAID", "complete": "PAID", "success": "PAID",
            "cancelled": "CANCELLED", "canceled": "CANCELLED",
            "refunded": "REFUNDED", "refund": "REFUNDED",
            "pending": "PENDING"
        }
        df_pay["normalized_payment_status"] = df_pay["raw_payment_status"].str.strip().str.lower().map(pay_status_map)
        df_pay["has_unknown_category"] = df_pay["raw_payment_status"].ne("") & df_pay["normalized_payment_status"].isna()

        # Payment method normalization
        df_pay["raw_payment_method"] = df_pay["payment_method"]
        method_map = {
            "cod": "COD", "cash on delivery": "COD",
            "card": "CARD", "credit/debit card": "CARD", "debit card": "CARD",
            "jazzcash": "JAZZCASH", "jazz cash": "JAZZCASH",
            "easypaisa": "EASYPAISA", "easy paisa": "EASYPAISA",
            "bank transfer": "BANK_TRANSFER", "bank trf": "BANK_TRANSFER"
        }
        df_pay["normalized_payment_method"] = df_pay["raw_payment_method"].str.strip().str.lower().map(method_map)

        # Numeric amount
        amt_num = pd.to_numeric(df_pay["amount"], errors="coerce")
        df_pay["amount_pkr"] = amt_num
        df_pay["has_invalid_numeric_value"] = df_pay["amount"].ne("") & (amt_num.isna() | (amt_num < 0))

        # Date parsing
        dates_parsed = [parse_date_safe(x) for x in df_pay["payment_date"]]
        df_pay["parsed_payment_date"] = [p[0] for p in dates_parsed]
        df_pay["has_invalid_date"] = [p[1] for p in dates_parsed]

        # Orphan order_id
        df_pay["has_orphan_reference"] = df_pay["order_id"].ne("") & ~df_pay["order_id"].isin(valid_order_ids)

        df_pay["audit_issue_codes"] = ""
        df_pay.loc[df_pay["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_pay.loc[df_pay["has_invalid_date"], "audit_issue_codes"] += "INVALID_PAYMENT_DATE;"
        df_pay.loc[df_pay["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_AMOUNT;"
        df_pay.loc[df_pay["has_orphan_reference"], "audit_issue_codes"] += "ORPHAN_ORDER_ID;"

        cleaned["payments"] = df_pay
        self._record_reconciliation("payments.csv", input_count, df_pay)

        # 8. CLEAN SHIPPING
        logger.info("Processing shipping.csv...")
        df_ship = raw_tables["shipping"].copy()
        input_count = len(df_ship)
        df_ship["is_exact_duplicate"] = df_ship.duplicated(keep=False)
        df_ship["has_missing_required_value"] = df_ship["shipment_id"].eq("") | df_ship["order_id"].eq("")

        # Courier normalization
        df_ship["raw_courier"] = df_ship["courier"]
        courier_map = {
            "tcs": "TCS", "tcs express": "TCS", "t.c.s": "TCS",
            "leopards": "LEOPARDS", "leopard courier": "LEOPARDS",
            "trax": "TRAX", "postex": "POSTEX", "blueex": "BLUEEX",
            "blue ex": "BLUEEX", "blue-ex": "BLUEEX", "m&p": "M&P",
            "m & p": "M&P", "mnp": "M&P"
        }
        df_ship["normalized_courier"] = df_ship["raw_courier"].str.strip().str.lower().map(courier_map)

        # Delivery status normalization
        df_ship["raw_delivery_status"] = df_ship["delivery_status"]
        del_status_map = {
            "delivered": "DELIVERED", "deliverd": "DELIVERED",
            "complete": "COMPLETED", "completed": "COMPLETED",
            "returned to seller": "RETURNED_TO_SELLER", "return to seller": "RETURNED_TO_SELLER",
            "rto": "RETURNED_TO_SELLER",
            "in transit": "IN_TRANSIT", "in-transit": "IN_TRANSIT",
            "shipped": "SHIPPED"
        }
        df_ship["normalized_delivery_status"] = df_ship["raw_delivery_status"].str.strip().str.lower().map(del_status_map)

        # Dates
        ship_dates = [parse_date_safe(x) for x in df_ship["shipped_date"]]
        del_dates = [parse_date_safe(x) for x in df_ship["delivered_date"]]
        df_ship["parsed_shipped_date"] = [p[0] for p in ship_dates]
        df_ship["parsed_delivered_date"] = [p[0] for p in del_dates]
        df_ship["has_invalid_date"] = [p[1] for p in ship_dates] | np.array([p[1] for p in del_dates])

        # Shipping fee numeric
        fee_num = pd.to_numeric(df_ship["shipping_fee"], errors="coerce")
        df_ship["shipping_fee_pkr"] = fee_num
        df_ship["has_invalid_numeric_value"] = df_ship["shipping_fee"].ne("") & (fee_num.isna() | (fee_num < 0))

        # Orphan order_id
        df_ship["has_orphan_reference"] = df_ship["order_id"].ne("") & ~df_ship["order_id"].isin(valid_order_ids)

        df_ship["audit_issue_codes"] = ""
        df_ship.loc[df_ship["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_ship.loc[df_ship["has_invalid_date"], "audit_issue_codes"] += "INVALID_DATE;"
        df_ship.loc[df_ship["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_SHIPPING_FEE;"
        df_ship.loc[df_ship["has_orphan_reference"], "audit_issue_codes"] += "ORPHAN_ORDER_ID;"

        cleaned["shipping"] = df_ship
        self._record_reconciliation("shipping.csv", input_count, df_ship)

        # 9. CLEAN RETURNS
        logger.info("Processing returns.csv...")
        df_ret = raw_tables["returns"].copy()
        input_count = len(df_ret)
        df_ret["is_exact_duplicate"] = df_ret.duplicated(keep=False)
        df_ret["has_missing_required_value"] = df_ret["return_id"].eq("") | df_ret["order_item_id"].eq("")

        # Return status normalization
        df_ret["raw_return_status"] = df_ret["return_status"]
        ret_status_map = {
            "refunded": "REFUNDED", "refund": "REFUNDED",
            "approved": "APPROVED",
            "rejected": "REJECTED", "declined": "REJECTED"
        }
        df_ret["normalized_return_status"] = df_ret["raw_return_status"].str.strip().str.lower().map(ret_status_map)
        df_ret["is_real_return"] = df_ret["normalized_return_status"].ne("REJECTED")

        # Date parsing
        dates_parsed = [parse_date_safe(x) for x in df_ret["return_date"]]
        df_ret["parsed_return_date"] = [p[0] for p in dates_parsed]
        df_ret["has_invalid_date"] = [p[1] for p in dates_parsed]

        # Numeric refund amount
        ref_num = pd.to_numeric(df_ret["refund_amount"], errors="coerce")
        df_ret["refund_amount_pkr"] = ref_num
        df_ret["has_invalid_numeric_value"] = df_ret["refund_amount"].ne("") & (ref_num.isna() | (ref_num < 0))

        # Orphan order_item_id
        df_ret["has_orphan_reference"] = df_ret["order_item_id"].ne("") & ~df_ret["order_item_id"].isin(valid_item_ids)

        df_ret["audit_issue_codes"] = ""
        df_ret.loc[df_ret["is_exact_duplicate"], "audit_issue_codes"] += "EXACT_DUPLICATE;"
        df_ret.loc[df_ret["has_invalid_date"], "audit_issue_codes"] += "INVALID_RETURN_DATE;"
        df_ret.loc[df_ret["has_invalid_numeric_value"], "audit_issue_codes"] += "INVALID_REFUND_AMOUNT;"
        df_ret.loc[df_ret["has_orphan_reference"], "audit_issue_codes"] += "ORPHAN_ORDER_ITEM_ID;"

        cleaned["returns"] = df_ret
        self._record_reconciliation("returns.csv", input_count, df_ret)

        return cleaned

    def export_quarantine_reports(self, cleaned_tables: Dict[str, pd.DataFrame]) -> None:
        """
        Exports copies of flagged records to data/processed/rejects/.
        CRITICAL NOTE: Records are COPIED to quarantine for audit inspection,
        NEVER removed from the cleaned output.
        """
        self.rejects_dir.mkdir(parents=True, exist_ok=True)
        for name, df in cleaned_tables.items():
            issue_mask = df["audit_issue_codes"].ne("")
            df_quarantine = df[issue_mask]
            quarantine_path = self.rejects_dir / f"quarantine_{name}.csv"
            safe_atomic_write(df_quarantine, quarantine_path)
            logger.info(f"Quarantined {len(df_quarantine):,} flagged rows to {quarantine_path.name}")

    def _record_reconciliation(self, source_filename: str, input_count: int, df_cleaned: pd.DataFrame) -> None:
        """Records row-count reconciliation and flag counts."""
        output_count = len(df_cleaned)
        diff = output_count - input_count
        exact_dups = int(df_cleaned["is_exact_duplicate"].sum())
        missing_vals = int(df_cleaned["has_missing_required_value"].sum()) if "has_missing_required_value" in df_cleaned else 0
        invalid_vals = int(df_cleaned["has_invalid_numeric_value"].sum()) if "has_invalid_numeric_value" in df_cleaned else 0
        if "has_invalid_date" in df_cleaned:
            invalid_vals += int(df_cleaned["has_invalid_date"].sum())
        orphans = int(df_cleaned["has_orphan_reference"].sum()) if "has_orphan_reference" in df_cleaned else 0
        quarantine_count = int(df_cleaned["audit_issue_codes"].ne("").sum())

        status = "100% PRESERVED (ZERO DATA LOSS)" if diff == 0 else f"ERROR: DIFF {diff}"

        self.reconciliation_records.append({
            "source_filename": source_filename,
            "input_row_count": input_count,
            "cleaned_output_row_count": output_count,
            "exact_duplicate_rows_flagged": exact_dups,
            "rows_with_missing_values_flagged": missing_vals,
            "rows_with_invalid_values_flagged": invalid_vals,
            "orphan_reference_rows_flagged": orphans,
            "quarantine_copy_count": quarantine_count,
            "unexplained_row_count_difference": diff,
            "preservation_status": status
        })


def run_cleaning_pipeline(raw_dir: Path, cleaned_dir: Path, rejects_dir: Path, reports_dir: Path) -> pd.DataFrame:
    """Entry point for the cleaning pipeline."""
    pipeline = NexusMartCleaningPipeline(raw_dir, cleaned_dir, rejects_dir, reports_dir)
    return pipeline.run()


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_path = repo_root / "data" / "raw"
    clean_path = repo_root / "data" / "processed" / "cleaned"
    reject_path = repo_root / "data" / "processed" / "rejects"
    report_path = repo_root / "reports" / "profiling"

    logger.info("Executing clean_data.py module...")
    run_cleaning_pipeline(raw_path, clean_path, reject_path, report_path)
