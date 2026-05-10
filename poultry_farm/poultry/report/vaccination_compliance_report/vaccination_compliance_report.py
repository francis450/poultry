import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Crop", "fieldname": "crop", "fieldtype": "Link", "options": "Poultry Crop", "width": 180},
		{"label": "Farm", "fieldname": "farm_name", "fieldtype": "Data", "width": 150},
		{"label": "Day", "fieldname": "day_number", "fieldtype": "Int", "width": 60},
		{"label": "Vaccine", "fieldname": "vaccine_name", "fieldtype": "Data", "width": 160},
		{"label": "Scheduled Date", "fieldname": "scheduled_date", "fieldtype": "Date", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": "Actual Date", "fieldname": "actual_date", "fieldtype": "Date", "width": 110},
		{"label": "Delay (Days)", "fieldname": "delay_days", "fieldtype": "Int", "width": 100},
		{"label": "Administered By", "fieldname": "administered_by", "fieldtype": "Data", "width": 140},
		{"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 200},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("crop"):
		conditions.append("cvl.crop = %(crop)s")
		values["crop"] = filters["crop"]

	if filters.get("status"):
		conditions.append("cvr.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("from_date"):
		conditions.append("cvr.scheduled_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("cvr.scheduled_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	rows = frappe.db.sql(f"""
		SELECT
			cvl.crop,
			pc.farm_name,
			cvr.day_number,
			cvr.vaccine_name,
			cvr.scheduled_date,
			cvr.status,
			cvr.actual_date,
			cvr.administered_by,
			cvr.remarks
		FROM `tabCrop Vaccination Row` cvr
		JOIN `tabCrop Vaccination Log` cvl ON cvl.name = cvr.parent
		JOIN `tabPoultry Crop` pc ON pc.name = cvl.crop
		{where}
		ORDER BY cvl.crop, cvr.day_number
	""", values, as_dict=True)

	for row in rows:
		if row.actual_date and row.scheduled_date:
			delta = (frappe.utils.getdate(row.actual_date) - frappe.utils.getdate(row.scheduled_date)).days
			row.delay_days = delta if delta > 0 else 0
		elif row.status == "Overdue":
			import datetime
			row.delay_days = (datetime.date.today() - frappe.utils.getdate(row.scheduled_date)).days
		else:
			row.delay_days = 0

	return rows
