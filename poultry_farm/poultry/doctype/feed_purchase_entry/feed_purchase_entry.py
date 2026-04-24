import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class FeedPurchaseEntry(Document):

	def validate(self):
		self.calculate_totals()
		self.fetch_warehouse_from_crop()

	def calculate_totals(self):
		total_bags = total_kgs = total_cost = 0
		for row in self.feed_items:
			row.total_kgs  = (row.no_of_bags or 0) * (row.pack_weight_kg or 0)
			row.total_cost = (row.no_of_bags or 0) * (row.price_per_bag  or 0)
			total_bags += row.no_of_bags or 0
			total_kgs  += row.total_kgs
			total_cost += row.total_cost
		self.total_bags = total_bags
		self.total_kgs  = total_kgs
		self.total_cost = total_cost

	def fetch_warehouse_from_crop(self):
		if self.crop and not self.warehouse:
			self.warehouse = frappe.db.get_value("Poultry Crop", self.crop, "warehouse")


def on_submit(doc, method):
	"""Generate a reference number to acknowledge the feed purchase is recorded."""
	ref = f"FEED-REC-{doc.name}"
	frappe.db.set_value("Feed Purchase Entry", doc.name, "stock_entry_reference", ref)
	frappe.msgprint(
		f"Feed purchase recorded. Reference: {ref}",
		alert=True
	)


def on_cancel(doc, method):
	frappe.db.set_value("Feed Purchase Entry", doc.name, "stock_entry_reference", "")
