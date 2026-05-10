import frappe


def execute(filters=None):
	filters = filters or {}

	columns = [
		{"label": "Crop",                    "fieldname": "crop",            "fieldtype": "Link",    "options": "Poultry Crop", "width": 200},
		{"label": "Farm",                    "fieldname": "farm_name",       "fieldtype": "Data",    "width": 150},
		{"label": "Week",                    "fieldname": "week_number",     "fieldtype": "Int",     "width": 70},
		{"label": "Deaths This Week",        "fieldname": "total_mortality",  "fieldtype": "Int",     "width": 130},
		{"label": "Avg Daily Deaths",        "fieldname": "avg_mortality",   "fieldtype": "Float",   "width": 130},
		{"label": "Cumulative Mortality %",  "fieldname": "mortality_pct",   "fieldtype": "Percent", "width": 170},
		{"label": "Closing Stock (Week End)","fieldname": "closing_stock",   "fieldtype": "Int",     "width": 180},
	]

	clauses = ["1 = 1"]
	if filters.get("crop"):
		clauses.append("fdr.crop = %(crop)s")
	if filters.get("from_date"):
		clauses.append("fdr.date >= %(from_date)s")
	if filters.get("to_date"):
		clauses.append("fdr.date <= %(to_date)s")

	where = " AND ".join(clauses)

	data = frappe.db.sql(
		f"""
		SELECT
			fdr.crop,
			pc.farm_name,
			fdr.week_number,
			SUM(fdr.mortality) AS total_mortality,
			ROUND(AVG(fdr.mortality), 2) AS avg_mortality,
			ROUND(AVG(fdr.mortality_pct), 2) AS mortality_pct,
			CAST(
				SUBSTRING_INDEX(
					GROUP_CONCAT(fdr.closing_stock ORDER BY fdr.day_age DESC),
					',', 1
				) AS UNSIGNED
			) AS closing_stock
		FROM `tabFlock Daily Record` fdr
		JOIN `tabPoultry Crop` pc ON pc.name = fdr.crop
		WHERE {where}
		GROUP BY fdr.crop, pc.farm_name, fdr.week_number
		ORDER BY fdr.crop, fdr.week_number
		""",
		filters,
		as_dict=True,
	)

	for row in data:
		if (row.mortality_pct or 0) > 5:
			row["bold"] = 1

	chart = _build_chart(data, filters.get("crop"))
	return columns, data, None, chart, None


def _build_chart(data, crop_filter):
	if not data or not crop_filter:
		return None

	crop_data = [r for r in data if r.crop == crop_filter]
	if not crop_data:
		return None

	return {
		"data": {
			"labels": [f"Wk {r.week_number}" for r in crop_data],
			"datasets": [
				{"name": "Deaths", "values": [r.total_mortality or 0 for r in crop_data]},
			],
		},
		"type": "bar",
		"colors": ["#FF5858"],
		"height": 240,
	}
