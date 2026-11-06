"""
Run all advanced SQL queries on the star schema using SQLite.
Loads all dimension + fact tables, then executes each query.
"""

import os, sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data", "clean")

# ── Load all tables into SQLite ──────────────────────────────────────────
conn = sqlite3.connect(":memory:")
tables = {
    "dim_cities":    "dim_cities.csv",
    "dim_products":  "dim_products.csv",
    "dim_customers": "dim_customers.csv",
    "dim_dates":     "dim_dates.csv",
    "fact_orders":   "fact_orders.csv",
}

for table_name, filename in tables.items():
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.to_sql(table_name, conn, index=False, if_exists="replace")
        print(f"  ✅ Loaded {table_name:20s} → {len(df):>6,} rows")
    else:
        print(f"  ❌ Missing: {path}")

# Also load cleaned fact if available
cleaned_path = os.path.join(DATA_DIR, "fact_orders_cleaned.csv")
if os.path.exists(cleaned_path):
    df_cleaned = pd.read_csv(cleaned_path)
    df_cleaned.to_sql("fact_orders_cleaned", conn, index=False, if_exists="replace")
    print(f"  ✅ Loaded {'fact_orders_cleaned':20s} → {len(df_cleaned):>6,} rows")

print()

# ── Read and run the SQL file ────────────────────────────────────────────
SQL_FILE = os.path.join(BASE_DIR, "sql", "advanced_analysis.sql")

with open(SQL_FILE, "r", encoding="utf-8") as f:
    sql_content = f.read()

# Split by the query separator comments (lines starting with "-- ┌")
# We'll extract individual queries between separators
import re

# Find all query blocks: everything between separator headers
query_blocks = re.split(r"\n-- ┌─+┐\n-- │.*?│\n-- └─+┘\n", sql_content)

# Find all titles
titles = re.findall(r"-- │\s*(.+?)\s*│", sql_content)

# Filter out empty blocks
queries_with_titles = []
for i, block in enumerate(query_blocks):
    block = block.strip()
    if block and not block.startswith("-- ══"):
        # There may be multiple statements (e.g., Q5a/Q5b); split by semicolons
        statements = [s.strip() for s in block.split(";") if s.strip() and not s.strip().startswith("--")]
        if statements and i - 1 < len(titles):
            queries_with_titles.append((titles[i - 1] if i - 1 < len(titles) else f"Query {i}", statements))

for title, statements in queries_with_titles:
    print(f"{'═' * 72}")
    print(f"  {title}")
    print(f"{'═' * 72}")
    for stmt in statements:
        try:
            result = pd.read_sql_query(stmt, conn)
            print(result.to_string(index=False))
            print()
        except Exception as e:
            print(f"  ⚠️  Error: {e}\n")

conn.close()
print("✅  All advanced queries executed.")

