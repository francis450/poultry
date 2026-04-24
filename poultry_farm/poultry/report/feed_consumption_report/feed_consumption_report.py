import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": "Crop", "fieldname": "crop", "fieldtype": "Link", "options": "Poultry Crop", "width": 200},
		{"label": "Week", "fieldname": "week_number", "fieldtype": "Int", "width": 70},
		{"label": "Feed In (KG)", "fieldname": "actual_feed_kg", "fieldtype": "Float", "width": 130},
		{"label": "Std Feed (KG)", "fieldname": "std_feed_kg", "fieldtype": "Float", "width": 130},
		{"label": "Variance (KG)", "fieldname": "variance_kg", "fieldtype": "Float", "width": 120},
		{"label": "Variance %", "fieldname": "variance_pct", "fieldtype": "Percent", "width": 110},
	]

	conditions = []
	query_filters = {}

	if filters.crop:
		conditions.append("fdr.crop = %(crop)s")
		query_filters["crop"] = filters.crop

	if filters.status:
		conditions.append("pc.status = %(status)s")
		query_filters["status"] = filters.status

	if filters.week_number:
		conditions.append("fdr.week_number = %(week_number)s")
		query_filters["week_number"] = filters.week_number

	if filters.from_date:
		conditions.append("fdr.date >= %(from_date)s")
		query_filters["from_date"] = filters.from_date

	if filters.to_date:
		conditions.append("fdr.date <= %(to_date)s")
		query_filters["to_date"] = filters.to_date

	where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

	data = frappe.db.sql(
		f"""
		SELECT
			fdr.crop,
			fdr.week_number,
			SUM(fdr.feed_in_kg) AS actual_feed_kg,
			SUM(fdr.std_total_kg) AS std_feed_kg,
			SUM(fdr.feed_in_kg) - SUM(fdr.std_total_kg) AS variance_kg,
			CASE
				WHEN SUM(fdr.std_total_kg) > 0
				THEN ((SUM(fdr.feed_in_kg) - SUM(fdr.std_total_kg)) / SUM(fdr.std_total_kg)) * 100
				ELSE 0
			END AS variance_pct
		FROM `tabFlock Daily Record` fdr
		LEFT JOIN `tabPoultry Crop` pc ON pc.name = fdr.crop
		{where_clause}
		GROUP BY fdr.crop, fdr.week_number
		ORDER BY fdr.crop, fdr.week_number
		""",
		query_filters,
		as_dict=True,
	)

	return columns, data
