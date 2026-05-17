"""
etl_pipeline.py
Reads raw license CSV, applies transformations, validates data quality,
and loads a clean analytical table into SQLite.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

RAW_CSV    = "data/licenses.csv"
OUTPUT_DB  = "data/licenses.db"
LOG_FILE   = "outputs/etl_log.txt"

os.makedirs("outputs", exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── EXTRACT ───────────────────────────────────────────────
log("EXTRACT: Reading raw license data")
df = pd.read_csv(RAW_CSV)
log(f"  Loaded {len(df)} rows, {df.shape[1]} columns")

# ── VALIDATE ──────────────────────────────────────────────
log("VALIDATE: Running data quality checks")

null_counts = df.isnull().sum()
if null_counts.any():
    log(f"  WARNING — nulls found: {null_counts[null_counts > 0].to_dict()}")
else:
    log("  [✓] No nulls found")

dupes = df.duplicated(subset=["license_id"]).sum()
log(f"  [✓] Duplicate license_ids: {dupes}")

invalid_util = df[(df["avg_utilization"] < 0) | (df["avg_utilization"] > 100)]
log(f"  [✓] Invalid utilization values: {len(invalid_util)}")

# ── TRANSFORM ─────────────────────────────────────────────
log("TRANSFORM: Applying business logic")

# Utilization band
def util_band(u):
    if u < 25:  return "Critical Underuse"
    if u < 50:  return "Underutilized"
    if u < 75:  return "Moderate"
    return "Optimal"

df["utilization_band"]  = df["avg_utilization"].apply(util_band)

# Renewal urgency label
df["renewal_urgency"] = df["days_to_expiry"].apply(
    lambda d: "Expired"   if d < 0   else
              "30 Days"   if d <= 30  else
              "60 Days"   if d <= 60  else
              "90 Days"   if d <= 90  else "Stable"
)

# Cost efficiency score (higher = worse value)
df["cost_efficiency_score"] = round(
    df["total_cost_usd"] / df["avg_utilization"].replace(0, 0.1), 2
)

# Optimization priority
def priority(row):
    if row["renewal_risk"] in ["Critical", "Expired"]: return "Urgent"
    if row["over_licensed"] and row["potential_savings"] > 50000: return "High"
    if row["over_licensed"]: return "Medium"
    return "Monitor"

df["optimization_priority"] = df.apply(priority, axis=1)
df["etl_load_timestamp"]    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

log(f"  [✓] Utilization bands assigned")
log(f"  [✓] Renewal urgency labels assigned")
log(f"  [✓] Optimization priority scored")

# ── LOAD ──────────────────────────────────────────────────
log("LOAD: Writing to SQLite")
conn = sqlite3.connect(OUTPUT_DB)
df.to_sql("licenses_clean", conn, if_exists="replace", index=False)

# Summary view
conn.execute("""
CREATE VIEW IF NOT EXISTS v_renewal_risk_summary AS
SELECT
    renewal_risk,
    COUNT(*)                          AS license_count,
    SUM(total_cost_usd)               AS total_cost,
    ROUND(AVG(avg_utilization), 1)    AS avg_utilization,
    SUM(potential_savings)            AS potential_savings
FROM licenses_clean
GROUP BY renewal_risk
ORDER BY
    CASE renewal_risk
        WHEN 'Expired'  THEN 1
        WHEN 'Critical' THEN 2
        WHEN 'High'     THEN 3
        WHEN 'Medium'   THEN 4
        ELSE 5
    END
""")
conn.commit()
conn.close()
log(f"  [✓] licenses_clean table loaded ({len(df)} rows)")
log(f"  [✓] v_renewal_risk_summary view created")

# ── REPORT ────────────────────────────────────────────────
log("\n── ETL Output Summary ───────────────────────────────")
log(f"  Records processed : {len(df)}")
log(f"  Urgent renewals   : {(df['optimization_priority'] == 'Urgent').sum()}")
log(f"  Over-licensed     : {df['over_licensed'].sum()}")
log(f"  Potential savings : ${df['potential_savings'].sum():,.0f}")
log(f"  ETL status        : SUCCESS")
