import frappe
from frappe.model.document import Document


class CropConsumableSheet(Document):

	def before_insert(self):
		self._fetch_warehouse()
		if not self.items:
			self._populate_from_catalogue()

	def validate(self):
		self._fetch_warehouse()
		self.calculate_totals()

	def _fetch_warehouse(self):
		if self.crop and not self.warehouse:
			self.warehouse = frappe.db.get_value("Poultry Crop", self.crop, "warehouse")

	def calculate_totals(self):
		total_cost = 0
		for row in self.items:
			row.qty_in_store = (row.qty_brought_forward or 0) + (row.qty_purchased or 0)
			row.qty_balance = row.qty_in_store - (row.qty_used or 0)
			row.total_purchase_cost = (row.qty_purchased or 0) * (row.unit_cost or 0)
			total_cost += row.total_purchase_cost
		self.total_cost = total_cost

	def _populate_from_catalogue(self):
		"""Insert one row per Consumable Item with Brought Forward from warehouse or previous sheet."""
		carryover = _get_brought_forward(self.crop, self.warehouse)
		for ci in _catalogue_items():
			row = self.append("items", {})
			row.item = ci.name
			row.unit = ci.default_unit or ""
			row.qty_brought_forward = carryover.get(ci.name, 0)
		self.calculate_totals()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _catalogue_items():
	return frappe.get_all(
		"Consumable Item",
		fields=["name", "default_unit", "item_code"],
		order_by="category asc, item_name asc",
	)


def _get_brought_forward(crop_name, warehouse):
	"""
	Return {consumable_item_name: qty} for Brought Forward.
	Priority:
	  1. Live warehouse bin balance (if warehouse set and item has item_code)
	  2. Previous submitted sheet Expected Next Crop for the same farm (fallback)
	"""
	items = _catalogue_items()

	# Build item_code → consumable item name map for items that have a stock mapping
	mapped = {ci.item_code: ci.name for ci in items if ci.item_code}

	result = {}

	if warehouse and mapped:
		# Read actual bin balances for all mapped items in one query
		placeholders = ", ".join(["%s"] * len(mapped))
		bins = frappe.db.sql(
			f"""
			SELECT item_code, actual_qty
			FROM `tabBin`
			WHERE item_code IN ({placeholders})
			  AND warehouse = %s
			""",
			list(mapped.keys()) + [warehouse],
			as_dict=True,
		)
		for b in bins:
			consumable_name = mapped[b.item_code]
			result[consumable_name] = b.actual_qty or 0

	# For items without a warehouse mapping, fall back to previous sheet carryover
	unmapped_items = {ci.name for ci in items if ci.name not in result}
	if unmapped_items:
		fallback = _previous_sheet_carryover(crop_name)
		for name in unmapped_items:
			result[name] = fallback.get(name, 0)

	return result


def _previous_sheet_carryover(crop_name):
	"""Return {item: qty_expected_next_crop} from the most recent submitted sheet for the same farm."""
	farm_name = frappe.db.get_value("Poultry Crop", crop_name, "farm_name")
	if not farm_name:
		return {}

	prev = frappe.db.sql("""
		SELECT css.name
		FROM `tabCrop Consumable Sheet` css
		JOIN `tabPoultry Crop` pc ON pc.name = css.crop
		WHERE pc.farm_name = %(farm)s
		  AND css.crop != %(crop)s
		  AND css.docstatus = 1
		ORDER BY css.modified DESC
		LIMIT 1
	""", {"farm": farm_name, "crop": crop_name}, as_dict=True)

	if not prev:
		return {}

	rows = frappe.db.sql("""
		SELECT item, qty_expected_next_crop
		FROM `tabConsumable Sheet Item`
		WHERE parent = %(sheet)s
	""", {"sheet": prev[0].name}, as_dict=True)

	return {r.item: (r.qty_expected_next_crop or 0) for r in rows}


# ---------------------------------------------------------------------------
# Whitelisted API — called from JS
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_catalogue_with_carryover(crop):
	"""Return all catalogue items with Brought Forward for a new sheet."""
	warehouse = frappe.db.get_value("Poultry Crop", crop, "warehouse")
	carryover = _get_brought_forward(crop, warehouse)
	return [
		{
			"item": ci.name,
			"unit": ci.default_unit or "",
			"qty_brought_forward": carryover.get(ci.name, 0),
		}
		for ci in _catalogue_items()
	]


@frappe.whitelist()
def get_missing_catalogue_items(crop, existing_items):
	"""Return catalogue items not yet in the sheet — used by the Refresh button."""
	import json
	existing = set(json.loads(existing_items) if isinstance(existing_items, str) else existing_items)
	warehouse = frappe.db.get_value("Poultry Crop", crop, "warehouse")
	carryover = _get_brought_forward(crop, warehouse)
	return [
		{
			"item": ci.name,
			"unit": ci.default_unit or "",
			"qty_brought_forward": carryover.get(ci.name, 0),
		}
		for ci in _catalogue_items()
		if ci.name not in existing
	]


# ---------------------------------------------------------------------------
# Doc event hooks (registered in hooks.py)
# ---------------------------------------------------------------------------

def on_submit(doc, method):
	_create_stock_entries(doc)
	_refresh_cfs_consumable_costs(doc.crop)


def on_cancel(doc, method):
	_cancel_stock_entries(doc)
	_refresh_cfs_consumable_costs(doc.crop)


def _create_stock_entries(doc):
	"""Create Material Receipt (purchases) and Material Issue (usage) against the warehouse."""
	if not doc.warehouse:
		return

	company = frappe.db.get_value("Warehouse", doc.warehouse, "company")
	if not company:
		return

	receipt_ref = _make_stock_entry(
		entry_type="Material Receipt",
		company=company,
		posting_date=doc.date_prepared,
		remarks=f"Consumable purchases for crop {doc.crop} — {doc.name}",
		rows=[
			{"item_code": row.item_code, "qty": row.qty_purchased, "t_warehouse": doc.warehouse, "basic_rate": row.unit_cost or 0}
			for row in doc.items
			if (row.item_code and (row.qty_purchased or 0) > 0)
		],
	)

	issue_ref = _make_stock_entry(
		entry_type="Material Issue",
		company=company,
		posting_date=doc.date_prepared,
		remarks=f"Consumable usage for crop {doc.crop} — {doc.name}",
		rows=[
			{"item_code": row.item_code, "qty": row.qty_used, "s_warehouse": doc.warehouse}
			for row in doc.items
			if (row.item_code and (row.qty_used or 0) > 0)
		],
	)

	updates = {}
	if receipt_ref:
		updates["stock_entry_receipt"] = receipt_ref
		frappe.msgprint(f"Material Receipt {receipt_ref} created for consumable purchases.", alert=True)
	if issue_ref:
		updates["stock_entry_issue"] = issue_ref
		frappe.msgprint(f"Material Issue {issue_ref} created for consumable usage.", alert=True)
	if not receipt_ref and not issue_ref:
		frappe.msgprint(
			"No stock entries created — map Consumable Items to ERPNext Item Codes to enable warehouse tracking.",
			alert=True,
		)

	if updates:
		frappe.db.set_value("Crop Consumable Sheet", doc.name, updates)


def _make_stock_entry(entry_type, company, posting_date, remarks, rows):
	"""Create and submit a Stock Entry. Returns the name or None if rows is empty."""
	if not rows:
		return None

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = entry_type
	se.company = company
	se.posting_date = posting_date
	se.remarks = remarks

	for r in rows:
		se.append("items", {"conversion_factor": 1, "uom": "Nos", "stock_uom": "Nos", **r})

	se.insert(ignore_permissions=True)
	se.submit()
	return se.name


def _cancel_stock_entries(doc):
	"""Cancel both stock entries if they exist and are submitted."""
	for field in ("stock_entry_receipt", "stock_entry_issue"):
		ref = doc.get(field)
		if ref and frappe.db.exists("Stock Entry", ref):
			se = frappe.get_doc("Stock Entry", ref)
			if se.docstatus == 1:
				se.cancel()
				frappe.msgprint(f"Stock Entry {ref} cancelled.", alert=True)
	frappe.db.set_value("Crop Consumable Sheet", doc.name, {
		"stock_entry_receipt": "",
		"stock_entry_issue": "",
	})


def _refresh_cfs_consumable_costs(crop_name):
	cfs = frappe.db.exists("Crop Financial Summary", {"crop": crop_name})
	if not cfs:
		return

	rows = frappe.db.sql("""
		SELECT ci.category, COALESCE(SUM(csi.total_purchase_cost), 0) AS cost
		FROM `tabConsumable Sheet Item` csi
		JOIN `tabCrop Consumable Sheet` ccs ON ccs.name = csi.parent
		JOIN `tabConsumable Item` ci ON ci.name = csi.item
		WHERE ccs.crop = %s AND ccs.docstatus = 1
		GROUP BY ci.category
	""", crop_name, as_dict=True)

	cat_map = {r.category: (r.cost or 0) for r in rows}

	frappe.db.set_value("Crop Financial Summary", cfs, {
		"vet_cost":              cat_map.get("Veterinary", 0),
		"biosecurity_cost":      cat_map.get("Biosecurity", 0) + cat_map.get("Water Treatment", 0),
		"fuel_heating_cost":     cat_map.get("Fuel & Heating", 0),
		"other_consumable_cost": (
			cat_map.get("Bedding", 0)
			+ cat_map.get("Cleaning", 0)
			+ cat_map.get("Miscellaneous", 0)
		),
		"consumable_cost": sum(cat_map.values()),
	})
