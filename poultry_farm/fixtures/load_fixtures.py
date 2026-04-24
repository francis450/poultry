import frappe


def run():
	create_item_groups()
	create_uoms()
	create_feed_items()
	create_warehouse_group()
	create_roles()
	create_feed_standards()
	frappe.db.commit()
	print("Poultry Farm fixtures loaded successfully.")


def get_company():
	company = None
	if frappe.db.exists("DocType", "Global Defaults"):
		company = frappe.db.get_single_value("Global Defaults", "default_company")

	if not company:
		companies = frappe.get_all("Company", pluck="name", limit=1)
		company = companies[0] if companies else None

	return company


def create_item_groups():
	groups = [
		{"item_group_name": "Poultry Feed", "parent_item_group": "All Item Groups"},
		{"item_group_name": "Live Birds", "parent_item_group": "All Item Groups"},
		{"item_group_name": "Veterinary Inputs", "parent_item_group": "All Item Groups"},
	]

	for group in groups:
		if not frappe.db.exists("Item Group", group["item_group_name"]):
			frappe.get_doc({"doctype": "Item Group", **group}).insert(ignore_permissions=True)
			print(f"  Created Item Group: {group['item_group_name']}")
		else:
			print(f"  Item Group already exists: {group['item_group_name']}")


def create_uoms():
	uoms = ["KG", "Bag", "Bird", "Gram"]
	for uom in uoms:
		if not frappe.db.exists("UOM", uom):
			frappe.get_doc({"doctype": "UOM", "uom_name": uom}).insert(ignore_permissions=True)
			print(f"  Created UOM: {uom}")
		else:
			print(f"  UOM already exists: {uom}")


def create_feed_items():
	items = [
		{
			"item_code": "FEED-PRESTARTER",
			"item_name": "Pre-Starter Feed (PBS)",
			"item_group": "Poultry Feed",
			"stock_uom": "KG",
			"is_stock_item": 1,
			"description": "Pre-starter broiler feed. Used Days 1-7.",
		},
		{
			"item_code": "FEED-C1",
			"item_name": "C1 Grower Feed",
			"item_group": "Poultry Feed",
			"stock_uom": "KG",
			"is_stock_item": 1,
			"description": "C1 grower broiler feed. Used Days 8-14.",
		},
		{
			"item_code": "FEED-C2",
			"item_name": "C2 Grower Feed",
			"item_group": "Poultry Feed",
			"stock_uom": "KG",
			"is_stock_item": 1,
			"description": "C2 grower broiler feed. Used Days 15-21.",
		},
		{
			"item_code": "FEED-C3",
			"item_name": "C3 Grower Feed",
			"item_group": "Poultry Feed",
			"stock_uom": "KG",
			"is_stock_item": 1,
			"description": "C3 grower broiler feed. Used Days 22-35.",
		},
		{
			"item_code": "FEED-FINISHER",
			"item_name": "Finisher Pellets",
			"item_group": "Poultry Feed",
			"stock_uom": "KG",
			"is_stock_item": 1,
			"description": "Finisher pellets. Used Days 36-42.",
		},
	]

	for item in items:
		if not frappe.db.exists("Item", item["item_code"]):
			frappe.get_doc({"doctype": "Item", **item}).insert(ignore_permissions=True)
			print(f"  Created Item: {item['item_code']}")
		else:
			print(f"  Item already exists: {item['item_code']}")


def create_warehouse_group():
	company = get_company()
	if not company:
		print("  No default company set. Skipping warehouse creation.")
		return

	group_doc = frappe.db.get_value(
		"Warehouse", {"warehouse_name": "Anirita Farms", "is_group": 1}, "name"
	)
	if not group_doc:
		group_doc = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": "Anirita Farms",
				"is_group": 1,
				"company": company,
			}
		).insert(ignore_permissions=True).name
		print(f"  Created Warehouse Group: {group_doc}")
	else:
		print(f"  Warehouse Group already exists: {group_doc}")

	for warehouse_name in ["Belmonte Farm Store", "Paul Farm Store"]:
		warehouse_doc = frappe.db.get_value(
			"Warehouse", {"warehouse_name": warehouse_name, "company": company}, "name"
		)
		if not warehouse_doc:
			warehouse_doc = frappe.get_doc(
				{
					"doctype": "Warehouse",
					"warehouse_name": warehouse_name,
					"parent_warehouse": group_doc,
					"company": company,
				}
			).insert(ignore_permissions=True).name
			print(f"  Created Warehouse: {warehouse_doc}")
		else:
			print(f"  Warehouse already exists: {warehouse_doc}")


# ─── ROLES ───────────────────────────────────────────────────────────────────

def create_roles():
	roles = ["Farm Manager", "Store Manager", "Farm Director"]
	for role_name in roles:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)
			print(f"  Created Role: {role_name}")
		else:
			print(f"  Role already exists: {role_name}")


# ─── FEED STANDARD CONFIG ────────────────────────────────────────────────────

def create_feed_standards():
	"""
	Populates Feed Standard Config (Single) with the age-to-feed-standard
	mapping from the paper forms. feed_type matches the Select options on
	Feed Standard Row (Pre-Starter, C1 Grower, etc.).
	"""
	standards = [
		# (day_from, day_to, feed_std_gms, bwt_std_gms, feed_type)
		(1,  7,  20,  165,  "Pre-Starter"),
		(8,  14, 47,  420,  "C1 Grower"),
		(15, 21, 71,  765,  "C2 Grower"),
		(22, 28, 115, 1250, "C3 Grower"),
		(29, 35, 152, 1850, "C3 Grower"),
		(36, 42, 175, 2200, "Finisher"),
	]

	config = frappe.get_doc("Feed Standard Config")
	config.standards = []
	for row in standards:
		config.append("standards", {
			"day_from":     row[0],
			"day_to":       row[1],
			"feed_std_gms": row[2],
			"bwt_std_gms":  row[3],
			"feed_type":    row[4],
		})
	config.save(ignore_permissions=True)
	print(f"  Feed Standard Config populated with {len(standards)} rows.")


# ─── HISTORICAL CROP 14 ──────────────────────────────────────────────────────

def create_crop_14():
	"""
	Bootstrap Crop 14 (Paul Farm Belmonte) as a closed historical record.
	Chicks received: 5858, Placement date: 17/02/2023.
	Run this separately after all doctypes are migrated.
	"""
	if frappe.db.exists("Poultry Crop", {"crop_number": 14, "farm_code": "PAUL"}):
		print("  Crop 14 already exists. Skipping.")
		return

	company = get_company()
	warehouse = frappe.db.get_value(
		"Warehouse", {"warehouse_name": "Paul Farm Store", "company": company}, "name"
	) or "Paul Farm Store"

	crop = frappe.get_doc({
		"doctype":           "Poultry Crop",
		"crop_number":       14,
		"farm_name":         "Paul Farm Belmonte",
		"farm_code":         "PAUL",
		"status":            "Closed",
		"placement_date":    "2023-02-17",
		"chicks_received":   5858,
		"chick_cost_per_unit": 75,
		"total_chick_cost":  439350,
		"warehouse":         warehouse,
		"total_mortality":   99,
		"total_birds_collected": 5740,
		"remarks":           "Historical crop migrated from paper records.",
	})
	crop.insert(ignore_permissions=True)
	frappe.db.commit()
	print(f"  Created Crop 14: {crop.name}")
