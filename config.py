"""
Centralized configuration for the Festive E-Commerce Sales Analytics project.
All paths, constants, valid values, and theme settings in one place.
"""

import os

# ═══════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
RAW_DIR      = os.path.join(DATA_DIR, "raw")
CLEAN_DIR    = os.path.join(DATA_DIR, "clean")
REPORTS_DIR  = os.path.join(DATA_DIR, "reports")
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")
SQL_DIR      = os.path.join(PROJECT_ROOT, "sql")

# Source files
RAW_ORDERS_PATH     = os.path.join(RAW_DIR, "fact_orders_raw.csv")
CLEAN_ORDERS_PATH   = os.path.join(CLEAN_DIR, "fact_orders.csv")
CLEANED_ORDERS_PATH = os.path.join(CLEAN_DIR, "fact_orders_cleaned.csv")
DIM_CITIES_PATH     = os.path.join(CLEAN_DIR, "dim_cities.csv")
DIM_PRODUCTS_PATH   = os.path.join(CLEAN_DIR, "dim_products.csv")
DIM_CUSTOMERS_PATH  = os.path.join(CLEAN_DIR, "dim_customers.csv")
DIM_DATES_PATH      = os.path.join(CLEAN_DIR, "dim_dates.csv")

# Report outputs
PROFILE_REPORT_PATH   = os.path.join(REPORTS_DIR, "data_profile_report.html")
CLEANING_LOG_PATH     = os.path.join(REPORTS_DIR, "cleaning_log.txt")
VALIDATION_REPORT_PATH= os.path.join(REPORTS_DIR, "validation_report.txt")
STATS_RESULTS_PATH    = os.path.join(ANALYSIS_DIR, "statistical_results.json")
EDA_SUMMARY_PATH      = os.path.join(ANALYSIS_DIR, "eda_summary.md")
PIPELINE_LOG_PATH     = os.path.join(REPORTS_DIR, "pipeline_run.log")

# ═══════════════════════════════════════════════════════════════════════════
# SALE WINDOW
# ═══════════════════════════════════════════════════════════════════════════

SALE_START_DATE = "2025-10-23"
SALE_END_DATE   = "2025-10-29"
VALID_SALE_DATES = [f"2025-10-{d}" for d in range(23, 30)]

# ═══════════════════════════════════════════════════════════════════════════
# VALID DOMAIN VALUES
# ═══════════════════════════════════════════════════════════════════════════

VALID_CATEGORIES = [
    "Electronics", "Ethnic Wear", "Home Appliances", "Footwear",
    "Beauty & Personal Care", "Mobile Accessories", "Home Décor",
    "Jewellery", "Toys & Games",
]

VALID_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Indore",
    "Nagpur", "Bhopal", "Coimbatore", "Visakhapatnam", "Kochi", "Surat",
    "Patna", "Vadodara", "Thiruvananthapuram", "Mysuru", "Udaipur",
    "Jalandhar", "Agra", "Varanasi", "Dehradun", "Jodhpur", "Raipur",
    "Guwahati", "Ranchi", "Bhubaneswar", "Jammu", "Shimla", "Amritsar",
    "Mangaluru", "Tirupati", "Aligarh", "Bareilly", "Moradabad",
    "Gorakhpur", "Hubli",
]

VALID_DELIVERY_STATUSES = ["On Time", "Delayed", "Cancelled"]
VALID_RETURN_STATUSES   = ["Kept", "Returned", "Not Applicable"]
VALID_PAYMENT_METHODS   = ["UPI", "Credit Card", "Debit Card", "COD", "Net Banking", "Wallet"]

CATEGORY_TYPO_MAP = {
    "electronics": "Electronics", "elec.": "Electronics", "electronicss": "Electronics",
    "ethnic wear": "Ethnic Wear", "ethnicwear": "Ethnic Wear", "ethic wear": "Ethnic Wear",
    "home appliances": "Home Appliances", "homeappliances": "Home Appliances", "home appl.": "Home Appliances",
    "footwear": "Footwear", "foot wear": "Footwear", "footware": "Footwear",
    "beauty & personal care": "Beauty & Personal Care", "beauty": "Beauty & Personal Care",
    "b&pc": "Beauty & Personal Care", "beauty and personal care": "Beauty & Personal Care",
    "mobile accessories": "Mobile Accessories",
    "home décor": "Home Décor", "home decor": "Home Décor",
    "jewellery": "Jewellery", "jewelry": "Jewellery",
    "toys & games": "Toys & Games", "toys and games": "Toys & Games",
}

PAYMENT_TYPO_MAP = {
    "upi": "UPI", "credit card": "Credit Card", "debit card": "Debit Card",
    "cod": "COD", "c.o.d": "COD", "cash on delivery": "COD",
    "net banking": "Net Banking", "neft": "Net Banking", "wallet": "Wallet",
}

CITY_LOOKUP = {c.lower(): c for c in VALID_CITIES}

# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

FACT_ORDERS_SCHEMA = {
    "Order_ID":         {"type": "str",   "nullable": False},
    "Customer_ID":      {"type": "str",   "nullable": False},
    "Product_ID":       {"type": "str",   "nullable": False},
    "City_ID":          {"type": "str",   "nullable": False},
    "Order_Date":       {"type": "str",   "nullable": False},
    "Order_Time":       {"type": "str",   "nullable": False},
    "Quantity":         {"type": "int",   "nullable": False, "min": 1, "max": 10},
    "Item_Price_INR":   {"type": "float", "nullable": False, "min": 1, "max": 100000},
    "Order_Value_INR":  {"type": "float", "nullable": False, "min": 1},
    "Payment_Method":   {"type": "str",   "nullable": False},
    "Delivery_Status":  {"type": "str",   "nullable": False},
    "Return_Status":    {"type": "str",   "nullable": False},
}

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD THEME (Diwali)
# ═══════════════════════════════════════════════════════════════════════════

COLORS = {
    "primary":     "#FF6F00",      # Saffron
    "secondary":   "#FFD700",      # Gold
    "bg_dark":     "#0E1117",      # Streamlit dark
    "card_bg":     "#1E2A3A",      # Card background
    "success":     "#4CAF50",      # Green
    "warning":     "#FFC107",      # Amber
    "danger":      "#F44336",      # Red
    "text_light":  "#FAFAFA",
    "text_muted":  "#B0BEC5",
    "chart_palette": [
        "#FF6F00", "#FFD700", "#FF8F00", "#FFA726", "#FFB74D",
        "#4FC3F7", "#4DD0E1", "#4DB6AC", "#81C784", "#AED581",
    ],
    "heatmap_scale": ["#1B2A4A", "#FF6F00", "#FFD700"],  # navy → saffron → gold
    "delivery": {
        "On Time":   "#4CAF50",
        "Delayed":   "#FFC107",
        "Cancelled": "#F44336",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

MAX_PRICE_THRESHOLD = 100_000   # ₹ — anything above is an outlier
MIN_VALID_QUANTITY  = 1
DUPLICATE_SUBSET    = ["Order_ID", "Customer_ID", "Product_ID", "Order_Date", "Order_Time"]

