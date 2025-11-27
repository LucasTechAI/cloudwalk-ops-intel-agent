-- =======================
-- VIEWS: KPIs & BUSINESS INTELLIGENCE
-- =======================
-- Purpose: Provide pre-aggregated data for operations intelligence queries
-- Created: 2024-11-27
-- Database: SQLite3
-- Author: CloudWalk Operations Intelligence Team

-- =======================
-- DROP EXISTING VIEWS (for clean setup)
-- =======================
DROP VIEW IF EXISTS v_kpi;
DROP VIEW IF EXISTS v_segmentation;
DROP VIEW IF EXISTS v_daily_kpis;
DROP VIEW IF EXISTS v_alerts;
DROP VIEW IF EXISTS v_weekday_analysis;
DROP VIEW IF EXISTS v_installments_analysis;
DROP VIEW IF EXISTS v_price_tier_comparison;
DROP VIEW IF EXISTS v_anticipation_analysis;
DROP VIEW IF EXISTS v_product_comparison;

-- =======================
-- VIEW 1: v_kpi - Daily KPI Metrics
-- =======================
-- Purpose: Aggregated daily metrics for dashboard and reporting
-- Usage: SELECT * FROM v_kpi WHERE day = '2024-01-15' AND entity = 'business';
-- Performance: Uses idx_day_entity_product for optimal query speed
CREATE VIEW v_kpi AS
SELECT
    day,
    entity,
    product,
    payment_method,
    price_tier,
    anticipation_method,
    installments,
    
    -- Core KPIs
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    SUM(quantity_of_merchants) AS total_merchants,
    
    -- Derived Metrics
    COUNT(DISTINCT id) AS num_records,
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS average_ticket,
    MIN(amount_transacted) AS min_transaction,
    MAX(amount_transacted) AS max_transaction,
    
    -- Concentration Metrics
    ROUND(SUM(amount_transacted) / NULLIF(SUM(quantity_of_merchants), 0), 2) AS tpv_per_merchant,
    ROUND(SUM(quantity_transactions) / NULLIF(SUM(quantity_of_merchants), 0), 2) AS transactions_per_merchant
FROM transactions
WHERE deleted_at IS NULL
GROUP BY
    day, entity, product, payment_method, price_tier, anticipation_method, installments;

-- =======================
-- VIEW 2: v_segmentation - Business Segmentation Analysis
-- =======================
-- Purpose: High-level segmentation for strategic analysis
-- Usage: SELECT * FROM v_segmentation WHERE entity = 'business' ORDER BY tpv DESC;
-- Answers: "Which segment has the highest TPV? Which has the highest Average Ticket?"
CREATE VIEW v_segmentation AS
SELECT
    entity,
    product,
    payment_method,
    price_tier,
    anticipation_method,
    
    -- Aggregated KPIs
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    SUM(quantity_of_merchants) AS total_merchants,
    
    -- Average Metrics
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    ROUND(AVG(amount_transacted), 2) AS avg_tpv_per_record,
    ROUND(AVG(quantity_transactions), 2) AS avg_transactions_per_record,
    
    -- Activity Metrics
    COUNT(DISTINCT day) AS days_active,
    MIN(day) AS first_transaction_date,
    MAX(day) AS last_transaction_date,
    
    -- Distribution Percentages
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (), 2) AS tpv_pct_of_total
FROM transactions
WHERE deleted_at IS NULL
GROUP BY
    entity, product, payment_method, price_tier, anticipation_method;

-- =======================
-- VIEW 3: v_daily_kpis - Temporal Analysis with Variations
-- =======================
-- Purpose: Daily KPIs with period-over-period comparisons (D-1, D-7, D-30)
-- Usage: SELECT * FROM v_daily_kpis WHERE day >= date('now', '-30 days') AND var_d7_pct < -10;
-- Answers: "How did TPV change compared to last week/month?"
CREATE VIEW v_daily_kpis AS
WITH daily_metrics AS (
    SELECT 
        day,
        entity,
        product,
        payment_method,
        SUM(amount_transacted) AS tpv,
        SUM(quantity_transactions) AS total_transactions,
        SUM(quantity_of_merchants) AS total_merchants,
        AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket
    FROM transactions
    WHERE deleted_at IS NULL
    GROUP BY day, entity, product, payment_method
)
SELECT 
    d.day,
    d.entity,
    d.product,
    d.payment_method,
    d.tpv,
    d.total_transactions,
    d.total_merchants,
    d.avg_ticket,
    
    -- Previous period values
    LAG(d.tpv, 1) OVER w AS tpv_d1,
    LAG(d.tpv, 7) OVER w AS tpv_d7,
    LAG(d.tpv, 30) OVER w AS tpv_d30,
    
    -- Absolute variations
    ROUND(d.tpv - LAG(d.tpv, 1) OVER w, 2) AS var_d1_abs,
    ROUND(d.tpv - LAG(d.tpv, 7) OVER w, 2) AS var_d7_abs,
    ROUND(d.tpv - LAG(d.tpv, 30) OVER w, 2) AS var_d30_abs,
    
    -- Percentage variations
    ROUND((d.tpv - LAG(d.tpv, 1) OVER w) / NULLIF(LAG(d.tpv, 1) OVER w, 0) * 100, 2) AS var_d1_pct,
    ROUND((d.tpv - LAG(d.tpv, 7) OVER w) / NULLIF(LAG(d.tpv, 7) OVER w, 0) * 100, 2) AS var_d7_pct,
    ROUND((d.tpv - LAG(d.tpv, 30) OVER w) / NULLIF(LAG(d.tpv, 30) OVER w, 0) * 100, 2) AS var_d30_pct,
    
    -- Moving averages (for smoothing and trend detection)
    ROUND(AVG(d.tpv) OVER (
        PARTITION BY entity, product, payment_method 
        ORDER BY day 
        ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ), 2) AS avg_7d,
    
    ROUND(AVG(d.tpv) OVER (
        PARTITION BY entity, product, payment_method 
        ORDER BY day 
        ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
    ), 2) AS avg_14d,
    
    ROUND(AVG(d.tpv) OVER (
        PARTITION BY entity, product, payment_method 
        ORDER BY day 
        ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
    ), 2) AS avg_30d
FROM daily_metrics d
WINDOW w AS (PARTITION BY entity, product, payment_method ORDER BY day);

-- =======================
-- VIEW 4: v_alerts - Automatic Anomaly Detection
-- =======================
-- Purpose: Identify significant variations for automated alerting
-- Usage: SELECT * FROM v_alerts WHERE day = date('now') ORDER BY alert_level;
-- Answers: "What are today's critical alerts?" "Which segments dropped significantly?"
CREATE VIEW v_alerts AS
SELECT 
    day,
    entity,
    product,
    payment_method,
    tpv,
    avg_ticket,
    var_d1_pct,
    var_d7_pct,
    var_d30_pct,
    ROUND((tpv - avg_14d) / NULLIF(avg_14d, 0) * 100, 2) AS var_vs_14d_pct,
    ROUND((tpv - avg_30d) / NULLIF(avg_30d, 0) * 100, 2) AS var_vs_30d_pct,
    
    -- Alert classification (ordered by severity)
    CASE 
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) < -0.18 THEN '🔴 CRITICAL'
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) < -0.12 THEN '🟠 HIGH'
        WHEN var_d7_pct < -10 THEN '🟡 MEDIUM'
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) > 0.20 THEN '🟢 POSITIVE'
        ELSE '⚪ NORMAL'
    END AS alert_level,
    
    -- Descriptive alert message
    CASE 
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) < -0.18 THEN 
            'TPV fell ' || ROUND(ABS((tpv - avg_14d) / NULLIF(avg_14d, 0) * 100), 1) || '% vs 14-day average'
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) < -0.12 THEN 
            'TPV dropped ' || ROUND(ABS((tpv - avg_14d) / NULLIF(avg_14d, 0) * 100), 1) || '% vs 14-day average'
        WHEN var_d7_pct < -10 THEN 
            'TPV fell ' || ROUND(ABS(var_d7_pct), 1) || '% vs D-7'
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) > 0.20 THEN 
            'TPV rose ' || ROUND((tpv - avg_14d) / NULLIF(avg_14d, 0) * 100, 1) || '% vs 14-day average'
        ELSE 'No significant variation'
    END AS alert_message,
    
    -- Severity score (for sorting and filtering)
    CASE 
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) < -0.18 THEN 5
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) < -0.12 THEN 4
        WHEN var_d7_pct < -10 THEN 3
        WHEN (tpv - avg_14d) / NULLIF(avg_14d, 0) > 0.20 THEN 2
        ELSE 1
    END AS severity_score
FROM v_daily_kpis
WHERE 
    -- Filter for significant variations only
    ABS((tpv - avg_14d) / NULLIF(avg_14d, 0)) > 0.12  -- Variation > 12%
    OR ABS(var_d7_pct) > 10  -- Variation > 10% vs D-7
    OR ABS(var_d30_pct) > 15;  -- Variation > 15% vs D-30

-- =======================
-- VIEW 5: v_weekday_analysis - Day of Week Performance
-- =======================
-- Purpose: Analyze transaction patterns by day of week
-- Usage: SELECT * FROM v_weekday_analysis WHERE entity = 'business' ORDER BY weekday_num;
-- Answers: "How do weekdays influence TPV?" "What's the best performing day?"
CREATE VIEW v_weekday_analysis AS
SELECT
    CASE CAST(strftime('%w', day) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS weekday,
    CAST(strftime('%w', day) AS INTEGER) AS weekday_num,
    entity,
    product,
    payment_method,
    
    -- Aggregated metrics
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    SUM(quantity_of_merchants) AS total_merchants,
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    
    -- Activity metrics
    COUNT(DISTINCT day) AS num_days,
    ROUND(SUM(amount_transacted) / NULLIF(COUNT(DISTINCT day), 0), 2) AS avg_daily_tpv,
    ROUND(SUM(quantity_transactions) / NULLIF(COUNT(DISTINCT day), 0), 2) AS avg_daily_transactions,
    
    -- Distribution
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (PARTITION BY entity, product, payment_method), 2) AS tpv_pct
FROM transactions
WHERE deleted_at IS NULL
GROUP BY weekday_num, entity, product, payment_method
ORDER BY weekday_num;

-- =======================
-- VIEW 6: v_installments_analysis - Installment Impact Analysis
-- =======================
-- Purpose: Analyze how installments affect volume and transaction metrics
-- Usage: SELECT * FROM v_installments_analysis WHERE entity = 'individual' ORDER BY installments;
-- Answers: "How do installments impact TPV?" "What's the most common installment count?"
CREATE VIEW v_installments_analysis AS
SELECT
    installments,
    entity,
    product,
    payment_method,
    
    -- Volume metrics
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    
    -- Distribution percentages
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (PARTITION BY entity, product, payment_method), 2) AS tpv_pct,
    ROUND(SUM(quantity_transactions) * 100.0 / 
        SUM(SUM(quantity_transactions)) OVER (PARTITION BY entity, product, payment_method), 2) AS transactions_pct,
    
    -- Merchant metrics
    SUM(quantity_of_merchants) AS total_merchants,
    ROUND(SUM(amount_transacted) / NULLIF(SUM(quantity_of_merchants), 0), 2) AS tpv_per_merchant,
    
    -- Activity
    COUNT(DISTINCT day) AS days_active
FROM transactions
WHERE deleted_at IS NULL
GROUP BY installments, entity, product, payment_method
ORDER BY installments;

-- =======================
-- VIEW 7: v_price_tier_comparison - Price Tier Performance Comparison
-- =======================
-- Purpose: Compare performance differences across price tiers
-- Usage: SELECT * FROM v_price_tier_comparison WHERE entity = 'business' ORDER BY tpv DESC;
-- Answers: "How do price tiers compare in volume/transactions?"
CREATE VIEW v_price_tier_comparison AS
SELECT
    price_tier,
    entity,
    product,
    
    -- Volume metrics
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    SUM(quantity_of_merchants) AS total_merchants,
    
    -- Average metrics
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    ROUND(AVG(amount_transacted), 2) AS avg_tpv_per_record,
    
    -- Distribution percentages
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (PARTITION BY entity, product), 2) AS tpv_pct,
    ROUND(SUM(quantity_transactions) * 100.0 / 
        SUM(SUM(quantity_transactions)) OVER (PARTITION BY entity, product), 2) AS transactions_pct,
    
    -- Activity
    COUNT(DISTINCT day) AS days_active,
    ROUND(SUM(amount_transacted) / NULLIF(COUNT(DISTINCT day), 0), 2) AS avg_daily_tpv
FROM transactions
WHERE deleted_at IS NULL
GROUP BY price_tier, entity, product
ORDER BY entity, product, tpv DESC;

-- =======================
-- VIEW 8: v_anticipation_analysis - Anticipation Method Analysis
-- =======================
-- Purpose: Analyze which anticipation methods are most used by individuals and businesses
-- Usage: SELECT * FROM v_anticipation_analysis WHERE entity = 'individual' ORDER BY tpv DESC;
-- Answers: "Which anticipation method is most used by individuals? By businesses?"
CREATE VIEW v_anticipation_analysis AS
SELECT
    entity,
    anticipation_method,
    product,
    
    -- Volume metrics
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    SUM(quantity_of_merchants) AS total_merchants,
    
    -- Average metrics
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    
    -- Distribution by entity
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (PARTITION BY entity), 2) AS tpv_pct_by_entity,
    ROUND(SUM(quantity_transactions) * 100.0 / 
        SUM(SUM(quantity_transactions)) OVER (PARTITION BY entity), 2) AS transactions_pct_by_entity,
    
    -- Distribution by entity and product
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (PARTITION BY entity, product), 2) AS tpv_pct_by_product,
    
    -- Activity
    COUNT(DISTINCT day) AS days_active
FROM transactions
WHERE deleted_at IS NULL
GROUP BY entity, anticipation_method, product
ORDER BY entity, tpv DESC;

-- =======================
-- VIEW 9: v_product_comparison - Product Performance Comparison
-- =======================
-- Purpose: Compare products by TPV and other metrics
-- Usage: SELECT * FROM v_product_comparison ORDER BY tpv DESC;
-- Answers: "Which product has the highest TPV?" "How do products compare?"
CREATE VIEW v_product_comparison AS
SELECT
    product,
    entity,
    
    -- Volume metrics
    SUM(amount_transacted) AS tpv,
    SUM(quantity_transactions) AS total_transactions,
    SUM(quantity_of_merchants) AS total_merchants,
    
    -- Average metrics
    AVG(amount_transacted / NULLIF(quantity_transactions, 0)) AS avg_ticket,
    ROUND(AVG(amount_transacted), 2) AS avg_tpv_per_record,
    
    -- Distribution
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (), 2) AS tpv_pct_of_total,
    ROUND(SUM(amount_transacted) * 100.0 / 
        SUM(SUM(amount_transacted)) OVER (PARTITION BY entity), 2) AS tpv_pct_by_entity,
    
    -- Activity
    COUNT(DISTINCT day) AS days_active,
    MIN(day) AS first_transaction_date,
    MAX(day) AS last_transaction_date,
    ROUND(SUM(amount_transacted) / NULLIF(COUNT(DISTINCT day), 0), 2) AS avg_daily_tpv
FROM transactions
WHERE deleted_at IS NULL
GROUP BY product, entity
ORDER BY tpv DESC;

-- =======================
-- USAGE EXAMPLES
-- =======================

-- Example 1: Which product has the highest TPV?
--   SELECT product, SUM(tpv) as total_tpv 
--   FROM v_product_comparison 
--   GROUP BY product 
--   ORDER BY total_tpv DESC 
--   LIMIT 1;

-- Example 2: How do weekdays influence TPV?
--   SELECT weekday, SUM(tpv) as total_tpv 
--   FROM v_weekday_analysis 
--   GROUP BY weekday, weekday_num 
--   ORDER BY weekday_num;

-- Example 3: Which segment has the highest average TPV?
--   SELECT entity, product, payment_method, AVG(tpv) as avg_tpv
--   FROM v_segmentation 
--   GROUP BY entity, product, payment_method
--   ORDER BY avg_tpv DESC 
--   LIMIT 1;

-- Example 4: Which segment has the highest Average Ticket?
--   SELECT entity, product, avg_ticket 
--   FROM v_segmentation 
--   ORDER BY avg_ticket DESC 
--   LIMIT 1;

-- Example 5: Which anticipation method is most used by individuals?
--   SELECT anticipation_method, SUM(total_transactions) as usage
--   FROM v_anticipation_analysis
--   WHERE entity = 'individual'
--   GROUP BY anticipation_method
--   ORDER BY usage DESC
--   LIMIT 1;

-- Example 6: Which anticipation method is most used by businesses?
--   SELECT anticipation_method, SUM(total_transactions) as usage
--   FROM v_anticipation_analysis
--   WHERE entity = 'business'
--   GROUP BY anticipation_method
--   ORDER BY usage DESC
--   LIMIT 1;

-- Example 7: Get today's critical alerts
--   SELECT * 
--   FROM v_alerts 
--   WHERE day = date('now') 
--     AND alert_level IN ('🔴 CRITICAL', '🟠 HIGH')
--   ORDER BY severity_score DESC;

-- Example 8: Compare weekend vs weekday performance
--   SELECT 
--     CASE WHEN weekday_num IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END as period,
--     SUM(tpv) as total_tpv,
--     AVG(avg_ticket) as avg_ticket
--   FROM v_weekday_analysis
--   GROUP BY period;