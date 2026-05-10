import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Crop", "fieldname": "crop", "fieldtype": "Link", "options": "Poultry Crop", "width": 180},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 140},
		{"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 180},
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 130},
		{"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 70},
		{"label": "Brought Forward", "fieldname": "qty_brought_forward", "fieldtype": "Float", "width": 120},
		{"label": "Purchased", "fieldname": "qty_purchased", "fieldtype": "Float", "width": 100},
		{"label": "Used", "fieldname": "qty_used", "fieldtype": "Float", "width": 80},
		{"label": "Balance", "fieldname": "qty_balance", "fieldtype": "Float", "width": 90},
		{"label": "Next Crop", "fieldname": "qty_expected_next_crop", "fieldtype": "Float", "width": 100},
		{"label": "Purchase Cost (KES)", "fieldname": "total_purchase_cost", "fieldtype": "Currency", "options": "KES", "width": 140},
	]


def get_data(filters):
	conditions = ["ccs.docstatus = 1"]
	values = {}

	if filters.get("crop"):
		conditions.append("ccs.crop = %(crop)s")
		values["crop"] = filters["crop"]

	if filters.get("category"):
		conditions.append("ci.category = %(category)s")
		values["category"] = filters["category"]

	if filters.get("from_date"):
		conditions.append("ccs.date_prepared >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("ccs.date_prepared <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = "WHERE " + " AND ".join(conditions)

	return frappe.db.sql(f"""
		SELECT
			ccs.crop,
			pc.farm_name,
			ci.item_name AS item,
			ci.category,
			csi.unit,
			csi.qty_brought_forward,
			csi.qty_purchased,
			csi.qty_used,
			csi.qty_balance,
			csi.qty_expected_next_crop,
			csi.total_purchase_cost
		FROM `tabConsumable Sheet Item` csi
		JOIN `tabCrop Consumable Sheet` ccs ON ccs.name = csi.parent
		JOIN `tabPoultry Crop` pc ON pc.name = ccs.crop
		LEFT JOIN `tabConsumable Item` ci ON ci.name = csi.item
		{where}
		ORDER BY ccs.crop, ci.category, ci.item_name
	""", values, as_dict=True)
