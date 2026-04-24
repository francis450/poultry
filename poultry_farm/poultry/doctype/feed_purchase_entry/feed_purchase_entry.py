import frappe
from frappe.model.document import Document


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


FEED_ITEM_MAP = {
	"Pre-Starter": "FEED-PRESTARTER",
	"C1 Grower": "FEED-C1",
	"C2 Grower": "FEED-C2",
	"C3 Grower": "FEED-C3",
	"Finisher": "FEED-FINISHER",
}


def get_company_for_entry(doc):
	company = None
	if doc.warehouse:
		company = frappe.db.get_value("Warehouse", doc.warehouse, "company")

	if not company and frappe.db.exists("DocType", "Global Defaults"):
		company = frappe.db.get_single_value("Global Defaults", "default_company")

	if not company:
		companies = frappe.get_all("Company", pluck="name", limit=1)
		company = companies[0] if companies else None

	if not company:
		frappe.throw("No Company found to create Stock Entry.")

	return company


def on_submit(doc, method):
	"""Create a Stock Entry (Material Receipt) for all feed items purchased."""
	company = get_company_for_entry(doc)

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Receipt"
	se.company = company
	se.posting_date = doc.purchase_date
	se.remarks = f"Feed purchase for crop {doc.crop} - {doc.name}"

	for row in doc.feed_items:
		item_code = FEED_ITEM_MAP.get(row.feed_type)
		if not item_code:
			frappe.throw(f"No stock item mapping found for feed type {row.feed_type}.")
		if not frappe.db.exists("Item", item_code):
			frappe.throw(f"Feed item {item_code} does not exist.")
		if not row.total_kgs:
			continue

		basic_rate = (row.price_per_bag or 0) / (row.pack_weight_kg or 1)
		se.append(
			"items",
			{
				"item_code": item_code,
				"qty": row.total_kgs,
				"uom": "KG",
				"stock_uom": "KG",
				"t_warehouse": doc.warehouse,
				"basic_rate": basic_rate,
				"conversion_factor": 1,
			},
		)

	if not se.items:
		frappe.throw("No feed items with quantity were provided for stock receipt.")

	se.insert(ignore_permissions=True)
	se.submit()

	frappe.db.set_value("Feed Purchase Entry", doc.name, "stock_entry_reference", se.name)
	frappe.msgprint(f"Stock Entry {se.name} created for feed receipt.", alert=True)


def on_cancel(doc, method):
	if doc.stock_entry_reference and frappe.db.exists("Stock Entry", doc.stock_entry_reference):
		se = frappe.get_doc("Stock Entry", doc.stock_entry_reference)
		if se.docstatus == 1:
			se.cancel()
			frappe.msgprint(f"Stock Entry {se.name} cancelled.", alert=True)

	frappe.db.set_value("Feed Purchase Entry", doc.name, "stock_entry_reference", "")
