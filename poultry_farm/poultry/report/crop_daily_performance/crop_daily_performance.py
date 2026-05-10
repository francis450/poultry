import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Date",              "fieldname": "date",              "fieldtype": "Data",     "width": 110},
		{"label": "Day",               "fieldname": "day_age",           "fieldtype": "Int",      "width": 55},
		{"label": "Week",              "fieldname": "week_number",       "fieldtype": "Int",      "width": 55},
		{"label": "Opening Stock",     "fieldname": "opening_stock",     "fieldtype": "Int",      "width": 115},
		{"label": "Mortality",         "fieldname": "mortality",         "fieldtype": "Int",      "width": 85},
		{"label": "Mortality %",       "fieldname": "mortality_pct",     "fieldtype": "Percent",  "width": 95},
		{"label": "Closing Stock",     "fieldname": "closing_stock",     "fieldtype": "Int",      "width": 115},
		{"label": "Feed Std (GMS)",    "fieldname": "feed_std_gms",      "fieldtype": "Float",    "width": 115},
		{"label": "Feed In (KG)",      "fieldname": "feed_in_kg",        "fieldtype": "Float",    "width": 100},
		{"label": "Std Total (KG)",    "fieldname": "std_total_kg",      "fieldtype": "Float",    "width": 110},
		{"label": "Feed Variance",     "fieldname": "feed_variance_kg",  "fieldtype": "Float",    "width": 110},
		{"label": "B.Wt Actual (GMS)", "fieldname": "bwt_actual_gms",   "fieldtype": "Float",    "width": 130},
		{"label": "B.Wt Std (GMS)",    "fieldname": "bwt_std_gms",      "fieldtype": "Float",    "width": 120},
		{"label": "B.Wt Variance",     "fieldname": "bwt_variance_gms", "fieldtype": "Float",    "width": 115},
		{"label": "Vaccinated",        "fieldname": "vaccination",       "fieldtype": "Check",    "width": 90},
		{"label": "Treated",           "fieldname": "treated",           "fieldtype": "Check",    "width": 80},
		{"label": "Treatment Products","fieldname": "treatment_products","fieldtype": "Data",     "width": 220},
		{"label": "Vaccination Notes", "fieldname": "remarks",           "fieldtype": "Data",     "width": 200},
	]


def get_data(filters):
	conditions = ["fdr.crop = %(crop)s"]
	if filters.get("from_date"):
		conditions.append("fdr.date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("fdr.date <= %(to_date)s")

	rows = frappe.db.sql(
		f"""
		SELECT
			fdr.date,
			fdr.day_age,
			fdr.week_number,
			fdr.opening_stock,
			fdr.mortality,
			fdr.mortality_pct,
			fdr.closing_stock,
			fdr.feed_std_gms,
			fdr.feed_in_kg,
			fdr.std_total_kg,
			fdr.feed_variance_kg,
			fdr.bwt_actual_gms,
			fdr.bwt_std_gms,
			fdr.bwt_variance_gms,
			fdr.vaccination,
			fdr.vaccination_details AS remarks,
			CASE WHEN trt.products IS NOT NULL THEN 1 ELSE 0 END AS treated,
			COALESCE(trt.products, '') AS treatment_products
		FROM `tabFlock Daily Record` fdr
		LEFT JOIN (
			SELECT
				cte.crop,
				cte.treatment_date,
				GROUP_CONCAT(ti.product ORDER BY ti.idx SEPARATOR ', ') AS products
			FROM `tabCrop Treatment Entry` cte
			INNER JOIN `tabTreatment Item` ti ON ti.parent = cte.name
			WHERE cte.docstatus = 1
			GROUP BY cte.crop, cte.treatment_date
		) trt ON trt.crop = fdr.crop AND trt.treatment_date = fdr.date
		WHERE {" AND ".join(conditions)}
		ORDER BY fdr.day_age ASC
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
		result.append({
			"date":         f"WEEK {week_number} TOTAL",
			"mortality":    sum(r.mortality  or 0 for r in week_rows),
			"feed_in_kg":   round(sum(r.feed_in_kg  or 0 for r in week_rows), 2),
			"std_total_kg": round(sum(r.std_total_kg or 0 for r in week_rows), 2),
			"bold":         1,
		})

	return result
