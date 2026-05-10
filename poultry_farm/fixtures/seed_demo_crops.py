"""
Demo data seeder — three complete broiler crop lifecycle examples.

Creates three crops (Draft → Active → Slaughter → Closed) with realistic
daily records, feed purchases, consumable sheets, labor, treatments,
bird collections, and financial summaries.

Run with:
    bench execute poultry_farm.fixtures.seed_demo_crops.seed
"""

import frappe
from frappe.utils import add_days, getdate

from poultry_farm.poultry.doctype.crop_vaccination_log.crop_vaccination_log import (
    create_vaccination_log,
)
from poultry_farm.poultry.doctype.poultry_crop.poultry_crop import generate_financial_summary


# ─── Crop definitions ────────────────────────────────────────────────────────

CROP_CONFIGS = [
    {
        # ── Kamiti Farm — Crop 34 ─────────────────────────────────────────
        # Good performance: low mortality, great FCR, heavy birds.
        "label":                 "Kamiti Farm — Crop 34",
        "farm_name":             "Kamiti Farm",
        "farm_code":             "KAMITI",
        "crop_number":           34,
        "placement_date":        "2026-01-05",
        "num_days":              41,
        "chicks_received":       5000,
        "birds_dead_on_arrival": 5,
        "chick_cost_per_unit":   120,
        "chick_supplier":        "Kenchic Limited",
        "scenario":              "good",
        "feed_purchases": [
            {"offset":  0, "feed_type": "Pre-Starter", "bags": 12, "price": 5400},
            {"offset":  7, "feed_type": "C1 Grower",   "bags": 30, "price": 5000},
            {"offset": 14, "feed_type": "C2 Grower",   "bags": 30, "price": 4800},
            {"offset": 21, "feed_type": "C3 Grower",   "bags": 30, "price": 4600},
            {"offset": 28, "feed_type": "Finisher",    "bags": 25, "price": 4400},
        ],
        # (item_name, unit_label, qty_purchased, unit_cost)
        "consumables": [
            ("Vacsure",        "litres", 5,  2500),
            ("Bimakleen",      "litres", 10, 1800),
            ("Farmguard",      "litres", 5,  2000),
            ("Glucose",        "kg",     3,  800),
            ("Vitastress",     "litres", 2,  1500),
            ("Chlorine",       "gms",    5,  600),
            ("Charcoal",       "bags",   2,  500),
            ("Woodshavings",   "bags",   50, 300),
            ("Rodenticide",    "gms",    1,  1200),
            ("Liquid Soap",    "litres", 5,  400),
        ],
        "treatments": [
            {
                "day_offset":     9,
                "symptoms":       "Mild respiratory distress in lower house. "
                                  "Approximately 60 birds gasping; feed uptake slightly reduced.",
                "birds_affected": 60,
                "products": [
                    ("Vitastress", 1.0, 1500),
                    ("Glucose",    0.5, 800),
                ],
                "outcome":        "Resolved",
                "administered_by":"Dr. Kamau Njoroge",
            },
        ],
        "labor": {
            "salaried": {"workers": 1, "days": 41, "rate": 2000, "activity": "General Farm Work"},
            "casual": [
                {"workers": 3, "days": 2, "rate": 600, "activity": "Loading"},
                {"workers": 4, "days": 2, "rate": 500, "activity": "Cleaning"},
            ],
        },
        # (day_offset, [{ band, birds, avg_kg, price_per_kg }])
        "collections": [
            (40, [
                {"band": "Below 1.6 KG",  "birds": 500,  "avg": 1.40, "price": 195},
                {"band": "1.6 to 1.8 KG", "birds": 1500, "avg": 1.70, "price": 215},
                {"band": "Above 1.8 KG",  "birds": 500,  "avg": 2.00, "price": 235},
            ]),
            (40, [
                {"band": "Below 1.6 KG",  "birds": 424,  "avg": 1.40, "price": 195},
                {"band": "1.6 to 1.8 KG", "birds": 1500, "avg": 1.70, "price": 215},
                {"band": "Above 1.8 KG",  "birds": 500,  "avg": 2.00, "price": 235},
            ]),
        ],
    },
    {
        # ── Ruiru Farm — Crop 12 ──────────────────────────────────────────
        # Disease outbreak in Week 2: high mortality spike, smaller birds,
        # two treatment entries, shorter cycle (38 days).
        "label":                 "Ruiru Farm — Crop 12",
        "farm_name":             "Ruiru Farm",
        "farm_code":             "RUIRU",
        "crop_number":           12,
        "placement_date":        "2026-02-02",
        "num_days":              38,
        "chicks_received":       4500,
        "birds_dead_on_arrival": 8,
        "chick_cost_per_unit":   125,
        "chick_supplier":        "Rainbow Chickens",
        "scenario":              "outbreak",
        "feed_purchases": [
            {"offset":  0, "feed_type": "Pre-Starter", "bags": 11, "price": 5400},
            {"offset":  7, "feed_type": "C1 Grower",   "bags": 25, "price": 5000},
            {"offset": 14, "feed_type": "C2 Grower",   "bags": 22, "price": 4800},
            {"offset": 21, "feed_type": "C3 Grower",   "bags": 20, "price": 4600},
        ],
        "consumables": [
            ("Vacsure",           "litres", 5,  2500),
            ("Enrocure",          "litres", 10, 3200),
            ("Bimakleen",         "litres", 15, 1800),
            ("Farmguard",         "litres", 8,  2000),
            ("Vitastress",        "litres", 5,  1500),
            ("Glucose",           "kg",     5,  800),
            ("Hydrogen Peroxide", "litres", 5,  1100),
            ("Charcoal",          "bags",   3,  500),
            ("Woodshavings",      "bags",   55, 300),
            ("Liquid Paraffin",   "mls",    3,  950),
        ],
        "treatments": [
            {
                "day_offset":       7,
                "symptoms":         "Rapid onset: severe respiratory distress, birds huddled at heat "
                                    "source, not eating. High overnight mortality. Suspected Newcastle "
                                    "or IBD challenge.",
                "birds_affected":   400,
                "products": [
                    ("Enrocure",   5.0, 3200),
                    ("Vitastress", 2.0, 1500),
                    ("Glucose",    2.0, 800),
                ],
                "outcome":          "Mortality Increase",
                "follow_up_required": 1,
                "follow_up_offset": 14,
                "administered_by":  "Dr. Faith Wanjiku",
            },
            {
                "day_offset":       14,
                "symptoms":         "Follow-up — mortality rate has declined but respiratory signs "
                                    "persist in ~10% of flock. Birds eating again.",
                "birds_affected":   150,
                "products": [
                    ("Enrocure",   3.0, 3200),
                    ("Vitastress", 1.5, 1500),
                ],
                "outcome":          "Recovering",
                "administered_by":  "Dr. Faith Wanjiku",
            },
        ],
        "labor": {
            "salaried": {"workers": 1, "days": 38, "rate": 2000, "activity": "General Farm Work"},
            "casual": [
                {"workers": 3, "days": 2, "rate": 600, "activity": "Loading"},
                {"workers": 4, "days": 2, "rate": 500, "activity": "Cleaning"},
            ],
        },
        "collections": [
            (37, [
                {"band": "Below 1.6 KG",  "birds": 850,  "avg": 1.35, "price": 190},
                {"band": "1.6 to 1.8 KG", "birds": 870,  "avg": 1.68, "price": 210},
                {"band": "Above 1.8 KG",  "birds": 430,  "avg": 1.90, "price": 230},
            ]),
            (37, [
                {"band": "Below 1.6 KG",  "birds": 803,  "avg": 1.35, "price": 190},
                {"band": "1.6 to 1.8 KG", "birds": 830,  "avg": 1.68, "price": 210},
                {"band": "Above 1.8 KG",  "birds": 470,  "avg": 1.90, "price": 230},
            ]),
        ],
    },
    {
        # ── Thika Farm — Crop 7 ───────────────────────────────────────────
        # Best performance: largest flock, lowest mortality rate, heaviest
        # birds, highest revenue per bird.
        "label":                 "Thika Farm — Crop 7",
        "farm_name":             "Thika Farm",
        "farm_code":             "THIKA",
        "crop_number":           7,
        "placement_date":        "2026-03-02",
        "num_days":              41,
        "chicks_received":       6000,
        "birds_dead_on_arrival": 10,
        "chick_cost_per_unit":   115,
        "chick_supplier":        "Kenchic Limited",
        "scenario":              "best",
        "feed_purchases": [
            {"offset":  0, "feed_type": "Pre-Starter", "bags": 15, "price": 5400},
            {"offset":  7, "feed_type": "C1 Grower",   "bags": 36, "price": 5000},
            {"offset": 14, "feed_type": "C2 Grower",   "bags": 36, "price": 4800},
            {"offset": 21, "feed_type": "C3 Grower",   "bags": 35, "price": 4600},
            {"offset": 28, "feed_type": "Finisher",    "bags": 30, "price": 4400},
        ],
        "consumables": [
            ("Vacsure",      "litres", 6,  2500),
            ("Bimakleen",    "litres", 12, 1800),
            ("Farmguard",    "litres", 6,  2000),
            ("Glucose",      "kg",     3,  800),
            ("Vitastress",   "litres", 3,  1500),
            ("Chlorine",     "gms",    6,  600),
            ("Charcoal",     "bags",   3,  500),
            ("Woodshavings", "bags",   65, 300),
            ("Insecticide",  "litres", 2,  1500),
            ("Liquid Soap",  "litres", 6,  400),
        ],
        "treatments": [
            {
                "day_offset":     11,
                "symptoms":       "Loose droppings in one house section. Around 50 birds mildly "
                                  "lethargic, likely water quality issue.",
                "birds_affected": 50,
                "products": [
                    ("Glucose",    1.0, 800),
                    ("Vitastress", 0.5, 1500),
                ],
                "outcome":        "Resolved",
                "administered_by":"James Mwangi",
            },
        ],
        "labor": {
            "salaried": {"workers": 1, "days": 41, "rate": 2200, "activity": "General Farm Work"},
            "casual": [
                {"workers": 4, "days": 2, "rate": 600, "activity": "Loading"},
                {"workers": 5, "days": 2, "rate": 500, "activity": "Cleaning"},
            ],
        },
        "collections": [
            (40, [
                {"band": "Below 1.6 KG",  "birds": 300,  "avg": 1.42, "price": 200},
                {"band": "1.6 to 1.8 KG", "birds": 1200, "avg": 1.72, "price": 220},
                {"band": "Above 1.8 KG",  "birds": 1500, "avg": 2.10, "price": 240},
            ]),
            (40, [
                {"band": "Below 1.6 KG",  "birds": 292,  "avg": 1.42, "price": 200},
                {"band": "1.6 to 1.8 KG", "birds": 1170, "avg": 1.72, "price": 220},
                {"band": "Above 1.8 KG",  "birds": 1460, "avg": 2.10, "price": 240},
            ]),
        ],
    },
]


# ─── Mortality patterns ───────────────────────────────────────────────────────

def _daily_mortality(day, scenario):
    if scenario == "good":
        if day <= 3:  return 8
        if day <= 7:  return 3
        if day <= 14: return 2
        if day <= 28: return 1
        return 0 if day % 2 == 0 else 1

    if scenario == "outbreak":
        if day <= 3:  return 8
        if day <= 7:  return 4
        if day <= 13: return 22   # outbreak peak (Days 8–13)
        if day <= 15: return 10   # declining
        if day <= 23: return 4
        return 1

    # best
    if day <= 3:  return 8
    if day <= 7:  return 3
    if day <= 14: return 2
    if day <= 28: return 1
    return 0 if day % 3 != 0 else 1


# ─── Feed intake (grams / bird / day) ────────────────────────────────────────

def _feed_gms(day):
    if day <= 3:  return 13 + day * 2
    if day <= 7:  return 19 + (day - 3) * 3
    if day <= 14: return 31 + (day - 7)  * 4
    if day <= 21: return 59 + (day - 14) * 6
    if day <= 28: return 101 + (day - 21) * 6
    if day <= 35: return 143 + (day - 28) * 5
    return 178 + (day - 35) * 3


# ─── Body weight on weigh days (grams) ───────────────────────────────────────

_BWT_STD = {7: 180, 14: 470, 21: 900, 28: 1400, 35: 1900}
_SCENARIO_BWt_MULT = {"good": 1.00, "best": 1.04, "outbreak": 0.88}

def _body_weight(day, scenario):
    base = _BWT_STD.get(day)
    if not base:
        return None
    return round(base * _SCENARIO_BWt_MULT.get(scenario, 1.0))


# ─── Warehouse helper ────────────────────────────────────────────────────────

def _get_default_warehouse():
    """Return the name of any non-group warehouse available in the system."""
    # Prefer a store-type warehouse
    for keyword in ["Store", "Stores", "Warehouse", "Feed"]:
        wh = frappe.db.get_value(
            "Warehouse",
            {"is_group": 0, "name": ["like", f"%{keyword}%"]},
            "name",
        )
        if wh:
            return wh
    # Fall back to the first non-group warehouse found
    return frappe.db.get_value("Warehouse", {"is_group": 0}, "name")


# ─── Entry point ─────────────────────────────────────────────────────────────

def seed():
    frappe.set_user("Administrator")

    print("\n── Poultry Farm Demo Seeder ─────────────────────────────────────")
    _ensure_fixtures()

    created = []
    for c in CROP_CONFIGS:
        name = _seed_crop(c)
        if name:
            created.append(name)

    frappe.db.commit()

    print("\n─────────────────────────────────────────────────────────────────")
    if created:
        print(f"✅  Seeded {len(created)} crop(s):")
        for n in created:
            print(f"    • {n}")
    else:
        print("⚠   No new crops were seeded (all already exist).")
    print()


# ─── Fixtures guard ───────────────────────────────────────────────────────────

def _ensure_fixtures():
    from poultry_farm.fixtures.load_fixtures import (
        create_consumable_items,
        create_vaccination_schedule_template,
    )
    print("  Ensuring master data …")
    create_consumable_items()
    create_vaccination_schedule_template()
    frappe.db.commit()


# ─── Partial crop cleanup ────────────────────────────────────────────────────

def _cleanup_partial_crop(crop_name):
    """Delete a partially seeded crop and all its linked child records."""
    # Cancel + delete submitted child docs first
    for doctype in [
        "Feed Purchase Entry",
        "Crop Consumable Sheet",
        "Crop Labor Entry",
        "Crop Treatment Entry",
        "Bird Collection Entry",
    ]:
        for name in frappe.get_all(doctype, filters={"crop": crop_name}, pluck="name"):
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)

    # Delete non-submittable linked records
    for doctype in ["Flock Daily Record", "Crop Vaccination Log", "Crop Financial Summary"]:
        for name in frappe.get_all(doctype, filters={"crop": crop_name}, pluck="name"):
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)

    frappe.delete_doc("Poultry Crop", crop_name, ignore_permissions=True, force=True)
    frappe.db.commit()
    print(f"     Cleaned up {crop_name}")


# ─── Crop lifecycle ───────────────────────────────────────────────────────────

def _seed_crop(c):
    existing = frappe.db.get_value(
        "Poultry Crop",
        {"farm_code": c["farm_code"], "placement_date": c["placement_date"]},
        ["name", "status"],
        as_dict=True,
    )
    if existing:
        if existing.status == "Closed":
            print(f"\n  → {c['label']} already closed ({existing.name}), skipping.")
            return None
        print(f"\n  → Removing incomplete crop {existing.name} (status: {existing.status}) …")
        _cleanup_partial_crop(existing.name)

    warehouse = _get_default_warehouse()
    if not warehouse:
        frappe.throw("No warehouse found. Please create one in ERPNext before seeding.")

    print(f"\n  ┌─ {c['label']}")
    print(f"  │  Warehouse:             {warehouse}")

    placement_date = getdate(c["placement_date"])
    slaughter_date = add_days(placement_date, c["num_days"] - 1)

    # 1 ── Create crop (Draft) ─────────────────────────────────────────────
    crop = frappe.new_doc("Poultry Crop")
    crop.farm_name             = c["farm_name"]
    crop.farm_code             = c["farm_code"]
    crop.crop_number           = c["crop_number"]
    crop.placement_date        = placement_date
    crop.chicks_received       = c["chicks_received"]
    crop.birds_dead_on_arrival = c["birds_dead_on_arrival"]
    crop.chick_cost_per_unit   = c["chick_cost_per_unit"]
    crop.chick_supplier        = c["chick_supplier"]
    crop.warehouse             = warehouse
    crop.status                = "Draft"
    crop.save(ignore_permissions=True)
    crop_name = crop.name
    print(f"  │  Created (Draft):       {crop_name}")

    # 2 ── Activate → auto-create Vaccination Log ──────────────────────────
    crop.status = "Active"
    crop.save(ignore_permissions=True)
    create_vaccination_log(crop_name)
    print(f"  │  Activated + VAC log")

    # 3 ── Daily records ───────────────────────────────────────────────────
    _create_daily_records(
        crop_name, placement_date,
        c["num_days"],
        c["chicks_received"] - c["birds_dead_on_arrival"],
        c["scenario"],
    )
    print(f"  │  Daily records:         {c['num_days']} days")

    # 4 ── Feed purchases ──────────────────────────────────────────────────
    for fp in c["feed_purchases"]:
        _create_feed_purchase(crop_name, placement_date, fp)
    print(f"  │  Feed purchases:        {len(c['feed_purchases'])} entries")

    # 5 ── Consumable sheet ────────────────────────────────────────────────
    _create_consumable_sheet(crop_name, placement_date, c["consumables"])
    print(f"  │  Consumable sheet:      {len(c['consumables'])} items")

    # 6 ── Labor entry ─────────────────────────────────────────────────────
    _create_labor_entry(crop_name, slaughter_date, c["labor"])
    print(f"  │  Labor entry:           submitted")

    # 7 ── Treatment entries ───────────────────────────────────────────────
    for t in c.get("treatments", []):
        _create_treatment_entry(crop_name, placement_date, t)
    print(f"  │  Treatment entries:     {len(c.get('treatments', []))}")

    # 8 ── Move to Slaughter ───────────────────────────────────────────────
    crop.reload()
    crop.status = "Slaughter"
    crop.actual_slaughter_date = slaughter_date
    crop.save(ignore_permissions=True)
    print(f"  │  Status → Slaughter     ({slaughter_date})")

    # 9 ── Bird collection ─────────────────────────────────────────────────
    for (offset, details) in c["collections"]:
        _create_collection_entry(crop_name, placement_date, offset, details)
    print(f"  │  Collections:           {len(c['collections'])} batches")

    # 10 ── Close + Financial Summary ──────────────────────────────────────
    crop.reload()
    crop.status = "Closed"
    crop.save(ignore_permissions=True)
    generate_financial_summary(crop_name)
    print(f"  └─ Closed + CFS generated")

    frappe.db.commit()
    return crop_name


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _create_daily_records(crop_name, placement_date, num_days, opening_stock, scenario):
    current_stock = opening_stock
    for day in range(1, num_days + 1):
        mortality = min(_daily_mortality(day, scenario), current_stock)
        closing   = current_stock - mortality
        avg_stock = (current_stock + closing) / 2
        feed_in   = round(_feed_gms(day) * avg_stock / 1000, 2)

        rec = frappe.new_doc("Flock Daily Record")
        rec.crop          = crop_name
        rec.date          = add_days(placement_date, day - 1)
        rec.day_age       = day
        rec.opening_stock = current_stock
        rec.mortality     = mortality
        rec.feed_in_kg    = feed_in
        rec.alert_sent    = 1   # suppress email alerts during seeding

        if day % 7 == 0:
            bwt = _body_weight(day, scenario)
            if bwt:
                rec.is_weigh_day   = 1
                rec.bwt_actual_gms = bwt

        rec.save(ignore_permissions=True)
        current_stock = closing


def _create_feed_purchase(crop_name, placement_date, fp):
    entry = frappe.new_doc("Feed Purchase Entry")
    entry.crop          = crop_name
    entry.purchase_date = add_days(placement_date, fp["offset"])
    entry.supplier      = "General Feed Supplier"
    entry.append("feed_items", {
        "feed_type":      fp["feed_type"],
        "no_of_bags":     fp["bags"],
        "pack_weight_kg": 50,
        "price_per_bag":  fp["price"],
    })
    entry.save(ignore_permissions=True)
    entry.submit()


def _create_consumable_sheet(crop_name, placement_date, consumables):
    sheet = frappe.new_doc("Crop Consumable Sheet")
    sheet.crop          = crop_name
    sheet.date_prepared = add_days(placement_date, 2)
    for (item_name, unit, qty, unit_cost) in consumables:
        item_id = frappe.db.get_value("Consumable Item", {"item_name": item_name}, "name")
        if not item_id:
            print(f"  │  ⚠ Consumable item not found: {item_name}")
            continue
        sheet.append("items", {
            "item":          item_id,
            "unit":          unit,
            "qty_purchased": qty,
            "unit_cost":     unit_cost,
            "qty_used":      round(qty * 0.85, 1),
        })
    sheet.save(ignore_permissions=True)
    sheet.submit()


def _create_labor_entry(crop_name, entry_date, labor_def):
    entry = frappe.new_doc("Crop Labor Entry")
    entry.crop       = crop_name
    entry.entry_date = entry_date

    sal = labor_def["salaried"]
    entry.append("labor_items", {
        "labor_type":   "Salaried",
        "activity":     sal["activity"],
        "description":  "Farm Manager",
        "num_workers":  sal["workers"],
        "num_days":     sal["days"],
        "rate_per_day": sal["rate"],
    })
    for row in labor_def.get("casual", []):
        entry.append("labor_items", {
            "labor_type":   "Casual",
            "activity":     row["activity"],
            "num_workers":  row["workers"],
            "num_days":     row["days"],
            "rate_per_day": row["rate"],
        })
    entry.save(ignore_permissions=True)
    entry.submit()


def _create_treatment_entry(crop_name, placement_date, t):
    te = frappe.new_doc("Crop Treatment Entry")
    te.crop             = crop_name
    te.treatment_date   = add_days(placement_date, t["day_offset"])
    te.symptoms         = t["symptoms"]
    te.birds_affected   = t.get("birds_affected", 0)
    te.outcome          = t.get("outcome", "")
    te.administered_by  = t.get("administered_by", "")
    if t.get("follow_up_required"):
        te.follow_up_required = 1
        te.follow_up_date = add_days(placement_date, t["follow_up_offset"])
    for (product_name, qty, unit_cost) in t.get("products", []):
        item_id = frappe.db.get_value("Consumable Item", {"item_name": product_name}, "name")
        te.append("treatment_items", {
            "product":       item_id or product_name,
            "route":         "Drinking Water",
            "quantity_used": qty,
            "unit_cost":     unit_cost,
            "duration_days": 3,
        })
    te.save(ignore_permissions=True)
    te.submit()


def _create_collection_entry(crop_name, placement_date, day_offset, details):
    entry = frappe.new_doc("Bird Collection Entry")
    entry.crop            = crop_name
    entry.collection_date = add_days(placement_date, day_offset)
    for d in details:
        entry.append("collection_details", {
            "weight_band":       d["band"],
            "no_of_birds":       d["birds"],
            "average_weight_kg": d["avg"],
            "price_per_kg":      d["price"],
        })
    entry.save(ignore_permissions=True)
    entry.submit()
