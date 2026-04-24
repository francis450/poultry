import frappe
from frappe.model.document import Document
from frappe.utils import date_diff


class BirdCollectionEntry(Document):

	def validate(self):
		self.calculate_summary()
		self.calculate_bird_age()

	def calculate_summary(self):
		total_birds = total_weight = total_revenue = 0
		for row in self.collection_details:
			row.total_weight_kg = (row.no_of_birds or 0) * (row.average_weight_kg or 0)
			row.total_amount    = row.total_weight_kg * (row.price_per_kg or 0)
			total_birds   += row.no_of_birds or 0
			total_weight  += row.total_weight_kg
			total_revenue += row.total_amount

		self.total_birds      = total_birds
		self.total_weight_kg  = round(total_weight, 2)
		self.total_revenue    = round(total_revenue, 2)
		self.average_weight_kg = round(total_weight / total_birds, 3) if total_birds else 0
		self.revenue_per_bird  = round(total_revenue / total_birds, 2) if total_birds else 0

	def calculate_bird_age(self):
		if self.crop and self.collection_date:
			placement = frappe.db.get_value("Poultry Crop", self.crop, "placement_date")
			if placement:
				self.bird_age_days = date_diff(self.collection_date, placement) + 1


def on_submit(doc, method):
	"""Update crop's running totals for birds collected and revenue."""
	all_collections = frappe.db.sql("""
		SELECT SUM(total_birds) as birds, SUM(total_revenue) as revenue
		FROM `tabBird Collection Entry`
		WHERE crop = %s AND docstatus = 1
	""", doc.crop, as_dict=True)

	if all_collections:
		frappe.db.set_value("Poultry Crop", doc.crop, {
			"total_birds_collected": all_collections[0].birds   or 0,
			"total_revenue":         all_collections[0].revenue or 0,
		})


def on_cancel(doc, method):
	on_submit(doc, method)
