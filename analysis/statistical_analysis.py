"""
Statistical Analysis — Festive E-Commerce Sales Dashboard
============================================================
Runs hypothesis tests and correlation analysis on the cleaned dataset
to add diagnostic depth beyond descriptive metrics.

Tests performed:
  1. Independent t-test     — Tier-1 vs Tier-3 AOV
  2. Chi-squared test       — Delivery Status vs Return Status independence
  3. One-way ANOVA          — AOV across product categories
  4. Mann-Whitney U test    — Weekend vs Weekday order values
  5. Pearson correlation    — Discount % vs Quantity sold per product
  6. Effect size (Cohen's d)— Repeat vs New customer spend

Results are saved as JSON and printed as a formatted summary.

Usage:
    from analysis.statistical_analysis import StatisticalAnalyzer
    analyzer = StatisticalAnalyzer()
    analyzer.run()
"""

import os, sys, json
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


class StatisticalAnalyzer:
    """Runs hypothesis tests and saves structured results."""

    def __init__(self):
        self.results = []
        self.df = None
        self.df_merged = None

    def _load_data(self):
        """Load and merge all tables into an analysis-ready DataFrame."""
        # Prefer cleaned data; fall back to clean fact table
        fact_path = cfg.CLEANED_ORDERS_PATH if os.path.exists(cfg.CLEANED_ORDERS_PATH) else cfg.CLEAN_ORDERS_PATH
        self.df = pd.read_csv(fact_path)

        # Drop redundant denormalized columns if present before merging with dimension tables
        redundant_cols = [c for c in ["City_Name", "Category", "Sub_Category"] if c in self.df.columns]
        if redundant_cols:
            self.df = self.df.drop(columns=redundant_cols)

        cities = pd.read_csv(cfg.DIM_CITIES_PATH)
        products = pd.read_csv(cfg.DIM_PRODUCTS_PATH)
        customers = pd.read_csv(cfg.DIM_CUSTOMERS_PATH)
        dates = pd.read_csv(cfg.DIM_DATES_PATH)

        self.df_merged = (
            self.df
            .merge(cities, on="City_ID", how="left")
            .merge(products, on="Product_ID", how="left")
            .merge(customers, on="Customer_ID", how="left")
            .merge(dates, left_on="Order_Date", right_on="Date", how="left")
        )
        # Derived columns
        self.df_merged["Order_Hour"] = self.df_merged["Order_Time"].str[:2].astype(int)

        print(f"  ✅ Loaded {len(self.df_merged):,} rows (merged with dimensions)\n")

    def _add_result(self, test_name: str, hypothesis: str, test_type: str,
                    statistic: float, p_value: float, conclusion: str,
                    effect_size: float = None, details: dict = None):
        result = {
            "test_name": test_name,
            "hypothesis": hypothesis,
            "test_type": test_type,
            "statistic": round(statistic, 4),
            "p_value": round(p_value, 6),
            "significant_at_05": p_value < 0.05,
            "conclusion": conclusion,
        }
        if effect_size is not None:
            result["effect_size"] = round(effect_size, 4)
        if details:
            result["details"] = details
        self.results.append(result)

    def _cohens_d(self, group1, group2):
        """Calculate Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        var1, var2 = group1.var(), group2.var()
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        return (group1.mean() - group2.mean()) / pooled_std if pooled_std > 0 else 0

    # ── Test 1: Tier-1 vs Tier-3 AOV ─────────────────────────────────────

    def test_tier_aov(self):
        print("  📊 Test 1: Tier-1 vs Tier-3 Average Order Value")
        tier1 = self.df_merged[self.df_merged["City_Tier"] == "Tier-1"]["Order_Value_INR"]
        tier3 = self.df_merged[self.df_merged["City_Tier"] == "Tier-3"]["Order_Value_INR"]

        t_stat, p_val = stats.ttest_ind(tier1, tier3, equal_var=False)
        d = self._cohens_d(tier1, tier3)

        conclusion = (
            f"{'Significant' if p_val < 0.05 else 'No significant'} difference in AOV "
            f"between Tier-1 (₹{tier1.mean():,.0f}) and Tier-3 (₹{tier3.mean():,.0f}). "
            f"Cohen's d = {d:.2f} ({'small' if abs(d) < 0.5 else 'medium' if abs(d) < 0.8 else 'large'} effect)."
        )
        self._add_result(
            "Tier-1 vs Tier-3 AOV", "H₀: μ_Tier1 = μ_Tier3", "Welch's t-test",
            t_stat, p_val, conclusion, effect_size=d,
            details={"tier1_mean": round(tier1.mean(), 2), "tier1_n": len(tier1),
                     "tier3_mean": round(tier3.mean(), 2), "tier3_n": len(tier3)}
        )
        print(f"     t = {t_stat:.4f}, p = {p_val:.6f}, d = {d:.4f}")
        print(f"     → {conclusion}\n")

    # ── Test 2: Delivery Status vs Return Status independence ─────────────

    def test_delivery_return_independence(self):
        print("  📊 Test 2: Delivery Status vs Return Status Independence")
        delivered = self.df_merged[self.df_merged["Delivery_Status"] != "Cancelled"]
        contingency = pd.crosstab(delivered["Delivery_Status"], delivered["Return_Status"])

        chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
        cramers_v = np.sqrt(chi2 / (len(delivered) * (min(contingency.shape) - 1)))

        conclusion = (
            f"Delivery status and return status are {'NOT independent' if p_val < 0.05 else 'independent'} "
            f"(χ² = {chi2:.2f}, df = {dof}, Cramér's V = {cramers_v:.3f}). "
            f"{'Delayed deliveries are associated with higher return rates.' if p_val < 0.05 else ''}"
        )
        self._add_result(
            "Delivery vs Return Independence", "H₀: Variables are independent",
            "Chi-squared test", chi2, p_val, conclusion, effect_size=cramers_v,
            details={"dof": dof, "cramers_v": round(cramers_v, 4),
                     "contingency_table": contingency.to_dict()}
        )
        print(f"     χ² = {chi2:.4f}, p = {p_val:.6f}, Cramér's V = {cramers_v:.4f}")
        print(f"     → {conclusion}\n")

    # ── Test 3: AOV across Product Categories (ANOVA) ─────────────────────

    def test_category_aov_anova(self):
        print("  📊 Test 3: AOV Across Product Categories (One-way ANOVA)")
        groups = [
            group["Order_Value_INR"].values
            for _, group in self.df_merged.groupby("Category")
        ]

        f_stat, p_val = stats.f_oneway(*groups)
        # Eta-squared effect size
        grand_mean = self.df_merged["Order_Value_INR"].mean()
        ss_between = sum(
            len(g) * (g.mean() - grand_mean) ** 2 for g in groups
        )
        ss_total = ((self.df_merged["Order_Value_INR"] - grand_mean) ** 2).sum()
        eta_sq = ss_between / ss_total if ss_total > 0 else 0

        cat_means = (
            self.df_merged.groupby("Category")["Order_Value_INR"]
            .agg(["mean", "count"])
            .round(2)
            .to_dict()
        )

        conclusion = (
            f"{'Significant' if p_val < 0.05 else 'No significant'} difference in AOV across categories "
            f"(F = {f_stat:.2f}, η² = {eta_sq:.3f}). "
            f"Category explains {eta_sq*100:.1f}% of AOV variance."
        )
        self._add_result(
            "AOV Across Categories", "H₀: All category AOVs are equal",
            "One-way ANOVA", f_stat, p_val, conclusion, effect_size=eta_sq,
            details={"eta_squared": round(eta_sq, 4), "category_means": cat_means}
        )
        print(f"     F = {f_stat:.4f}, p = {p_val:.6f}, η² = {eta_sq:.4f}")
        print(f"     → {conclusion}\n")

    # ── Test 4: Weekend vs Weekday Order Values ───────────────────────────

    def test_weekend_weekday(self):
        print("  📊 Test 4: Weekend vs Weekday Order Values")
        weekend = self.df_merged[self.df_merged["Is_Weekend"] == True]["Order_Value_INR"]
        weekday = self.df_merged[self.df_merged["Is_Weekend"] == False]["Order_Value_INR"]

        # Mann-Whitney U (non-parametric, doesn't assume normality)
        u_stat, p_val = stats.mannwhitneyu(weekend, weekday, alternative="two-sided")
        d = self._cohens_d(weekend, weekday)

        conclusion = (
            f"{'Significant' if p_val < 0.05 else 'No significant'} difference between "
            f"weekend (₹{weekend.mean():,.0f}, n={len(weekend):,}) and "
            f"weekday (₹{weekday.mean():,.0f}, n={len(weekday):,}) order values."
        )
        self._add_result(
            "Weekend vs Weekday AOV", "H₀: Distributions are equal",
            "Mann-Whitney U test", float(u_stat), p_val, conclusion, effect_size=d,
            details={"weekend_mean": round(weekend.mean(), 2), "weekend_n": len(weekend),
                     "weekday_mean": round(weekday.mean(), 2), "weekday_n": len(weekday)}
        )
        print(f"     U = {u_stat:.0f}, p = {p_val:.6f}, d = {d:.4f}")
        print(f"     → {conclusion}\n")

    # ── Test 5: Discount % vs Units Sold Correlation ──────────────────────

    def test_discount_vs_quantity(self):
        print("  📊 Test 5: Discount % vs Units Sold Correlation")
        product_stats = (
            self.df_merged
            .groupby("Product_ID")
            .agg(
                discount_pct=("Discount_Pct", "first"),
                total_units=("Quantity", "sum"),
            )
            .dropna()
        )

        r, p_val = stats.pearsonr(product_stats["discount_pct"], product_stats["total_units"])

        conclusion = (
            f"{'Significant' if p_val < 0.05 else 'No significant'} correlation between "
            f"discount % and units sold (r = {r:.3f}). "
            f"{'Higher discounts are associated with more sales.' if r > 0 and p_val < 0.05 else 'Discount level alone does not strongly predict sales volume.'}"
        )
        self._add_result(
            "Discount vs Units Sold", "H₀: ρ = 0 (no correlation)",
            "Pearson correlation", r, p_val, conclusion,
            details={"pearson_r": round(r, 4), "n_products": len(product_stats)}
        )
        print(f"     r = {r:.4f}, p = {p_val:.6f}")
        print(f"     → {conclusion}\n")

    # ── Test 6: New vs Repeat Customer Spend ──────────────────────────────

    def test_new_vs_repeat_spend(self):
        print("  📊 Test 6: New vs Repeat Customer Spend")
        customer_spend = (
            self.df_merged[self.df_merged["Delivery_Status"] != "Cancelled"]
            .groupby(["Customer_ID", "Is_Repeat_Customer"])
            .agg(total_spend=("Order_Value_INR", "sum"))
            .reset_index()
        )

        new_spend = customer_spend[customer_spend["Is_Repeat_Customer"] == False]["total_spend"]
        repeat_spend = customer_spend[customer_spend["Is_Repeat_Customer"] == True]["total_spend"]

        t_stat, p_val = stats.ttest_ind(repeat_spend, new_spend, equal_var=False)
        d = self._cohens_d(repeat_spend, new_spend)

        conclusion = (
            f"Repeat customers spend {'significantly' if p_val < 0.05 else 'not significantly'} "
            f"{'more' if repeat_spend.mean() > new_spend.mean() else 'less'} "
            f"(₹{repeat_spend.mean():,.0f}) than new customers (₹{new_spend.mean():,.0f}). "
            f"Cohen's d = {d:.2f}."
        )
        self._add_result(
            "New vs Repeat Customer Spend", "H₀: μ_repeat = μ_new",
            "Welch's t-test", t_stat, p_val, conclusion, effect_size=d,
            details={"repeat_mean": round(repeat_spend.mean(), 2), "repeat_n": len(repeat_spend),
                     "new_mean": round(new_spend.mean(), 2), "new_n": len(new_spend)}
        )
        print(f"     t = {t_stat:.4f}, p = {p_val:.6f}, d = {d:.4f}")
        print(f"     → {conclusion}\n")

    # ── Run all tests ─────────────────────────────────────────────────────

    def run(self):
        print("=" * 65)
        print("   📐 STATISTICAL ANALYSIS — Hypothesis Testing")
        print("=" * 65)
        print()

        self._load_data()

        self.test_tier_aov()
        self.test_delivery_return_independence()
        self.test_category_aov_anova()
        self.test_weekend_weekday()
        self.test_discount_vs_quantity()
        self.test_new_vs_repeat_spend()

        # Save results
        os.makedirs(cfg.ANALYSIS_DIR, exist_ok=True)
        with open(cfg.STATS_RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"  💾 Results saved → {cfg.STATS_RESULTS_PATH}")

        # Summary
        sig_count = sum(1 for r in self.results if r["significant_at_05"])
        print(f"\n{'=' * 65}")
        print(f"  SUMMARY: {sig_count}/{len(self.results)} tests significant at α = 0.05")
        print(f"{'=' * 65}")

        return self.results

    def generate_eda_summary(self):
        """Generate a markdown EDA summary."""
        if self.df_merged is None:
            self._load_data()

        dm = self.df_merged
        delivered = dm[dm["Delivery_Status"] != "Cancelled"]

        lines = [
            "# 📊 Exploratory Data Analysis Summary\n",
            f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n",
            "---\n",
            "## Dataset Overview\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Orders | {len(dm):,} |",
            f"| Unique Customers | {dm['Customer_ID'].nunique():,} |",
            f"| Unique Products | {dm['Product_ID'].nunique():,} |",
            f"| Date Range | {dm['Order_Date'].min()} → {dm['Order_Date'].max()} |",
            f"| Gross GMV | ₹{dm['Order_Value_INR'].sum():,.0f} |",
            f"| Net Revenue | ₹{delivered['Order_Value_INR'].sum():,.0f} |",
            f"| Avg Order Value | ₹{dm['Order_Value_INR'].mean():,.0f} |",
            f"| Median Order Value | ₹{dm['Order_Value_INR'].median():,.0f} |",
            "",
            "## Revenue Distribution by Category\n",
            "| Category | Orders | Revenue (₹) | Share % | AOV (₹) |",
            "|----------|--------|-------------|---------|---------|",
        ]

        cat_stats = (
            dm.groupby("Category")
            .agg(orders=("Order_ID", "count"),
                 revenue=("Order_Value_INR", "sum"),
                 aov=("Order_Value_INR", "mean"))
            .sort_values("revenue", ascending=False)
        )
        total_rev = cat_stats["revenue"].sum()
        for cat, row in cat_stats.iterrows():
            share = 100 * row["revenue"] / total_rev
            lines.append(f"| {cat} | {int(row['orders']):,} | ₹{row['revenue']:,.0f} | {share:.1f}% | ₹{row['aov']:,.0f} |")

        lines += [
            "",
            "## Customer Demographics\n",
            "| Age Group | Orders | Avg Spend (₹) |",
            "|-----------|--------|---------------|",
        ]
        age_stats = dm.groupby("Age_Group").agg(
            orders=("Order_ID", "count"), avg_spend=("Order_Value_INR", "mean")
        ).sort_index()
        for age, row in age_stats.iterrows():
            lines.append(f"| {age} | {int(row['orders']):,} | ₹{row['avg_spend']:,.0f} |")

        lines += [
            "",
            "## Operational Metrics\n",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| On-Time Delivery | {100 * (dm['Delivery_Status'] == 'On Time').mean():.1f}% |",
            f"| Delayed Orders | {100 * (dm['Delivery_Status'] == 'Delayed').mean():.1f}% |",
            f"| Cancellation Rate | {100 * (dm['Delivery_Status'] == 'Cancelled').mean():.1f}% |",
            f"| Return Rate (of delivered) | {100 * (delivered['Return_Status'] == 'Returned').mean():.1f}% |",
            f"| Top Payment Method | {dm['Payment_Method'].mode().iloc[0]} ({100 * (dm['Payment_Method'] == dm['Payment_Method'].mode().iloc[0]).mean():.1f}%) |",
        ]

        summary = "\n".join(lines)
        os.makedirs(cfg.ANALYSIS_DIR, exist_ok=True)
        with open(cfg.EDA_SUMMARY_PATH, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"  📄 EDA summary saved → {cfg.EDA_SUMMARY_PATH}")
        return summary


if __name__ == "__main__":
    analyzer = StatisticalAnalyzer()
    analyzer.run()
    analyzer.generate_eda_summary()

