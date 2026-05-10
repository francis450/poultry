import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = [
		{"label": "Crop",               "fieldname": "crop",              "fieldtype": "Link",     "options": "Poultry Crop", "width": 200},
		{"label": "Farm",               "fieldname": "farm_name",         "fieldtype": "Data",     "width": 140},
		{"label": "Status",             "fieldname": "status",            "fieldtype": "Data",     "width": 90},
		{"label": "Pre-Starter (KG)",   "fieldname": "qty_prestarter",    "fieldtype": "Float",    "width": 130},
		{"label": "C1 Grower (KG)",     "fieldname": "qty_c1",            "fieldtype": "Float",    "width": 120},
		{"label": "C2 Grower (KG)",     "fieldname": "qty_c2",            "fieldtype": "Float",    "width": 120},
		{"label": "C3 Grower (KG)",     "fieldname": "qty_c3",            "fieldtype": "Float",    "width": 120},
		{"label": "Finisher (KG)",      "fieldname": "qty_finisher",      "fieldtype": "Float",    "width": 120},
		{"label": "Total Purchased (KG)","fieldname": "total_purchased_kg","fieldtype": "Float",   "width": 150},
		{"label": "Total Consumed (KG)","fieldname": "total_consumed_kg", "fieldtype": "Float",    "width": 150},
		{"label": "Variance (KG)",      "fieldname": "variance_kg",       "fieldtype": "Float",    "width": 120},
		{"label": "Total Feed Cost (KES)","fieldname":"total_feed_cost",  "fieldtype": "Currency", "width": 160},
		{"label": "Cost / KG (KES)",    "fieldname": "cost_per_kg",       "fieldtype": "Currency", "width": 130},
	]

	clauses = ["fpe.docstatus = 1"]
	query_filters = {}

	if filters.crop:
		clauses.append("fpe.crop = %(crop)s")
		query_filters["crop"] = filters.crop

	if filters.status:
		clauses.append("pc.status = %(status)s")
		query_filters["status"] = filters.status

	if filters.from_date:
		clauses.append("fpe.purchase_date >= %(from_date)s")
		query_filters["from_date"] = filters.from_date

	if filters.to_date:
		clauses.append("fpe.purchase_date <= %(to_date)s")
		query_filters["to_date"] = filters.to_date

	where = "WHERE " + " AND ".join(clauses)

	# Feed purchased per type per crop
	purchased = frappe.db.sql(
		f"""
		SELECT
			fpe.crop,
			pc.farm_name,
			pc.status,
			SUM(CASE WHEN fpi.feed_type = 'Pre-Starter' THEN fpi.total_kgs ELSE 0 END) AS qty_prestarter,
			SUM(CASE WHEN fpi.feed_type = 'C1 Grower'   THEN fpi.total_kgs ELSE 0 END) AS qty_c1,
			SUM(CASE WHEN fpi.feed_type = 'C2 Grower'   THEN fpi.total_kgs ELSE 0 END) AS qty_c2,
			SUM(CASE WHEN fpi.feed_type = 'C3 Grower'   THEN fpi.total_kgs ELSE 0 END) AS qty_c3,
			SUM(CASE WHEN fpi.feed_type = 'Finisher'    THEN fpi.total_kgs ELSE 0 END) AS qty_finisher,
			SUM(fpi.total_kgs)  AS total_purchased_kg,
			SUM(fpi.total_cost) AS total_feed_cost
		FROM `tabFeed Purchase Item` fpi
		JOIN `tabFeed Purchase Entry` fpe ON fpe.name = fpi.parent
		JOIN `tabPoultry Crop` pc ON pc.name = fpe.crop
		{where}
		GROUP BY fpe.crop, pc.farm_name, pc.status
		ORDER BY pc.placement_date DESC
		""",
		query_filters,
		as_dict=True,
	)

	# Total feed consumed (distributed to birds) per crop from daily records
	consumed_raw = frappe.db.sql(
		"""
		SELECT crop, SUM(feed_in_kg) AS total_consumed_kg
		FROM `tabFlock Daily Record`
		GROUP BY crop
		""",
		as_dict=True,
	)
	consumed_map = {r.crop: (r.total_consumed_kg or 0) for r in consumed_raw}

	data = []
	for row in purchased:
		consumed = consumed_map.get(row.crop, 0)
		purchased_kg = row.total_purchased_kg or 0
		cost = row.total_feed_cost or 0
		row["total_consumed_kg"] = round(consumed, 2)
		row["variance_kg"] = round(purchased_kg - consumed, 2)
		row["cost_per_kg"] = round(cost / purchased_kg, 2) if purchased_kg else 0
		data.append(row)

	summary = _build_summary(data)
	return columns, data, None, None, summary


def _build_summary(data):
	if not data:
		return []

	total_purchased = sum(r.total_purchased_kg or 0 for r in data)
	total_consumed  = sum(r.total_consumed_kg  or 0 for r in data)
	total_cost      = sum(r.total_feed_cost    or 0 for r in data)
	avg_cost_per_kg = round(total_cost / total_purchased, 2) if total_purchased else 0

	return [
		{"label": "Total Purchased (KG)", "value": round(total_purchased, 2), "datatype": "Float",    "indicator": "blue"},
		{"label": "Total Consumed (KG)",  "value": round(total_consumed,  2), "datatype": "Float",    "indicator": "blue"},
		{"label": "Total Feed Cost",      "value": total_cost,                "datatype": "Currency", "currency": "KES", "indicator": "orange"},
		{"label": "Avg Cost / KG",        "value": avg_cost_per_kg,           "datatype": "Currency", "currency": "KES", "indicator": "green"},
	]
