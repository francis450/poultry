import frappe


def execute(filters=None):
	filters = filters or {}

	columns = [
		{"label": "Crop", "fieldname": "crop", "fieldtype": "Link", "options": "Poultry Crop", "width": 220},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 150},
		{"label": "Placement Date", "fieldname": "placement_date", "fieldtype": "Date", "width": 120},
		{"label": "Chick Cost (KES)", "fieldname": "chick_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Feed Cost (KES)", "fieldname": "total_feed_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Mortality Loss (KES)", "fieldname": "mortality_loss_value", "fieldtype": "Currency", "width": 160},
		{"label": "Vet & Med (KES)", "fieldname": "vet_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Biosecurity & Water (KES)", "fieldname": "biosecurity_cost", "fieldtype": "Currency", "width": 180},
		{"label": "Fuel & Heating (KES)", "fieldname": "fuel_heating_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Other Consumables (KES)", "fieldname": "other_consumable_cost", "fieldtype": "Currency", "width": 170},
		{"label": "Total Consumables (KES)", "fieldname": "consumable_cost", "fieldtype": "Currency", "width": 170},
		{"label": "Salaried Labor (KES)", "fieldname": "salaried_labor_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Casual Labor (KES)", "fieldname": "casual_labor_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Total Labor (KES)", "fieldname": "labor_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Treatment Cost (KES)", "fieldname": "treatment_cost", "fieldtype": "Currency", "width": 150},
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

	conditions, values = _build_conditions(filters)

	data = frappe.db.sql(
		f"""
		SELECT
			cfs.crop,
			pc.farm_name,
			pc.placement_date,
			cfs.chick_cost,
			cfs.total_feed_cost,
			cfs.mortality_loss_value,
			cfs.vet_cost,
			cfs.biosecurity_cost,
			cfs.fuel_heating_cost,
			cfs.other_consumable_cost,
			cfs.consumable_cost,
			cfs.salaried_labor_cost,
			cfs.casual_labor_cost,
			cfs.labor_cost,
			cfs.treatment_cost,
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
		ORDER BY pc.placement_date ASC
		""",
		values,
		as_dict=True,
	)

	for row in data:
		if (row.net_profit or 0) < 0:
			row["bold"] = 1

	chart         = _build_chart(data)
	report_summary = _build_summary(data)

	return columns, data, None, chart, report_summary


def _build_conditions(filters):
	clauses = []
	values  = {}

	if filters.get("crop"):
		clauses.append("cfs.crop = %(crop)s")
		values["crop"] = filters["crop"]

	if filters.get("farm_name"):
		clauses.append("pc.farm_name LIKE %(farm_name)s")
		values["farm_name"] = f"%{filters['farm_name']}%"

	if filters.get("status"):
		clauses.append("pc.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("from_date"):
		clauses.append("pc.placement_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		clauses.append("pc.placement_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
	return where, values


def _build_chart(data):
	if not data:
		return None

	labels       = [r.crop for r in data]
	revenues     = [r.total_revenue     or 0 for r in data]
	total_costs  = [r.cumulative_cost   or 0 for r in data]
	net_profits  = [r.net_profit        or 0 for r in data]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Revenue (KES)",    "values": revenues},
				{"name": "Total Cost (KES)", "values": total_costs},
				{"name": "Net Profit (KES)", "values": net_profits},
			],
		},
		"type": "bar",
		"colors": ["#5E64FF", "#FF5858", "#28a745"],
		"barOptions": {"stacked": 0},
		"axisOptions": {"xIsSeries": 1},
		"height": 280,
	}


def _build_summary(data):
	if not data:
		return []

	total_revenue      = sum(r.total_revenue       or 0 for r in data)
	total_net          = sum(r.net_profit          or 0 for r in data)
	total_feed         = sum(r.total_feed_cost     or 0 for r in data)
	total_consumable   = sum(r.consumable_cost     or 0 for r in data)
	total_labor        = sum(r.labor_cost          or 0 for r in data)
	total_treatment    = sum(r.treatment_cost      or 0 for r in data)
	total_cost         = sum(r.cumulative_cost     or 0 for r in data)

	margins = [r.profit_margin_pct for r in data if r.profit_margin_pct is not None]
	fcrs    = [r.fcr               for r in data if r.fcr]

	avg_margin = round(sum(margins) / len(margins), 2) if margins else 0
	avg_fcr    = round(sum(fcrs)    / len(fcrs),    3) if fcrs    else 0

	profit_indicator = "green" if total_net >= 0 else "red"

	return [
		{
			"label": "Total Revenue",
			"value": total_revenue,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": "blue",
		},
		{
			"label": "Total Net Profit",
			"value": total_net,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": profit_indicator,
		},
		{
			"label": "Total Feed Cost",
			"value": total_feed,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": "orange",
		},
		{
			"label": "Total Consumables",
			"value": total_consumable,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": "orange",
		},
		{
			"label": "Total Labor",
			"value": total_labor,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": "orange",
		},
		{
			"label": "Total Treatment",
			"value": total_treatment,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": "orange",
		},
		{
			"label": "Total Cost",
			"value": total_cost,
			"datatype": "Currency",
			"currency": "KES",
			"indicator": "orange",
		},
		{
			"label": "Avg Margin %",
			"value": avg_margin,
			"datatype": "Percent",
			"indicator": "green" if avg_margin >= 0 else "red",
		},
		{
			"label": "Avg FCR",
			"value": avg_fcr,
			"datatype": "Float",
			"indicator": "blue",
		},
	]
