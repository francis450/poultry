# CLAUDE.md — Anirita Poultry Farm ERPNext Custom App

## Project Overview

You are implementing a **Poultry Farm Management module** inside a Frappe/ERPNext custom app
for **Anirita Poultry Farm Ltd, Nairobi**. The goal is to digitise paper-based crop (batch)
records currently managed on printed contract-farmer forms.

The site and custom app are already created and installed. Your job is to build all
doctypes, fixtures, scripts, and reports exactly as specified in the companion files.

---

## App Context

| Item | Value |
|------|-------|
| App name | `anirita_poultry` *(confirm with `bench list-apps`)* |
| Module name | `Poultry` |
| ERPNext modules in use | Stock, Buying, Accounts, Projects |
| Primary language | Python 3 / Frappe v15 conventions |
| Database | MariaDB (use `frappe.db.*` APIs, never raw SQL in hooks) |

---

## Companion Files — Read in This Order

| # | File | Purpose |
|---|------|---------|
| 1 | `01_ARCHITECTURE.md` | System design, module map, data flow |
| 2 | `02_DOCTYPES.md` | Every doctype, every field, every option |
| 3 | `03_FIXTURES.md` | Seed data: item groups, items, warehouses, UOMs |
| 4 | `04_CLIENT_SCRIPTS.md` | All JavaScript client scripts per doctype |
| 5 | `05_SERVER_SCRIPTS.md` | All Python server scripts, hooks, and scheduled jobs |
| 6 | `06_REPORTS.md` | All custom report definitions and queries |
| 7 | `07_BUILD_ORDER.md` | Exact step-by-step implementation sequence |

---

## Core Rules

1. **Never skip `07_BUILD_ORDER.md`** — it defines the safe dependency order.
2. All doctypes go in the `Poultry` module folder inside the app.
3. Use `frappe.model.set_value` on the client, never direct DOM manipulation.
4. All monetary fields use `Currency` fieldtype with `options: KES`.
5. All weight fields use `Float` with a `description` noting the unit (grams or kg).
6. Every doctype must have `naming_rule: Expression` configured as specified.
7. After creating each doctype via JSON, run `bench migrate` before writing scripts.
8. Fixtures must be loaded via `bench execute` helper scripts, not manually.
9. Server scripts that send alerts use `frappe.sendmail` — never `smtplib` directly.
10. All reports are `Script Report` type using Python + Jinja where specified.

---

## Directory Structure to Create

```
apps/anirita_poultry/anirita_poultry/
├── __init__.py
├── hooks.py                          ← update as instructed
├── poultry/                          ← module folder
│   ├── __init__.py
│   ├── doctype/
│   │   ├── poultry_crop/
│   │   ├── flock_daily_record/
│   │   ├── feed_purchase_entry/
│   │   ├── feed_purchase_item/       ← child table
│   │   ├── bird_collection_entry/
│   │   ├── bird_collection_detail/   ← child table
│   │   └── crop_financial_summary/
│   └── report/
│       ├── crop_performance_report/
│       ├── weekly_mortality_report/
│       ├── feed_consumption_report/
│       └── crop_profit_loss/
└── fixtures/
    └── load_fixtures.py
```

---

## Quick Bench Commands Reference

```bash
# After any doctype JSON change
bench --site [site-name] migrate

# Clear cache after script changes
bench --site [site-name] clear-cache

# Load fixtures
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.run

# Tail logs during testing
tail -f logs/web.log

# Restart after hooks.py changes
bench restart
```

---

## Business Logic Summary (memorise this)

- One **Poultry Crop** = one batch of chicks, one farm, one grow-out cycle (~39 days)
- Each day of the crop has one **Flock Daily Record** (mortality, feed, weight)
- Feed purchased goes into **Feed Purchase Entry** which creates a Stock Entry (Material Receipt)
- Daily feed consumption creates a **Stock Entry (Material Issue)** from the farm warehouse
- When birds are collected for slaughter, a **Bird Collection Entry** is created
- The **Crop Financial Summary** auto-calculates P&L when the crop is marked `Closed`
- Weekly roll-ups (1st–6th Week) are computed fields, not stored rows

---

## Crop Status Flow

```
Draft → Active → Slaughter → Closed
```

- `Draft`: crop created, chicks not yet received
- `Active`: chicks received, daily records being logged
- `Slaughter`: collection entries being recorded
- `Closed`: all birds collected, P&L finalised, read-only
