# Power BI Setup Guide
# Enterprise License Intelligence Platform

## Step 1 — Run the Python scripts first

```bash
pip install pandas numpy
python generate_data.py     # creates data/licenses.csv + licenses.db
python etl_pipeline.py      # creates data/licenses_clean table
```

## Step 2 — Connect Power BI to SQLite

1. Open Power BI Desktop
2. Click: Home → Get Data → More → Database → ODBC
3. If ODBC not available: Get Data → Text/CSV
   - Import data/licenses.csv directly (easier option)
4. Alternatively: Get Data → Python Script
   - Paste this to load directly:

```python
import pandas as pd
df = pd.read_csv(r"C:\YOUR_PATH\license_platform\data\licenses.csv")
```

## Step 3 — Build these visuals (in order)

### Row 1 — KPI Cards (top strip)
| Card | Field | Format |
|------|-------|--------|
| Total Licenses | COUNT(license_id) | Number |
| Portfolio Cost | SUM(total_cost_usd) | $0.0M |
| Avg Utilization | AVG(avg_utilization) | 0.0% |
| At-Risk Renewals | COUNTIF renewal_risk = Critical/Expired | Number |
| Savings Opportunity | SUM(potential_savings) | $0.0M |

### Row 2 — Main Charts
- **Clustered Bar** : Vendor vs Avg Utilization + Avg Peak Utilization
- **Donut Chart**   : Utilization Band distribution (4 segments)
- **Matrix Table**  : Renewal Risk by Vendor (conditional formatting — red = Critical)

### Row 3 — Detail Tables
- **Top Savings Table** : license_id, tool, dept, unused_seats, potential_savings
  - Sort by potential_savings DESC
  - Add data bars to potential_savings column
- **Renewal Calendar** : expiry_date (month), license count, cost at renewal
  - Use a bar chart sorted by month

### Row 4 — Filters / Slicers
- Vendor slicer (dropdown)
- Region slicer (dropdown)
- Renewal Risk slicer (checkbox)
- Department slicer (checkbox)

## Step 4 — DAX Measures to create

```dax
Total Licenses = COUNTROWS(licenses_clean)

Total Portfolio Cost = SUM(licenses_clean[total_cost_usd])

Avg Utilization % = AVERAGE(licenses_clean[avg_utilization])

At-Risk Count =
CALCULATE(
    COUNTROWS(licenses_clean),
    licenses_clean[renewal_risk] IN {"Critical", "Expired"}
)

Total Savings Opportunity = SUM(licenses_clean[potential_savings])

Over-Licensed Count =
CALCULATE(
    COUNTROWS(licenses_clean),
    licenses_clean[over_licensed] = TRUE()
)

Utilization Status =
SWITCH(
    TRUE(),
    AVERAGE(licenses_clean[avg_utilization]) < 25, "Critical Underuse",
    AVERAGE(licenses_clean[avg_utilization]) < 50, "Underutilized",
    AVERAGE(licenses_clean[avg_utilization]) < 75, "Moderate",
    "Optimal"
)
```

## Step 5 — Formatting tips for clean screenshots

- Theme     : Use "Executive" or custom dark/teal theme
- Font      : Segoe UI throughout
- Colors    : Red = Critical/Expired, Orange = High, Yellow = Medium, Green = Stable
- Add title : "Enterprise License Intelligence Platform"
- Add subtitle: "Powered by synthetic data | Portfolio Project"

## Step 6 — Screenshots to take for GitHub README

1. Full dashboard overview (main screenshot — use this as hero image)
2. KPI cards row closeup
3. Vendor utilization bar chart
4. Renewal risk matrix
5. Top savings opportunity table

Save as PNG: File → Export → Export as Image
