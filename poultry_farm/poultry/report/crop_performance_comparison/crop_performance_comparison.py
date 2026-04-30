import frappe


def execute(filters=None):
	columns = [
		{"label": "Crop", "fieldname": "name", "fieldtype": "Link", "options": "Poultry Crop", "width": 200},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": "Day Age", "fieldname": "day_age", "fieldtype": "Int", "width": 80},
		{"label": "Chicks In", "fieldname": "chicks_received", "fieldtype": "Int", "width": 100},
		{"label": "Current Stock", "fieldname": "current_stock", "fieldtype": "Int", "width": 110},
		{"label": "Mortality %", "fieldname": "mortality_pct", "fieldtype": "Percent", "width": 100},
		{"label": "Feed Consumed (KG)", "fieldname": "total_feed_consumed_kg", "fieldtype": "Float", "width": 150},
		{"label": "FCR", "fieldname": "fcr", "fieldtype": "Float", "width": 80},
		{"label": "Avg Weight (KG)", "fieldname": "avg_weight", "fieldtype": "Float", "width": 130},
		{"label": "Revenue (KES)", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 130},
		{"label": "Net Profit (KES)", "fieldname": "net_profit", "fieldtype": "Currency", "width": 130},
	]

	data = frappe.db.sql(
		"""
		SELECT
			pc.name,
			pc.farm_name,
			pc.status,
			pc.chicks_received,
			pc.current_stock,
			pc.mortality_pct,
			pc.total_feed_consumed_kg,
			pc.fcr,
			DATEDIFF(CURDATE(), pc.placement_date) + 1 AS day_age,
			bce_agg.avg_weight,
			pc.total_revenue,
			cfs.net_profit
		FROM `tabPoultry Crop` pc
		LEFT JOIN `tabCrop Financial Summary` cfs ON cfs.crop = pc.name
		LEFT JOIN (
			SELECT crop, AVG(average_weight_kg) AS avg_weight
			FROM `tabBird Collection Entry`
			WHERE docstatus = 1
			GROUP BY crop
		) bce_agg ON bce_agg.crop = pc.name
		ORDER BY pc.status ASC, pc.placement_date DESC
		""",
		as_dict=True,
	)

	return columns, data
