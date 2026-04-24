# 03_FIXTURES.md — Seed Data & Fixtures

Run all fixture functions via:
```bash
bench --site [site-name] execute anirita_poultry.fixtures.load_fixtures.run
```

---

## Fixture File: `anirita_poultry/fixtures/load_fixtures.py`

Create this file exactly as written below. Each section is a function called by `run()`.

```python
import frappe

def run():
    create_item_groups()
    create_uoms()
    create_feed_items()
    create_warehouse_group()
    create_roles()
    create_feed_standards()
    frappe.db.commit()
    print("✅ Anirita Poultry fixtures loaded successfully.")


# ─── 1. ITEM GROUPS ─────────────────────────────────────────────────────────

def create_item_groups():
    groups = [
        {"item_group_name": "Poultry Feed",     "parent_item_group": "All Item Groups"},
        {"item_group_name": "Live Birds",        "parent_item_group": "All Item Groups"},
        {"item_group_name": "Veterinary Inputs", "parent_item_group": "All Item Groups"},
    ]
    for g in groups:
        if not frappe.db.exists("Item Group", g["item_group_name"]):
            doc = frappe.get_doc({"doctype": "Item Group", **g})
            doc.insert(ignore_permissions=True)
            print(f"  Created Item Group: {g['item_group_name']}")


# ─── 2. UOMs ────────────────────────────────────────────────────────────────

def create_uoms():
    uoms = ["KG", "Bag", "Bird", "Gram"]
    for uom in uoms:
        if not frappe.db.exists("UOM", uom):
            frappe.get_doc({"doctype": "UOM", "uom_name": uom}).insert(ignore_permissions=True)
            print(f"  Created UOM: {uom}")


# ─── 3. FEED ITEMS ──────────────────────────────────────────────────────────

def create_feed_items():
    """
    These map exactly to the feed types seen on the paper forms:
    Pre-Starter (PBS), C1 Grower, C2 Grower, C3 Grower, Finisher Pellets
    """
    items = [
        {
            "item_code": "FEED-PRESTARTER",
            "item_name": "Pre-Starter Feed (PBS)",
            "item_group": "Poultry Feed",
            "stock_uom": "KG",
            "is_stock_item": 1,
            "description": "Pre-starter broiler feed. Used Days 1-7."
        },
        {
            "item_code": "FEED-C1",
            "item_name": "C1 Grower Feed",
            "item_group": "Poultry Feed",
            "stock_uom": "KG",
            "is_stock_item": 1,
            "description": "C1 Grower broiler feed. Used Days 8-14."
        },
        {
            "item_code": "FEED-C2",
            "item_name": "C2 Grower Feed",
            "item_group": "Poultry Feed",
            "stock_uom": "KG",
            "is_stock_item": 1,
            "description": "C2 Grower broiler feed. Used Days 15-21."
        },
        {
            "item_code": "FEED-C3",
            "item_name": "C3 Grower Feed",
            "item_group": "Poultry Feed",
            "stock_uom": "KG",
            "is_stock_item": 1,
            "description": "C3 Grower broiler feed. Used Days 22-35."
        },
        {
            "item_code": "FEED-FINISHER",
            "item_name": "Finisher Pellets",
            "item_group": "Poultry Feed",
            "stock_uom": "KG",
            "is_stock_item": 1,
            "description": "Finisher pellets. Used Days 35+ / Slaughter week."
        },
    ]
    for item_data in items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            doc = frappe.get_doc({"doctype": "Item", **item_data})
            doc.insert(ignore_permissions=True)
            print(f"  Created Item: {item_data['item_code']}")


# ─── 4. WAREHOUSE GROUP ─────────────────────────────────────────────────────

def create_warehouse_group():
    """
    Creates the parent warehouse group for all Anirita farms.
    Individual farm warehouses are created manually in ERPNext UI
    under this group, or via additional fixture entries below.
    """
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        print("  ⚠️  No default company set. Skipping warehouse group creation.")
        return

    group_name = f"Anirita Farms - {company}"
    if not frappe.db.exists("Warehouse", group_name):
        frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": "Anirita Farms",
            "is_group": 1,
            "company": company,
        }).insert(ignore_permissions=True)
        print(f"  Created Warehouse Group: {group_name}")

    # Create the first farm warehouse
    farm_warehouses = [
        "Belmonte Farm Store",
        "Paul Farm Store",
    ]
    parent_wh = frappe.db.get_value(
        "Warehouse", {"warehouse_name": "Anirita Farms", "is_group": 1}, "name"
    )
    for wh_name in farm_warehouses:
        full_name = f"{wh_name} - {company}"
        if not frappe.db.exists("Warehouse", full_name):
            frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": wh_name,
                "is_group": 0,
                "parent_warehouse": parent_wh,
                "company": company,
            }).insert(ignore_permissions=True)
            print(f"  Created Warehouse: {full_name}")


# ─── 5. ROLES ───────────────────────────────────────────────────────────────

def create_roles():
    roles = ["Farm Manager", "Store Manager", "Farm Director"]
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)
            print(f"  Created Role: {role_name}")


# ─── 6. FEED STANDARDS ──────────────────────────────────────────────────────

def create_feed_standards():
    """
    Populates the Feed Standard Config single doctype with the
    age-to-feed-standard mapping derived from the paper forms.
    """
    standards = [
        # day_from, day_to, feed_std_gms, bwt_std_gms, feed_type_item_code
        (1,  7,  20,  165,  "FEED-PRESTARTER"),
        (8,  14, 47,  420,  "FEED-C1"),
        (15, 21, 71,  765,  "FEED-C2"),
        (22, 28, 115, 1250, "FEED-C3"),
        (29, 35, 152, 1850, "FEED-C3"),
        (36, 42, 175, 2200, "FEED-FINISHER"),
    ]

    config = frappe.get_doc("Feed Standard Config")
    config.standards = []
    for row in standards:
        config.append("standards", {
            "day_from":     row[0],
            "day_to":       row[1],
            "feed_std_gms": row[2],
            "bwt_std_gms":  row[3],
            "feed_type":    row[4],
        })
    config.save(ignore_permissions=True)
    print("  Feed Standard Config populated.")
```

---

## Supplier Fixtures (Run Separately or Add to `run()`)

```python
def create_suppliers():
    suppliers = [
        {
            "supplier_name": "Kenchic Limited",
            "supplier_group": "Local",
            "supplier_type": "Company",
            "country": "Kenya",
        },
        {
            "supplier_name": "Anirita Feeds Division",
            "supplier_group": "Local",
            "supplier_type": "Company",
            "country": "Kenya",
        },
    ]
    for s in suppliers:
        if not frappe.db.exists("Supplier", s["supplier_name"]):
            frappe.get_doc({"doctype": "Supplier", **s}).insert(ignore_permissions=True)
            print(f"  Created Supplier: {s['supplier_name']}")
```

---

## First Crop Fixture (Historical Data — Crop 14)

Use this to bootstrap Crop 14 data from the paper forms.
Run **after** all doctypes are created and migrated.

```python
def create_crop_14():
    """
    Creates Crop 14 (Paul Farm Belmonte) as a Closed historical record.
    Chicks received: 5858, Placement date: 17/02/2023
    """
    if frappe.db.exists("Poultry Crop", {"crop_number": 14, "farm_code": "PAUL"}):
        print("  Crop 14 already exists. Skipping.")
        return

    company = frappe.db.get_single_value("Global Defaults", "default_company")

    crop = frappe.get_doc({
        "doctype": "Poultry Crop",
        "crop_number": 14,
        "farm_name": "Paul Farm Belmonte",
        "farm_code": "PAUL",
        "status": "Closed",
        "placement_date": "2023-02-17",
        "chicks_received": 5858,
        "chick_cost_per_unit": 75,
        "total_chick_cost": 435000,
        "warehouse": f"Paul Farm Store - {company}",
        "total_mortality": 99,
        "total_birds_collected": 5740,
        "remarks": "Historical crop migrated from paper records."
    })
    crop.insert(ignore_permissions=True)
    print(f"  Created Crop 14: {crop.name}")
```
