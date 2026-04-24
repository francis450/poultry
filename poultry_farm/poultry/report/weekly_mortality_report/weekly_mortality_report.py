import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Crop", "fieldname": "crop", "fieldtype": "Link", "options": "Poultry Crop", "width": 200},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 150},
		{"label": "Week", "fieldname": "week_number", "fieldtype": "Int", "width": 70},
		{"label": "Mortality", "fieldname": "total_mortality", "fieldtype": "Int", "width": 100},
		{"label": "Avg Daily Mort.", "fieldname": "avg_mortality", "fieldtype": "Float", "width": 130},
		{"label": "Mortality %", "fieldname": "mortality_pct", "fieldtype": "Percent", "width": 110},
		{
			"label": "Closing Stock (End of Week)",
			"fieldname": "closing_stock",
			"fieldtype": "Int",
			"width": 200,
		},
	]

	conditions = ""
	if filters.get("crop"):
		conditions = "AND fdr.crop = %(crop)s"

	data = frappe.db.sql(
		f"""
		SELECT
			fdr.crop,
			pc.farm_name,
			fdr.week_number,
			SUM(fdr.mortality) AS total_mortality,
			AVG(fdr.mortality) AS avg_mortality,
			AVG(fdr.mortality_pct) AS mortality_pct,
			MIN(fdr.closing_stock) AS closing_stock
		FROM `tabFlock Daily Record` fdr
		JOIN `tabPoultry Crop` pc ON pc.name = fdr.crop
		WHERE 1 = 1 {conditions}
		GROUP BY fdr.crop, pc.farm_name, fdr.week_number
		ORDER BY fdr.crop, fdr.week_number
		""",
		filters,
		as_dict=True,
	)

	return columns, data
