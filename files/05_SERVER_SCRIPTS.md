# 05_SERVER_SCRIPTS.md — Python Server Scripts, Hooks & Scheduled Jobs

---

## hooks.py Updates

Add the following to your app's `hooks.py`. Do NOT replace existing content — append only.

```python
# anirita_poultry/hooks.py (additions)

doc_events = {
    "Flock Daily Record": {
        "on_submit": "anirita_poultry.poultry.doctype.flock_daily_record.flock_daily_record.on_submit",
        "after_save": "anirita_poultry.poultry.doctype.flock_daily_record.flock_daily_record.after_save",
    },
    "Feed Purchase Entry": {
        "on_submit":  "anirita_poultry.poultry.doctype.feed_purchase_entry.feed_purchase_entry.on_submit",
        "on_cancel":  "anirita_poultry.poultry.doctype.feed_purchase_entry.feed_purchase_entry.on_cancel",
    },
    "Bird Collection Entry": {
        "on_submit":  "anirita_poultry.poultry.doctype.bird_collection_entry.bird_collection_entry.on_submit",
        "on_cancel":  "anirita_poultry.poultry.doctype.bird_collection_entry.bird_collection_entry.on_cancel",
    },
}

scheduler_events = {
    "daily": [
        "anirita_poultry.poultry.scheduled.create_daily_records",
    ],
    "weekly": [
        "anirita_poultry.poultry.scheduled.send_weekly_summary",
    ]
}
```

---

## Flock Daily Record Controller

**File:** `poultry/doctype/flock_daily_record/flock_daily_record.py`

```python
import frappe
from frappe.model.document import Document


class FlockDailyRecord(Document):

    def validate(self):
        self.calculate_stock()
        self.calculate_week_number()
        self.calculate_feed_variance()
        self.calculate_bwt_variance()

    def calculate_stock(self):
        self.closing_stock = (self.opening_stock or 0) - (self.mortality or 0)
        if self.opening_stock:
            self.mortality_pct = round(
                ((self.mortality or 0) / self.opening_stock) * 100, 2
            )

    def calculate_week_number(self):
        if self.day_age:
            import math
            self.week_number = math.ceil(self.day_age / 7)

    def calculate_feed_variance(self):
        if self.feed_std_gms and self.closing_stock:
            self.std_total_kg = round(
                (self.feed_std_gms * self.closing_stock) / 1000, 3
            )
        self.feed_variance_kg = round(
            (self.feed_in_kg or 0) - (self.std_total_kg or 0), 3
        )

    def calculate_bwt_variance(self):
        if self.is_weigh_day and self.bwt_actual_gms:
            self.bwt_variance_gms = (self.bwt_actual_gms or 0) - (self.bwt_std_gms or 0)


def after_save(doc, method):
    """Update Poultry Crop live stats after each daily record is saved."""
    update_crop_stats(doc.crop)
    check_mortality_alert(doc)


def on_submit(doc, method):
    update_crop_stats(doc.crop)


def update_crop_stats(crop_name):
    """Recalculate and update the parent Poultry Crop's aggregated stats."""
    crop = frappe.get_doc("Poultry Crop", crop_name)

    # Latest closing stock and weight
    latest = frappe.db.sql("""
        SELECT closing_stock, bwt_actual_gms, day_age
        FROM `tabFlock Daily Record`
        WHERE crop = %s
        ORDER BY day_age DESC
        LIMIT 1
    """, crop_name, as_dict=True)

    if latest:
        crop.current_stock          = latest[0].closing_stock
        crop.last_recorded_weight_gms = latest[0].bwt_actual_gms or crop.last_recorded_weight_gms

    # Total mortality
    result = frappe.db.sql("""
        SELECT SUM(mortality) as total_mortality, SUM(feed_in_kg) as total_feed
        FROM `tabFlock Daily Record`
        WHERE crop = %s
    """, crop_name, as_dict=True)

    if result:
        crop.total_mortality        = result[0].total_mortality or 0
        crop.total_feed_consumed_kg = round(result[0].total_feed or 0, 2)
        if crop.chicks_received:
            crop.mortality_pct = round(
                (crop.total_mortality / crop.chicks_received) * 100, 2
            )

    crop.save(ignore_permissions=True)


def check_mortality_alert(doc):
    """Send email alert to Farm Director if daily mortality > 1%."""
    if (doc.mortality_pct or 0) > 1.0 and not doc.alert_sent:
        directors = frappe.get_all(
            "Has Role",
            filters={"role": "Farm Director", "parenttype": "User"},
            fields=["parent"]
        )
        recipients = [d.parent for d in directors if frappe.db.get_value("User", d.parent, "enabled")]

        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=f"⚠️ High Mortality Alert — {doc.crop} Day {doc.day_age}",
                message=f"""
                    <p>High mortality recorded on <b>{doc.crop}</b>:</p>
                    <ul>
                        <li>Date: {doc.date}</li>
                        <li>Day Age: {doc.day_age}</li>
                        <li>Mortality: {doc.mortality} birds ({doc.mortality_pct}%)</li>
                        <li>Closing Stock: {doc.closing_stock}</li>
                    </ul>
                    <p>Please investigate immediately.</p>
                """
            )
        frappe.db.set_value("Flock Daily Record", doc.name, "alert_sent", 1)


@frappe.whitelist()
def get_standards_for_day(day_age):
    """Return feed and body weight standards for a given day age."""
    day_age = int(day_age)
    config  = frappe.get_doc("Feed Standard Config")
    for row in config.standards:
        if row.day_from <= day_age <= row.day_to:
            return {
                "feed_std_gms": row.feed_std_gms,
                "bwt_std_gms":  row.bwt_std_gms,
                "feed_type":    row.feed_type,
            }
    return None


@frappe.whitelist()
def get_previous_closing_stock(crop, day_age):
    """Return closing stock of the previous day's record."""
    prev = frappe.db.sql("""
        SELECT closing_stock
        FROM `tabFlock Daily Record`
        WHERE crop = %s AND day_age = %s
        LIMIT 1
    """, (crop, int(day_age) - 1), as_dict=True)
    return prev[0].closing_stock if prev else None
```

---

## Poultry Crop Controller

**File:** `poultry/doctype/poultry_crop/poultry_crop.py`

```python
import frappe
from frappe.model.document import Document


class PoultryCrop(Document):

    def validate(self):
        self.total_chick_cost = (self.chicks_received or 0) * (self.chick_cost_per_unit or 0)
        if not self.crop_title:
            self.crop_title = f"{self.farm_name} — Crop {self.crop_number}"

    @frappe.whitelist()
    def activate_crop(self):
        if self.status != "Draft":
            frappe.throw("Only Draft crops can be activated.")
        self.status = "Active"
        self.save()
        frappe.msgprint(f"Crop {self.name} is now Active. Start logging daily records.", alert=True)

    @frappe.whitelist()
    def start_slaughter(self):
        if self.status != "Active":
            frappe.throw("Crop must be Active to begin Slaughter.")
        self.status = "Slaughter"
        import datetime
        self.actual_slaughter_date = datetime.date.today()
        self.save()
        frappe.msgprint("Crop moved to Slaughter. Create Bird Collection Entries.", alert=True)

    @frappe.whitelist()
    def close_crop(self):
        if self.status != "Slaughter":
            frappe.throw("Crop must be in Slaughter status to Close.")
        self.status = "Closed"
        self.save()
        generate_financial_summary(self.name)
        frappe.msgprint("Crop Closed. Financial Summary generated.", alert=True)


def generate_financial_summary(crop_name):
    """Auto-generate or refresh the Crop Financial Summary."""
    crop = frappe.get_doc("Poultry Crop", crop_name)

    # Feed costs by type
    feed_costs = frappe.db.sql("""
        SELECT fpi.feed_type, SUM(fpi.total_cost) as cost
        FROM `tabFeed Purchase Item` fpi
        JOIN `tabFeed Purchase Entry` fpe ON fpe.name = fpi.parent
        WHERE fpe.crop = %s AND fpe.docstatus = 1
        GROUP BY fpi.feed_type
    """, crop_name, as_dict=True)

    cost_map = {r.feed_type: r.cost for r in feed_costs}
    total_feed_cost = sum(cost_map.values())

    # Revenue from bird collections
    revenue_data = frappe.db.sql("""
        SELECT SUM(total_birds) as birds, SUM(total_revenue) as revenue
        FROM `tabBird Collection Entry`
        WHERE crop = %s AND docstatus = 1
    """, crop_name, as_dict=True)

    total_birds_slaughtered = revenue_data[0].birds     if revenue_data else 0
    total_revenue           = revenue_data[0].revenue   if revenue_data else 0

    chick_cost        = crop.total_chick_cost or 0
    mortality_loss    = (crop.total_mortality or 0) * (crop.chick_cost_per_unit or 0)
    cumulative_cost   = chick_cost + total_feed_cost + mortality_loss
    gross_profit      = total_revenue - chick_cost - total_feed_cost
    net_profit        = total_revenue - cumulative_cost
    profit_margin_pct = round((net_profit / total_revenue * 100), 2) if total_revenue else 0
    cost_per_bird     = round(cumulative_cost / total_birds_slaughtered, 2) if total_birds_slaughtered else 0
    revenue_per_bird  = round(total_revenue   / total_birds_slaughtered, 2) if total_birds_slaughtered else 0

    # FCR
    total_live_weight_kg = frappe.db.sql("""
        SELECT SUM(total_weight_kg) FROM `tabBird Collection Detail` bcd
        JOIN `tabBird Collection Entry` bce ON bce.name = bcd.parent
        WHERE bce.crop = %s AND bce.docstatus = 1
    """, crop_name)[0][0] or 0

    fcr = round(
        (crop.total_feed_consumed_kg or 0) / total_live_weight_kg, 3
    ) if total_live_weight_kg else 0

    # Upsert summary
    existing = frappe.db.exists("Crop Financial Summary", {"crop": crop_name})
    if existing:
        summary = frappe.get_doc("Crop Financial Summary", existing)
    else:
        summary = frappe.new_doc("Crop Financial Summary")
        summary.crop = crop_name

    import datetime
    summary.generated_date          = datetime.date.today()
    summary.chick_cost              = chick_cost
    summary.feed_cost_prestarter    = cost_map.get("FEED-PRESTARTER", 0)
    summary.feed_cost_c1            = cost_map.get("FEED-C1", 0)
    summary.feed_cost_c2            = cost_map.get("FEED-C2", 0)
    summary.feed_cost_c3            = cost_map.get("FEED-C3", 0)
    summary.feed_cost_finisher      = cost_map.get("FEED-FINISHER", 0)
    summary.total_feed_cost         = total_feed_cost
    summary.total_mortality_birds   = crop.total_mortality or 0
    summary.mortality_loss_value    = mortality_loss
    summary.cumulative_cost         = cumulative_cost
    summary.total_birds_slaughtered = total_birds_slaughtered
    summary.total_revenue           = total_revenue
    summary.gross_profit            = gross_profit
    summary.net_profit              = net_profit
    summary.profit_margin_pct       = profit_margin_pct
    summary.cost_per_bird           = cost_per_bird
    summary.revenue_per_bird        = revenue_per_bird
    summary.fcr                     = fcr

    summary.save(ignore_permissions=True)
    frappe.msgprint(f"Financial Summary {summary.name} created/updated.", alert=True)
```

---

## Feed Purchase Entry Controller

**File:** `poultry/doctype/feed_purchase_entry/feed_purchase_entry.py`

```python
import frappe
from frappe.model.document import Document


class FeedPurchaseEntry(Document):

    def validate(self):
        self.calculate_totals()
        self.fetch_warehouse_from_crop()

    def calculate_totals(self):
        total_bags = total_kgs = total_cost = 0
        for row in self.feed_items:
            row.total_kgs  = (row.no_of_bags or 0) * (row.pack_weight_kg or 0)
            row.total_cost = (row.no_of_bags or 0) * (row.price_per_bag  or 0)
            total_bags    += row.no_of_bags or 0
            total_kgs     += row.total_kgs
            total_cost    += row.total_cost
        self.total_bags = total_bags
        self.total_kgs  = total_kgs
        self.total_cost = total_cost

    def fetch_warehouse_from_crop(self):
        if self.crop and not self.warehouse:
            self.warehouse = frappe.db.get_value("Poultry Crop", self.crop, "warehouse")


def on_submit(doc, method):
    """Create a Stock Entry (Material Receipt) for all feed items purchased."""
    company = frappe.db.get_single_value("Global Defaults", "default_company")

    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Receipt"
    se.company          = company
    se.posting_date     = doc.purchase_date
    se.remarks          = f"Feed purchase for crop {doc.crop} — {doc.name}"

    for row in doc.feed_items:
        if row.total_kgs:
            se.append("items", {
                "item_code":        row.feed_type,
                "qty":              row.total_kgs,
                "uom":              "KG",
                "t_warehouse":      doc.warehouse,
                "basic_rate":       (row.price_per_bag or 0) / (row.pack_weight_kg or 1),
                "conversion_factor": 1,
            })

    se.insert(ignore_permissions=True)
    se.submit()

    frappe.db.set_value("Feed Purchase Entry", doc.name, "stock_entry_reference", se.name)
    frappe.msgprint(f"Stock Entry {se.name} created for feed receipt.", alert=True)


def on_cancel(doc, method):
    """Cancel the linked Stock Entry when Feed Purchase Entry is cancelled."""
    if doc.stock_entry_reference:
        se = frappe.get_doc("Stock Entry", doc.stock_entry_reference)
        if se.docstatus == 1:
            se.cancel()
            frappe.msgprint(f"Stock Entry {se.name} cancelled.", alert=True)
```

---

## Bird Collection Entry Controller

**File:** `poultry/doctype/bird_collection_entry/bird_collection_entry.py`

```python
import frappe
from frappe.model.document import Document


class BirdCollectionEntry(Document):

    def validate(self):
        self.calculate_summary()
        self.calculate_bird_age()

    def calculate_summary(self):
        total_birds = total_weight = total_revenue = 0
        for row in self.collection_details:
            row.total_weight_kg = (row.no_of_birds or 0) * (row.average_weight_kg or 0)
            row.total_amount    = row.total_weight_kg * (row.price_per_kg or 0)
            total_birds   += row.no_of_birds or 0
            total_weight  += row.total_weight_kg
            total_revenue += row.total_amount

        self.total_birds    = total_birds
        self.total_weight_kg = round(total_weight, 2)
        self.total_revenue   = round(total_revenue, 2)
        self.average_weight_kg  = round(total_weight / total_birds, 3) if total_birds else 0
        self.revenue_per_bird   = round(total_revenue / total_birds, 2) if total_birds else 0

    def calculate_bird_age(self):
        if self.crop and self.collection_date:
            placement = frappe.db.get_value("Poultry Crop", self.crop, "placement_date")
            if placement:
                from frappe.utils import date_diff
                self.bird_age_days = date_diff(self.collection_date, placement) + 1


def on_submit(doc, method):
    """Update crop's total birds collected and revenue."""
    crop = frappe.get_doc("Poultry Crop", doc.crop)

    all_collections = frappe.db.sql("""
        SELECT SUM(total_birds) as birds, SUM(total_revenue) as revenue
        FROM `tabBird Collection Entry`
        WHERE crop = %s AND docstatus = 1
    """, doc.crop, as_dict=True)

    if all_collections:
        crop.total_birds_collected = all_collections[0].birds    or 0
        crop.total_revenue         = all_collections[0].revenue  or 0
        crop.save(ignore_permissions=True)


def on_cancel(doc, method):
    on_submit(doc, method)  # Recalculate on cancel (values will decrease)
```

---

## Scheduled Jobs

**File:** `poultry/scheduled.py`

```python
import frappe


def create_daily_records():
    """
    Runs every night at midnight.
    Creates a Flock Daily Record for each Active crop for tomorrow's date.
    Farm manager just opens and fills in mortality/feed — no need to create from scratch.
    """
    import datetime
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    active_crops = frappe.get_all(
        "Poultry Crop",
        filters={"status": "Active"},
        fields=["name", "placement_date", "current_stock", "chicks_received"]
    )

    for crop in active_crops:
        placement = frappe.utils.getdate(crop.placement_date)
        day_age   = (tomorrow - placement).days + 1

        # Skip if record already exists for this day
        existing = frappe.db.exists("Flock Daily Record", {
            "crop": crop.name, "day_age": day_age
        })
        if existing:
            continue

        # Get previous closing stock
        prev = frappe.db.sql("""
            SELECT closing_stock FROM `tabFlock Daily Record`
            WHERE crop = %s ORDER BY day_age DESC LIMIT 1
        """, crop.name, as_dict=True)

        opening = prev[0].closing_stock if prev else (crop.current_stock or crop.chicks_received)

        doc = frappe.new_doc("Flock Daily Record")
        doc.crop          = crop.name
        doc.date          = tomorrow
        doc.day_age       = day_age
        doc.opening_stock = opening
        doc.mortality     = 0
        doc.insert(ignore_permissions=True)

    frappe.db.commit()


def send_weekly_summary():
    """
    Runs every Monday. Emails Farm Director a summary of all active crops.
    """
    active_crops = frappe.get_all(
        "Poultry Crop",
        filters={"status": ["in", ["Active", "Slaughter"]]},
        fields=["name", "farm_name", "crop_number", "current_stock",
                "total_mortality", "mortality_pct", "total_feed_consumed_kg"]
    )

    if not active_crops:
        return

    rows = "".join([
        f"<tr><td>{c.farm_name}</td><td>{c.crop_number}</td>"
        f"<td>{c.current_stock}</td><td>{c.total_mortality}</td>"
        f"<td>{c.mortality_pct}%</td><td>{c.total_feed_consumed_kg} KG</td></tr>"
        for c in active_crops
    ])

    table = f"""
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Farm</th><th>Crop</th><th>Current Stock</th>
            <th>Total Mortality</th><th>Mortality %</th><th>Feed Consumed</th>
        </tr>
        {rows}
    </table>
    """

    directors = frappe.get_all(
        "Has Role",
        filters={"role": "Farm Director", "parenttype": "User"},
        fields=["parent"]
    )
    recipients = [d.parent for d in directors]

    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject="📊 Weekly Poultry Farm Summary — Anirita",
            message=f"<p>Weekly summary of active crops:</p>{table}"
        )
```
