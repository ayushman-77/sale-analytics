"""
ETL Pipeline — Festive E-Commerce Sales Dashboard
====================================================
A production-style ETL pipeline with three stages:
  Stage 1: DATA PROFILING   — Automated quality assessment of raw data
  Stage 2: DATA CLEANING    — Rule-based transformations with full audit trail
  Stage 3: DATA VALIDATION  — Schema and business-rule checks on cleaned output

Usage:
    from pipeline.etl_pipeline import ETLPipeline
    pipeline = ETLPipeline()
    pipeline.run()
"""

import os, sys, time, json, logging
from datetime import datetime
from collections import OrderedDict

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════════════

def setup_logger():
    os.makedirs(cfg.REPORTS_DIR, exist_ok=True)
    logger = logging.getLogger("ETL")
    logger.setLevel(logging.DEBUG)
    # File handler
    fh = logging.FileHandler(cfg.PIPELINE_LOG_PATH, mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s │ %(levelname)-8s │ %(message)s"))
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("  %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

log = setup_logger()


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 1: DATA PROFILER
# ═══════════════════════════════════════════════════════════════════════════

class DataProfiler:
    """Generates an automated data quality report for any DataFrame."""

    def __init__(self, df: pd.DataFrame, name: str = "Dataset"):
        self.df = df
        self.name = name
        self.profile = {}

    def run(self) -> dict:
        log.info("─" * 60)
        log.info("STAGE 1: DATA PROFILING")
        log.info("─" * 60)
        start = time.time()

        self.profile = {
            "dataset_name": self.name,
            "generated_at": datetime.now().isoformat(),
            "shape": {"rows": len(self.df), "columns": len(self.df.columns)},
            "memory_mb": round(self.df.memory_usage(deep=True).sum() / 1024**2, 2),
            "duplicate_rows": int(self.df.duplicated().sum()),
            "columns": {},
        }

        for col in self.df.columns:
            series = self.df[col]
            col_profile = {
                "dtype": str(series.dtype),
                "null_count": int(series.isna().sum()),
                "null_pct": round(100.0 * series.isna().sum() / len(series), 2),
                "unique_count": int(series.nunique()),
                "unique_pct": round(100.0 * series.nunique() / len(series), 2),
            }

            # Numeric columns: add stats
            if pd.api.types.is_numeric_dtype(series):
                desc = series.describe()
                col_profile.update({
                    "mean": round(float(desc.get("mean", 0)), 2),
                    "std": round(float(desc.get("std", 0)), 2),
                    "min": float(desc.get("min", 0)),
                    "25%": float(desc.get("25%", 0)),
                    "50%": float(desc.get("50%", 0)),
                    "75%": float(desc.get("75%", 0)),
                    "max": float(desc.get("max", 0)),
                    "zeros": int((series == 0).sum()),
                    "negatives": int((series < 0).sum()),
                })
            else:
                # String/categorical: top values
                top_5 = series.dropna().value_counts().head(5)
                col_profile["top_values"] = {str(k): int(v) for k, v in top_5.items()}

            self.profile["columns"][col] = col_profile

        elapsed = round(time.time() - start, 2)
        self.profile["profiling_time_sec"] = elapsed

        # Log summary
        log.info(f"  📊 Shape: {self.profile['shape']['rows']:,} rows × {self.profile['shape']['columns']} cols")
        log.info(f"  💾 Memory: {self.profile['memory_mb']} MB")
        log.info(f"  🔁 Duplicate rows: {self.profile['duplicate_rows']:,}")

        # Flag issues
        issues = []
        for col, p in self.profile["columns"].items():
            if p["null_pct"] > 0:
                issues.append(f"    ⚠ {col}: {p['null_pct']}% null ({p['null_count']:,} rows)")
            if "negatives" in p and p["negatives"] > 0:
                issues.append(f"    ⚠ {col}: {p['negatives']} negative values")
            if "zeros" in p and p["zeros"] > 0 and col in ("Quantity", "Item_Price_INR"):
                issues.append(f"    ⚠ {col}: {p['zeros']} zero values")

        if issues:
            log.info(f"  🔍 Quality issues found ({len(issues)}):")
            for issue in issues:
                log.info(issue)
        else:
            log.info("  ✅ No quality issues detected")

        log.info(f"  ⏱ Profiling completed in {elapsed}s\n")
        return self.profile

    def save_html_report(self, path: str = None):
        """Generate an HTML data quality report."""
        path = path or cfg.PROFILE_REPORT_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)

        html = ["""<!DOCTYPE html><html><head><meta charset="utf-8">
        <title>Data Quality Profile Report</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0E1117; color: #FAFAFA; padding: 40px; }
            h1 { color: #FF6F00; border-bottom: 2px solid #FFD700; padding-bottom: 10px; }
            h2 { color: #FFD700; margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th { background: #1E2A3A; color: #FFD700; padding: 10px; text-align: left; border: 1px solid #333; }
            td { padding: 8px 10px; border: 1px solid #333; }
            tr:nth-child(even) { background: #1a1a2e; }
            .warn { color: #FFC107; font-weight: bold; }
            .good { color: #4CAF50; }
            .bad { color: #F44336; font-weight: bold; }
            .summary-card { display: inline-block; background: #1E2A3A; border-radius: 8px;
                            padding: 20px; margin: 8px; min-width: 160px; text-align: center;
                            border: 1px solid #333; }
            .summary-card .value { font-size: 28px; font-weight: bold; color: #FF6F00; }
            .summary-card .label { font-size: 13px; color: #B0BEC5; margin-top: 5px; }
        </style></head><body>"""]

        html.append(f"<h1>🪔 Data Quality Profile Report</h1>")
        html.append(f"<p>Generated: {self.profile['generated_at']}</p>")

        # Summary cards
        html.append('<div>')
        cards = [
            (f"{self.profile['shape']['rows']:,}", "Total Rows"),
            (f"{self.profile['shape']['columns']}", "Columns"),
            (f"{self.profile['memory_mb']} MB", "Memory"),
            (f"{self.profile['duplicate_rows']:,}", "Duplicates"),
        ]
        for val, label in cards:
            html.append(f'<div class="summary-card"><div class="value">{val}</div><div class="label">{label}</div></div>')
        html.append('</div>')

        # Column details table
        html.append("<h2>Column Details</h2>")
        html.append("<table><tr><th>Column</th><th>Type</th><th>Nulls</th><th>Null %</th>"
                     "<th>Unique</th><th>Min</th><th>Max</th><th>Mean</th><th>Issues</th></tr>")

        for col, p in self.profile["columns"].items():
            null_cls = "bad" if p["null_pct"] > 5 else ("warn" if p["null_pct"] > 0 else "good")
            issues_list = []
            if p["null_pct"] > 0:
                issues_list.append(f"{p['null_pct']}% null")
            if p.get("negatives", 0) > 0:
                issues_list.append(f"{p['negatives']} negatives")
            if p.get("zeros", 0) > 0 and col in ("Quantity", "Item_Price_INR"):
                issues_list.append(f"{p['zeros']} zeros")

            issues_str = ", ".join(issues_list) if issues_list else '<span class="good">✓ Clean</span>'
            mn = p.get("min", "—")
            mx = p.get("max", "—")
            mean = p.get("mean", "—")

            html.append(f'<tr><td><b>{col}</b></td><td>{p["dtype"]}</td>'
                         f'<td class="{null_cls}">{p["null_count"]:,}</td>'
                         f'<td class="{null_cls}">{p["null_pct"]}%</td>'
                         f'<td>{p["unique_count"]:,}</td>'
                         f'<td>{mn}</td><td>{mx}</td><td>{mean}</td>'
                         f'<td>{issues_str}</td></tr>')

        html.append("</table>")

        # Top values for string columns
        html.append("<h2>Top Values (Categorical Columns)</h2>")
        for col, p in self.profile["columns"].items():
            if "top_values" in p:
                html.append(f"<h3 style='color:#FF8F00'>{col}</h3><table><tr><th>Value</th><th>Count</th></tr>")
                for val, cnt in p["top_values"].items():
                    html.append(f"<tr><td>{val}</td><td>{cnt:,}</td></tr>")
                html.append("</table>")

        html.append("</body></html>")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))
        log.info(f"  📄 HTML profile report saved → {path}")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 2: DATA CLEANER
# ═══════════════════════════════════════════════════════════════════════════

class DataCleaner:
    """Rule-based data cleaning with full audit trail."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.audit_log = []
        self.initial_rows = len(df)

    def _log_step(self, step_num: int, description: str, before: int, after: int):
        removed = before - after
        entry = {"step": step_num, "description": description,
                 "before": before, "after": after, "removed": removed}
        self.audit_log.append(entry)
        icon = "🔧" if removed > 0 else "✅"
        log.info(f"  {icon} Step {step_num}: {description}")
        log.info(f"       {before:,} → {after:,} rows (Δ {removed:,})")

    def run(self) -> pd.DataFrame:
        log.info("─" * 60)
        log.info("STAGE 2: DATA CLEANING")
        log.info("─" * 60)
        start = time.time()
        step = 0

        # Step 1: Remove exact duplicates
        step += 1
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=cfg.DUPLICATE_SUBSET)
        self._log_step(step, "Remove exact duplicate rows", before, len(self.df))

        # Step 2: Drop rows with null Order_ID
        step += 1
        before = len(self.df)
        self.df = self.df.dropna(subset=["Order_ID"])
        self._log_step(step, "Remove rows with NULL Order_ID", before, len(self.df))

        # Step 3: Standardize category names
        step += 1
        before_unique = self.df["Category"].nunique()
        self.df["Category"] = (
            self.df["Category"].str.strip().str.lower()
            .map(cfg.CATEGORY_TYPO_MAP)
            .fillna(self.df["Category"])
        )
        after_unique = self.df["Category"].nunique()
        self._log_step(step, f"Standardize categories ({before_unique} → {after_unique} unique)", len(self.df), len(self.df))

        # Step 4: Standardize city names
        step += 1
        self.df["City_Name"] = (
            self.df["City_Name"].str.strip().str.lower()
            .map(cfg.CITY_LOOKUP)
        )
        self._log_step(step, "Standardize city names to title case", len(self.df), len(self.df))

        # Step 5: Normalize payment methods
        step += 1
        self.df["Payment_Method"] = (
            self.df["Payment_Method"].str.strip().str.lower()
            .map(cfg.PAYMENT_TYPO_MAP)
            .fillna("Unknown")
        )
        self._log_step(step, "Normalize payment method values", len(self.df), len(self.df))

        # Step 6: Remove invalid quantities
        step += 1
        before = len(self.df)
        self.df = self.df[self.df["Quantity"] > 0]
        self._log_step(step, "Remove rows with quantity ≤ 0", before, len(self.df))

        # Step 7: Handle null and outlier prices
        step += 1
        before = len(self.df)
        self.df = self.df.dropna(subset=["Item_Price_INR"])
        self.df = self.df[
            (self.df["Item_Price_INR"] > 0) &
            (self.df["Item_Price_INR"] <= cfg.MAX_PRICE_THRESHOLD)
        ]
        self._log_step(step, f"Remove NULL / negative / outlier prices (> ₹{cfg.MAX_PRICE_THRESHOLD:,})", before, len(self.df))

        # Step 8: Recalculate order value
        step += 1
        self.df["Order_Value_INR"] = (self.df["Item_Price_INR"] * self.df["Quantity"]).round(2)
        self._log_step(step, "Recalculate Order_Value = Price × Quantity", len(self.df), len(self.df))

        # Step 9: Filter to valid sale dates
        step += 1
        before = len(self.df)
        self.df = self.df[self.df["Order_Date"].isin(cfg.VALID_SALE_DATES)]
        self._log_step(step, f"Filter to valid sale window ({cfg.SALE_START_DATE} → {cfg.SALE_END_DATE})", before, len(self.df))

        # Step 10: Enforce business logic
        step += 1
        mask_cancelled = self.df["Delivery_Status"] == "Cancelled"
        self.df.loc[mask_cancelled, "Return_Status"] = "Not Applicable"
        self._log_step(step, "Enforce Return_Status = 'Not Applicable' for cancelled orders", len(self.df), len(self.df))

        # Step 11: Reset index and conform to canonical fact table schema
        self.df = self.df.reset_index(drop=True)
        fact_cols = [
            c for c in [
                "Order_ID", "Customer_ID", "Product_ID", "City_ID",
                "Order_Date", "Order_Time", "Quantity", "Item_Price_INR",
                "Order_Value_INR", "Payment_Method", "Delivery_Status", "Return_Status"
            ] if c in self.df.columns
        ]
        self.df = self.df[fact_cols]

        elapsed = round(time.time() - start, 2)
        log.info(f"\n  ⏱ Cleaning completed in {elapsed}s")
        log.info(f"  📊 Result: {self.initial_rows:,} → {len(self.df):,} rows "
                 f"({self.initial_rows - len(self.df):,} removed, "
                 f"{(self.initial_rows - len(self.df)) / self.initial_rows * 100:.1f}%)\n")

        return self.df

    def save_audit_log(self, path: str = None):
        path = path or cfg.CLEANING_LOG_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Data Cleaning Audit Log — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 65 + "\n\n")
            for e in self.audit_log:
                f.write(f"[Step {e['step']}] {e['description']}\n")
                f.write(f"  Before: {e['before']:,} │ After: {e['after']:,} │ Removed: {e['removed']:,}\n\n")
            f.write("=" * 65 + "\n")
            f.write(f"FINAL: {self.initial_rows:,} → {len(self.df):,} rows\n")
        log.info(f"  📄 Cleaning audit log saved → {path}")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 3: DATA VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

class DataValidator:
    """Schema and business-rule validation on the cleaned dataset."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = []

    def _check(self, name: str, condition_series: pd.Series, severity: str = "ERROR"):
        failures = (~condition_series).sum()
        passed = failures == 0
        self.results.append({
            "check": name,
            "severity": severity,
            "passed": passed,
            "failures": int(failures),
            "failure_pct": round(100.0 * failures / len(self.df), 2),
        })
        icon = "✅" if passed else ("❌" if severity == "ERROR" else "⚠️")
        log.info(f"  {icon} {name}: {'PASS' if passed else f'FAIL ({failures:,} rows)'}")

    def run(self) -> list:
        log.info("─" * 60)
        log.info("STAGE 3: DATA VALIDATION")
        log.info("─" * 60)
        start = time.time()

        # Schema checks
        log.info("  [Schema Checks]")
        self._check("No null Order_IDs", self.df["Order_ID"].notna())
        self._check("No null Customer_IDs", self.df["Customer_ID"].notna())
        self._check("No null Product_IDs", self.df["Product_ID"].notna())
        self._check("No null City_IDs", self.df["City_ID"].notna())
        self._check("No null prices", self.df["Item_Price_INR"].notna())
        self._check("No null quantities", self.df["Quantity"].notna())

        # Range checks
        log.info("  [Range Checks]")
        self._check("Quantity > 0", self.df["Quantity"] > 0)
        self._check("Item_Price > 0", self.df["Item_Price_INR"] > 0)
        self._check(f"Item_Price ≤ ₹{cfg.MAX_PRICE_THRESHOLD:,}", self.df["Item_Price_INR"] <= cfg.MAX_PRICE_THRESHOLD)
        self._check("Order_Value > 0", self.df["Order_Value_INR"] > 0)

        # Domain checks
        log.info("  [Domain Checks]")
        self._check("Valid sale dates only", self.df["Order_Date"].isin(cfg.VALID_SALE_DATES))
        self._check("Valid delivery statuses", self.df["Delivery_Status"].isin(cfg.VALID_DELIVERY_STATUSES))
        self._check("Valid return statuses", self.df["Return_Status"].isin(cfg.VALID_RETURN_STATUSES))

        # Business logic checks
        log.info("  [Business Logic]")
        cancelled = self.df["Delivery_Status"] == "Cancelled"
        self._check("Cancelled → Return = 'Not Applicable'",
                     ~cancelled | (self.df["Return_Status"] == "Not Applicable"))

        price_qty_match = (self.df["Item_Price_INR"] * self.df["Quantity"]).round(2) == self.df["Order_Value_INR"]
        self._check("Order_Value = Price × Quantity", price_qty_match)

        # Referential integrity
        log.info("  [Referential Integrity]")
        if os.path.exists(cfg.DIM_CITIES_PATH):
            dim_cities = pd.read_csv(cfg.DIM_CITIES_PATH)
            self._check("All City_IDs exist in dim_cities",
                         self.df["City_ID"].isin(dim_cities["City_ID"]))
        if os.path.exists(cfg.DIM_PRODUCTS_PATH):
            dim_products = pd.read_csv(cfg.DIM_PRODUCTS_PATH)
            self._check("All Product_IDs exist in dim_products",
                         self.df["Product_ID"].isin(dim_products["Product_ID"]))
        if os.path.exists(cfg.DIM_CUSTOMERS_PATH):
            dim_customers = pd.read_csv(cfg.DIM_CUSTOMERS_PATH)
            self._check("All Customer_IDs exist in dim_customers",
                         self.df["Customer_ID"].isin(dim_customers["Customer_ID"]))

        elapsed = round(time.time() - start, 2)
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        log.info(f"\n  ⏱ Validation completed in {elapsed}s")
        log.info(f"  📊 Result: {passed}/{total} checks passed\n")

        return self.results

    def save_report(self, path: str = None):
        path = path or cfg.VALIDATION_REPORT_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Data Validation Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 65 + "\n\n")
            for r in self.results:
                status = "PASS ✓" if r["passed"] else f"FAIL ✗ ({r['failures']:,} rows, {r['failure_pct']}%)"
                f.write(f"[{r['severity']:7s}] {r['check']}\n")
                f.write(f"          → {status}\n\n")
            passed = sum(1 for r in self.results if r["passed"])
            f.write("=" * 65 + "\n")
            f.write(f"SUMMARY: {passed}/{len(self.results)} checks passed\n")
        log.info(f"  📄 Validation report saved → {path}")


# ═══════════════════════════════════════════════════════════════════════════
# MASTER PIPELINE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

class ETLPipeline:
    """Orchestrates the full ETL pipeline: Profile → Clean → Validate."""

    def __init__(self):
        self.raw_df = None
        self.clean_df = None
        self.profile = None
        self.validation_results = None

    def run(self):
        log.info("=" * 60)
        log.info("   🪔 ETL PIPELINE — Diwali Sale Data Processing")
        log.info("=" * 60)
        pipeline_start = time.time()

        # ── Load raw data ──────────────────────────────────────────
        if not os.path.exists(cfg.RAW_ORDERS_PATH):
            log.error(f"❌ Raw data not found: {cfg.RAW_ORDERS_PATH}")
            log.error("   Run 'python generate_star_schema.py' first.")
            return False

        self.raw_df = pd.read_csv(cfg.RAW_ORDERS_PATH)
        log.info(f"\n  📥 Loaded raw data: {len(self.raw_df):,} rows from {cfg.RAW_ORDERS_PATH}\n")

        # ── Stage 1: Profile ───────────────────────────────────────
        profiler = DataProfiler(self.raw_df, name="fact_orders_raw")
        self.profile = profiler.run()
        profiler.save_html_report()

        # ── Stage 2: Clean ─────────────────────────────────────────
        cleaner = DataCleaner(self.raw_df)
        self.clean_df = cleaner.run()
        cleaner.save_audit_log()

        # Save cleaned data
        os.makedirs(cfg.CLEAN_DIR, exist_ok=True)
        self.clean_df.to_csv(cfg.CLEANED_ORDERS_PATH, index=False)
        log.info(f"  💾 Cleaned data saved → {cfg.CLEANED_ORDERS_PATH}")

        # ── Stage 3: Validate ──────────────────────────────────────
        validator = DataValidator(self.clean_df)
        self.validation_results = validator.run()
        validator.save_report()

        # ── Summary ────────────────────────────────────────────────
        elapsed = round(time.time() - pipeline_start, 2)
        passed = sum(1 for r in self.validation_results if r["passed"])
        total = len(self.validation_results)

        log.info("=" * 60)
        log.info("   ✅ PIPELINE COMPLETE")
        log.info("=" * 60)
        log.info(f"  Total time:     {elapsed}s")
        log.info(f"  Rows in:        {len(self.raw_df):,}")
        log.info(f"  Rows out:       {len(self.clean_df):,}")
        log.info(f"  Rows removed:   {len(self.raw_df) - len(self.clean_df):,}")
        log.info(f"  Validations:    {passed}/{total} passed")
        log.info(f"\n  📁 Reports:")
        log.info(f"     {cfg.PROFILE_REPORT_PATH}")
        log.info(f"     {cfg.CLEANING_LOG_PATH}")
        log.info(f"     {cfg.VALIDATION_REPORT_PATH}")
        log.info(f"     {cfg.PIPELINE_LOG_PATH}")
        log.info("=" * 60)

        return True


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pipeline = ETLPipeline()
    success = pipeline.run()
    sys.exit(0 if success else 1)

