-- ══════════════════════════════════════════════════════════════════════════
-- ADVANCED SQL ANALYSIS — Festive E-Commerce Sales Dashboard v2
-- ══════════════════════════════════════════════════════════════════════════
-- Demonstrates: Window functions, CTEs, RFM segmentation, cohort analysis,
-- basket analysis, and multi-table JOINs on the star schema.
--
-- Tables used:
--   fact_orders, dim_customers, dim_products, dim_cities, dim_dates
-- ══════════════════════════════════════════════════════════════════════════


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q1. DAY-OVER-DAY REVENUE GROWTH WITH RUNNING TOTAL (Window Functions)  │
-- └──────────────────────────────────────────────────────────────────────────┘

WITH daily_revenue AS (
    SELECT
        f.Order_Date,
        d.Day_Name,
        d.Day_Number,
        d.Sale_Day_Label,
        COUNT(*)                       AS orders,
        ROUND(SUM(f.Order_Value_INR), 2) AS revenue
    FROM fact_orders f
    JOIN dim_dates d ON f.Order_Date = d.Date
    GROUP BY f.Order_Date, d.Day_Name, d.Day_Number, d.Sale_Day_Label
)
SELECT
    Order_Date,
    Day_Name,
    Sale_Day_Label,
    orders,
    revenue,
    -- Running total
    SUM(revenue) OVER (ORDER BY Day_Number
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        AS cumulative_revenue,
    -- Day-over-day change
    LAG(revenue) OVER (ORDER BY Day_Number) AS prev_day_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY Day_Number))
          / LAG(revenue) OVER (ORDER BY Day_Number), 1)
        AS dod_growth_pct
FROM daily_revenue
ORDER BY Day_Number;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q2. PRODUCT CATEGORY RANKING WITHIN EACH CITY TIER (RANK + PARTITION)  │
-- └──────────────────────────────────────────────────────────────────────────┘

WITH tier_category_sales AS (
    SELECT
        ci.City_Tier,
        p.Category,
        COUNT(*)                        AS total_orders,
        ROUND(SUM(f.Order_Value_INR), 2) AS total_revenue
    FROM fact_orders f
    JOIN dim_cities ci ON f.City_ID = ci.City_ID
    JOIN dim_products p ON f.Product_ID = p.Product_ID
    GROUP BY ci.City_Tier, p.Category
)
SELECT
    City_Tier,
    Category,
    total_orders,
    total_revenue,
    RANK() OVER (PARTITION BY City_Tier ORDER BY total_revenue DESC)  AS revenue_rank,
    ROUND(100.0 * total_revenue
          / SUM(total_revenue) OVER (PARTITION BY City_Tier), 1)      AS pct_of_tier_revenue
FROM tier_category_sales
ORDER BY City_Tier, revenue_rank;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q3. HOURLY MOVING AVERAGE OF ORDER VOLUME (3-HOUR WINDOW)              │
-- └──────────────────────────────────────────────────────────────────────────┘

WITH hourly_orders AS (
    SELECT
        CAST(SUBSTR(Order_Time, 1, 2) AS INTEGER) AS order_hour,
        COUNT(*) AS total_orders
    FROM fact_orders
    GROUP BY order_hour
)
SELECT
    order_hour,
    total_orders,
    ROUND(AVG(total_orders * 1.0) OVER (
        ORDER BY order_hour
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ), 1) AS moving_avg_3hr
FROM hourly_orders
ORDER BY order_hour;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q4. NEW vs REPEAT CUSTOMER COHORT ANALYSIS                             │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    CASE WHEN c.Is_Repeat_Customer = 1 THEN 'Repeat' ELSE 'New' END
        AS customer_type,
    COUNT(DISTINCT f.Customer_ID)         AS unique_customers,
    COUNT(*)                              AS total_orders,
    ROUND(SUM(f.Order_Value_INR), 2)       AS total_revenue,
    ROUND(AVG(f.Order_Value_INR), 2)       AS avg_order_value,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT f.Customer_ID), 2)
        AS orders_per_customer,
    -- Delivery quality
    ROUND(100.0 * SUM(CASE WHEN f.Delivery_Status = 'Delayed' THEN 1 ELSE 0 END)
          / COUNT(*), 1)                  AS delay_pct,
    ROUND(100.0 * SUM(CASE WHEN f.Return_Status = 'Returned' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN f.Delivery_Status <> 'Cancelled' THEN 1 ELSE 0 END), 0), 1)
        AS return_pct
FROM fact_orders f
JOIN dim_customers c ON f.Customer_ID = c.Customer_ID
GROUP BY customer_type;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q5. DAILY COHORT COMPARISON — New vs Repeat by Day                     │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    f.Order_Date,
    d.Sale_Day_Label,
    SUM(CASE WHEN c.Is_Repeat_Customer = 0 THEN 1 ELSE 0 END) AS new_orders,
    SUM(CASE WHEN c.Is_Repeat_Customer = 1 THEN 1 ELSE 0 END) AS repeat_orders,
    ROUND(SUM(CASE WHEN c.Is_Repeat_Customer = 0 THEN f.Order_Value_INR ELSE 0 END), 2)
        AS new_revenue,
    ROUND(SUM(CASE WHEN c.Is_Repeat_Customer = 1 THEN f.Order_Value_INR ELSE 0 END), 2)
        AS repeat_revenue
FROM fact_orders f
JOIN dim_customers c ON f.Customer_ID = c.Customer_ID
JOIN dim_dates d ON f.Order_Date = d.Date
GROUP BY f.Order_Date, d.Sale_Day_Label
ORDER BY f.Order_Date;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q6. RFM SEGMENTATION — Recency, Frequency, Monetary Scoring           │
-- └──────────────────────────────────────────────────────────────────────────┘
-- Recency: how recently the customer's last order was (within the 7-day window)
-- Frequency: how many orders they placed
-- Monetary: total spend

WITH rfm_raw AS (
    SELECT
        f.Customer_ID,
        c.Customer_Name,
        c.Is_Repeat_Customer,
        MAX(f.Order_Date)                  AS last_order_date,
        COUNT(*)                           AS frequency,
        ROUND(SUM(f.Order_Value_INR), 2)    AS monetary
    FROM fact_orders f
    JOIN dim_customers c ON f.Customer_ID = c.Customer_ID
    WHERE f.Delivery_Status <> 'Cancelled'
    GROUP BY f.Customer_ID, c.Customer_Name, c.Is_Repeat_Customer
),
rfm_scored AS (
    SELECT
        *,
        -- Recency score: 5 = most recent, 1 = least recent
        NTILE(5) OVER (ORDER BY last_order_date ASC)  AS R_score,
        NTILE(5) OVER (ORDER BY frequency ASC)         AS F_score,
        NTILE(5) OVER (ORDER BY monetary ASC)           AS M_score
    FROM rfm_raw
)
SELECT
    Customer_ID,
    Customer_Name,
    last_order_date,
    frequency,
    monetary,
    R_score,
    F_score,
    M_score,
    (R_score + F_score + M_score)          AS RFM_total,
    CASE
        WHEN R_score >= 4 AND F_score >= 4 AND M_score >= 4 THEN 'Champion'
        WHEN R_score >= 3 AND F_score >= 3 AND M_score >= 3 THEN 'Loyal'
        WHEN R_score >= 4 AND F_score <= 2                  THEN 'New High-Value'
        WHEN R_score <= 2 AND F_score >= 3                  THEN 'At Risk'
        WHEN R_score <= 2 AND F_score <= 2 AND M_score <= 2 THEN 'Hibernating'
        ELSE 'Potential'
    END AS customer_segment
FROM rfm_scored
ORDER BY RFM_total DESC
LIMIT 20;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q7. RFM SEGMENT DISTRIBUTION (Summary)                                 │
-- └──────────────────────────────────────────────────────────────────────────┘

WITH rfm_raw AS (
    SELECT
        f.Customer_ID,
        MAX(f.Order_Date)                  AS last_order_date,
        COUNT(*)                           AS frequency,
        SUM(f.Order_Value_INR)              AS monetary
    FROM fact_orders f
    WHERE f.Delivery_Status <> 'Cancelled'
    GROUP BY f.Customer_ID
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY last_order_date ASC)  AS R,
        NTILE(5) OVER (ORDER BY frequency ASC)         AS F,
        NTILE(5) OVER (ORDER BY monetary ASC)           AS M
    FROM rfm_raw
),
rfm_segments AS (
    SELECT *,
        CASE
            WHEN R >= 4 AND F >= 4 AND M >= 4 THEN 'Champion'
            WHEN R >= 3 AND F >= 3 AND M >= 3 THEN 'Loyal'
            WHEN R >= 4 AND F <= 2             THEN 'New High-Value'
            WHEN R <= 2 AND F >= 3             THEN 'At Risk'
            WHEN R <= 2 AND F <= 2 AND M <= 2 THEN 'Hibernating'
            ELSE 'Potential'
        END AS segment
    FROM rfm_scored
)
SELECT
    segment,
    COUNT(*)                                AS customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM rfm_segments), 1)
        AS pct,
    ROUND(AVG(monetary), 2)                  AS avg_spend,
    ROUND(AVG(frequency), 2)                 AS avg_orders
FROM rfm_segments
GROUP BY segment
ORDER BY customers DESC;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q8. DISCOUNT EFFECTIVENESS ANALYSIS                                    │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    p.Discount_Pct,
    COUNT(*)                              AS orders,
    SUM(f.Quantity)                         AS units_sold,
    ROUND(SUM(f.Order_Value_INR), 2)        AS revenue,
    ROUND(AVG(f.Order_Value_INR), 2)        AS avg_order_value,
    -- Revenue that could have been at MRP
    ROUND(SUM(p.MRP_INR * f.Quantity), 2)   AS potential_mrp_revenue,
    -- Discount cost = MRP revenue - actual revenue
    ROUND(SUM(p.MRP_INR * f.Quantity) - SUM(f.Order_Value_INR), 2)
        AS discount_cost,
    -- Conversion quality
    ROUND(100.0 * SUM(CASE WHEN f.Delivery_Status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*), 1)                  AS cancel_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN f.Return_Status = 'Returned' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN f.Delivery_Status <> 'Cancelled' THEN 1 ELSE 0 END), 0), 1)
        AS return_rate_pct
FROM fact_orders f
JOIN dim_products p ON f.Product_ID = p.Product_ID
GROUP BY p.Discount_Pct
ORDER BY p.Discount_Pct;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q9. CROSS-CATEGORY BASKET ANALYSIS                                     │
-- └──────────────────────────────────────────────────────────────────────────┘
-- Find customers who bought from multiple categories in the same sale,
-- then identify the most common category pairs.

WITH customer_categories AS (
    SELECT DISTINCT
        f.Customer_ID,
        p.Category
    FROM fact_orders f
    JOIN dim_products p ON f.Product_ID = p.Product_ID
    WHERE f.Delivery_Status <> 'Cancelled'
),
category_pairs AS (
    SELECT
        a.Category AS category_a,
        b.Category AS category_b,
        COUNT(DISTINCT a.Customer_ID) AS shared_customers
    FROM customer_categories a
    JOIN customer_categories b
        ON a.Customer_ID = b.Customer_ID
        AND a.Category < b.Category   -- avoid duplicates and self-joins
    GROUP BY a.Category, b.Category
)
SELECT
    category_a,
    category_b,
    shared_customers,
    RANK() OVER (ORDER BY shared_customers DESC) AS pair_rank
FROM category_pairs
ORDER BY shared_customers DESC
LIMIT 10;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q10. REGIONAL PERFORMANCE DEEP-DIVE (Multi-table JOIN)                 │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    ci.Region,
    ci.City_Tier,
    COUNT(DISTINCT ci.City_ID)             AS cities,
    COUNT(*)                               AS total_orders,
    COUNT(DISTINCT f.Customer_ID)           AS unique_customers,
    ROUND(SUM(f.Order_Value_INR), 2)        AS total_revenue,
    ROUND(AVG(f.Order_Value_INR), 2)        AS avg_order_value,
    -- Top category per region-tier
    (SELECT p2.Category
     FROM fact_orders f2
     JOIN dim_products p2 ON f2.Product_ID = p2.Product_ID
     JOIN dim_cities ci2 ON f2.City_ID = ci2.City_ID
     WHERE ci2.Region = ci.Region AND ci2.City_Tier = ci.City_Tier
     GROUP BY p2.Category
     ORDER BY SUM(f2.Order_Value_INR) DESC
     LIMIT 1)                               AS top_category,
    -- Delay rate
    ROUND(100.0 * SUM(CASE WHEN f.Delivery_Status = 'Delayed' THEN 1 ELSE 0 END)
          / COUNT(*), 1)                    AS delay_pct,
    -- UPI adoption
    ROUND(100.0 * SUM(CASE WHEN f.Payment_Method = 'UPI' THEN 1 ELSE 0 END)
          / COUNT(*), 1)                    AS upi_pct
FROM fact_orders f
JOIN dim_cities ci ON f.City_ID = ci.City_ID
GROUP BY ci.Region, ci.City_Tier
ORDER BY ci.Region, ci.City_Tier;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q11. GENDER-BASED PURCHASING PATTERNS                                  │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    c.Gender,
    c.Age_Group,
    COUNT(*)                              AS orders,
    ROUND(AVG(f.Order_Value_INR), 2)       AS avg_order_value,
    -- Most popular category for this demographic
    (SELECT p2.Category
     FROM fact_orders f2
     JOIN dim_products p2 ON f2.Product_ID = p2.Product_ID
     JOIN dim_customers c2 ON f2.Customer_ID = c2.Customer_ID
     WHERE c2.Gender = c.Gender AND c2.Age_Group = c.Age_Group
     GROUP BY p2.Category
     ORDER BY COUNT(*) DESC
     LIMIT 1)                              AS top_category,
    -- Payment preference
    (SELECT f3.Payment_Method
     FROM fact_orders f3
     JOIN dim_customers c3 ON f3.Customer_ID = c3.Customer_ID
     WHERE c3.Gender = c.Gender AND c3.Age_Group = c.Age_Group
     GROUP BY f3.Payment_Method
     ORDER BY COUNT(*) DESC
     LIMIT 1)                              AS preferred_payment
FROM fact_orders f
JOIN dim_customers c ON f.Customer_ID = c.Customer_ID
GROUP BY c.Gender, c.Age_Group
ORDER BY c.Gender, c.Age_Group;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q12. PAYMENT METHOD PERFORMANCE & AOV COMPARISON                       │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    f.Payment_Method,
    COUNT(*)                              AS orders,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_orders), 1)
        AS order_share_pct,
    ROUND(SUM(f.Order_Value_INR), 2)       AS total_revenue,
    ROUND(AVG(f.Order_Value_INR), 2)       AS avg_order_value,
    -- Cancel rate by payment method
    ROUND(100.0 * SUM(CASE WHEN f.Delivery_Status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*), 1)                  AS cancel_rate_pct,
    -- COD vs prepaid return behavior
    ROUND(100.0 * SUM(CASE WHEN f.Return_Status = 'Returned' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN f.Delivery_Status <> 'Cancelled' THEN 1 ELSE 0 END), 0), 1)
        AS return_rate_pct
FROM fact_orders f
GROUP BY f.Payment_Method
ORDER BY total_revenue DESC;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q13. TOP 10 CUSTOMERS BY LIFETIME VALUE (this sale period)             │
-- └──────────────────────────────────────────────────────────────────────────┘

SELECT
    f.Customer_ID,
    c.Customer_Name,
    c.Gender,
    c.Age_Group,
    CASE WHEN c.Is_Repeat_Customer THEN 'Repeat' ELSE 'New' END AS type,
    COUNT(*)                              AS total_orders,
    COUNT(DISTINCT p.Category)             AS categories_bought,
    ROUND(SUM(f.Order_Value_INR), 2)       AS total_spend,
    ROUND(AVG(f.Order_Value_INR), 2)       AS avg_order_value,
    MIN(f.Order_Date) || ' → ' || MAX(f.Order_Date) AS active_window
FROM fact_orders f
JOIN dim_customers c ON f.Customer_ID = c.Customer_ID
JOIN dim_products p ON f.Product_ID = p.Product_ID
WHERE f.Delivery_Status <> 'Cancelled'
GROUP BY f.Customer_ID, c.Customer_Name, c.Gender, c.Age_Group, c.Is_Repeat_Customer
ORDER BY total_spend DESC
LIMIT 10;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │ Q14. SUB-CATEGORY PERFORMANCE WITH CATEGORY CONTEXT (PARTITION BY)     │
-- └──────────────────────────────────────────────────────────────────────────┘

WITH subcat_stats AS (
    SELECT
        p.Category,
        p.Sub_Category,
        COUNT(*)                              AS orders,
        ROUND(SUM(f.Order_Value_INR), 2)       AS revenue,
        ROUND(AVG(f.Order_Value_INR), 2)       AS aov
    FROM fact_orders f
    JOIN dim_products p ON f.Product_ID = p.Product_ID
    GROUP BY p.Category, p.Sub_Category
)
SELECT
    Category,
    Sub_Category,
    orders,
    revenue,
    aov,
    -- Rank within category
    RANK() OVER (PARTITION BY Category ORDER BY revenue DESC) AS rank_in_category,
    -- % share within category
    ROUND(100.0 * revenue
          / SUM(revenue) OVER (PARTITION BY Category), 1) AS pct_of_category,
    -- % share of total
    ROUND(100.0 * revenue
          / SUM(revenue) OVER (), 1)  AS pct_of_total
FROM subcat_stats
ORDER BY Category, revenue DESC;

