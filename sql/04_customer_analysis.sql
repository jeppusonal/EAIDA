-- EAIDA MVP — Day 4 customer-level analytical views
-- Day 3 established WHAT happened: Sydney revenue fell ~40% starting
-- May 2026, spread evenly across categories, with no stockout signal.
-- Day 4 asks WHO drove that: is it fewer new customers arriving
-- (acquisition), existing customers leaving (retention), existing
-- customers ordering less often (frequency), or existing customers
-- spending less per order (AOV)? Revenue = customers x frequency x AOV,
-- so these views decompose the Day 3 number into that formula.
--
-- Same convention as 02_analytical_views.sql: "activity" always means a
-- completed order. Cancelled/pending orders never count as engagement.

-- 1. Monthly active customers by city — the customer-count side of the
-- revenue equation. If this falls in lockstep with revenue, the drop is
-- about fewer people buying, not people buying less per person.
CREATE OR REPLACE VIEW vw_monthly_active_customers_by_city AS
SELECT
    s.city,
    date_trunc('month', o.order_date)::date AS month,
    COUNT(DISTINCT o.customer_id)           AS active_customers
FROM orders o
JOIN stores s ON s.store_id = o.store_id
WHERE o.order_status = 'completed'
GROUP BY s.city, date_trunc('month', o.order_date)
ORDER BY s.city, month;


-- 2. New vs returning customers by city/month.
-- "New" = this month is the customer's first-ever completed order month,
-- globally (a customer's first purchase happens once, regardless of
-- which city they order from afterward). This separates an acquisition
-- problem (new customers drying up) from a retention problem (existing
-- customers stop coming back) — the two have very different fixes.
CREATE OR REPLACE VIEW vw_new_vs_returning_customers_by_city_month AS
WITH customer_first_order AS (
    SELECT customer_id, MIN(date_trunc('month', order_date))::date AS first_order_month
    FROM orders
    WHERE order_status = 'completed'
    GROUP BY customer_id
),
city_month_customers AS (
    SELECT DISTINCT o.customer_id, s.city, date_trunc('month', o.order_date)::date AS month
    FROM orders o
    JOIN stores s ON s.store_id = o.store_id
    WHERE o.order_status = 'completed'
)
SELECT
    cmc.city,
    cmc.month,
    COUNT(*) FILTER (WHERE cfo.first_order_month = cmc.month) AS new_customers,
    COUNT(*) FILTER (WHERE cfo.first_order_month < cmc.month) AS returning_customers,
    COUNT(*)                                                  AS total_active_customers
FROM city_month_customers cmc
JOIN customer_first_order cfo ON cfo.customer_id = cmc.customer_id
GROUP BY cmc.city, cmc.month
ORDER BY cmc.city, cmc.month;


-- 3. Repeat purchase rate by city/month — of customers active in a given
-- month, what share ordered more than once that same month? This is the
-- order-frequency side of the revenue equation. A city can have stable
-- customer counts but falling revenue if those customers simply order
-- less often.
CREATE OR REPLACE VIEW vw_repeat_purchase_rate_by_city_month AS
WITH orders_per_customer_month AS (
    SELECT
        s.city,
        date_trunc('month', o.order_date)::date AS month,
        o.customer_id,
        COUNT(*) AS orders_in_month
    FROM orders o
    JOIN stores s ON s.store_id = o.store_id
    WHERE o.order_status = 'completed'
    GROUP BY s.city, date_trunc('month', o.order_date), o.customer_id
)
SELECT
    city,
    month,
    COUNT(*)                                       AS active_customers,
    COUNT(*) FILTER (WHERE orders_in_month > 1)     AS repeat_customers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE orders_in_month > 1) / NULLIF(COUNT(*), 0)
    , 1)                                            AS repeat_purchase_rate_pct
FROM orders_per_customer_month
GROUP BY city, month
ORDER BY city, month;


-- 4. Average order value by city/month — reuses vw_monthly_revenue_by_city
-- rather than recomputing revenue, so the two views can never disagree.
-- This is the spend-per-order side of the revenue equation.
CREATE OR REPLACE VIEW vw_avg_order_value_by_city_month AS
SELECT
    city,
    month,
    order_count,
    revenue,
    ROUND(revenue / NULLIF(order_count, 0), 2) AS avg_order_value
FROM vw_monthly_revenue_by_city
ORDER BY city, month;


-- 5. Sydney customer retention / churn proxy — for each month, what share
-- of customers active the PRIOR month came back this month? This is a
-- proxy, not a true churn label (a customer who skips a month and returns
-- two months later isn't captured as "retained" here) but it's the
-- standard MVP-grade approximation and cheap to compute.
-- Scoped to Sydney only, since that's the city under investigation.
CREATE OR REPLACE VIEW vw_sydney_customer_retention AS
WITH sydney_monthly_customers AS (
    SELECT DISTINCT o.customer_id, date_trunc('month', o.order_date)::date AS month
    FROM orders o
    JOIN stores s ON s.store_id = o.store_id
    WHERE o.order_status = 'completed' AND s.city = 'Sydney'
),
months AS (
    SELECT DISTINCT month FROM sydney_monthly_customers
),
base AS (
    SELECT
        m.month,
        (SELECT COUNT(*) FROM sydney_monthly_customers c
         WHERE c.month = m.month)                                   AS active_customers,
        (SELECT COUNT(*) FROM sydney_monthly_customers p
         WHERE p.month = m.month - INTERVAL '1 month')              AS active_prior_month,
        (SELECT COUNT(*) FROM sydney_monthly_customers c
         JOIN sydney_monthly_customers p
           ON p.customer_id = c.customer_id
          AND p.month = m.month - INTERVAL '1 month'
         WHERE c.month = m.month)                                   AS retained_from_prior_month
    FROM months m
)
SELECT
    month,
    active_customers,
    active_prior_month,
    retained_from_prior_month,
    (active_prior_month - retained_from_prior_month)              AS churned_from_prior_month,
    ROUND(100.0 * retained_from_prior_month / NULLIF(active_prior_month, 0), 1)
        AS retention_rate_pct,
    ROUND(100.0 * (active_prior_month - retained_from_prior_month) / NULLIF(active_prior_month, 0), 1)
        AS churn_rate_pct
FROM base
ORDER BY month;


-- 6. Cohort-style summary — group customers by signup month (their
-- "cohort"), then track what share of each cohort is still placing
-- completed orders N months after signup. This shows whether *newer*
-- cohorts are behaving differently from older ones (e.g. a cohort that
-- signed up right before the drop churning unusually fast), which a
-- single retention curve for all customers combined would hide.
-- Capped at 6 months of offset to keep the MVP output readable.
CREATE OR REPLACE VIEW vw_customer_cohort_summary AS
WITH customer_cohort AS (
    SELECT customer_id, city, date_trunc('month', signup_date)::date AS cohort_month
    FROM customers
),
customer_orders_month AS (
    SELECT DISTINCT o.customer_id, date_trunc('month', o.order_date)::date AS order_month
    FROM orders o
    WHERE o.order_status = 'completed'
),
cohort_activity AS (
    SELECT
        cc.city,
        cc.cohort_month,
        cc.customer_id,
        (
            (EXTRACT(YEAR FROM com.order_month) - EXTRACT(YEAR FROM cc.cohort_month)) * 12
            + (EXTRACT(MONTH FROM com.order_month) - EXTRACT(MONTH FROM cc.cohort_month))
        )::int AS month_offset
    FROM customer_cohort cc
    JOIN customer_orders_month com ON com.customer_id = cc.customer_id
    WHERE com.order_month >= cc.cohort_month
),
cohort_sizes AS (
    SELECT city, cohort_month, COUNT(*) AS cohort_size
    FROM customer_cohort
    GROUP BY city, cohort_month
)
SELECT
    ca.city,
    ca.cohort_month,
    cs.cohort_size,
    ca.month_offset,
    COUNT(DISTINCT ca.customer_id)                                          AS active_customers,
    ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / NULLIF(cs.cohort_size, 0), 1)
        AS pct_of_cohort_active
FROM cohort_activity ca
JOIN cohort_sizes cs ON cs.city = ca.city AND cs.cohort_month = ca.cohort_month
WHERE ca.month_offset BETWEEN 0 AND 6
GROUP BY ca.city, ca.cohort_month, cs.cohort_size, ca.month_offset
ORDER BY ca.city, ca.cohort_month, ca.month_offset;
