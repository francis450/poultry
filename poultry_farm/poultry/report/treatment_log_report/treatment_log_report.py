import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = [
		{"label": "Entry",           "fieldname": "name",            "fieldtype": "Link",     "options": "Crop Treatment Entry", "width": 160},
		{"label": "Crop",            "fieldname": "crop",            "fieldtype": "Link",     "options": "Poultry Crop",         "width": 180},
		{"label": "Farm",            "fieldname": "farm_name",       "fieldtype": "Data",     "width": 140},
		{"label": "Date",            "fieldname": "treatment_date",  "fieldtype": "Date",     "width": 100},
		{"label": "Bird Age (Days)", "fieldname": "day_age",         "fieldtype": "Int",      "width": 110},
		{"label": "Symptoms",        "fieldname": "symptoms",        "fieldtype": "Data",     "width": 220},
		{"label": "Birds Affected",  "fieldname": "birds_affected",  "fieldtype": "Int",      "width": 120},
		{"label": "Products Used",   "fieldname": "products",        "fieldtype": "Data",     "width": 240},
		{"label": "Treatment Cost (KES)", "fieldname": "treatment_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Outcome",         "fieldname": "outcome",         "fieldtype": "Data",     "width": 130},
		{"label": "Follow-up Date",  "fieldname": "follow_up_date",  "fieldtype": "Date",     "width": 120},
		{"label": "Administered By", "fieldname": "administered_by", "fieldtype": "Data",     "width": 140},
		{"label": "Remarks",         "fieldname": "remarks",         "fieldtype": "Data",     "width": 200},
	]

	clauses = ["cte.docstatus = 1"]
	query_filters = {}

	if filters.crop:
		clauses.append("cte.crop = %(crop)s")
		query_filters["crop"] = filters.crop

	if filters.farm_name:
		clauses.append("pc.farm_name LIKE %(farm_name)s")
		query_filters["farm_name"] = f"%{filters.farm_name}%"

	if filters.outcome:
		clauses.append("cte.outcome = %(outcome)s")
		query_filters["outcome"] = filters.outcome

	if filters.from_date:
		clauses.append("cte.treatment_date >= %(from_date)s")
		query_filters["from_date"] = filters.from_date

	if filters.to_date:
		clauses.append("cte.treatment_date <= %(to_date)s")
		query_filters["to_date"] = filters.to_date

	where = "WHERE " + " AND ".join(clauses)

	data = frappe.db.sql(
		f"""
		SELECT
			cte.name,
			cte.crop,
			pc.farm_name,
			cte.treatment_date,
			cte.day_age,
			cte.symptoms,
			cte.birds_affected,
			cte.treatment_cost,
			cte.outcome,
			cte.follow_up_date,
			cte.administered_by,
			cte.remarks
		FROM `tabCrop Treatment Entry` cte
		JOIN `tabPoultry Crop` pc ON pc.name = cte.crop
		{where}
		ORDER BY cte.treatment_date DESC, cte.crop ASC
		""",
		query_filters,
		as_dict=True,
	)

	# Fetch products for each entry in one query
	if data:
		entry_names = [r.name for r in data]
		placeholders = ", ".join(["%s"] * len(entry_names))
		products_raw = frappe.db.sql(
			f"""
			SELECT parent, GROUP_CONCAT(product ORDER BY idx SEPARATOR ', ') AS products
			FROM `tabTreatment Item`
			WHERE parent IN ({placeholders})
			GROUP BY parent
			""",
			entry_names,
			as_dict=True,
		)
		products_map = {r.parent: r.products for r in products_raw}
		for row in data:
			row["products"] = products_map.get(row.name, "")
			if row.outcome == "Mortality Increase":
				row["bold"] = 1

	chart   = _build_chart(data)
	summary = _build_summary(data)
	return columns, data, None, chart, summary


def _build_chart(data):
	"""Bar chart: treatment cost by crop (top 10)."""
	if not data:
		return None

	crop_totals = {}
	for row in data:
		crop_totals[row.crop] = crop_totals.get(row.crop, 0) + (row.treatment_cost or 0)

	top = sorted(crop_totals.items(), key=lambda x: x[1], reverse=True)[:10]
	if not top:
		return None

	return {
		"data": {
			"labels": [t[0] for t in top],
			"datasets": [{"name": "Treatment Cost (KES)", "values": [t[1] for t in top]}],
		},
		"type": "bar",
		"colors": ["#E8AE00"],
		"height": 260,
	}


def _build_summary(data):
	if not data:
		return []

	total_entries    = len(data)
	total_cost       = sum(r.treatment_cost   or 0 for r in data)
	mortality_events = sum(1 for r in data if r.outcome == "Mortality Increase")
	unique_crops     = len({r.crop for r in data})

	return [
		{"label": "Total Treatments",    "value": total_entries,    "datatype": "Int",      "indicator": "blue"},
		{"label": "Crops Treated",       "value": unique_crops,     "datatype": "Int",      "indicator": "blue"},
		{"label": "Total Treatment Cost","value": total_cost,       "datatype": "Currency", "currency": "KES", "indicator": "orange"},
		{"label": "Mortality Increase Events", "value": mortality_events, "datatype": "Int", "indicator": "red" if mortality_events else "green"},
	]
