"""
Raw Data Profiler for NexusMart Datathon.

This module performs comprehensive, non-destructive profiling across all raw CSV files in data/raw/.
Safety rules strictly enforced:
- Zero data loss: never modifies, deletes, or alters original files in data/raw/.
- Never silently drops records or fabricates values.
- Categorizes hypotheses (identifiers, measures, dates, categories, statuses) without changing source types.
- Generates machine-readable CSV reports and a structured Markdown summary.
"""

import os
import re
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils.logging_config import setup_logger

logger = setup_logger("profiler")

# Suspected placeholder values to track across columns
SUSPICIOUS_PLACEHOLDERS = {
    "na", "n/a", "null", "none", "unknown", "nil", "?", "-", "--", "undefined", "empty"
}


def is_placeholder(val: str) -> bool:
    """Checks if a string representation matches known dirty placeholder tokens."""
    if not isinstance(val, str):
        return False
    cleaned = val.strip().lower()
    return cleaned in SUSPICIOUS_PLACEHOLDERS


def profile_single_file(file_path: Path, reports_dir: Path) -> dict:
    """
    Profiles a single raw CSV file without modifying its contents or altering data types prematurely.
    """
    table_name = file_path.stem
    logger.info(f"Profiling {table_name} from {file_path.name}...")

    # Read data with all columns as object (string) initially to preserve leading zeros, exact whitespace, dirty strings
    df_raw_str = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    row_count = len(df_raw_str)
    col_count = len(df_raw_str.columns)

    # Overview record
    overview = {
        "table_name": table_name,
        "filename": file_path.name,
        "row_count": row_count,
        "column_count": col_count,
        "column_names": ", ".join(df_raw_str.columns.tolist()),
        "file_size_bytes": file_path.stat().st_size
    }

    # Duplicate complete rows
    exact_duplicates_count = int(df_raw_str.duplicated().sum())
    duplicate_info = {
        "table_name": table_name,
        "total_rows": row_count,
        "exact_duplicate_rows": exact_duplicates_count,
        "exact_duplicate_pct": round((exact_duplicates_count / row_count * 100), 4) if row_count > 0 else 0.0
    }

    # Column-level profiles
    column_profiles = []
    missing_profiles = []
    candidate_key_profiles = []
    date_profiles = []
    numeric_profiles = []
    category_profiles = []

    for col in df_raw_str.columns:
        series_str = df_raw_str[col]

        # Whitespace and blank analysis
        is_whitespace_only = series_str.str.strip().eq("") & series_str.ne("")
        is_exact_empty = series_str.eq("")
        has_leading_trailing_ws = series_str.str.strip().ne(series_str) & ~is_exact_empty
        placeholder_mask = series_str.apply(is_placeholder)

        # Standard nulls in raw string import (empty string is the true missing in keep_default_na=False)
        missing_count = int((is_exact_empty | placeholder_mask).sum())
        missing_pct = round((missing_count / row_count * 100), 2) if row_count > 0 else 0.0

        blank_exact_count = int(is_exact_empty.sum())
        whitespace_count = int(is_whitespace_only.sum())
        leading_trailing_ws_count = int(has_leading_trailing_ws.sum())
        placeholder_count = int(placeholder_mask.sum())

        # Unique values
        unique_count = int(series_str.nunique())
        unique_pct = round((unique_count / row_count * 100), 2) if row_count > 0 else 0.0

        # Leading zero detection (e.g., "0123" that is numeric but has leading zeros)
        has_leading_zero = bool(
            series_str.str.match(r"^0\d+$").any()
        )

        # Inferred type hypothesis
        non_empty = series_str[~is_exact_empty & ~placeholder_mask]
        
        # Test numeric parseability on non-empty values
        # Strip currency symbols, commas if any to check
        cleaned_num_series = non_empty.str.replace(r"[Rs\.,\s]", "", regex=True)
        numeric_convertible = pd.to_numeric(non_empty, errors="coerce")
        numeric_count = int(numeric_convertible.notna().sum())

        # Test date parseability
        date_convertible = pd.to_datetime(non_empty, errors="coerce")
        date_count = int(date_convertible.notna().sum())

        type_hypothesis = "string"
        if len(non_empty) > 0:
            if numeric_count / len(non_empty) >= 0.8:
                type_hypothesis = "numeric_measure" if not has_leading_zero else "identifier_with_leading_zero"
            elif date_count / len(non_empty) >= 0.8:
                type_hypothesis = "date_time"
            elif col.endswith("_id") or col == "id":
                type_hypothesis = "candidate_identifier"
            elif unique_count <= 50 or (row_count > 1000 and unique_count <= 100):
                type_hypothesis = "category_or_status"

        # Refine candidate key hypothesis
        is_candidate_key = (unique_count == row_count) and (missing_count == 0)

        # Column profile record
        col_prof = {
            "table_name": table_name,
            "column_name": col,
            "inferred_type_hypothesis": type_hypothesis,
            "total_rows": row_count,
            "missing_or_placeholder_count": missing_count,
            "missing_pct": missing_pct,
            "unique_values_count": unique_count,
            "unique_pct": unique_pct,
            "leading_zeros_detected": has_leading_zero,
            "whitespace_issues_count": leading_trailing_ws_count + whitespace_count,
            "placeholder_count": placeholder_count,
            "sample_values": "; ".join(series_str.dropna().unique()[:3])
        }
        column_profiles.append(col_prof)

        # Missing values profile record
        missing_profiles.append({
            "table_name": table_name,
            "column_name": col,
            "total_rows": row_count,
            "exact_empty_count": blank_exact_count,
            "whitespace_only_count": whitespace_count,
            "placeholder_count": placeholder_count,
            "total_missing_or_placeholder": missing_count,
            "missing_pct": missing_pct
        })

        # Candidate key profile record
        candidate_key_profiles.append({
            "table_name": table_name,
            "column_name": col,
            "total_rows": row_count,
            "unique_values": unique_count,
            "duplicate_values_count": row_count - unique_count,
            "missing_count": missing_count,
            "is_unique_candidate_key": is_candidate_key,
            "hypothesis": "Primary Key Candidate" if is_candidate_key else ("Foreign Key / Non-Unique Attribute")
        })

        # Date profile if dates detected
        if type_hypothesis == "date_time" or "date" in col.lower():
            unparseable_mask = non_empty.notna() & date_convertible.isna()
            unparseable_examples = non_empty[unparseable_mask].unique()[:5].tolist()
            date_profiles.append({
                "table_name": table_name,
                "column_name": col,
                "total_non_empty": len(non_empty),
                "parseable_count": int(date_convertible.notna().sum()),
                "unparseable_count": int(unparseable_mask.sum()),
                "min_date": str(date_convertible.min()) if date_convertible.notna().any() else "N/A",
                "max_date": str(date_convertible.max()) if date_convertible.notna().any() else "N/A",
                "unparseable_examples": "; ".join([str(x) for x in unparseable_examples])
            })

        # Numeric profile if numeric detected
        if type_hypothesis in ("numeric_measure", "identifier_with_leading_zero") or any(kw in col.lower() for kw in ["amount", "price", "total", "fee", "quantity", "rating", "year", "latitude", "longitude"]):
            # Also attempt to parse strings with "Rs.", commas, etc.
            numeric_cleaned = non_empty.str.replace(r"[Rs\.,\s]", "", regex=True)
            num_series = pd.to_numeric(numeric_cleaned, errors="coerce")
            
            # Direct numeric attempt without stripping
            direct_num = pd.to_numeric(non_empty, errors="coerce")
            active_num = direct_num if direct_num.notna().sum() >= num_series.notna().sum() else num_series

            if active_num.notna().sum() > 0:
                clean_num = active_num.dropna()
                q25 = clean_num.quantile(0.25)
                q75 = clean_num.quantile(0.75)
                iqr = q75 - q25
                outliers_count = int(((clean_num < (q25 - 1.5 * iqr)) | (clean_num > (q75 + 1.5 * iqr))).sum())
                negative_count = int((clean_num < 0).sum())
                zero_count = int((clean_num == 0).sum())

                numeric_profiles.append({
                    "table_name": table_name,
                    "column_name": col,
                    "total_non_empty": len(non_empty),
                    "parseable_numeric_count": len(clean_num),
                    "unparseable_numeric_count": len(non_empty) - len(clean_num),
                    "min_value": clean_num.min(),
                    "max_value": clean_num.max(),
                    "mean_value": round(float(clean_num.mean()), 2),
                    "median_value": round(float(clean_num.median()), 2),
                    "zero_count": zero_count,
                    "negative_count": negative_count,
                    "possible_outliers_iqr": outliers_count
                })

        # Category profile for reasonable cardinality (<= 60 distinct values)
        if unique_count <= 60 and row_count > 0:
            val_counts = series_str.value_counts(dropna=False).head(20).to_dict()
            val_freq_str = "; ".join([f"{k!r}: {v}" for k, v in val_counts.items()])
            category_profiles.append({
                "table_name": table_name,
                "column_name": col,
                "cardinality": unique_count,
                "top_categories_and_counts": val_freq_str,
                "has_casing_variations": len(set(series_str.str.lower().unique())) < unique_count
            })

    return {
        "overview": overview,
        "duplicate_info": duplicate_info,
        "column_profiles": column_profiles,
        "missing_profiles": missing_profiles,
        "candidate_key_profiles": candidate_key_profiles,
        "date_profiles": date_profiles,
        "numeric_profiles": numeric_profiles,
        "category_profiles": category_profiles
    }


def run_full_profiling(raw_data_dir: Path, reports_dir: Path) -> None:
    """
    Executes profiling across all available CSV files in raw_data_dir, saving
    machine-readable CSVs and a structured Markdown summary.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(list(raw_data_dir.glob("*.csv")))

    if not csv_files:
        logger.error(f"No CSV files found in {raw_data_dir}")
        return

    all_overviews = []
    all_duplicates = []
    all_columns = []
    all_missing = []
    all_candidate_keys = []
    all_dates = []
    all_numerics = []
    all_categories = []

    for file_path in csv_files:
        res = profile_single_file(file_path, reports_dir)
        all_overviews.append(res["overview"])
        all_duplicates.append(res["duplicate_info"])
        all_columns.extend(res["column_profiles"])
        all_missing.extend(res["missing_profiles"])
        all_candidate_keys.extend(res["candidate_key_profiles"])
        all_dates.extend(res["date_profiles"])
        all_numerics.extend(res["numeric_profiles"])
        all_categories.extend(res["category_profiles"])

    # Export machine-readable CSVs
    logger.info("Exporting machine-readable CSV profiling reports...")
    pd.DataFrame(all_overviews).to_csv(reports_dir / "data_overview.csv", index=False)
    pd.DataFrame(all_duplicates).to_csv(reports_dir / "duplicate_rows.csv", index=False)
    pd.DataFrame(all_columns).to_csv(reports_dir / "column_profile.csv", index=False)
    pd.DataFrame(all_missing).to_csv(reports_dir / "missing_values.csv", index=False)
    pd.DataFrame(all_candidate_keys).to_csv(reports_dir / "candidate_key_profile.csv", index=False)
    pd.DataFrame(all_dates).to_csv(reports_dir / "date_profile.csv", index=False)
    pd.DataFrame(all_numerics).to_csv(reports_dir / "numeric_profile.csv", index=False)
    pd.DataFrame(all_categories).to_csv(reports_dir / "category_profile.csv", index=False)

    # Generate Markdown Summary
    summary_path = reports_dir / "profiling_summary.md"
    logger.info(f"Generating profiling summary markdown at {summary_path}...")
    generate_markdown_summary(
        summary_path,
        all_overviews,
        all_duplicates,
        all_columns,
        all_missing,
        all_candidate_keys,
        all_dates,
        all_numerics,
        all_categories
    )
    logger.info("Profiling completed successfully!")


def generate_markdown_summary(
    summary_path: Path,
    overviews: list,
    duplicates: list,
    columns: list,
    missing: list,
    candidate_keys: list,
    dates: list,
    numerics: list,
    categories: list
) -> None:
    """
    Renders an executive and technical summary of the profiling findings.
    """
    df_over = pd.DataFrame(overviews)
    df_dup = pd.DataFrame(duplicates)
    df_col = pd.DataFrame(columns)
    df_miss = pd.DataFrame(missing)
    df_keys = pd.DataFrame(candidate_keys)
    df_dates = pd.DataFrame(dates)
    df_num = pd.DataFrame(numerics)
    df_cat = pd.DataFrame(categories)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# NexusMart Datathon: Raw Data Profiling Summary Report\n\n")
        f.write("**Generated Automatically by Non-Destructive Profiler**\n")
        f.write("**Zero Data Loss Rule Enforced**: Raw source files in `data/raw/` untouched.\n\n")

        f.write("## 1. Dataset Overview\n\n")
        f.write("| Table Name | File Name | Rows | Columns | File Size (KB) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for _, r in df_over.iterrows():
            f.write(f"| **{r['table_name']}** | `{r['filename']}` | {r['row_count']:,} | {r['column_count']} | {round(r['file_size_bytes']/1024, 1):,} |\n")
        f.write("\n")

        f.write("## 2. Duplicate Complete Rows Analysis\n\n")
        f.write("| Table Name | Total Rows | Exact Duplicate Rows | Duplicate % |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for _, r in df_dup.iterrows():
            f.write(f"| {r['table_name']} | {r['total_rows']:,} | {r['exact_duplicate_rows']:,} | {r['exact_duplicate_pct']}% |\n")
        f.write("\n")

        f.write("## 3. High Missing or Placeholder Values (Columns with >0% missing)\n\n")
        suspicious_missing = df_miss[df_miss["missing_pct"] > 0].sort_values(by="missing_pct", ascending=False)
        if not suspicious_missing.empty:
            f.write("| Table Name | Column Name | Total Rows | Exact Empty | Whitespace | Placeholders | Missing % |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for _, r in suspicious_missing.iterrows():
                f.write(f"| {r['table_name']} | `{r['column_name']}` | {r['total_rows']:,} | {r['exact_empty_count']:,} | {r['whitespace_only_count']:,} | {r['placeholder_count']:,} | **{r['missing_pct']}%** |\n")
        else:
            f.write("No missing or placeholder values detected across all columns.\n")
        f.write("\n")

        f.write("## 4. Key Findings & Data Quality Highlights\n\n")
        f.write("### Casing & Formatting Variations\n")
        casing_issues = df_cat[df_cat["has_casing_variations"] == True]
        if not casing_issues.empty:
            f.write("Columns with inconsistent casing detected (e.g. 'DELIVERD' vs 'Delivered', 'Refunded' vs 'REFUNDED'):\n")
            for _, r in casing_issues.iterrows():
                f.write(f"- **{r['table_name']}.{r['column_name']}** (Distinct variants: {r['cardinality']})\n")
        else:
            f.write("No casing variations detected in categorical columns.\n")
        f.write("\n")

        f.write("### Whitespace & Formatting Trailing Issues\n")
        ws_issues = df_col[df_col["whitespace_issues_count"] > 0]
        if not ws_issues.empty:
            for _, r in ws_issues.iterrows():
                f.write(f"- **{r['table_name']}.{r['column_name']}**: {r['whitespace_issues_count']:,} rows with leading/trailing whitespace.\n")
        else:
            f.write("No whitespace issues detected.\n")
        f.write("\n")

        f.write("### Currency Formatting in Numeric Columns\n")
        unparsed_num = df_num[df_num["unparseable_numeric_count"] > 0]
        if not unparsed_num.empty:
            f.write("Columns with dirty currency strings (such as 'Rs. 2,290') requiring normalization:\n")
            for _, r in unparsed_num.iterrows():
                f.write(f"- **{r['table_name']}.{r['column_name']}**: {r['unparseable_numeric_count']:,} rows contain non-standard numeric tokens.\n")
        f.write("\n")

        f.write("## 5. Candidate Primary Keys Verification\n\n")
        f.write("| Table Name | Column Name | Total Rows | Unique Values | Duplicate Count | Is 100% Unique PK Candidate? |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for _, r in df_keys.iterrows():
            if r['is_unique_candidate_key'] or r['column_name'].endswith('_id'):
                status = "✅ YES" if r['is_unique_candidate_key'] else "❌ NO (Duplicates or Nulls)"
                f.write(f"| {r['table_name']} | `{r['column_name']}` | {r['total_rows']:,} | {r['unique_values']:,} | {r['duplicate_values_count']:,} | {status} |\n")
        f.write("\n")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = repo_root / "data" / "raw"
    reports_output_dir = repo_root / "reports" / "profiling"
    logger.info(f"Starting raw data profiling on {raw_dir}...")
    run_full_profiling(raw_dir, reports_output_dir)
