import frappe
from frappe.model.document import Document


class CropTreatmentEntry(Document):

	def validate(self):
		self.calculate_day_age()
		self.calculate_treatment_cost()

	def calculate_day_age(self):
		if self.crop and self.treatment_date:
			placement_date = frappe.db.get_value("Poultry Crop", self.crop, "placement_date")
			if placement_date:
				delta = (
					frappe.utils.getdate(self.treatment_date)
					- frappe.utils.getdate(placement_date)
				).days + 1
				self.day_age = max(delta, 1)

	def calculate_treatment_cost(self):
		total = 0.0
		for row in (self.treatment_items or []):
			row.total_cost = (row.quantity_used or 0) * (row.unit_cost or 0)
			total += row.total_cost
		self.treatment_cost = total

	def on_submit(self):
		_refresh_cfs_treatment_cost(self.crop)

	def on_cancel(self):
		_refresh_cfs_treatment_cost(self.crop)


def _refresh_cfs_treatment_cost(crop_name):
	"""Recompute treatment_cost on Crop Financial Summary from all submitted Treatment Entries."""
	result = frappe.db.sql("""
		SELECT COALESCE(SUM(cte.treatment_cost), 0)
		FROM `tabCrop Treatment Entry` cte
		WHERE cte.crop = %s AND cte.docstatus = 1
	""", crop_name)

	treatment_cost = (result[0][0] or 0) if result else 0

	cfs_name = frappe.db.exists("Crop Financial Summary", {"crop": crop_name})
	if not cfs_name:
		return

	cfs = frappe.get_doc("Crop Financial Summary", cfs_name)
	cfs.treatment_cost = treatment_cost
	cfs.cumulative_cost = (
		(cfs.chick_cost or 0)
		+ (cfs.total_feed_cost or 0)
		+ (cfs.consumable_cost or 0)
		+ (cfs.labor_cost or 0)
		+ (cfs.treatment_cost or 0)
		+ (cfs.mortality_loss_value or 0)
		+ (cfs.other_costs or 0)
	)
	net_profit = (cfs.total_revenue or 0) - cfs.cumulative_cost
	cfs.net_profit = net_profit
	cfs.gross_profit = (cfs.total_revenue or 0) - (cfs.chick_cost or 0) - (cfs.total_feed_cost or 0)
	if cfs.total_revenue:
		cfs.profit_margin_pct = round(net_profit / cfs.total_revenue * 100, 2)
	slaughtered = cfs.total_birds_slaughtered or 0
	if slaughtered:
		cfs.cost_per_bird    = round(cfs.cumulative_cost / slaughtered, 2)
		cfs.revenue_per_bird = round((cfs.total_revenue or 0) / slaughtered, 2)
	cfs.budget_variance = cfs.cumulative_cost - (cfs.budgeted_total or 0)
	if cfs.budgeted_total:
		cfs.budget_variance_pct = round(cfs.budget_variance / cfs.budgeted_total * 100, 2)
	cfs.save(ignore_permissions=True)
