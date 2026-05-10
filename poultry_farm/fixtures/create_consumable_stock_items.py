"""
Creates ERPNext Items for every Consumable Item and links them back.

Safe to re-run — skips items that are already linked.

Run once after bench migrate:
    bench --site mysite.local execute poultry_farm.fixtures.create_consumable_stock_items.create
"""

import re
import frappe

# ---------------------------------------------------------------------------
# UOM mapping — Consumable Item default_unit → ERPNext UOM name
# ---------------------------------------------------------------------------

UOM_MAP = {
    "lts":     "Litre",
    "litre":   "Litre",
    "litres":  "Litre",
    "liter":   "Litre",
    "liters":  "Litre",
    "l":       "Litre",
    "gms":     "Gram",
    "gm":      "Gram",
    "g":       "Gram",
    "gram":    "Gram",
    "grams":   "Gram",
    "kgs":     "Kg",
    "kg":      "Kg",
    "kilo":    "Kg",
    "kilos":   "Kg",
    "mls":     "Ml",
    "ml":      "Ml",
    "millilitre": "Ml",
    "milliliter": "Ml",
}


def _resolve_uom(default_unit):
    """Map free-text unit to an ERPNext UOM name. Defaults to Nos."""
    if not default_unit:
        return "Nos"
    return UOM_MAP.get(default_unit.strip().lower(), "Nos")


def _to_item_code(item_name):
    """Convert item name to a clean ERPNext item code: CONS-LIQUID-PARAFFIN."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", item_name.strip()).upper().strip("-")
    return f"CONS-{slug}"


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def _ensure_uom(uom_name):
    if not frappe.db.exists("UOM", uom_name):
        doc = frappe.new_doc("UOM")
        doc.uom_name = uom_name
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  [uom created]        {uom_name}")


def _ensure_item_group(name, parent="Consumable"):
    if not frappe.db.exists("Item Group", name):
        doc = frappe.new_doc("Item Group")
        doc.item_group_name = name
        doc.parent_item_group = parent
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  [item group created] {name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CATEGORY_GROUP_MAP = {
    "Veterinary":    "Farm Consumables - Veterinary",
    "Biosecurity":   "Farm Consumables - Biosecurity",
    "Water Treatment": "Farm Consumables - Water Treatment",
    "Fuel & Heating": "Farm Consumables - Fuel & Heating",
    "Bedding":       "Farm Consumables - Bedding",
    "Cleaning":      "Farm Consumables - Cleaning",
    "Miscellaneous": "Farm Consumables - Miscellaneous",
}


def create():
    """Create ERPNext Items for all Consumable Items and link them back. Idempotent."""

    # 1. Ensure UOMs
    for uom in ("Ml",):
        _ensure_uom(uom)

    # 2. Ensure item groups
    _ensure_item_group("Farm Consumables", parent="Consumable")
    for group_name in CATEGORY_GROUP_MAP.values():
        _ensure_item_group(group_name, parent="Farm Consumables")

    # 3. Fetch all consumable items
    consumables = frappe.get_all(
        "Consumable Item",
        fields=["name", "item_name", "category", "default_unit", "item_code"],
    )

    created = skipped = linked = 0

    for ci in consumables:
        if ci.item_code:
            # Already linked — nothing to do
            skipped += 1
            continue

        item_code = _to_item_code(ci.item_name)
        uom = _resolve_uom(ci.default_unit)
        item_group = CATEGORY_GROUP_MAP.get(ci.category, "Farm Consumables")

        if frappe.db.exists("Item", item_code):
            # ERPNext item already exists (e.g. from a previous partial run) — just link
            print(f"  [item exists]        {item_code}  →  {ci.item_name}")
            linked += 1
        else:
            # Create the ERPNext Item
            item = frappe.new_doc("Item")
            item.item_code      = item_code
            item.item_name      = ci.item_name
            item.item_group     = item_group
            item.stock_uom      = uom
            item.is_stock_item  = 1
            item.include_item_in_manufacturing = 0
            item.description    = f"{ci.category} — {ci.item_name}"
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"  [item created]       {item_code}  ({uom})  →  {ci.item_name}")
            created += 1

        # Link back to the Consumable Item master
        frappe.db.set_value("Consumable Item", ci.name, "item_code", item_code)
        frappe.db.commit()

    print(f"\nDone.  Created: {created}  Already existed: {linked}  Already linked: {skipped}")
    print("Run 'bench --site <site> clear-cache' after this script.")
