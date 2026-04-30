import datetime

import frappe
from frappe.model.document import Document


class PoultryCrop(Document):

	def validate(self):
		self.total_chick_cost = (self.chicks_received or 0) * (self.chick_cost_per_unit or 0)
		if not self.crop_title:
			self.crop_title = f"{self.farm_name} — Crop {self.crop_number}"

	@frappe.whitelist()
	def activate_crop(self):
		if self.status != "Draft":
			frappe.throw("Only Draft crops can be activated.")
		self.status = "Active"
		self.save()
		frappe.msgprint(f"Crop {self.name} is now Active. Start logging daily records.", alert=True)

	@frappe.whitelist()
	def start_slaughter(self):
		if self.status != "Active":
			frappe.throw("Crop must be Active to begin Slaughter.")
		self.status = "Slaughter"
		self.actual_slaughter_date = datetime.date.today()
		self.save()
		frappe.msgprint("Crop moved to Slaughter. Create Bird Collection Entries.", alert=True)

	@frappe.whitelist()
	def close_crop(self):
		if self.status != "Slaughter":
			frappe.throw("Crop must be in Slaughter status to Close.")
		self.status = "Closed"
		self.save()
		generate_financial_summary(self.name)
		frappe.msgprint("Crop Closed. Financial Summary generated.", alert=True)


def generate_financial_summary(crop_name):
	"""Auto-generate or refresh the Crop Financial Summary."""
	crop = frappe.get_doc("Poultry Crop", crop_name)

	# Feed costs grouped by feed type
	feed_costs = frappe.db.sql("""
		SELECT fpi.feed_type, SUM(fpi.total_cost) as cost
		FROM `tabFeed Purchase Item` fpi
		JOIN `tabFeed Purchase Entry` fpe ON fpe.name = fpi.parent
		WHERE fpe.crop = %s AND fpe.docstatus = 1
		GROUP BY fpi.feed_type
	""", crop_name, as_dict=True)

	cost_map = {r.feed_type: (r.cost or 0) for r in feed_costs}
	total_feed_cost = sum(cost_map.values())

	# Revenue from bird collections
	revenue_data = frappe.db.sql("""
		SELECT SUM(total_birds) as birds, SUM(total_revenue) as revenue
		FROM `tabBird Collection Entry`
		WHERE crop = %s AND docstatus = 1
	""", crop_name, as_dict=True)

	total_birds_slaughtered = (revenue_data[0].birds   or 0) if revenue_data else 0
	total_revenue           = (revenue_data[0].revenue or 0) if revenue_data else 0

	chick_cost        = crop.total_chick_cost or 0
	mortality_loss    = (crop.total_mortality or 0) * (crop.chick_cost_per_unit or 0)
	cumulative_cost   = chick_cost + total_feed_cost + mortality_loss
	gross_profit      = total_revenue - chick_cost - total_feed_cost
	net_profit        = total_revenue - cumulative_cost
	profit_margin_pct = round((net_profit / total_revenue * 100), 2) if total_revenue else 0
	cost_per_bird     = round(cumulative_cost / total_birds_slaughtered, 2) if total_birds_slaughtered else 0
	revenue_per_bird  = round(total_revenue   / total_birds_slaughtered, 2) if total_birds_slaughtered else 0

	# FCR
	total_live_weight_kg = frappe.db.sql("""
		SELECT SUM(bcd.total_weight_kg)
		FROM `tabBird Collection Detail` bcd
		JOIN `tabBird Collection Entry` bce ON bce.name = bcd.parent
		WHERE bce.crop = %s AND bce.docstatus = 1
	""", crop_name)[0][0] or 0

	fcr = round(
		(crop.total_feed_consumed_kg or 0) / total_live_weight_kg, 3
	) if total_live_weight_kg else 0

	# Upsert summary
	existing = frappe.db.exists("Crop Financial Summary", {"crop": crop_name})
	if existing:
		summary = frappe.get_doc("Crop Financial Summary", existing)
	else:
		summary = frappe.new_doc("Crop Financial Summary")
		summary.crop = crop_name

	summary.generated_date          = datetime.date.today()
	summary.chick_cost               = chick_cost
	# feed_type values match our Select options
	summary.feed_cost_prestarter     = cost_map.get("Pre-Starter", 0)
	summary.feed_cost_c1             = cost_map.get("C1 Grower", 0)
	summary.feed_cost_c2             = cost_map.get("C2 Grower", 0)
	summary.feed_cost_c3             = cost_map.get("C3 Grower", 0)
	summary.feed_cost_finisher       = cost_map.get("Finisher", 0)
	summary.total_feed_cost          = total_feed_cost
	summary.total_mortality_birds    = crop.total_mortality or 0
	summary.mortality_loss_value     = mortality_loss
	summary.cumulative_cost          = cumulative_cost
	summary.total_birds_slaughtered  = total_birds_slaughtered
	summary.total_revenue            = total_revenue
	summary.gross_profit             = gross_profit
	summary.net_profit               = net_profit
	summary.profit_margin_pct        = profit_margin_pct
	summary.cost_per_bird            = cost_per_bird
	summary.revenue_per_bird         = revenue_per_bird
	summary.fcr                      = fcr

	summary.save(ignore_permissions=True)
	frappe.db.set_value("Poultry Crop", crop_name, "fcr", fcr)
	frappe.msgprint(f"Financial Summary {summary.name} created/updated.", alert=True)
