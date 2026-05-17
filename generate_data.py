"""
generate_data.py
Generates synthetic enterprise software license data.
All data is fictional and created for portfolio demonstration only.
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# ── Config ────────────────────────────────────────────────
NUM_LICENSES    = 520
OUTPUT_CSV      = "data/licenses.csv"
OUTPUT_DB       = "data/licenses.db"

VENDORS  = ["Vendor_A", "Vendor_B", "Vendor_C"]
TOOLS    = {
    "Vendor_A": ["DesignTool_Pro", "DesignTool_Lite", "LayoutEditor", "SchematicCapture"],
    "Vendor_B": ["SimEngine_X",   "SimEngine_Pro",   "WaveformViewer", "TimingAnalyzer"],
    "Vendor_C": ["VerifyTool_A",  "VerifyTool_B",    "CoverageAnalyzer","FormalChecker"],
}
DEPTS    = ["ASIC Design", "Verification", "Physical Design", "DFT", "Mixed-Signal", "Analog"]
REGIONS  = ["APAC", "EMEA", "Americas"]
LIC_TYPE = ["Floating", "Node-Locked"]

# ── Helpers ───────────────────────────────────────────────
def random_date(start_days_ago=730, end_days_ago=0):
    offset = random.randint(end_days_ago, start_days_ago)
    return datetime.today() - timedelta(days=offset)

def expiry_date(issue_date, years=1):
    return issue_date + timedelta(days=365 * years)

# ── Generate ──────────────────────────────────────────────
records = []
for i in range(1, NUM_LICENSES + 1):
    vendor     = random.choice(VENDORS)
    tool       = random.choice(TOOLS[vendor])
    dept       = random.choice(DEPTS)
    region     = random.choice(REGIONS)
    lic_type   = random.choices(LIC_TYPE, weights=[0.7, 0.3])[0]
    total_seats= random.choice([5, 10, 15, 20, 25, 50])

    # Utilization: intentionally skewed — some over, some under
    avg_util   = round(np.random.beta(2, 3) * 100, 1)          # many underutilized
    peak_util  = min(round(avg_util + random.uniform(5, 30), 1), 100)

    cost_seat  = random.choice([8000, 12000, 15000, 20000, 25000, 30000])
    total_cost = total_seats * cost_seat

    issue_date = random_date(start_days_ago=730, end_days_ago=90)
    exp_date   = expiry_date(issue_date, years=random.choice([1, 2]))

    days_to_exp = (exp_date - datetime.today()).days

    # Risk scoring
    if days_to_exp < 0:
        risk = "Expired"
    elif days_to_exp <= 30:
        risk = "Critical"
    elif days_to_exp <= 60:
        risk = "High"
    elif days_to_exp <= 90:
        risk = "Medium"
    else:
        risk = "Low"

    # Over-licensing flag
    over_licensed = avg_util < 40

    # Potential savings
    unused_seats   = max(0, int(total_seats * (1 - avg_util / 100)) - 1)
    potential_save = unused_seats * cost_seat

    records.append({
        "license_id"       : f"LIC-{i:04d}",
        "vendor"           : vendor,
        "tool_name"        : tool,
        "license_type"     : lic_type,
        "department"       : dept,
        "region"           : region,
        "total_seats"      : total_seats,
        "avg_utilization"  : avg_util,
        "peak_utilization" : peak_util,
        "cost_per_seat_usd": cost_seat,
        "total_cost_usd"   : total_cost,
        "issue_date"       : issue_date.strftime("%Y-%m-%d"),
        "expiry_date"      : exp_date.strftime("%Y-%m-%d"),
        "days_to_expiry"   : days_to_exp,
        "renewal_risk"     : risk,
        "over_licensed"    : over_licensed,
        "unused_seats"     : unused_seats,
        "potential_savings": potential_save,
    })

df = pd.DataFrame(records)

# ── Save CSV ──────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(f"[✓] CSV saved  → {OUTPUT_CSV}  ({len(df)} rows)")

# ── Save SQLite ───────────────────────────────────────────
conn = sqlite3.connect(OUTPUT_DB)
df.to_sql("licenses", conn, if_exists="replace", index=False)
conn.close()
print(f"[✓] DB saved   → {OUTPUT_DB}")

# ── Quick summary ─────────────────────────────────────────
print("\n── Dataset Summary ──────────────────────────────────")
print(f"  Total licenses    : {len(df)}")
print(f"  Total cost (USD)  : ${df['total_cost_usd'].sum():,.0f}")
print(f"  Over-licensed     : {df['over_licensed'].sum()} licenses")
print(f"  Potential savings : ${df['potential_savings'].sum():,.0f}")
print(f"  Critical/Expired  : {df[df['renewal_risk'].isin(['Critical','Expired'])].shape[0]} licenses")
print(f"  Avg utilization   : {df['avg_utilization'].mean():.1f}%")
