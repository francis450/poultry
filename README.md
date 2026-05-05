# Poultry Farm

Poultry Farm is a custom Frappe app for managing broiler crop lifecycles from chick placement to daily flock tracking, feed purchasing, bird collection, crop closure, and profitability reporting.

The app is built around one operational idea: a **Poultry Crop** represents one batch of birds on a farm. Every daily record, feed purchase, bird collection, dashboard card, and financial report links back to that crop.

## Table of Contents

- [What the App Does](#what-the-app-does)
- [Core Business Flow](#core-business-flow)
- [Application Architecture](#application-architecture)
- [DocTypes](#doctypes)
- [Operational Workflows](#operational-workflows)
- [Automation and Hooks](#automation-and-hooks)
- [ERPNext Integration](#erpnext-integration)
- [Workspace, Dashboards, and Reports](#workspace-dashboards-and-reports)
- [Setup and Installation](#setup-and-installation)
- [Roles and Access](#roles-and-access)
- [Developer Notes](#developer-notes)
- [Known Current Limitations](#known-current-limitations)
- [Reference Files](#reference-files)

## What the App Does

The app helps a poultry farm team answer the daily and financial questions that matter during a crop:

- How many birds were placed, how many are alive, and how many have died?
- What is the current age and week number of the flock?
- Is daily mortality above the configured warning threshold?
- Is actual feed intake above or below the expected standard?
- Are birds meeting body-weight targets on weigh days?
- How much feed has been purchased for the crop and what did it cost?
- How many birds were collected at slaughter and at what weight/price bands?
- What is the crop's revenue, total cost, profit, margin, cost per bird, revenue per bird, and FCR?

The system is designed for a simple operating rhythm:

1. Create a crop when chicks are placed.
2. Activate the crop.
3. Record daily mortality, feed intake, vaccination, and weight checks.
4. Record feed purchases when feed is received.
5. Move the crop to slaughter.
6. Record bird collections by weight band.
7. Close the crop to generate financial results.

## Core Business Flow

```text
Poultry Crop
  |
  |-- Flock Daily Record
  |     Daily mortality, stock, feed intake, body weight, vaccination
  |
  |-- Feed Purchase Entry
  |     Feed purchased for the crop
  |     Creates ERPNext Stock Entry on submit
  |
  |-- Bird Collection Entry
  |     Birds collected by weight band and price
  |     Updates crop collection totals and FCR on submit
  |
  |-- Crop Financial Summary
        Generated or refreshed when the crop is closed
```

The `Poultry Crop` is the parent record. It stores the crop status and running totals. The other documents feed information back into it.

## Application Architecture

The app follows the normal Frappe app layout:

```text
poultry_farm/
  hooks.py
  modules.txt
  patches.txt
  poultry/
    doctype/
      poultry_crop/
      flock_daily_record/
      feed_purchase_entry/
      feed_purchase_item/
      bird_collection_entry/
      bird_collection_detail/
      crop_financial_summary/
      feed_standard_config/
      feed_standard_row/
    report/
      crop_daily_performance/
      weekly_mortality_report/
      feed_consumption_report/
      crop_profit_loss/
      crop_performance_comparison/
    workspace/
    number_card/
    dashboard_chart/
    scheduled.py
    workspace_access.py
  fixtures/
    load_fixtures.py
```

The app has one Frappe module, `Poultry`. Most behavior is implemented in DocType controller Python files and form client scripts.

Key files:

- `poultry_farm/hooks.py` registers document events, scheduler jobs, and after-migrate workspace syncing.
- `poultry/doctype/*/*.py` contains server-side validation, calculations, submit/cancel behavior, and whitelisted helper methods.
- `poultry/doctype/*/*.js` contains form behavior, custom buttons, and client-side calculations.
- `poultry/scheduled.py` contains scheduled daily and weekly background jobs.
- `poultry/workspace_access.py` keeps the Poultry workspace, reports, number cards, and dashboard charts aligned after migration.
- `fixtures/load_fixtures.py` creates required ERPNext master data such as item groups, UOMs, feed items, warehouses, roles, and feed standards.

## DocTypes

### Poultry Crop

The master record for one batch of birds.

Main fields:

- `crop_number`: sequential crop number for the farm.
- `status`: `Draft`, `Active`, `Slaughter`, or `Closed`.
- `farm_name` and `farm_code`: identify the farm and support naming/title logic.
- `warehouse`: farm store or destination warehouse used by feed purchase stock entries.
- `placement_date`: chick placement date. This is day 1.
- `chicks_received`: number of chicks placed.
- `chick_cost_per_unit` and `total_chick_cost`: used in financial summaries.
- Running totals: `current_stock`, `total_mortality`, `mortality_pct`, `total_feed_consumed_kg`, `fcr`, `last_recorded_weight_gms`, `total_birds_collected`, and `total_revenue`.

Important behavior:

- On validation, the app calculates `total_chick_cost`.
- If no title exists, it sets `crop_title` from farm name and crop number.
- The form adds lifecycle buttons:
  - `Activate Crop` when status is `Draft`.
  - `New Daily Record`, `New Feed Purchase`, and `Start Slaughter` when status is `Active`.
  - `New Collection Entry` and `Close Crop` when status is `Slaughter`.
  - `View P&L Summary` when status is `Closed`.
- Closing the crop generates or refreshes a `Crop Financial Summary`.

### Flock Daily Record

The daily operational record for one crop.

Main fields:

- `crop`: linked Poultry Crop.
- `date`: record date.
- `day_age`: bird age in days, calculated from crop placement date.
- `week_number`: calculated from day age.
- `opening_stock`, `mortality`, and `closing_stock`.
- `mortality_pct`.
- `feed_std_gms`, `feed_in_kg`, `std_total_kg`, and `feed_variance_kg`.
- `is_weigh_day`, `bwt_actual_gms`, `bwt_std_gms`, and `bwt_variance_gms`.
- `vaccination`, `vaccination_details`, `remarks`, and `alert_sent`.

Important behavior:

- Calculates day age from the crop placement date.
- Pulls opening stock from the previous day's closing stock. If there is no previous record, it uses crop current stock or chicks received.
- Pulls feed and body-weight standards from `Feed Standard Config`.
- Calculates closing stock as opening stock minus mortality.
- Calculates mortality percentage, week number, expected feed total, feed variance, and body-weight variance.
- After saving, updates the parent crop's current stock, total mortality, mortality percentage, total feed consumed, last recorded weight, and running FCR.
- Sends health warning emails to enabled users with the `Farm Director` role when configured thresholds are breached.

### Feed Purchase Entry

A submittable document for feed received for a crop.

Main fields:

- `crop`: linked Poultry Crop.
- `purchase_date`.
- `supplier`: stored as data in the current implementation.
- `warehouse`: populated from the linked crop.
- `feed_items`: child table of `Feed Purchase Item`.
- `total_bags`, `total_kgs`, `total_cost`.
- `stock_entry_reference`: ERPNext Stock Entry created on submit.

Important behavior:

- Calculates row totals and document totals.
- Uses the crop warehouse if the entry has no warehouse.
- On submit, creates and submits an ERPNext `Stock Entry` with type `Material Receipt`.
- On cancel, cancels the linked Stock Entry and clears the reference.

Feed type to stock item mapping:

| Feed Type | ERPNext Item Code |
| --- | --- |
| Pre-Starter | `FEED-PRESTARTER` |
| C1 Grower | `FEED-C1` |
| C2 Grower | `FEED-C2` |
| C3 Grower | `FEED-C3` |
| Finisher | `FEED-FINISHER` |

### Feed Purchase Item

Child table used inside Feed Purchase Entry.

Fields:

- `feed_type`: one of `Pre-Starter`, `C1 Grower`, `C2 Grower`, `C3 Grower`, or `Finisher`.
- `no_of_bags`.
- `pack_weight_kg`.
- `total_kgs`: calculated as bags times pack weight.
- `price_per_bag`.
- `total_cost`: calculated as bags times price per bag.

### Bird Collection Entry

A submittable document for recording birds collected during slaughter.

Main fields:

- `crop`: linked Poultry Crop.
- `collection_date`.
- `bird_age_days`: calculated from placement date.
- `collection_details`: child table of `Bird Collection Detail`.
- `total_birds`, `total_weight_kg`, `average_weight_kg`, `total_revenue`, and `revenue_per_bird`.

Important behavior:

- Calculates bird age from placement date.
- Calculates collection totals from the child rows.
- On submit or cancel, recalculates crop-level `total_birds_collected`, `total_revenue`, and FCR from submitted collection entries.

### Bird Collection Detail

Child table used inside Bird Collection Entry.

Fields:

- `weight_band`: `Below 1.6 KG`, `1.6 to 1.8 KG`, or `Above 1.8 KG`.
- `no_of_birds`.
- `average_weight_kg`.
- `price_per_kg`.
- `total_weight_kg`: calculated as birds times average weight.
- `total_amount`: calculated as total weight times price per kg.

### Crop Financial Summary

Read-mostly summary generated when a crop is closed.

Main fields:

- `crop` and `generated_date`.
- Cost fields: chick cost, feed cost by type, total feed cost, mortality loss value, other costs, cumulative cost.
- Revenue fields: total birds slaughtered and total revenue.
- Profitability fields: gross profit, net profit, profit margin, cost per bird, revenue per bird, feed cost per bird, and FCR.

Important behavior:

- Created or refreshed by `PoultryCrop.close_crop()`.
- Pulls feed cost from submitted Feed Purchase Entries.
- Pulls revenue and slaughtered birds from submitted Bird Collection Entries.
- Calculates mortality loss from total mortality times chick cost per unit.
- Calculates FCR from crop feed consumed divided by collected live weight.

### Feed Standard Config

A Single DocType that stores the production standards and alert thresholds.

Fields:

- `standards`: child table of `Feed Standard Row`.
- `mortality_alert_pct`: daily mortality warning threshold.
- `feed_drop_alert_pct`: feed intake drop threshold below standard.
- `bwt_deficit_alert_pct`: body-weight deficit threshold below standard.

Default standards loaded by the fixture:

| Days | Feed Type | Feed Std GMS/Bird | B.Wt Std GMS |
| --- | --- | ---: | ---: |
| 1-7 | Pre-Starter | 20 | 165 |
| 8-14 | C1 Grower | 47 | 420 |
| 15-21 | C2 Grower | 71 | 765 |
| 22-28 | C3 Grower | 115 | 1250 |
| 29-35 | C3 Grower | 152 | 1850 |
| 36-42 | Finisher | 175 | 2200 |

### Feed Standard Row

Child table used inside Feed Standard Config.

Fields:

- `day_from` and `day_to`.
- `feed_std_gms`.
- `bwt_std_gms`.
- `feed_type`.

## Operational Workflows

### 1. Creating and Activating a Crop

1. Open the Poultry workspace.
2. Create a new `Poultry Crop`.
3. Enter crop number, farm name, farm code, warehouse, placement date, chicks received, and chick cost per unit.
4. Save the crop.
5. Click `Activate Crop`.

After activation, daily records and feed purchases can be created from the crop form.

### 2. Daily Flock Recording

1. Open the active crop.
2. Click `New Daily Record`, or open the auto-created record for the day.
3. Confirm the date and day age.
4. Enter mortality.
5. Enter feed consumed in KG.
6. If it is a weigh day, check `Weigh Day?` and enter actual body weight.
7. Add vaccination information and remarks where relevant.
8. Save.

The system calculates stock, mortality percentage, feed variance, body-weight variance, and updates the parent crop.

### 3. Feed Purchase Recording

1. Open an active crop.
2. Click `New Feed Purchase`.
3. Enter purchase date and supplier.
4. Add feed item rows with feed type, number of bags, pack weight, and price per bag.
5. Save and submit.

On submit, the app creates a Material Receipt Stock Entry in ERPNext for the mapped feed items and crop warehouse.

### 4. Starting Slaughter

1. Open an active crop.
2. Click `Start Slaughter`.

The crop status changes from `Active` to `Slaughter`, and the actual slaughter date is set to today.

### 5. Bird Collection

1. Open the crop in `Slaughter` status.
2. Click `New Collection Entry`.
3. Enter collection date.
4. Add one row per weight band.
5. Enter number of birds, average weight, and price per kg.
6. Save and submit.

The system calculates total birds, total weight, average weight, total revenue, and revenue per bird. On submit it updates the crop's collected birds, revenue, and FCR.

### 6. Closing a Crop

1. Open the crop in `Slaughter` status.
2. Click `Close Crop`.

The crop status changes to `Closed`, and the app creates or updates the linked financial summary.

## Automation and Hooks

Registered in `poultry_farm/hooks.py`:

### Document Events

| DocType | Event | Handler |
| --- | --- | --- |
| Flock Daily Record | `after_save` | Updates crop stats and checks health alerts |
| Flock Daily Record | `on_submit` | Updates crop stats |
| Feed Purchase Entry | `on_submit` | Creates Material Receipt Stock Entry |
| Feed Purchase Entry | `on_cancel` | Cancels linked Stock Entry |
| Bird Collection Entry | `on_submit` | Updates collection totals and FCR |
| Bird Collection Entry | `on_cancel` | Recalculates collection totals and FCR |

### Scheduled Jobs

Daily:

- `poultry_farm.poultry.scheduled.create_daily_records`
- Creates tomorrow's `Flock Daily Record` for each active crop if it does not already exist.

Weekly:

- `poultry_farm.poultry.scheduled.send_weekly_summary`
- Emails enabled Farm Directors a summary of active and slaughter crops.

### After Migrate

After every migration:

- `poultry_farm.poultry.workspace_access.sync_workspace_roles`
- Syncs Poultry workspace roles and layout.
- Syncs report JSON, dashboard chart JSON, and number card JSON back into their Frappe documents.

## ERPNext Integration

The app depends on standard Frappe and ERPNext objects for stock and master data.

### Items and Item Groups

The fixture creates:

- Item Groups: `Poultry Feed`, `Live Birds`, `Veterinary Inputs`.
- Feed Items: `FEED-PRESTARTER`, `FEED-C1`, `FEED-C2`, `FEED-C3`, and `FEED-FINISHER`.
- UOMs: `KG`, `Bag`, `Bird`, and `Gram`.

### Warehouses

The fixture creates an `Anirita Farms` warehouse group and farm stores such as:

- `Belmonte Farm Store`
- `Paul Farm Store`

Each crop stores a warehouse value. Feed purchases receive stock into that warehouse.

### Stock Entry

When a Feed Purchase Entry is submitted, the app creates a submitted ERPNext Stock Entry:

- `stock_entry_type`: `Material Receipt`
- `posting_date`: feed purchase date
- `company`: resolved from the warehouse company, Global Defaults, or the first Company record
- one item row per feed item with quantity in KG and calculated basic rate

## Workspace, Dashboards, and Reports

The app includes a public `Poultry` workspace for:

- `System Manager`
- `Farm Manager`
- `Store Manager`
- `Farm Director`

Workspace components include:

- Number cards: open crops, live birds, closed crops, and revenue.
- Dashboard charts: crop statuses and daily feed intake.
- Shortcuts to operational DocTypes and key reports.
- Cards for operations, planning/setup, stock/masters, and reports.

### Reports

| Report | Purpose |
| --- | --- |
| Crop Daily Performance | Day-by-day flock record for a selected crop with weekly total rows |
| Weekly Mortality Report | Mortality grouped by crop and week |
| Feed Consumption Report | Actual feed, standard feed, variance KG, and variance percentage by crop/week |
| Crop Profit Loss | Revenue, cost, net profit, margin, per-bird metrics, FCR, and summary cards |
| Crop Performance Comparison | Compares crops by status, stock, mortality, feed consumed, FCR, average weight, revenue, and profit |

## Setup and Installation

Install the app in a Frappe bench:

```bash
cd /path/to/frappe-bench
bench get-app <repo-url> --branch develop
bench --site <site-name> install-app poultry_farm
bench --site <site-name> migrate
```

Load the app's required master data:

```bash
bench --site <site-name> execute poultry_farm.fixtures.load_fixtures.run
```

Optional demo data helpers are available in `poultry_farm/fixtures/load_fixtures.py`, including historical/demo crop creation functions. They are not run by default from `run()`.

## Roles and Access

The fixture creates these custom roles:

- `Farm Manager`
- `Store Manager`
- `Farm Director`

The workspace role sync grants the Poultry workspace to:

- `System Manager`
- `Farm Manager`
- `Store Manager`
- `Farm Director`

All other workspaces are restricted to `System Manager` by `sync_workspace_roles()`. This is useful for a dedicated poultry site, but it is important if this app is installed on a shared ERPNext site because it intentionally narrows workspace visibility.

Recommended role responsibilities:

| Role | Typical Responsibility |
| --- | --- |
| Farm Manager | Create and maintain crops, enter daily flock records, monitor mortality/feed/body-weight performance |
| Store Manager | Record feed purchases and manage feed receipts |
| Farm Director | Monitor health alerts, weekly summaries, crop performance, and profitability |
| System Manager | Configure users, roles, workspaces, fixtures, and ERPNext masters |

## Developer Notes

### Naming and Module

- App name: `poultry_farm`
- App title: `Poultry Farm`
- Module: `Poultry`
- Python target: `>=3.10`
- Formatting/linting config is in `pyproject.toml`.

### Important Calculations

Daily stock:

```text
closing_stock = opening_stock - mortality
mortality_pct = mortality / opening_stock * 100
week_number = ceil(day_age / 7)
std_total_kg = feed_std_gms * closing_stock / 1000
feed_variance_kg = feed_in_kg - std_total_kg
```

Body weight:

```text
bwt_variance_gms = bwt_actual_gms - bwt_std_gms
```

Feed purchase:

```text
row.total_kgs = no_of_bags * pack_weight_kg
row.total_cost = no_of_bags * price_per_bag
basic_rate = price_per_bag / pack_weight_kg
```

Bird collection:

```text
row.total_weight_kg = no_of_birds * average_weight_kg
row.total_amount = total_weight_kg * price_per_kg
average_weight_kg = total_weight_kg / total_birds
revenue_per_bird = total_revenue / total_birds
```

Financial summary:

```text
chick_cost = crop.total_chick_cost
total_feed_cost = sum(submitted Feed Purchase Item total_cost)
mortality_loss = crop.total_mortality * crop.chick_cost_per_unit
cumulative_cost = chick_cost + total_feed_cost + mortality_loss
gross_profit = total_revenue - chick_cost - total_feed_cost
net_profit = total_revenue - cumulative_cost
profit_margin_pct = net_profit / total_revenue * 100
cost_per_bird = cumulative_cost / total_birds_slaughtered
revenue_per_bird = total_revenue / total_birds_slaughtered
fcr = total_feed_consumed_kg / collected_live_weight_kg
```

### Useful Bench Commands

```bash
bench --site <site-name> migrate
bench --site <site-name> clear-cache
bench --site <site-name> execute poultry_farm.fixtures.load_fixtures.run
bench --site <site-name> execute poultry_farm.poultry.scheduled.create_daily_records
bench --site <site-name> execute poultry_farm.poultry.scheduled.send_weekly_summary
bench --site <site-name> execute poultry_farm.poultry.workspace_access.sync_workspace_roles
```

## Known Current Limitations

- `Bird Collection Entry` does not currently create an ERPNext Delivery Note. It only updates crop collection totals, revenue, and FCR.
- `Poultry Crop.warehouse`, `Feed Purchase Entry.warehouse`, supplier fields, farmer fields, and chick supplier fields are currently stored as `Data` in the live DocType JSON, even though some planning notes describe them as Link fields.
- `close_crop()` does not currently validate that all birds have been collected or that closing stock is zero before closure.
- `Crop Financial Summary.other_costs` exists as a field, but generated summary calculations do not currently add it into `cumulative_cost` or `net_profit`.
- `Crop Financial Summary.feed_cost_per_bird` exists as a field, but the current generator does not populate it.
- Flock Daily Record is not submittable in the current DocType JSON, although an `on_submit` hook is registered.
- The `patches.txt` file has no custom migration patches at the moment.

## Reference Files

Additional planning and build notes are stored in `files/`:

- `files/01_ARCHITECTURE.md`
- `files/02_DOCTYPES.md`
- `files/03_FIXTURES.md`
- `files/04_CLIENT_SCRIPTS.md`
- `files/05_SERVER_SCRIPTS.md`
- `files/06_REPORTS.md`
- `files/07_BUILD_ORDER.md`

Those files are useful historical design references. This README describes the app as implemented in the current codebase.

## License

MIT
