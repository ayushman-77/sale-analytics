"""
Star Schema Data Generator — Festive E-Commerce Sales Performance Dashboard v2
================================================================================
Generates a relational star schema with:
  • dim_cities.csv      (42 rows)
  • dim_products.csv    (~200 rows)
  • dim_customers.csv   (~3,000 rows)
  • dim_dates.csv       (7 rows)
  • fact_orders.csv     (10,000 rows — clean)
  • fact_orders_raw.csv (~10,300 rows — intentionally messy)

Dependencies: pip install pandas numpy faker
"""

import os, random, string
import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("en_IN")
np.random.seed(42)
random.seed(42)
Faker.seed(42)

NUM_ORDERS = 10_000
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(os.path.join(OUTPUT_DIR, "raw"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "clean"), exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# DIMENSION 1: CITIES
# ═══════════════════════════════════════════════════════════════════════════

CITY_DATA = [
    # Tier-1
    ("Mumbai",              "Tier-1", "Maharashtra",       "West"),
    ("Delhi",               "Tier-1", "Delhi",             "North"),
    ("Bengaluru",           "Tier-1", "Karnataka",         "South"),
    ("Hyderabad",           "Tier-1", "Telangana",         "South"),
    ("Chennai",             "Tier-1", "Tamil Nadu",        "South"),
    ("Kolkata",             "Tier-1", "West Bengal",       "East"),
    ("Pune",                "Tier-1", "Maharashtra",       "West"),
    ("Ahmedabad",           "Tier-1", "Gujarat",           "West"),
    # Tier-2
    ("Jaipur",              "Tier-2", "Rajasthan",         "North"),
    ("Lucknow",             "Tier-2", "Uttar Pradesh",     "North"),
    ("Chandigarh",          "Tier-2", "Chandigarh",        "North"),
    ("Indore",              "Tier-2", "Madhya Pradesh",    "Central"),
    ("Nagpur",              "Tier-2", "Maharashtra",       "West"),
    ("Bhopal",              "Tier-2", "Madhya Pradesh",    "Central"),
    ("Coimbatore",          "Tier-2", "Tamil Nadu",        "South"),
    ("Visakhapatnam",       "Tier-2", "Andhra Pradesh",    "South"),
    ("Kochi",               "Tier-2", "Kerala",            "South"),
    ("Surat",               "Tier-2", "Gujarat",           "West"),
    ("Patna",               "Tier-2", "Bihar",             "East"),
    ("Vadodara",            "Tier-2", "Gujarat",           "West"),
    ("Thiruvananthapuram",  "Tier-2", "Kerala",            "South"),
    ("Mysuru",              "Tier-2", "Karnataka",         "South"),
    # Tier-3
    ("Udaipur",             "Tier-3", "Rajasthan",         "North"),
    ("Jalandhar",           "Tier-3", "Punjab",            "North"),
    ("Agra",                "Tier-3", "Uttar Pradesh",     "North"),
    ("Varanasi",            "Tier-3", "Uttar Pradesh",     "North"),
    ("Dehradun",            "Tier-3", "Uttarakhand",       "North"),
    ("Jodhpur",             "Tier-3", "Rajasthan",         "North"),
    ("Raipur",              "Tier-3", "Chhattisgarh",      "Central"),
    ("Guwahati",            "Tier-3", "Assam",             "East"),
    ("Ranchi",              "Tier-3", "Jharkhand",         "East"),
    ("Bhubaneswar",         "Tier-3", "Odisha",            "East"),
    ("Jammu",               "Tier-3", "Jammu & Kashmir",   "North"),
    ("Shimla",              "Tier-3", "Himachal Pradesh",  "North"),
    ("Amritsar",            "Tier-3", "Punjab",            "North"),
    ("Mangaluru",           "Tier-3", "Karnataka",         "South"),
    ("Tirupati",            "Tier-3", "Andhra Pradesh",    "South"),
    ("Aligarh",             "Tier-3", "Uttar Pradesh",     "North"),
    ("Bareilly",            "Tier-3", "Uttar Pradesh",     "North"),
    ("Moradabad",           "Tier-3", "Uttar Pradesh",     "North"),
    ("Gorakhpur",           "Tier-3", "Uttar Pradesh",     "North"),
    ("Hubli",               "Tier-3", "Karnataka",         "South"),
]

dim_cities = pd.DataFrame(CITY_DATA, columns=["City_Name", "City_Tier", "State", "Region"])
dim_cities.insert(0, "City_ID", [f"CITY-{i+1:03d}" for i in range(len(dim_cities))])

# Tier-based sampling weights
TIER_WEIGHTS_MAP = {"Tier-1": 0.55, "Tier-2": 0.30, "Tier-3": 0.15}
city_weights = dim_cities["City_Tier"].map(TIER_WEIGHTS_MAP)
# Distribute tier weight equally among cities within each tier
for tier in ["Tier-1", "Tier-2", "Tier-3"]:
    mask = dim_cities["City_Tier"] == tier
    city_weights[mask] = city_weights[mask] / mask.sum()
city_weights = city_weights.values

# ═══════════════════════════════════════════════════════════════════════════
# DIMENSION 2: PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════

PRODUCT_CATALOG = {
    "Electronics": {
        "subcategories": {
            "Smartphones":  (12999, 79999),
            "Laptops":      (29999, 89999),
            "Tablets":      (9999, 44999),
            "Headphones":   (499, 14999),
            "Smartwatches":  (1499, 24999),
            "Cameras":      (8999, 59999),
        },
        "brands": ["Samsung", "Apple", "OnePlus", "Xiaomi", "Sony", "Boat", "Noise", "Dell", "HP", "Lenovo"],
    },
    "Ethnic Wear": {
        "subcategories": {
            "Sarees":       (799, 12999),
            "Kurta Sets":   (599, 5999),
            "Lehengas":     (1999, 14999),
            "Sherwanis":    (1499, 9999),
            "Dupattas":     (249, 1999),
        },
        "brands": ["Fabindia", "Biba", "W", "Manyavar", "Libas", "Aurelia", "Global Desi"],
    },
    "Home Appliances": {
        "subcategories": {
            "Mixer Grinders": (1499, 7999),
            "Air Purifiers":  (4999, 24999),
            "Vacuum Cleaners":(2999, 19999),
            "Irons":          (599, 3499),
            "Water Purifiers":(5999, 18999),
            "Microwaves":     (4999, 14999),
        },
        "brands": ["Prestige", "Philips", "Dyson", "Kent", "Havells", "Bajaj", "Crompton", "Bosch"],
    },
    "Footwear": {
        "subcategories": {
            "Sneakers":       (999, 8999),
            "Ethnic Footwear":(399, 3999),
            "Formal Shoes":   (999, 6999),
            "Sandals":        (299, 2499),
            "Sports Shoes":   (1499, 9999),
        },
        "brands": ["Nike", "Adidas", "Puma", "Bata", "Metro", "Woodland", "Red Tape", "Campus"],
    },
    "Beauty & Personal Care": {
        "subcategories": {
            "Skincare":       (199, 3999),
            "Haircare":       (149, 1999),
            "Fragrances":     (499, 5999),
            "Makeup":         (199, 3499),
            "Grooming Kits":  (499, 4999),
        },
        "brands": ["Lakme", "Maybelline", "L'Oreal", "Nivea", "Biotique", "Mamaearth", "The Body Shop", "Dove"],
    },
    "Mobile Accessories": {
        "subcategories": {
            "Cases & Covers": (149, 1499),
            "Chargers":       (299, 2499),
            "Power Banks":    (499, 3999),
            "Screen Guards":  (99, 799),
            "Earphones":      (249, 4999),
        },
        "brands": ["Spigen", "Samsung", "Anker", "Mi", "Boat", "Ambrane", "Belkin", "Portronics"],
    },
    "Home Décor": {
        "subcategories": {
            "Lighting":          (399, 7999),
            "Wall Art":          (499, 5999),
            "Cushions & Throws": (299, 2999),
            "Vases":             (349, 3499),
            "Candles & Diyas":   (149, 1999),
        },
        "brands": ["Home Centre", "FabIndia Home", "IKEA", "Elvy", "DecorTwist", "Nestasia"],
    },
    "Jewellery": {
        "subcategories": {
            "Gold Plated":   (999, 14999),
            "Silver":        (1499, 19999),
            "Artificial":    (199, 4999),
            "Bridal Sets":   (2999, 29999),
            "Bangles":       (299, 7999),
        },
        "brands": ["Tanishq", "Voylla", "GIVA", "Zaveri Pearls", "Sukkhi", "PC Jeweller", "Kalyan"],
    },
    "Toys & Games": {
        "subcategories": {
            "Board Games":      (299, 2999),
            "Action Figures":   (399, 3999),
            "Educational Toys": (499, 4999),
            "Building Blocks":  (599, 5999),
            "Outdoor Toys":     (399, 2999),
        },
        "brands": ["Funskool", "Lego", "Hot Wheels", "Nerf", "Toyzone", "Mattel", "Hasbro"],
    },
}

# Generate ~200 products
products = []
prod_id = 1
for category, config in PRODUCT_CATALOG.items():
    for subcat, (lo, hi) in config["subcategories"].items():
        # 3-5 products per subcategory
        n_products = random.randint(3, 5)
        for _ in range(n_products):
            brand = random.choice(config["brands"])
            mrp = round(np.exp(np.random.uniform(np.log(lo), np.log(hi))) / 10) * 10 - 1
            mrp = max(mrp, lo)
            # Diwali discount: 5-40% off MRP
            discount_pct = random.choice([5, 10, 15, 20, 25, 30, 35, 40])
            sale_price = round(mrp * (1 - discount_pct / 100))
            # Round to ₹9 ending
            sale_price = round(sale_price / 10) * 10 - 1
            sale_price = max(sale_price, 99)

            product_name = f"{brand} {subcat.rstrip('s')} {random.choice(['Pro', 'Plus', 'Lite', 'Max', 'Classic', 'Elite', 'Prime', ''])}"
            product_name = product_name.strip()

            products.append({
                "Product_ID": f"PROD-{prod_id:04d}",
                "Product_Name": product_name,
                "Category": category,
                "Sub_Category": subcat,
                "Brand": brand,
                "MRP_INR": mrp,
                "Sale_Price_INR": sale_price,
                "Discount_Pct": discount_pct,
            })
            prod_id += 1

dim_products = pd.DataFrame(products)

# Category-based sampling weights for order generation
CATEGORY_WEIGHTS = {
    "Electronics": 0.22, "Ethnic Wear": 0.18, "Home Appliances": 0.14,
    "Footwear": 0.10, "Beauty & Personal Care": 0.10, "Mobile Accessories": 0.08,
    "Home Décor": 0.07, "Jewellery": 0.06, "Toys & Games": 0.05,
}

# ═══════════════════════════════════════════════════════════════════════════
# DIMENSION 3: CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════

NUM_CUSTOMERS = 3000

customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    gender = np.random.choice(["Male", "Female", "Other"], p=[0.48, 0.48, 0.04])
    if gender == "Male":
        name = fake.name_male()
    elif gender == "Female":
        name = fake.name_female()
    else:
        name = fake.name()

    age_group = np.random.choice(
        ["18-24", "25-34", "35-44", "45-54", "55+"],
        p=[0.22, 0.35, 0.25, 0.12, 0.06],
    )

    # Signup date: older signups → repeat customers
    signup_date = fake.date_between(start_date="-5y", end_date="-7d")
    is_repeat = signup_date < pd.Timestamp("2024-10-01").date()

    customers.append({
        "Customer_ID": f"CUST-{i:05d}",
        "Customer_Name": name,
        "Gender": gender,
        "Age_Group": age_group,
        "Signup_Date": signup_date.strftime("%Y-%m-%d"),
        "Is_Repeat_Customer": is_repeat,
    })

dim_customers = pd.DataFrame(customers)

# ═══════════════════════════════════════════════════════════════════════════
# DIMENSION 4: DATES
# ═══════════════════════════════════════════════════════════════════════════

SALE_START = pd.Timestamp("2025-10-23")
sale_dates = pd.date_range(SALE_START, periods=7, freq="D")

dim_dates = pd.DataFrame({
    "Date": sale_dates.strftime("%Y-%m-%d"),
    "Day_Name": sale_dates.day_name(),
    "Day_Number": range(1, 8),
    "Is_Weekend": sale_dates.weekday.isin([5, 6]),
    "Sale_Day_Label": [
        "Day 1 — Launch",
        "Day 2 — Build-up",
        "Day 3 — Peak Day 1",
        "Day 4 — Peak Day 2 (Diwali Eve)",
        "Day 5 — Diwali Day",
        "Day 6 — Wind-down",
        "Day 7 — Final Day",
    ],
})

# ═══════════════════════════════════════════════════════════════════════════
# FACT TABLE: ORDERS (CLEAN)
# ═══════════════════════════════════════════════════════════════════════════

# Temporal weights
DAY_WEIGHTS = np.array([0.12, 0.14, 0.18, 0.18, 0.15, 0.13, 0.10])
DAY_WEIGHTS /= DAY_WEIGHTS.sum()

HOUR_WEIGHTS = np.array([
    1, 0.5, 0.3, 0.2, 0.2, 0.3,    # 00-05
    0.8, 1.5, 2.5, 4.0, 5.5, 5.0,  # 06-11
    4.0, 3.5, 3.0, 3.0, 3.5, 4.0,  # 12-17
    5.0, 6.0, 7.0, 6.5, 4.0, 2.5,  # 18-23
])
HOUR_WEIGHTS /= HOUR_WEIGHTS.sum()

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "COD", "Net Banking", "Wallet"]
PAYMENT_WEIGHTS = [0.35, 0.20, 0.15, 0.15, 0.08, 0.07]

DELIVERY_STATUSES = ["On Time", "Delayed", "Cancelled"]
DELIVERY_WEIGHTS  = [0.72, 0.18, 0.10]

orders = []
for i in range(1, NUM_ORDERS + 1):
    order_id = f"DW-{i:06d}"

    # Pick customer
    cust_idx = random.randint(0, NUM_CUSTOMERS - 1)
    customer_id = dim_customers.loc[cust_idx, "Customer_ID"]

    # Pick city (weighted)
    city_idx = np.random.choice(len(dim_cities), p=city_weights)
    city_id = dim_cities.loc[city_idx, "City_ID"]

    # Pick date (weighted)
    day_offset = np.random.choice(7, p=DAY_WEIGHTS)
    order_date = (SALE_START + pd.Timedelta(days=int(day_offset))).strftime("%Y-%m-%d")

    # Pick time (weighted)
    hour = int(np.random.choice(24, p=HOUR_WEIGHTS))
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    order_time = f"{hour:02d}:{minute:02d}:{second:02d}"

    # Pick product (weighted by category, then random within category)
    category = np.random.choice(list(CATEGORY_WEIGHTS.keys()), p=list(CATEGORY_WEIGHTS.values()))
    cat_products = dim_products[dim_products["Category"] == category]
    prod_row = cat_products.sample(1).iloc[0]
    product_id = prod_row["Product_ID"]
    item_price = prod_row["Sale_Price_INR"]

    # Quantity
    if category in ("Beauty & Personal Care", "Mobile Accessories", "Toys & Games"):
        quantity = int(np.random.choice([1, 2, 3], p=[0.70, 0.22, 0.08]))
    else:
        quantity = int(np.random.choice([1, 2, 3], p=[0.82, 0.14, 0.04]))

    order_value = round(item_price * quantity, 2)

    # Payment
    payment = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)

    # Delivery
    delivery = np.random.choice(DELIVERY_STATUSES, p=DELIVERY_WEIGHTS)

    # Return
    if delivery == "Cancelled":
        return_status = "Not Applicable"
    elif delivery == "Delayed":
        return_status = "Returned" if random.random() < 0.14 else "Kept"
    else:
        return_status = "Returned" if random.random() < 0.06 else "Kept"

    orders.append({
        "Order_ID": order_id,
        "Customer_ID": customer_id,
        "Product_ID": product_id,
        "City_ID": city_id,
        "Order_Date": order_date,
        "Order_Time": order_time,
        "Quantity": quantity,
        "Item_Price_INR": item_price,
        "Order_Value_INR": order_value,
        "Payment_Method": payment,
        "Delivery_Status": delivery,
        "Return_Status": return_status,
    })

fact_orders = pd.DataFrame(orders)

# ═══════════════════════════════════════════════════════════════════════════
# RAW / MESSY VERSION — for data cleaning practice
# ═══════════════════════════════════════════════════════════════════════════

raw = fact_orders.copy()

# We'll denormalize some columns back into raw for a more realistic "raw dump" feel
raw = raw.merge(dim_cities[["City_ID", "City_Name"]], on="City_ID", how="left")
raw = raw.merge(dim_products[["Product_ID", "Category", "Sub_Category"]], on="Product_ID", how="left")

# 1. Add ~250 exact duplicate rows
dup_indices = random.sample(range(len(raw)), 250)
duplicates = raw.iloc[dup_indices].copy()
raw = pd.concat([raw, duplicates], ignore_index=True)

# 2. Introduce ~150 NULL city names
null_city_indices = random.sample(range(len(raw)), 150)
raw.loc[null_city_indices, "City_Name"] = np.nan

# 3. Inconsistent category names (~120 rows)
CATEGORY_TYPOS = {
    "Electronics": ["electronics", "ELECTRONICS", "Elec.", "Electronicss"],
    "Ethnic Wear": ["ethnic wear", "Ethnic wear", "EthnicWear", "Ethic Wear"],
    "Home Appliances": ["home appliances", "Home appliances", "HomeAppliances", "Home Appl."],
    "Footwear": ["footwear", "FOOTWEAR", "Foot Wear", "Footware"],
    "Beauty & Personal Care": ["beauty & personal care", "Beauty", "B&PC", "Beauty and Personal Care"],
}
typo_indices = random.sample(range(len(raw)), 120)
for idx in typo_indices:
    orig_cat = raw.loc[idx, "Category"]
    if orig_cat in CATEGORY_TYPOS:
        raw.loc[idx, "Category"] = random.choice(CATEGORY_TYPOS[orig_cat])

# 4. NULL prices (~60 rows)
null_price_indices = random.sample(range(len(raw)), 60)
raw.loc[null_price_indices, "Item_Price_INR"] = np.nan
raw.loc[null_price_indices, "Order_Value_INR"] = np.nan

# 5. Negative / zero quantities (~35 rows)
bad_qty_indices = random.sample(range(len(raw)), 35)
raw.loc[bad_qty_indices, "Quantity"] = np.random.choice([-1, 0, -2], size=35)

# 6. Dates outside sale window (~40 rows)
bad_date_indices = random.sample(range(len(raw)), 40)
bad_dates = pd.date_range("2025-11-01", periods=10, freq="D").strftime("%Y-%m-%d").tolist()
bad_dates += ["2025-10-15", "2025-10-16", "2025-10-20", "2025-10-21", "2025-10-22"]
for idx in bad_date_indices:
    raw.loc[idx, "Order_Date"] = random.choice(bad_dates)

# 7. Mixed-case city names (~80 rows)
mixed_case_indices = random.sample(range(len(raw)), 80)
for idx in mixed_case_indices:
    city = raw.loc[idx, "City_Name"]
    if pd.notna(city):
        raw.loc[idx, "City_Name"] = random.choice([city.upper(), city.lower(), city.title()])

# 8. Some extreme outlier prices (~20 rows)
outlier_indices = random.sample(range(len(raw)), 20)
raw.loc[outlier_indices, "Item_Price_INR"] = np.random.choice([999999, -500, 0, 1], size=20)

# 9. Payment method inconsistencies (~30 rows)
bad_payment_indices = random.sample(range(len(raw)), 30)
raw.loc[bad_payment_indices, "Payment_Method"] = np.random.choice(
    ["upi", "credit card", "C.O.D", "cash on delivery", "NEFT", ""], size=30
)

# Shuffle the raw data so issues aren't clustered
raw = raw.sample(frac=1, random_state=42).reset_index(drop=True)

# ═══════════════════════════════════════════════════════════════════════════
# EXPORT ALL TABLES
# ═══════════════════════════════════════════════════════════════════════════

dim_cities.to_csv(os.path.join(OUTPUT_DIR, "clean", "dim_cities.csv"), index=False)
dim_products.to_csv(os.path.join(OUTPUT_DIR, "clean", "dim_products.csv"), index=False)
dim_customers.to_csv(os.path.join(OUTPUT_DIR, "clean", "dim_customers.csv"), index=False)
dim_dates.to_csv(os.path.join(OUTPUT_DIR, "clean", "dim_dates.csv"), index=False)
fact_orders.to_csv(os.path.join(OUTPUT_DIR, "clean", "fact_orders.csv"), index=False)
raw.to_csv(os.path.join(OUTPUT_DIR, "raw", "fact_orders_raw.csv"), index=False)

# Summary
print("=" * 65)
print("  ✅  STAR SCHEMA DATASET GENERATED SUCCESSFULLY")
print("=" * 65)
print(f"\n  📁 Output directory: {OUTPUT_DIR}")
print(f"\n  Dimension tables:")
print(f"     dim_cities.csv      → {len(dim_cities):>6,} rows")
print(f"     dim_products.csv    → {len(dim_products):>6,} rows")
print(f"     dim_customers.csv   → {len(dim_customers):>6,} rows")
print(f"     dim_dates.csv       → {len(dim_dates):>6,} rows")
print(f"\n  Fact tables:")
print(f"     fact_orders.csv     → {len(fact_orders):>6,} rows  (clean)")
print(f"     fact_orders_raw.csv → {len(raw):>6,} rows  (messy — for cleaning)")
print(f"\n  Data quality issues injected into raw:")
print(f"     • ~250 duplicate rows")
print(f"     • ~150 NULL city names")
print(f"     • ~120 inconsistent category names")
print(f"     • ~60 NULL prices")
print(f"     • ~35 negative/zero quantities")
print(f"     • ~40 dates outside sale window")
print(f"     • ~80 mixed-case city names")
print(f"     • ~20 outlier prices")
print(f"     • ~30 payment method inconsistencies")
print(f"\n  Clean fact table stats:")
print(f"     Gross GMV: ₹{fact_orders['Order_Value_INR'].sum():,.0f}")
print(f"     AOV:       ₹{fact_orders['Order_Value_INR'].mean():,.0f}")
print(f"     Categories: {fact_orders.merge(dim_products[['Product_ID','Category']], on='Product_ID')['Category'].nunique()}")
print("=" * 65)

