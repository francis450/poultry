import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Crop", "fieldname": "crop", "fieldtype": "Link", "options": "Poultry Crop", "width": 220},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 150},
		{"label": "Chick Cost (KES)", "fieldname": "chick_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Feed Cost (KES)", "fieldname": "total_feed_cost", "fieldtype": "Currency", "width": 140},
		{
			"label": "Mortality Loss (KES)",
			"fieldname": "mortality_loss_value",
			"fieldtype": "Currency",
			"width": 160,
		},
		{"label": "Other Costs (KES)", "fieldname": "other_costs", "fieldtype": "Currency", "width": 140},
		{"label": "Total Cost (KES)", "fieldname": "cumulative_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Revenue (KES)", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 140},
		{"label": "Net Profit (KES)", "fieldname": "net_profit", "fieldtype": "Currency", "width": 140},
		{"label": "Margin %", "fieldname": "profit_margin_pct", "fieldtype": "Percent", "width": 100},
		{"label": "Cost/Bird (KES)", "fieldname": "cost_per_bird", "fieldtype": "Currency", "width": 130},
		{"label": "Revenue/Bird (KES)", "fieldname": "revenue_per_bird", "fieldtype": "Currency", "width": 140},
		{"label": "FCR", "fieldname": "fcr", "fieldtype": "Float", "width": 80},
		{"label": "Mortality %", "fieldname": "mortality_pct", "fieldtype": "Percent", "width": 100},
	]

	conditions = ""
	if filters.get("crop"):
		conditions = "WHERE cfs.crop = %(crop)s"

	data = frappe.db.sql(
		f"""
		SELECT
			cfs.crop,
			pc.farm_name,
			cfs.chick_cost,
			cfs.total_feed_cost,
			cfs.mortality_loss_value,
			cfs.other_costs,
			cfs.cumulative_cost,
			cfs.total_revenue,
			cfs.net_profit,
			cfs.profit_margin_pct,
			cfs.cost_per_bird,
			cfs.revenue_per_bird,
			cfs.fcr,
			pc.mortality_pct
		FROM `tabCrop Financial Summary` cfs
		JOIN `tabPoultry Crop` pc ON pc.name = cfs.crop
		{conditions}
		ORDER BY cfs.crop DESC
		""",
		filters,
		as_dict=True,
	)

	for row in data:
		if (row.net_profit or 0) < 0:
			row["bold"] = 1

	return columns, data
