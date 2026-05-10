import datetime

import frappe
from frappe.model.document import Document


class PoultryCrop(Document):

	def validate(self):
		self.total_chick_cost = (self.chicks_received or 0) * (self.chick_cost_per_unit or 0)
		self.adjusted_opening_stock = (self.chicks_received or 0) - (self.birds_dead_on_arrival or 0)
		if not self.crop_title:
			self.crop_title = f"{self.farm_name} — Crop {self.crop_number}"

	@frappe.whitelist()
	def activate_crop(self):
		if self.status != "Draft":
			frappe.throw("Only Draft crops can be activated.")
		self.status = "Active"
		self.save()
		from poultry_farm.poultry.doctype.crop_vaccination_log.crop_vaccination_log import create_vaccination_log
		create_vaccination_log(self.name)
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

	# Consumable costs broken down by category
	consumable_by_category = frappe.db.sql("""
		SELECT ci.category, COALESCE(SUM(csi.total_purchase_cost), 0) AS cost
		FROM `tabConsumable Sheet Item` csi
		JOIN `tabCrop Consumable Sheet` ccs ON ccs.name = csi.parent
		JOIN `tabConsumable Item` ci ON ci.name = csi.item
		WHERE ccs.crop = %s AND ccs.docstatus = 1
		GROUP BY ci.category
	""", crop_name, as_dict=True)

	cat_map = {r.category: (r.cost or 0) for r in consumable_by_category}
	vet_cost              = cat_map.get("Veterinary", 0)
	biosecurity_cost      = cat_map.get("Biosecurity", 0) + cat_map.get("Water Treatment", 0)
	fuel_heating_cost     = cat_map.get("Fuel & Heating", 0)
	other_consumable_cost = (
		cat_map.get("Bedding", 0)
		+ cat_map.get("Cleaning", 0)
		+ cat_map.get("Miscellaneous", 0)
	)
	consumable_cost = sum(cat_map.values())

	# Labor costs broken down by type (Salaried vs Casual)
	labor_by_type = frappe.db.sql("""
		SELECT cli.labor_type, COALESCE(SUM(cli.total_cost), 0) AS cost
		FROM `tabCrop Labor Item` cli
		JOIN `tabCrop Labor Entry` cle ON cle.name = cli.parent
		WHERE cle.crop = %s AND cle.docstatus = 1
		GROUP BY cli.labor_type
	""", crop_name, as_dict=True)

	labor_type_map    = {r.labor_type: (r.cost or 0) for r in labor_by_type}
	salaried_labor_cost = labor_type_map.get("Salaried", 0)
	casual_labor_cost   = labor_type_map.get("Casual", 0)
	labor_cost          = salaried_labor_cost + casual_labor_cost

	# Treatment costs from submitted Treatment Entries
	treatment_result = frappe.db.sql("""
		SELECT COALESCE(SUM(treatment_cost), 0)
		FROM `tabCrop Treatment Entry`
		WHERE crop = %s AND docstatus = 1
	""", crop_name)
	treatment_cost = (treatment_result[0][0] or 0) if treatment_result else 0

	chick_cost        = crop.total_chick_cost or 0
	mortality_loss    = (crop.total_mortality or 0) * (crop.chick_cost_per_unit or 0)
	other_costs       = frappe.db.get_value("Crop Financial Summary", {"crop": crop_name}, "other_costs") or 0
	cumulative_cost   = chick_cost + total_feed_cost + consumable_cost + labor_cost + treatment_cost + mortality_loss + other_costs
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

	# Budget totals (preserve manually entered values if summary already exists)
	budgeted_chick_cost      = 0
	budgeted_feed_cost       = 0
	budgeted_consumable_cost = 0
	budgeted_labor_cost      = 0
	budgeted_other_cost      = 0
	if existing:
		prev = frappe.get_doc("Crop Financial Summary", existing)
		budgeted_chick_cost      = prev.budgeted_chick_cost or 0
		budgeted_feed_cost       = prev.budgeted_feed_cost or 0
		budgeted_consumable_cost = prev.budgeted_consumable_cost or 0
		budgeted_labor_cost      = prev.budgeted_labor_cost or 0
		budgeted_other_cost      = prev.budgeted_other_cost or 0

	budgeted_total       = budgeted_chick_cost + budgeted_feed_cost + budgeted_consumable_cost + budgeted_labor_cost + budgeted_other_cost
	budget_variance      = cumulative_cost - budgeted_total
	budget_variance_pct  = round((budget_variance / budgeted_total * 100), 2) if budgeted_total else 0

	summary.generated_date           = datetime.date.today()
	summary.chick_cost               = chick_cost
	summary.feed_cost_prestarter     = cost_map.get("Pre-Starter", 0)
	summary.feed_cost_c1             = cost_map.get("C1 Grower", 0)
	summary.feed_cost_c2             = cost_map.get("C2 Grower", 0)
	summary.feed_cost_c3             = cost_map.get("C3 Grower", 0)
	summary.feed_cost_finisher       = cost_map.get("Finisher", 0)
	summary.total_feed_cost          = total_feed_cost
	summary.total_mortality_birds    = crop.total_mortality or 0
	summary.mortality_loss_value     = mortality_loss
	summary.vet_cost                 = vet_cost
	summary.biosecurity_cost         = biosecurity_cost
	summary.fuel_heating_cost        = fuel_heating_cost
	summary.other_consumable_cost    = other_consumable_cost
	summary.consumable_cost          = consumable_cost
	summary.salaried_labor_cost      = salaried_labor_cost
	summary.casual_labor_cost        = casual_labor_cost
	summary.labor_cost               = labor_cost
	summary.treatment_cost           = treatment_cost
	summary.cumulative_cost          = cumulative_cost
	summary.total_birds_slaughtered  = total_birds_slaughtered
	summary.total_revenue            = total_revenue
	summary.gross_profit             = gross_profit
	summary.net_profit               = net_profit
	summary.profit_margin_pct        = profit_margin_pct
	summary.cost_per_bird            = cost_per_bird
	summary.revenue_per_bird         = revenue_per_bird
	summary.fcr                      = fcr
	summary.budgeted_chick_cost      = budgeted_chick_cost
	summary.budgeted_feed_cost       = budgeted_feed_cost
	summary.budgeted_consumable_cost = budgeted_consumable_cost
	summary.budgeted_labor_cost      = budgeted_labor_cost
	summary.budgeted_other_cost      = budgeted_other_cost
	summary.budgeted_total           = budgeted_total
	summary.budget_variance          = budget_variance
	summary.budget_variance_pct      = budget_variance_pct

	summary.save(ignore_permissions=True)
	frappe.db.set_value("Poultry Crop", crop_name, "fcr", fcr)
	frappe.msgprint(f"Financial Summary {summary.name} created/updated.", alert=True)
