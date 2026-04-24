import math

import frappe
from frappe.model.document import Document


class FlockDailyRecord(Document):

	def validate(self):
		self.calculate_stock()
		self.calculate_week_number()
		self.calculate_feed_variance()
		self.calculate_bwt_variance()

	def calculate_stock(self):
		self.closing_stock = (self.opening_stock or 0) - (self.mortality or 0)
		if self.opening_stock:
			self.mortality_pct = round(
				((self.mortality or 0) / self.opening_stock) * 100, 2
			)

	def calculate_week_number(self):
		if self.day_age:
			self.week_number = math.ceil(self.day_age / 7)

	def calculate_feed_variance(self):
		if self.feed_std_gms and self.closing_stock:
			self.std_total_kg = round(
				(self.feed_std_gms * self.closing_stock) / 1000, 3
			)
		self.feed_variance_kg = round(
			(self.feed_in_kg or 0) - (self.std_total_kg or 0), 3
		)

	def calculate_bwt_variance(self):
		if self.is_weigh_day and self.bwt_actual_gms:
			self.bwt_variance_gms = (self.bwt_actual_gms or 0) - (self.bwt_std_gms or 0)


def after_save(doc, method):
	update_crop_stats(doc.crop)
	check_mortality_alert(doc)


def on_submit(doc, method):
	update_crop_stats(doc.crop)


def update_crop_stats(crop_name):
	"""Recalculate and push aggregated stats back to the parent Poultry Crop."""
	crop = frappe.get_doc("Poultry Crop", crop_name)

	latest = frappe.db.sql("""
		SELECT closing_stock, bwt_actual_gms
		FROM `tabFlock Daily Record`
		WHERE crop = %s
		ORDER BY day_age DESC
		LIMIT 1
	""", crop_name, as_dict=True)

	if latest:
		crop.current_stock = latest[0].closing_stock
		if latest[0].bwt_actual_gms:
			crop.last_recorded_weight_gms = latest[0].bwt_actual_gms

	result = frappe.db.sql("""
		SELECT SUM(mortality) as total_mortality, SUM(feed_in_kg) as total_feed
		FROM `tabFlock Daily Record`
		WHERE crop = %s
	""", crop_name, as_dict=True)

	if result:
		crop.total_mortality        = result[0].total_mortality or 0
		crop.total_feed_consumed_kg = round(result[0].total_feed or 0, 2)
		if crop.chicks_received:
			crop.mortality_pct = round(
				(crop.total_mortality / crop.chicks_received) * 100, 2
			)

	crop.save(ignore_permissions=True)


def check_mortality_alert(doc):
	"""Email Farm Directors when daily mortality exceeds 1%."""
	if (doc.mortality_pct or 0) > 1.0 and not doc.alert_sent:
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
				subject=f"High Mortality Alert — {doc.crop} Day {doc.day_age}",
				message=f"""
					<p>High mortality recorded on <b>{doc.crop}</b>:</p>
					<ul>
						<li>Date: {doc.date}</li>
						<li>Day Age: {doc.day_age}</li>
						<li>Mortality: {doc.mortality} birds ({doc.mortality_pct}%)</li>
						<li>Closing Stock: {doc.closing_stock}</li>
					</ul>
					<p>Please investigate immediately.</p>
				"""
			)
		frappe.db.set_value("Flock Daily Record", doc.name, "alert_sent", 1)


@frappe.whitelist()
def get_standards_for_day(day_age):
	"""Return feed and body weight standards for a given day age from Feed Standard Config."""
	day_age = int(day_age)
	config = frappe.get_doc("Feed Standard Config")
	for row in config.standards:
		if row.day_from <= day_age <= row.day_to:
			return {
				"feed_std_gms": row.feed_std_gms,
				"bwt_std_gms":  row.bwt_std_gms,
				"feed_type":    row.feed_type,
			}
	return None


@frappe.whitelist()
def get_previous_closing_stock(crop, day_age):
	"""Return the closing stock of the immediately preceding day record."""
	prev = frappe.db.sql("""
		SELECT closing_stock
		FROM `tabFlock Daily Record`
		WHERE crop = %s AND day_age = %s
		LIMIT 1
	""", (crop, int(day_age) - 1), as_dict=True)
	return prev[0].closing_stock if prev else None
