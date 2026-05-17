-- ============================================================
-- sql_analysis.sql
-- Enterprise License Intelligence Platform
-- Key analytical queries for Power BI and reporting
-- ============================================================


-- ── 1. KPI SUMMARY (for Power BI cards) ──────────────────
SELECT
    COUNT(*)                                        AS total_licenses,
    SUM(total_cost_usd)                             AS total_portfolio_cost,
    ROUND(AVG(avg_utilization), 1)                  AS avg_utilization_pct,
    SUM(CASE WHEN renewal_risk IN ('Critical','Expired') THEN 1 ELSE 0 END)
                                                    AS at_risk_renewals,
    SUM(potential_savings)                          AS total_savings_opportunity,
    SUM(CASE WHEN over_licensed = 1 THEN 1 ELSE 0 END)
                                                    AS over_licensed_count
FROM licenses_clean;


-- ── 2. UTILIZATION BY VENDOR (bar chart) ─────────────────
SELECT
    vendor,
    COUNT(*)                            AS license_count,
    ROUND(AVG(avg_utilization), 1)      AS avg_utilization,
    ROUND(AVG(peak_utilization), 1)     AS avg_peak_utilization,
    SUM(total_cost_usd)                 AS total_cost,
    SUM(potential_savings)              AS savings_opportunity
FROM licenses_clean
GROUP BY vendor
ORDER BY avg_utilization ASC;


-- ── 3. RENEWAL RISK PIPELINE (timeline / matrix) ─────────
SELECT
    renewal_risk,
    renewal_urgency,
    COUNT(*)                            AS license_count,
    SUM(total_cost_usd)                 AS cost_at_risk,
    MIN(days_to_expiry)                 AS nearest_expiry_days,
    GROUP_CONCAT(DISTINCT vendor)       AS vendors_affected
FROM licenses_clean
WHERE renewal_risk IN ('Critical', 'High', 'Medium', 'Expired')
GROUP BY renewal_risk, renewal_urgency
ORDER BY
    CASE renewal_risk
        WHEN 'Expired'  THEN 1
        WHEN 'Critical' THEN 2
        WHEN 'High'     THEN 3
        ELSE 4
    END;


-- ── 4. OVER-LICENSING DETECTION (cost savings table) ─────
SELECT
    license_id,
    vendor,
    tool_name,
    department,
    total_seats,
    avg_utilization             AS utilization_pct,
    unused_seats,
    cost_per_seat_usd,
    potential_savings,
    optimization_priority
FROM licenses_clean
WHERE over_licensed = 1
ORDER BY potential_savings DESC
LIMIT 25;


-- ── 5. DEPARTMENT USAGE ANALYSIS ─────────────────────────
SELECT
    department,
    COUNT(*)                            AS license_count,
    ROUND(AVG(avg_utilization), 1)      AS avg_utilization,
    SUM(total_cost_usd)                 AS total_spend,
    SUM(potential_savings)              AS savings_opportunity,
    SUM(CASE WHEN over_licensed = 1 THEN 1 ELSE 0 END)
                                        AS over_licensed_count
FROM licenses_clean
GROUP BY department
ORDER BY total_spend DESC;


-- ── 6. REGIONAL BREAKDOWN ────────────────────────────────
SELECT
    region,
    COUNT(*)                            AS license_count,
    ROUND(AVG(avg_utilization), 1)      AS avg_utilization,
    SUM(total_cost_usd)                 AS total_cost,
    SUM(CASE WHEN renewal_risk = 'Critical' THEN 1 ELSE 0 END)
                                        AS critical_renewals
FROM licenses_clean
GROUP BY region
ORDER BY total_cost DESC;


-- ── 7. UTILIZATION BAND DISTRIBUTION (donut chart) ───────
SELECT
    utilization_band,
    COUNT(*)                            AS license_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1)
                                        AS pct_of_total,
    SUM(total_cost_usd)                 AS cost_in_band,
    SUM(potential_savings)              AS savings_in_band
FROM licenses_clean
GROUP BY utilization_band
ORDER BY
    CASE utilization_band
        WHEN 'Critical Underuse' THEN 1
        WHEN 'Underutilized'     THEN 2
        WHEN 'Moderate'          THEN 3
        ELSE 4
    END;


-- ── 8. VENDOR VARIANCE ANALYSIS ──────────────────────────
SELECT
    vendor,
    tool_name,
    ROUND(AVG(avg_utilization), 1)      AS avg_util,
    ROUND(MAX(avg_utilization), 1)      AS max_util,
    ROUND(MIN(avg_utilization), 1)      AS min_util,
    ROUND(MAX(avg_utilization) - MIN(avg_utilization), 1)
                                        AS util_variance,
    COUNT(*)                            AS tool_count
FROM licenses_clean
GROUP BY vendor, tool_name
ORDER BY util_variance DESC;


-- ── 9. TOP 10 PROCUREMENT OPTIMIZATION TARGETS ───────────
SELECT
    license_id,
    vendor,
    tool_name,
    department,
    region,
    avg_utilization,
    unused_seats,
    potential_savings,
    renewal_risk,
    optimization_priority
FROM licenses_clean
WHERE optimization_priority IN ('Urgent', 'High')
ORDER BY potential_savings DESC
LIMIT 10;


-- ── 10. MONTHLY RENEWAL CALENDAR ─────────────────────────
SELECT
    STRFTIME('%Y-%m', expiry_date)      AS renewal_month,
    COUNT(*)                            AS licenses_expiring,
    SUM(total_cost_usd)                 AS cost_up_for_renewal,
    GROUP_CONCAT(DISTINCT vendor)       AS vendors
FROM licenses_clean
WHERE days_to_expiry BETWEEN 0 AND 180
GROUP BY renewal_month
ORDER BY renewal_month;
