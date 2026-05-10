import frappe
from frappe.model.document import Document


class CropLaborEntry(Document):

	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		total = 0
		for row in self.labor_items:
			row.total_cost = (row.num_workers or 0) * (row.num_days or 0) * (row.rate_per_day or 0)
			total += row.total_cost
		self.total_cost = total


def on_submit(doc, method):
	_refresh_cfs_labor_cost(doc.crop)


def on_cancel(doc, method):
	_refresh_cfs_labor_cost(doc.crop)


def _refresh_cfs_labor_cost(crop_name):
	cfs = frappe.db.exists("Crop Financial Summary", {"crop": crop_name})
	if not cfs:
		return

	rows = frappe.db.sql("""
		SELECT cli.labor_type, COALESCE(SUM(cli.total_cost), 0) AS cost
		FROM `tabCrop Labor Item` cli
		JOIN `tabCrop Labor Entry` cle ON cle.name = cli.parent
		WHERE cle.crop = %s AND cle.docstatus = 1
		GROUP BY cli.labor_type
	""", crop_name, as_dict=True)

	labor_map           = {r.labor_type: (r.cost or 0) for r in rows}
	salaried_labor_cost = labor_map.get("Salaried", 0)
	casual_labor_cost   = labor_map.get("Casual", 0)

	frappe.db.set_value("Crop Financial Summary", cfs, {
		"salaried_labor_cost": salaried_labor_cost,
		"casual_labor_cost":   casual_labor_cost,
		"labor_cost":          salaried_labor_cost + casual_labor_cost,
	})
