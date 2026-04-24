import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Date", "fieldname": "date", "fieldtype": "Data", "width": 130},
		{"label": "Day", "fieldname": "day_age", "fieldtype": "Int", "width": 60},
		{"label": "Week", "fieldname": "week_number", "fieldtype": "Int", "width": 60},
		{"label": "Opening Stock", "fieldname": "opening_stock", "fieldtype": "Int", "width": 120},
		{"label": "Mortality", "fieldname": "mortality", "fieldtype": "Int", "width": 90},
		{"label": "Mortality %", "fieldname": "mortality_pct", "fieldtype": "Percent", "width": 100},
		{"label": "Closing Stock", "fieldname": "closing_stock", "fieldtype": "Int", "width": 120},
		{"label": "Feed Std (GMS)", "fieldname": "feed_std_gms", "fieldtype": "Float", "width": 120},
		{"label": "Feed In (KG)", "fieldname": "feed_in_kg", "fieldtype": "Float", "width": 100},
		{"label": "Std Total (KG)", "fieldname": "std_total_kg", "fieldtype": "Float", "width": 110},
		{"label": "Feed Variance", "fieldname": "feed_variance_kg", "fieldtype": "Float", "width": 110},
		{"label": "B.Wt Actual (GMS)", "fieldname": "bwt_actual_gms", "fieldtype": "Float", "width": 130},
		{"label": "B.Wt Std (GMS)", "fieldname": "bwt_std_gms", "fieldtype": "Float", "width": 120},
		{"label": "B.Wt Variance", "fieldname": "bwt_variance_gms", "fieldtype": "Float", "width": 120},
		{"label": "Vaccination", "fieldname": "vaccination", "fieldtype": "Check", "width": 100},
		{"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 200},
	]


def get_data(filters):
	conditions = ["crop = %(crop)s"]
	if filters.get("from_date"):
		conditions.append("date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("date <= %(to_date)s")

	rows = frappe.db.sql(
		f"""
		SELECT
			date,
			day_age,
			week_number,
			opening_stock,
			mortality,
			mortality_pct,
			closing_stock,
			feed_std_gms,
			feed_in_kg,
			std_total_kg,
			feed_variance_kg,
			bwt_actual_gms,
			bwt_std_gms,
			bwt_variance_gms,
			vaccination,
			vaccination_details AS remarks
		FROM `tabFlock Daily Record`
		WHERE {" AND ".join(conditions)}
		ORDER BY day_age ASC
		""",
		filters,
		as_dict=True,
	)

	result = []
	week_groups = {}
	for row in rows:
		week_groups.setdefault(row.week_number, []).append(row)

	for week_number, week_rows in sorted(week_groups.items()):
		result.extend(week_rows)
		result.append(
			{
				"date": f"WEEK {week_number} TOTAL",
				"mortality": sum(row.mortality or 0 for row in week_rows),
				"feed_in_kg": round(sum(row.feed_in_kg or 0 for row in week_rows), 2),
				"std_total_kg": round(sum(row.std_total_kg or 0 for row in week_rows), 2),
			}
		)

	return result
