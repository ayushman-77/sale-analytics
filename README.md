# Festive E-Commerce Sales Performance Dashboard

> An end-to-end data analytics portfolio project simulating a major **Diwali sale event** on an Indian e-commerce platform — featuring a production-grade ETL pipeline, statistical analysis, and interactive Streamlit dashboard.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?logo=sqlite&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Charts-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

---

## 📌 Project Overview

This project analyzes **10,000 synthetic orders** from a simulated 7-day Diwali sale (23–29 October 2025) on an Indian e-commerce platform. It goes beyond basic descriptive analytics to deliver:

- **Star-schema data model** with 4 dimension tables + 1 fact table
- **ETL pipeline** with automated data profiling, cleaning, and validation
- **14 advanced SQL queries** including window functions, CTEs, RFM segmentation, and cohort analysis
- **6 statistical hypothesis tests** (t-tests, ANOVA, chi-squared, correlations)
- **Interactive Streamlit dashboard** with 5 tabs and cross-filtering

### Business Questions Answered

1. What was the total **GMV** and how did daily revenue trend during the sale?
2. Which **product categories and sub-categories** drove the most revenue?
3. Which **Tier-2 and Tier-3 cities** showed the highest order volumes?
4. What were the **peak shopping hours** and how did they vary by day?
5. How do **new vs repeat customers** behave differently?
6. What is the **RFM segmentation** of the customer base?
7. Is the AOV difference between **Tier-1 and Tier-3 cities statistically significant**?
8. Are **delayed deliveries associated with higher return rates**? (Chi-squared)
9. Does **discount depth correlate with sales volume**?
10. How effective are different **payment methods** in terms of conversion?

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│  Data Generation │───▶│   ETL Pipeline   │───▶│  Analysis Layer    │
│  (Star Schema)   │    │ Profile → Clean  │    │ SQL + Statistics   │
│                  │    │ → Validate       │    │ + EDA              │
└─────────────────┘    └──────────────────┘    └────────────────────┘
                                                        │
                                                        ▼
                                               ┌────────────────────┐
                                               │  Streamlit         │
                                               │  Dashboard (5 tabs)│
                                               │  + Plotly Charts   │
                                               └────────────────────┘
```

---

## 📁 Repository Structure

```
sale-analytics/
├── main.py                        # 🎯 Master CLI orchestrator
├── config.py                      # ⚙️ Centralized configuration
├── requirements.txt               # 📦 Dependencies
├── README.md                      # 📖 This file
│
├── pipeline/                      # 🔧 ETL Pipeline
│   ├── __init__.py
│   └── etl_pipeline.py            #   DataProfiler → DataCleaner → DataValidator
│
├── analysis/                      # 📐 Analysis Layer
│   ├── __init__.py
│   └── statistical_analysis.py    #   6 hypothesis tests + EDA report
│
├── dashboard/                     # 📊 Interactive Frontend
│   ├── __init__.py
│   └── app.py                     #   Streamlit app with 5 tabs
│
├── sql/                           # 🗄️ SQL Queries
│   └── advanced_analysis.sql      #   14 production queries (Window funcs, CTEs, RFM)
│
├── data/
│   ├── raw/
│   │   └── fact_orders_raw.csv    #   Messy raw data (10,250 rows with injected flaws)
│   ├── clean/
│   │   ├── fact_orders.csv        #   Clean fact table (10,000 orders)
│   │   ├── fact_orders_cleaned.csv #  ETL pipeline output (9,852 valid orders)
│   │   ├── dim_cities.csv         #   42 Indian cities across 3 tiers
│   │   ├── dim_products.csv       #   190 products across 9 categories
│   │   ├── dim_customers.csv      #   3,000 customer demographic profiles
│   │   └── dim_dates.csv          #   7-day Diwali sale calendar
│   ├── reports/
│   │   ├── data_profile_report.html  # Automated HTML data quality report
│   │   ├── cleaning_log.txt       #   Step-by-step audit trail (row deltas)
│   │   ├── validation_report.txt  #   18/18 checks passed validation report
│   │   └── pipeline_run.log       #   Full pipeline execution log
│   └── analysis/
│       ├── statistical_results.json #  Hypothesis test outputs (p-values & effect sizes)
│       └── eda_summary.md         #   Automated Markdown EDA summary
│
├── generate_star_schema.py        # Star schema synthetic data generator
└── run_advanced_analysis.py       # SQLite execution harness for advanced SQL
```

---

## 📊 Data Model (Star Schema)

```
                        ┌──────────────────┐
                        │   dim_customers   │
                        │──────────────────│
                        │ Customer_ID (PK) │
                        │ Customer_Name    │
                        │ Gender           │
                        │ Age_Group        │
                        │ Signup_Date      │
                        │ Is_Repeat        │
                        └────────┬─────────┘
                                 │
┌──────────────────┐    ┌────────┴─────────┐    ┌──────────────────┐
│   dim_products   │    │   fact_orders    │    │   dim_cities     │
│──────────────────│    │──────────────────│    │──────────────────│
│ Product_ID (PK)  │◄───│ Order_ID (PK)   │───►│ City_ID (PK)    │
│ Product_Name     │    │ Customer_ID (FK) │    │ City_Name        │
│ Category         │    │ Product_ID (FK)  │    │ City_Tier        │
│ Sub_Category     │    │ City_ID (FK)     │    │ State            │
│ Brand            │    │ Order_Date (FK)  │    │ Region           │
│ MRP_INR          │    │ Order_Time       │    └──────────────────┘
│ Sale_Price_INR   │    │ Quantity         │
│ Discount_Pct     │    │ Item_Price_INR   │    ┌──────────────────┐
└──────────────────┘    │ Order_Value_INR  │    │   dim_dates      │
                        │ Payment_Method   │───►│──────────────────│
                        │ Delivery_Status  │    │ Date (PK)        │
                        │ Return_Status    │    │ Day_Name         │
                        └──────────────────┘    │ Day_Number       │
                                                │ Is_Weekend       │
                                                │ Sale_Day_Label   │
                                                └──────────────────┘
```

---

## 🛠️ Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### One-Command Full Run
```bash
python main.py all         # Generate data → ETL pipeline → Statistical analysis
python main.py dashboard   # Launch interactive Streamlit dashboard
```

### Step-by-Step
```bash
python main.py generate    # 1. Generate synthetic star-schema data
python main.py pipeline    # 2. Run ETL (profile → clean → validate)
python main.py analyze     # 3. Run hypothesis tests + EDA
python main.py dashboard   # 4. Launch dashboard at http://localhost:8501
```

---

## 🔬 Technical Highlights

### ETL Pipeline (`pipeline/etl_pipeline.py`)
- **Data Profiler** — Automated quality assessment: null rates, distributions, outlier detection → HTML report
- **Data Cleaner** — 10-step cleaning with full audit trail: dedup, standardization, outlier removal, business logic enforcement
- **Data Validator** — 15+ validation rules: schema checks, range checks, domain checks, referential integrity

### Statistical Analysis (`analysis/statistical_analysis.py`)
| Test | Question | Method |
|------|----------|--------|
| Tier-1 vs Tier-3 AOV | Do metro customers spend more? | Welch's t-test + Cohen's d |
| Delivery ↔ Returns | Are delays linked to higher returns? | Chi-squared + Cramér's V |
| Category AOV | Do categories differ in order value? | One-way ANOVA + η² |
| Weekend vs Weekday | Does timing affect spend? | Mann-Whitney U |
| Discount vs Volume | Do deeper discounts drive more sales? | Pearson correlation |
| New vs Repeat Spend | Do repeat customers spend more? | Welch's t-test + Cohen's d |

### Advanced SQL (`sql/advanced_analysis.sql`)
- `LAG()` / `SUM() OVER()` — Day-over-day growth with running totals
- `RANK() / NTILE() OVER (PARTITION BY ...)` — Category ranking within tiers, RFM scoring
- `WITH (CTE)` — Multi-step cohort analysis, basket analysis
- Self-joins — Cross-category co-purchase patterns
- Correlated subqueries — Top category per region-tier combination

### Interactive Dashboard (`dashboard/app.py`)
- **5 tabs**: Revenue Overview, Product Deep-Dive, Customer Intelligence, Operations, Statistical Insights
- **6 KPI cards** with conditional formatting
- **Plotly charts**: area, bar, treemap, heatmap, pie/donut, scatter
- **Sidebar filters**: Date range, City Tier, Category, Payment Method
- **Diwali theme**: Dark navy + saffron/gold color palette

---

## 🔑 Key Findings

| Metric | Value |
|--------|-------|
| Gross GMV | ~₹6.5 Crore |
| Total Orders | 10,000 |
| Avg Order Value | ~₹6,500 |
| Top Category | Electronics (~35% of revenue) |
| Peak Hours | 8–11 PM (evening spike) |
| On-Time Delivery | ~72% |
| Return Rate | ~7.8% (of delivered) |
| Delayed → Return correlation | Statistically significant (p < 0.05) |

---

## 🧰 Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Data Generation** | Python, Faker, NumPy | Synthetic star-schema with realistic distributions |
| **ETL Pipeline** | pandas, custom Python classes | Profile → Clean → Validate with audit logging |
| **SQL Analysis** | SQLite | 14 queries with window functions, CTEs, RFM |
| **Statistical Testing** | SciPy | 6 hypothesis tests with effect sizes |
| **Visualization** | Streamlit, Plotly | Interactive 5-tab dashboard |
| **Configuration** | Centralized config.py | Single source of truth for paths, schemas, themes |

---

## 📝 License

This project is for educational and portfolio purposes. The dataset is entirely synthetic.

---

*Built as an end-to-end data analytics portfolio project · 2025*
