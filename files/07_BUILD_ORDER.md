# 07_BUILD_ORDER.md — Exact Implementation Sequence

Follow every step in order. Do not skip steps or reorder.
After each `bench migrate`, verify in the browser before proceeding.

---

## PHASE 0 — Preparation

### Step 0.1 — Confirm App and Module

```bash
# List apps — confirm your app name
bench list-apps

# List sites — confirm your site name
ls sites/

# Confirm the app is installed on the site
bench --site [site-name] list-apps
```

### Step 0.2 — Create Module Folder Structure

```bash
cd apps/[app-name]

# Create module folder
mkdir -p [app-name]/poultry/doctype
mkdir -p [app-name]/poultry/report
mkdir -p [app-name]/fixtures

# Create __init__.py files
touch [app-name]/poultry/__init__.py
touch [app-name]/poultry/doctype/__init__.py
touch [app-name]/poultry/report/__init__.py
touch [app-name]/fixtures/__init__.py
```

### Step 0.3 — Register Module in modules.txt

Open `[app-name]/modules.txt` and add:
```
Poultry
```

### Step 0.4 — Restart and Migrate

```bash
bench --site [site-name] migrate
bench restart
```

Verify: Go to Desk → Module Poultry should appear in the module list.

---

## PHASE 1 — Child Table Doctypes (No Dependencies)

### Step 1.1 — Create Feed Purchase Item

```bash
cd apps/[app-name]/[app-name]/poultry/doctype
mkdir -p feed_purchase_item
```

Create file `feed_purchase_item/feed_purchase_item.json` with the JSON from `02_DOCTYPES.md § 1`.
Create file `feed_purchase_item/__init__.py` (empty).
Create file `feed_purchase_item/feed_purchase_item.py`:
```python
import frappe
from frappe.model.document import Document
class FeedPurchaseItem(Document):
    pass
```

```bash
bench --site [site-name] migrate
```

✅ Verify: Desk → Search → "Feed Purchase Item" doctype exists.

### Step 1.2 — Create Bird Collection Detail

```bash
mkdir -p bird_collection_detail
```

Create `bird_collection_detail/bird_collection_detail.json` from `02_DOCTYPES.md § 2`.
Create `bird_collection_detail/__init__.py` (empty).
Create `bird_collection_detail/bird_collection_detail.py`:
```python
import frappe
from frappe.model.document import Document
class BirdCollectionDetail(Document):
    pass
```

```bash
bench --site [site-name] migrate
```

### Step 1.3 — Create Feed Standard Row (child for config)

```bash
mkdir -p feed_standard_row
```

Create `feed_standard_row/feed_standard_row.json` from `02_DOCTYPES.md § 8 (child)`.
Create `feed_standard_row/__init__.py` (empty).
Create `feed_standard_row/feed_standard_row.py`:
```python
import frappe
from frappe.model.document import Document
class FeedStandardRow(Document):
    pass
```

```bash
bench --site [site-name] migrate
```

---

## PHASE 2 — Configuration Doctype

### Step 2.1 — Create Feed Standard Config (Single)

```bash
mkdir -p feed_standard_config
```

Create `feed_standard_config/feed_standard_config.json` from `02_DOCTYPES.md § 8`.
Create `feed_standard_config/__init__.py` (empty).
Create `feed_standard_config/feed_standard_config.py`:
```python
import frappe
from frappe.model.document import Document
class FeedStandardConfig(Document):
    pass
```

```bash
bench --site [site-name] migrate
```

✅ Verify: Desk → Search → "Feed Standard Config" → it should be a single (no list view).

---

## PHASE 3 — Master Doctype

### Step 3.1 — Create Poultry Crop

```bash
mkdir -p poultry_crop
```

Create `poultry_crop/poultry_crop.json` from `02_DOCTYPES.md § 3`.
Create `poultry_crop/__init__.py` (empty).
Create `poultry_crop/poultry_crop.py` from `05_SERVER_SCRIPTS.md § Poultry Crop Controller`.
Create `poultry_crop/poultry_crop.js` from `04_CLIENT_SCRIPTS.md § 4`.

```bash
bench --site [site-name] migrate
bench --site [site-name] clear-cache
```

✅ Verify: Create a test Poultry Crop. Set farm name, code, warehouse, placement date, chicks received.
Confirm `total_chick_cost` auto-calculates on save.

---

## PHASE 4 — Transaction Doctypes

### Step 4.1 — Flock Daily Record

```bash
mkdir -p flock_daily_record
```

Create `flock_daily_record/flock_daily_record.json` from `02_DOCTYPES.md § 4`.
Create `flock_daily_record/__init__.py` (empty).
Create `flock_daily_record/flock_daily_record.py` from `05_SERVER_SCRIPTS.md § Flock Daily Record Controller`.
Create `flock_daily_record/flock_daily_record.js` from `04_CLIENT_SCRIPTS.md § 1`.

```bash
bench --site [site-name] migrate
bench --site [site-name] clear-cache
```

✅ Verify:
- Create a Flock Daily Record linked to the test crop
- Confirm `day_age` auto-calculates from placement date
- Enter mortality → confirm `closing_stock` and `mortality_pct` update
- Enter `feed_in_kg` → confirm `feed_variance_kg` updates

### Step 4.2 — Feed Purchase Entry

```bash
mkdir -p feed_purchase_entry
```

Create `feed_purchase_entry/feed_purchase_entry.json` from `02_DOCTYPES.md § 5`.
Create `feed_purchase_entry/__init__.py` (empty).
Create `feed_purchase_entry/feed_purchase_entry.py` from `05_SERVER_SCRIPTS.md § Feed Purchase Entry Controller`.
Create `feed_purchase_entry/feed_purchase_entry.js` from `04_CLIENT_SCRIPTS.md § 2`.

```bash
bench --site [site-name] migrate
bench --site [site-name] clear-cache
```

✅ Verify:
- Create a Feed Purchase Entry for the test crop
- Add a row: FEED-C1, 10 bags, 50 KG/bag → `total_kgs` should be 500
- Add price → `total_cost` should calculate
- **Submit** the entry → confirm a Stock Entry (Material Receipt) is auto-created
- Check stock balance in ERPNext for FEED-C1 in the farm warehouse

### Step 4.3 — Bird Collection Entry

```bash
mkdir -p bird_collection_entry
```

Create `bird_collection_entry/bird_collection_entry.json` from `02_DOCTYPES.md § 6`.
Create `bird_collection_entry/__init__.py` (empty).
Create `bird_collection_entry/bird_collection_entry.py` from `05_SERVER_SCRIPTS.md § Bird Collection Entry Controller`.
Create `bird_collection_entry/bird_collection_entry.js` from `04_CLIENT_SCRIPTS.md § 3`.

```bash
bench --site [site-name] migrate
bench --site [site-name] clear-cache
```

✅ Verify:
- Move test crop to `Slaughter` status
- Create a Bird Collection Entry with 3 weight band rows
- Confirm `total_birds`, `total_revenue`, `average_weight_kg` auto-calculate

---

## PHASE 5 — Financial Summary Doctype

### Step 5.1 — Crop Financial Summary

```bash
mkdir -p crop_financial_summary
```

Create `crop_financial_summary/crop_financial_summary.json` from `02_DOCTYPES.md § 7`.
Create `crop_financial_summary/__init__.py` (empty).
Create `crop_financial_summary/crop_financial_summary.py`:
```python
import frappe
from frappe.model.document import Document
class CropFinancialSummary(Document):
    pass
```

```bash
bench --site [site-name] migrate
```

✅ Verify:
- Close the test crop: Poultry Crop → Actions → Close Crop
- A Crop Financial Summary should be auto-generated
- Confirm all cost and revenue fields are populated

---

## PHASE 6 — Hooks

### Step 6.1 — Update hooks.py

Open `[app-name]/hooks.py` and add the `doc_events` and `scheduler_events` from `05_SERVER_SCRIPTS.md § hooks.py Updates`.

### Step 6.2 — Create Scheduled Jobs File

Create `[app-name]/poultry/scheduled.py` from `05_SERVER_SCRIPTS.md § Scheduled Jobs`.

```bash
bench restart
```

✅ Verify hooks loaded: `bench --site [site-name] execute frappe.get_hooks --kwargs "{'hook': 'doc_events'}"` → should show your events.

---

## PHASE 7 — Fixtures

### Step 7.1 — Create Fixture File

Create `[app-name]/fixtures/load_fixtures.py` from `03_FIXTURES.md`.

### Step 7.2 — Run Fixtures

```bash
# IMPORTANT: Run in this order
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_item_groups
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_uoms
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_feed_items
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_warehouse_group
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_roles
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_feed_standards
```

✅ Verify:
- Desk → Item → Filter by Item Group "Poultry Feed" → 5 items should appear (PBS, C1, C2, C3, Finisher)
- Desk → Warehouse → Anirita Farms group and farm warehouses exist
- Desk → Role → Farm Manager, Store Manager, Farm Director exist
- Desk → Feed Standard Config → Standards table populated with 6 rows

---

## PHASE 8 — Reports

### Step 8.1 — Create Report Folders

```bash
cd [app-name]/poultry/report
mkdir -p crop_daily_performance weekly_mortality_report feed_consumption_report crop_profit_loss crop_performance_comparison

for d in crop_daily_performance weekly_mortality_report feed_consumption_report crop_profit_loss crop_performance_comparison; do
    touch $d/__init__.py
done
```

### Step 8.2 — Create Each Report

For each report in `06_REPORTS.md`:
1. Create `{report_folder}/{report_name}.json`:
```json
{
  "report_name": "Crop Daily Performance",
  "report_type": "Script Report",
  "module": "Poultry",
  "ref_doctype": "Flock Daily Record",
  "is_standard": "Yes"
}
```

2. Create `{report_folder}/{report_name}.py` with the Python `execute()` function from `06_REPORTS.md`.

```bash
bench --site [site-name] migrate
bench --site [site-name] clear-cache
```

✅ Verify: Desk → Report → filter by Module "Poultry" → 5 reports should appear.

---

## PHASE 9 — Permissions

Run in ERPNext UI (Role Permission Manager) or via script:

```python
# bench --site [site-name] console
import frappe

perms = [
    # (role, doctype, read, write, create, submit, cancel)
    ("Farm Manager",  "Poultry Crop",           1, 1, 1, 0, 0),
    ("Farm Manager",  "Flock Daily Record",      1, 1, 1, 0, 0),
    ("Farm Manager",  "Feed Purchase Entry",     1, 0, 0, 0, 0),
    ("Farm Manager",  "Bird Collection Entry",   1, 0, 0, 0, 0),
    ("Store Manager", "Feed Purchase Entry",     1, 1, 1, 1, 1),
    ("Store Manager", "Poultry Crop",            1, 0, 0, 0, 0),
    ("Farm Director", "Poultry Crop",            1, 1, 1, 0, 0),
    ("Farm Director", "Flock Daily Record",      1, 1, 1, 0, 0),
    ("Farm Director", "Feed Purchase Entry",     1, 1, 1, 1, 1),
    ("Farm Director", "Bird Collection Entry",   1, 1, 1, 1, 1),
    ("Farm Director", "Crop Financial Summary",  1, 1, 1, 0, 0),
]

for role, dt, read, write, create, submit, cancel in perms:
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": dt,
        "parenttype": "DocType",
        "parentfield": "permissions",
        "role": role,
        "read": read, "write": write, "create": create,
        "submit": submit, "cancel": cancel,
        "permlevel": 0
    }).insert(ignore_permissions=True)

frappe.db.commit()
```

---

## PHASE 10 — Historical Data Migration (Crop 14)

```bash
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.create_crop_14
```

Then manually enter the daily records from the paper forms via the UI, or
create a migration script using the data from Images 1, 4, and 5.

---

## PHASE 11 — Final Verification Checklist

Run through this checklist end-to-end on a fresh test crop:

- [ ] Create Poultry Crop (Draft) → chick cost auto-calculates
- [ ] Activate Crop → status changes to Active
- [ ] Create Flock Daily Record → day age, feed std, opening stock auto-populate
- [ ] Enter mortality → closing stock and % update
- [ ] Save → Poultry Crop `current_stock` and `total_mortality` update
- [ ] Create Feed Purchase Entry → warehouse auto-fetches from crop
- [ ] Submit Feed Purchase Entry → Stock Entry auto-created, stock balance increases
- [ ] Start Slaughter → status changes to Slaughter
- [ ] Create Bird Collection Entry → bird age auto-calculates, totals compute
- [ ] Submit Bird Collection Entry → Crop `total_birds_collected` and `total_revenue` update
- [ ] Close Crop → Crop Financial Summary auto-generated with correct P&L
- [ ] Run "Crop Daily Performance" report → data matches daily records
- [ ] Run "Crop Profit Loss" report → data matches Financial Summary
- [ ] Mortality alert email fires when mortality % > 1% (test by setting a high mortality)

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `LinkValidationError` | Doctype referenced before created | Follow Phase order strictly |
| `AttributeError: has no attribute 'get_doc'` | Module not found | Check `__init__.py` files exist in all folders |
| Stock Entry not created on submit | `on_submit` hook not registered | Verify `hooks.py` has `doc_events` and run `bench restart` |
| Feed Standard Config empty | Fixtures not run | Run `create_feed_standards` fixture |
| `Warehouse not found` | Company suffix mismatch | Confirm warehouse name includes ` - CompanyAbbr` |
| `autoname format error` | Invalid characters in farm_code | Use only alphanumeric in farm_code field |
