import frappe


def execute(filters=None):
	columns = [
		{"label": "Crop", "fieldname": "name", "fieldtype": "Link", "options": "Poultry Crop", "width": 200},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 150},
		{"label": "Chicks In", "fieldname": "chicks_received", "fieldtype": "Int", "width": 100},
		{
			"label": "Birds Out",
			"fieldname": "total_birds_collected",
			"fieldtype": "Int",
			"width": 100,
		},
		{"label": "Mortality %", "fieldname": "mortality_pct", "fieldtype": "Percent", "width": 100},
		{"label": "FCR", "fieldname": "fcr", "fieldtype": "Float", "width": 80},
		{"label": "Avg Weight (KG)", "fieldname": "avg_weight", "fieldtype": "Float", "width": 130},
		{"label": "Revenue (KES)", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 130},
		{"label": "Net Profit (KES)", "fieldname": "net_profit", "fieldtype": "Currency", "width": 130},
		{"label": "Rev/Bird (KES)", "fieldname": "revenue_per_bird", "fieldtype": "Currency", "width": 130},
	]

	data = frappe.db.sql(
		"""
		SELECT
			pc.name,
			pc.farm_name,
			pc.chicks_received,
			pc.total_birds_collected,
			pc.mortality_pct,
			cfs.fcr,
			bce_agg.avg_weight,
			pc.total_revenue,
			cfs.net_profit,
			cfs.revenue_per_bird
		FROM `tabPoultry Crop` pc
		LEFT JOIN `tabCrop Financial Summary` cfs ON cfs.crop = pc.name
		LEFT JOIN (
			SELECT crop, AVG(average_weight_kg) AS avg_weight
			FROM `tabBird Collection Entry`
			WHERE docstatus = 1
			GROUP BY crop
		) bce_agg ON bce_agg.crop = pc.name
		WHERE pc.status = 'Closed'
		ORDER BY pc.placement_date DESC
		""",
		as_dict=True,
	)

	return columns, data
