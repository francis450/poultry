# 06_REPORTS.md — Custom Report Definitions

All reports are **Script Report** type. Create via:
`Desk → Report → New → Report Type: Script Report → Module: Poultry`

---

## 1. Crop Daily Performance Report

**Report Name:** `Crop Daily Performance`
**Purpose:** Full daily log for a crop — mirrors the paper form exactly

**Filters:**
```python
[
    {
        "fieldname": "crop",
        "label": "Poultry Crop",
        "fieldtype": "Link",
        "options": "Poultry Crop",
        "reqd": 1
    },
    {
        "fieldname": "from_date",
        "label": "From Date",
        "fieldtype": "Date"
    },
    {
        "fieldname": "to_date",
        "label": "To Date",
        "fieldtype": "Date",
        "default": "Today"
    }
]
```

**Report Script (Python):**
```python
import frappe

def execute(filters=None):
    columns = get_columns()
    data    = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Date",              "fieldname": "date",              "fieldtype": "Date",    "width": 100},
        {"label": "Day",               "fieldname": "day_age",           "fieldtype": "Int",     "width": 60},
        {"label": "Week",              "fieldname": "week_number",       "fieldtype": "Int",     "width": 60},
        {"label": "Opening Stock",     "fieldname": "opening_stock",     "fieldtype": "Int",     "width": 120},
        {"label": "Mortality",         "fieldname": "mortality",         "fieldtype": "Int",     "width": 90},
        {"label": "Mortality %",       "fieldname": "mortality_pct",     "fieldtype": "Percent", "width": 100},
        {"label": "Closing Stock",     "fieldname": "closing_stock",     "fieldtype": "Int",     "width": 120},
        {"label": "Feed Std (GMS)",    "fieldname": "feed_std_gms",      "fieldtype": "Float",   "width": 120},
        {"label": "Feed In (KG)",      "fieldname": "feed_in_kg",        "fieldtype": "Float",   "width": 100},
        {"label": "Std Total (KG)",    "fieldname": "std_total_kg",      "fieldtype": "Float",   "width": 110},
        {"label": "Feed Variance",     "fieldname": "feed_variance_kg",  "fieldtype": "Float",   "width": 110},
        {"label": "B.Wt Actual (GMS)", "fieldname": "bwt_actual_gms",   "fieldtype": "Float",   "width": 130},
        {"label": "B.Wt Std (GMS)",    "fieldname": "bwt_std_gms",      "fieldtype": "Float",   "width": 120},
        {"label": "B.Wt Variance",     "fieldname": "bwt_variance_gms", "fieldtype": "Float",   "width": 120},
        {"label": "Vaccination",       "fieldname": "vaccination",       "fieldtype": "Check",   "width": 100},
        {"label": "Remarks",           "fieldname": "remarks",           "fieldtype": "Data",    "width": 200},
    ]

def get_data(filters):
    conditions = "WHERE crop = %(crop)s"
    if filters.get("from_date"):
        conditions += " AND date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND date <= %(to_date)s"

    data = frappe.db.sql(f"""
        SELECT
            date, day_age, week_number,
            opening_stock, mortality, mortality_pct, closing_stock,
            feed_std_gms, feed_in_kg, std_total_kg, feed_variance_kg,
            bwt_actual_gms, bwt_std_gms, bwt_variance_gms,
            vaccination, vaccination_details as remarks
        FROM `tabFlock Daily Record`
        {conditions}
        ORDER BY day_age ASC
    """, filters, as_dict=True)

    # Insert weekly subtotals
    result = []
    week_groups = {}
    for row in data:
        wk = row.week_number
        if wk not in week_groups:
            week_groups[wk] = []
        week_groups[wk].append(row)

    for wk, rows in sorted(week_groups.items()):
        result.extend(rows)
        # Weekly summary row
        result.append({
            "date":          f"── WEEK {wk} TOTAL ──",
            "mortality":     sum(r.mortality or 0 for r in rows),
            "feed_in_kg":    round(sum(r.feed_in_kg or 0 for r in rows), 2),
            "std_total_kg":  round(sum(r.std_total_kg or 0 for r in rows), 2),
            "is_subtotal":   True,
        })

    return result
```

---

## 2. Weekly Mortality Report

**Report Name:** `Weekly Mortality Report`
**Purpose:** Mortality breakdown by week across all active or selected crops

```python
import frappe

def execute(filters=None):
    columns = [
        {"label": "Crop",       "fieldname": "crop",            "fieldtype": "Link",    "options": "Poultry Crop", "width": 200},
        {"label": "Farm",       "fieldname": "farm_name",       "fieldtype": "Data",    "width": 150},
        {"label": "Week",       "fieldname": "week_number",     "fieldtype": "Int",     "width": 70},
        {"label": "Mortality",  "fieldname": "total_mortality", "fieldtype": "Int",     "width": 100},
        {"label": "Avg Daily Mort.", "fieldname": "avg_mortality","fieldtype": "Float",  "width": 130},
        {"label": "Mortality %","fieldname": "mortality_pct",   "fieldtype": "Percent", "width": 110},
        {"label": "Closing Stock (End of Week)", "fieldname": "closing_stock", "fieldtype": "Int", "width": 200},
    ]

    conditions = ""
    if filters.get("crop"):
        conditions = "AND fdr.crop = %(crop)s"

    data = frappe.db.sql(f"""
        SELECT
            fdr.crop,
            pc.farm_name,
            fdr.week_number,
            SUM(fdr.mortality)     as total_mortality,
            AVG(fdr.mortality)     as avg_mortality,
            AVG(fdr.mortality_pct) as mortality_pct,
            MIN(fdr.closing_stock) as closing_stock
        FROM `tabFlock Daily Record` fdr
        JOIN `tabPoultry Crop` pc ON pc.name = fdr.crop
        WHERE 1=1 {conditions}
        GROUP BY fdr.crop, fdr.week_number
        ORDER BY fdr.crop, fdr.week_number
    """, filters, as_dict=True)

    return columns, data
```

---

## 3. Feed Consumption vs Standard Report

**Report Name:** `Feed Consumption Report`
**Purpose:** Actual vs. standard feed tracking — identifies over/under-feeding

```python
import frappe

def execute(filters=None):
    columns = [
        {"label": "Crop",            "fieldname": "crop",             "fieldtype": "Link", "options": "Poultry Crop", "width": 200},
        {"label": "Week",            "fieldname": "week_number",      "fieldtype": "Int",  "width": 70},
        {"label": "Feed In (KG)",    "fieldname": "actual_feed_kg",   "fieldtype": "Float","width": 130},
        {"label": "Std Feed (KG)",   "fieldname": "std_feed_kg",      "fieldtype": "Float","width": 130},
        {"label": "Variance (KG)",   "fieldname": "variance_kg",      "fieldtype": "Float","width": 120},
        {"label": "Variance %",      "fieldname": "variance_pct",     "fieldtype": "Percent","width": 110},
    ]

    data = frappe.db.sql("""
        SELECT
            crop,
            week_number,
            SUM(feed_in_kg)   as actual_feed_kg,
            SUM(std_total_kg) as std_feed_kg,
            SUM(feed_in_kg) - SUM(std_total_kg) as variance_kg,
            CASE
                WHEN SUM(std_total_kg) > 0
                THEN ((SUM(feed_in_kg) - SUM(std_total_kg)) / SUM(std_total_kg)) * 100
                ELSE 0
            END as variance_pct
        FROM `tabFlock Daily Record`
        GROUP BY crop, week_number
        ORDER BY crop, week_number
    """, as_dict=True)

    return columns, data
```

---

## 4. Crop Profit & Loss Report

**Report Name:** `Crop Profit Loss`
**Purpose:** Full P&L per crop — the digitised version of the Account Details sheet

```python
import frappe

def execute(filters=None):
    columns = [
        {"label": "Crop",                "fieldname": "crop",               "fieldtype": "Link", "options": "Poultry Crop","width": 220},
        {"label": "Farm",                "fieldname": "farm_name",          "fieldtype": "Data", "width": 150},
        {"label": "Chick Cost (KES)",    "fieldname": "chick_cost",         "fieldtype": "Currency","width": 140},
        {"label": "Feed Cost (KES)",     "fieldname": "total_feed_cost",    "fieldtype": "Currency","width": 140},
        {"label": "Mortality Loss (KES)","fieldname": "mortality_loss_value","fieldtype": "Currency","width": 160},
        {"label": "Other Costs (KES)",   "fieldname": "other_costs",        "fieldtype": "Currency","width": 140},
        {"label": "Total Cost (KES)",    "fieldname": "cumulative_cost",    "fieldtype": "Currency","width": 140},
        {"label": "Revenue (KES)",       "fieldname": "total_revenue",      "fieldtype": "Currency","width": 140},
        {"label": "Net Profit (KES)",    "fieldname": "net_profit",         "fieldtype": "Currency","width": 140},
        {"label": "Margin %",            "fieldname": "profit_margin_pct",  "fieldtype": "Percent", "width": 100},
        {"label": "Cost/Bird (KES)",     "fieldname": "cost_per_bird",      "fieldtype": "Currency","width": 130},
        {"label": "Revenue/Bird (KES)",  "fieldname": "revenue_per_bird",   "fieldtype": "Currency","width": 140},
        {"label": "FCR",                 "fieldname": "fcr",                "fieldtype": "Float",   "width": 80},
        {"label": "Mortality %",         "fieldname": "mortality_pct",      "fieldtype": "Percent", "width": 100},
    ]

    conditions = ""
    if filters and filters.get("crop"):
        conditions = "WHERE cfs.crop = %(crop)s"

    data = frappe.db.sql(f"""
        SELECT
            cfs.crop,
            pc.farm_name,
            cfs.chick_cost,
            cfs.total_feed_cost,
            cfs.mortality_loss_value,
            cfs.other_costs,
            cfs.cumulative_cost,
            cfs.total_revenue,
            cfs.net_profit,
            cfs.profit_margin_pct,
            cfs.cost_per_bird,
            cfs.revenue_per_bird,
            cfs.fcr,
            pc.mortality_pct
        FROM `tabCrop Financial Summary` cfs
        JOIN `tabPoultry Crop` pc ON pc.name = cfs.crop
        {conditions}
        ORDER BY cfs.crop DESC
    """, filters or {}, as_dict=True)

    # Highlight rows where net_profit is negative
    for row in data:
        if (row.net_profit or 0) < 0:
            row["bold"] = 1

    return columns, data
```

---

## 5. Cross-Crop Performance Comparison

**Report Name:** `Crop Performance Comparison`
**Purpose:** Compare KPIs across multiple closed crops for benchmarking

```python
import frappe

def execute(filters=None):
    columns = [
        {"label": "Crop",           "fieldname": "name",              "fieldtype": "Link", "options": "Poultry Crop","width": 200},
        {"label": "Farm",           "fieldname": "farm_name",         "fieldtype": "Data", "width": 150},
        {"label": "Chicks In",      "fieldname": "chicks_received",   "fieldtype": "Int",  "width": 100},
        {"label": "Birds Out",      "fieldname": "total_birds_collected","fieldtype": "Int","width": 100},
        {"label": "Mortality %",    "fieldname": "mortality_pct",     "fieldtype": "Percent","width": 100},
        {"label": "FCR",            "fieldname": "fcr",               "fieldtype": "Float","width": 80},
        {"label": "Avg Weight (KG)","fieldname": "avg_weight",        "fieldtype": "Float","width": 130},
        {"label": "Revenue (KES)",  "fieldname": "total_revenue",     "fieldtype": "Currency","width": 130},
        {"label": "Net Profit (KES)","fieldname": "net_profit",       "fieldtype": "Currency","width": 130},
        {"label": "Rev/Bird (KES)", "fieldname": "revenue_per_bird",  "fieldtype": "Currency","width": 130},
    ]

    data = frappe.db.sql("""
        SELECT
            pc.name,
            pc.farm_name,
            pc.chicks_received,
            pc.total_birds_collected,
            pc.mortality_pct,
            cfs.fcr,
            bce_agg.avg_weight,
            pc.total_revenue,
            cfs.net_profit,
            cfs.revenue_per_bird
        FROM `tabPoultry Crop` pc
        LEFT JOIN `tabCrop Financial Summary` cfs ON cfs.crop = pc.name
        LEFT JOIN (
            SELECT crop, AVG(average_weight_kg) as avg_weight
            FROM `tabBird Collection Entry`
            WHERE docstatus = 1
            GROUP BY crop
        ) bce_agg ON bce_agg.crop = pc.name
        WHERE pc.status = 'Closed'
        ORDER BY pc.placement_date DESC
    """, as_dict=True)

    return columns, data
```
