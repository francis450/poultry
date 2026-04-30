import math

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff


class FlockDailyRecord(Document):

	def before_naming(self):
		self.populate_day_age()

	def validate(self):
		self.populate_day_age()
		self.populate_opening_stock()
		self.populate_standards()
		self.calculate_stock()
		self.calculate_week_number()
		self.calculate_feed_variance()
		self.calculate_bwt_variance()

	def populate_day_age(self):
		if self.crop and self.date and not self.day_age:
			placement_date = frappe.db.get_value("Poultry Crop", self.crop, "placement_date")
			if placement_date:
				self.day_age = date_diff(self.date, placement_date) + 1

	def populate_opening_stock(self):
		if not self.crop or self.opening_stock:
			return

		opening_stock = get_previous_closing_stock(self.crop, self.day_age) if self.day_age else None
		if opening_stock is None:
			crop = frappe.db.get_value(
				"Poultry Crop",
				self.crop,
				["current_stock", "chicks_received"],
				as_dict=True,
			)
			if crop:
				opening_stock = crop.current_stock or crop.chicks_received

		if opening_stock is not None:
			self.opening_stock = opening_stock

	def populate_standards(self):
		if not self.day_age:
			return

		standards = get_standards_for_day(self.day_age)
		if not standards:
			return

		if not self.feed_std_gms:
			self.feed_std_gms = standards.get("feed_std_gms")

		if self.is_weigh_day and not self.bwt_std_gms:
			self.bwt_std_gms = standards.get("bwt_std_gms")

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

	# Running FCR: feed consumed so far / projected live weight (current stock × last body weight)
	# Uses actual collected weight once birds are partially or fully harvested.
	collected_weight = frappe.db.sql("""
		SELECT COALESCE(SUM(total_weight_kg), 0)
		FROM `tabBird Collection Entry`
		WHERE crop = %s AND docstatus = 1
	""", crop_name)[0][0] or 0

	projected_weight = (crop.current_stock or 0) * (crop.last_recorded_weight_gms or 0) / 1000
	total_live_weight = collected_weight + projected_weight

	if total_live_weight and crop.total_feed_consumed_kg:
		crop.fcr = round(crop.total_feed_consumed_kg / total_live_weight, 3)

	crop.save(ignore_permissions=True)


def check_mortality_alert(doc):
	check_batch_health(doc)


def check_batch_health(doc):
	"""Alert Farm Directors when any early-warning threshold is breached."""
	if doc.alert_sent:
		return

	config = frappe.get_doc("Feed Standard Config")
	mortality_threshold   = config.mortality_alert_pct   or 1.0
	feed_drop_threshold   = config.feed_drop_alert_pct   or 20.0
	bwt_deficit_threshold = config.bwt_deficit_alert_pct or 10.0

	warnings = []

	# 1. Daily mortality
	if (doc.mortality_pct or 0) > mortality_threshold:
		warnings.append(
			f"<li><b>High Mortality:</b> {doc.mortality} birds "
			f"({doc.mortality_pct}% of opening stock — threshold {mortality_threshold}%)</li>"
		)

	# 2. Feed drop — actual intake more than feed_drop_threshold% below standard
	if doc.std_total_kg and (doc.feed_in_kg or 0) > 0:
		drop_pct = ((doc.std_total_kg - doc.feed_in_kg) / doc.std_total_kg) * 100
		if drop_pct >= feed_drop_threshold:
			warnings.append(
				f"<li><b>Feed Drop:</b> {doc.feed_in_kg} kg fed vs standard {doc.std_total_kg} kg "
				f"({round(drop_pct, 1)}% below standard — threshold {feed_drop_threshold}%)</li>"
			)

	# 3. Body weight deficit on weigh days
	if doc.is_weigh_day and doc.bwt_std_gms and (doc.bwt_actual_gms or 0) > 0:
		deficit_pct = ((doc.bwt_std_gms - doc.bwt_actual_gms) / doc.bwt_std_gms) * 100
		if deficit_pct >= bwt_deficit_threshold:
			warnings.append(
				f"<li><b>Low Body Weight:</b> {doc.bwt_actual_gms} g actual vs standard {doc.bwt_std_gms} g "
				f"({round(deficit_pct, 1)}% below standard — threshold {bwt_deficit_threshold}%)</li>"
			)

	if not warnings:
		return

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
		items = "".join(warnings)
		frappe.sendmail(
			recipients=recipients,
			subject=f"Batch Health Warning — {doc.crop} Day {doc.day_age}",
			message=f"""
				<p>Warning(s) recorded for <b>{doc.crop}</b> on Day {doc.day_age} ({doc.date}):</p>
				<ul>{items}</ul>
				<p>Please review this batch immediately.</p>
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
	if not day_age or int(day_age) <= 1:
		return None

	prev = frappe.db.sql("""
		SELECT closing_stock
		FROM `tabFlock Daily Record`
		WHERE crop = %s AND day_age = %s
		LIMIT 1
	""", (crop, int(day_age) - 1), as_dict=True)
	return prev[0].closing_stock if prev else None
