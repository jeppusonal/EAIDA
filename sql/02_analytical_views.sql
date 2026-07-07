-- EAIDA MVP — Day 3 analytical views
-- All views sit directly on the raw layer (no staging/mart split yet — MVP
-- shortcut, see README). Every view here is a candidate dbt model later:
-- the SQL logic won't change much, just where it lives.
--
-- Convention: revenue always means SUM(order_items.line_total) for orders
-- with order_status = 'completed'. Cancelled/pending orders never count.

-- 1. Monthly revenue by city — the baseline every other view compares against.
CREATE OR REPLACE VIEW vw_monthly_revenue_by_city AS
SELECT
    s.city,
    date_trunc('month', o.order_date)::date AS month,
    COUNT(DISTINCT o.order_id)              AS order_count,
    ROUND(SUM(oi.line_total), 2)            AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN stores s        ON s.store_id = o.store_id
WHERE o.order_status = 'completed'
GROUP BY s.city, date_trunc('month', o.order_date)
ORDER BY s.city, month;


-- 2. Sydney revenue trend with month-over-month % change.
-- LAG() reads the previous row's revenue within the same ordered window —
-- this is the standard SQL pattern for "compare this period to last period"
-- without a self-join.
CREATE OR REPLACE VIEW vw_sydney_revenue_trend AS
SELECT
    month,
    order_count,
    revenue,
    LAG(revenue) OVER (ORDER BY month)                       AS prev_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0)
    , 1)                                                      AS mom_pct_change
FROM vw_monthly_revenue_by_city
WHERE city = 'Sydney'
ORDER BY month;


-- 3. Marketing spend by city and month — did Sydney simply stop getting
-- marketing investment around the time revenue dropped?
CREATE OR REPLACE VIEW vw_marketing_spend_by_city_month AS
SELECT
    city_target                          AS city,
    date_trunc('month', start_date)::date AS month,
    COUNT(*)                             AS campaign_count,
    ROUND(SUM(budget), 2)                AS total_budget,
    ROUND(SUM(spend), 2)                 AS total_spend
FROM marketing_campaigns
GROUP BY city_target, date_trunc('month', start_date)
ORDER BY city, month;


-- 4. Stockout risk indicator for Sydney stores.
-- We use "at or below reorder level" rather than strictly stock_level = 0:
-- a store that's already at its reorder threshold is functionally
-- constrained (thin selection, likely partial stockouts on fast movers)
-- even before it hits absolute zero. Using only stock_level = 0 would
-- understate the signal.
CREATE OR REPLACE VIEW vw_sydney_stockout_indicators AS
SELECT
    date_trunc('month', i.snapshot_date)::date AS month,
    st.store_name,
    COUNT(*) FILTER (WHERE i.stock_level = 0)                AS zero_stock_snapshots,
    COUNT(*) FILTER (WHERE i.stock_level <= i.reorder_level)  AS at_or_below_reorder_snapshots,
    COUNT(*)                                                  AS total_snapshots,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE i.stock_level <= i.reorder_level) / COUNT(*)
    , 1)                                                       AS pct_snapshots_constrained
FROM inventory i
JOIN stores st ON st.store_id = i.store_id
WHERE st.city = 'Sydney'
GROUP BY date_trunc('month', i.snapshot_date), st.store_name
ORDER BY month, store_name;


-- 5. Return rate by city and month — returns per completed order.
CREATE OR REPLACE VIEW vw_return_rate_by_city_month AS
SELECT
    s.city,
    date_trunc('month', o.order_date)::date AS month,
    COUNT(DISTINCT o.order_id)              AS order_count,
    COUNT(DISTINCT r.return_id)             AS return_count,
    ROUND(
        100.0 * COUNT(DISTINCT r.return_id) / NULLIF(COUNT(DISTINCT o.order_id), 0)
    , 1)                                     AS return_rate_pct
FROM orders o
JOIN stores s        ON s.store_id = o.store_id
LEFT JOIN returns r  ON r.order_id = o.order_id
WHERE o.order_status = 'completed'
GROUP BY s.city, date_trunc('month', o.order_date)
ORDER BY s.city, month;


-- 6. Category contribution to revenue, by city and month.
-- The point of this view: a total-revenue drop can hide very different
-- stories — every category down evenly (demand-wide problem) vs. one or
-- two categories collapsing (assortment/supply problem). This view lets
-- you tell those apart for Sydney specifically.
CREATE OR REPLACE VIEW vw_category_revenue_by_city_month AS
SELECT
    s.city,
    date_trunc('month', o.order_date)::date AS month,
    p.category,
    ROUND(SUM(oi.line_total), 2)            AS revenue,
    ROUND(
        100.0 * SUM(oi.line_total) / SUM(SUM(oi.line_total)) OVER (
            PARTITION BY s.city, date_trunc('month', o.order_date)
        )
    , 1)                                     AS pct_of_city_month_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p      ON p.product_id = oi.product_id
JOIN stores s         ON s.store_id = o.store_id
WHERE o.order_status = 'completed'
GROUP BY s.city, date_trunc('month', o.order_date), p.category
ORDER BY s.city, month, revenue DESC;
