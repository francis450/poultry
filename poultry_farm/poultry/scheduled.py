import datetime

import frappe


def mark_overdue_vaccinations():
	"""
	Runs every night. Marks vaccination rows as Overdue when their
	scheduled_date has passed and they are still Pending.
	"""
	today = datetime.date.today()

	logs = frappe.get_all("Crop Vaccination Log", fields=["name"])
	for log_meta in logs:
		log = frappe.get_doc("Crop Vaccination Log", log_meta.name)
		changed = False
		for row in log.vaccinations:
			if row.status == "Pending" and row.scheduled_date and frappe.utils.getdate(row.scheduled_date) < today:
				row.status = "Overdue"
				changed = True
		if changed:
			log.save(ignore_permissions=True)

	frappe.db.commit()


def create_daily_records():
	"""
	Runs every night at midnight.
	Pre-creates a Flock Daily Record for each Active crop for the next day
	so the farm manager only needs to open it and fill in mortality/feed.
	"""
	tomorrow = datetime.date.today() + datetime.timedelta(days=1)

	active_crops = frappe.get_all(
		"Poultry Crop",
		filters={"status": "Active"},
		fields=["name", "placement_date", "current_stock", "chicks_received"]
	)

	for crop in active_crops:
		placement = frappe.utils.getdate(crop.placement_date)
		day_age   = (tomorrow - placement).days + 1

		if day_age < 1:
			continue

		if frappe.db.exists("Flock Daily Record", {"crop": crop.name, "day_age": day_age}):
			continue

		prev = frappe.db.sql("""
			SELECT closing_stock FROM `tabFlock Daily Record`
			WHERE crop = %s ORDER BY day_age DESC LIMIT 1
		""", crop.name, as_dict=True)

		opening = prev[0].closing_stock if prev else (crop.current_stock or crop.chicks_received)

		doc = frappe.new_doc("Flock Daily Record")
		doc.crop          = crop.name
		doc.date          = tomorrow
		doc.day_age       = day_age
		doc.opening_stock = opening
		doc.mortality     = 0
		doc.insert(ignore_permissions=True)

	frappe.db.commit()


def send_weekly_summary():
	"""
	Runs every Monday. Emails all Farm Directors a summary table
	of every Active or Slaughter crop.
	"""
	active_crops = frappe.get_all(
		"Poultry Crop",
		filters={"status": ["in", ["Active", "Slaughter"]]},
		fields=[
			"name", "farm_name", "crop_number", "current_stock",
			"total_mortality", "mortality_pct", "total_feed_consumed_kg"
		]
	)

	if not active_crops:
		return

	rows = "".join([
		f"<tr>"
		f"<td>{c.farm_name}</td><td>{c.crop_number}</td>"
		f"<td>{c.current_stock}</td><td>{c.total_mortality}</td>"
		f"<td>{c.mortality_pct}%</td><td>{c.total_feed_consumed_kg} KG</td>"
		f"</tr>"
		for c in active_crops
	])

	body = f"""
	<table border="1" cellpadding="5" cellspacing="0">
		<tr>
			<th>Farm</th><th>Crop #</th><th>Current Stock</th>
			<th>Total Mortality</th><th>Mortality %</th><th>Feed Consumed</th>
		</tr>
		{rows}
	</table>
	"""

	directors = frappe.get_all(
		"Has Role",
		filters={"role": "Farm Director", "parenttype": "User"},
		fields=["parent"]
	)
	recipients = [
		d.parent for d in directors
		if frappe.db.get_value("User", d.parent, "enabled")
	]

	if recipients:
		frappe.sendmail(
			recipients=recipients,
			subject="Weekly Poultry Farm Summary — Anirita",
			message=f"<p>Weekly summary of active crops:</p>{body}"
		)
