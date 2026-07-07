-- EAIDA MVP — Day 3: prove the drop, no ML yet.
-- Two techniques, both plain SQL window functions:
--   1. Month-over-month % change (already in vw_sydney_revenue_trend)
--   2. Expected-vs-actual: "expected" = trailing 3-month average revenue,
--      computed BEFORE the month being evaluated, so a month is never
--      used to predict itself.
--
-- Note: the current month (2026-07) is a partial month (data generated
-- up to "today"). It will always look like an anomaly and should be
-- excluded from any trend read — that's a data artifact, not a signal.

-- Query 1: month-over-month change, human-readable.
SELECT *
FROM vw_sydney_revenue_trend
WHERE month < date_trunc('month', CURRENT_DATE)  -- drop the partial current month
ORDER BY month;


-- Query 2: expected-vs-actual using a trailing 3-month average as the
-- naive forecast. ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING means "the
-- three rows before this one, not including this one" — this is what
-- keeps the comparison honest.
WITH sydney_monthly AS (
    SELECT month, revenue
    FROM vw_monthly_revenue_by_city
    WHERE city = 'Sydney'
      AND month < date_trunc('month', CURRENT_DATE)
)
SELECT
    month,
    revenue AS actual_revenue,
    ROUND(
        AVG(revenue) OVER (
            ORDER BY month
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        )
    , 2) AS expected_revenue_trailing_3mo,
    ROUND(
        revenue - AVG(revenue) OVER (
            ORDER BY month
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        )
    , 2) AS anomaly_amount,
    ROUND(
        100.0 * (revenue - AVG(revenue) OVER (
            ORDER BY month
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        )) / NULLIF(AVG(revenue) OVER (
            ORDER BY month
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ), 0)
    , 1) AS anomaly_pct
FROM sydney_monthly
ORDER BY month;


-- Query 3: candidate root causes side by side for the anomaly window.
-- Adjust the month filter once you see where Query 2 flags the anomaly.
SELECT city, month, total_spend
FROM vw_marketing_spend_by_city_month
WHERE city = 'Sydney'
ORDER BY month;

SELECT *
FROM vw_sydney_stockout_indicators
ORDER BY month, store_name;

SELECT month, order_count, return_count, return_rate_pct
FROM vw_return_rate_by_city_month
WHERE city = 'Sydney'
ORDER BY month;

SELECT city, month, category, revenue, pct_of_city_month_revenue
FROM vw_category_revenue_by_city_month
WHERE city = 'Sydney'
ORDER BY month, revenue DESC;
