import frappe
from frappe.utils import add_days, today


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


def create_demo_lifecycle_data():
	"""
	Seed a realistic demo lifecycle across Active, Slaughter, and Closed crops
	so the Poultry workspace cards and charts have data to render.
	"""
	company = get_company()
	warehouses = {
		"belmonte": frappe.db.get_value(
			"Warehouse", {"warehouse_name": "Belmonte Farm Store", "company": company}, "name"
		),
		"paul": frappe.db.get_value(
			"Warehouse", {"warehouse_name": "Paul Farm Store", "company": company}, "name"
		),
	}

	configs = [
		{
			"crop_number": 201,
			"farm_name": "Demo Active Farm",
			"farm_code": "DEMA",
			"warehouse": warehouses["belmonte"],
			"placement_date": add_days(today(), -9),
			"chicks_received": 300,
			"chick_cost_per_unit": 78,
			"daily_records": build_daily_rows(10, 300, default_feed=6.5),
			"target_status": "Active",
		},
		{
			"crop_number": 202,
			"farm_name": "Demo Slaughter Farm",
			"farm_code": "DEMS",
			"warehouse": warehouses["paul"],
			"placement_date": add_days(today(), -39),
			"chicks_received": 280,
			"chick_cost_per_unit": 80,
			"daily_records": build_daily_rows(40, 280, default_feed=9.0),
			"feed_purchases": [
				{
					"purchase_date": add_days(today(), -30),
					"supplier": "Demo Feed Supplier",
					"feed_items": [
						{"feed_type": "C1 Grower", "no_of_bags": 12, "pack_weight_kg": 50, "price_per_bag": 2450},
						{"feed_type": "C2 Grower", "no_of_bags": 10, "pack_weight_kg": 50, "price_per_bag": 2550},
					],
				}
			],
			"collection_date": add_days(today(), -2),
			"collection_details": [
				{"weight_band": "Below 1.6 KG", "no_of_birds": 45, "average_weight_kg": 1.55, "price_per_kg": 180},
				{"weight_band": "1.6 to 1.8 KG", "no_of_birds": 80, "average_weight_kg": 1.72, "price_per_kg": 186},
				{"weight_band": "Above 1.8 KG", "no_of_birds": 110, "average_weight_kg": 1.92, "price_per_kg": 192},
			],
			"target_status": "Slaughter",
		},
		{
			"crop_number": 203,
			"farm_name": "Demo Closed Farm",
			"farm_code": "DEMC",
			"warehouse": warehouses["belmonte"],
			"placement_date": add_days(today(), -46),
			"chicks_received": 260,
			"chick_cost_per_unit": 77,
			"daily_records": build_daily_rows(42, 260, default_feed=8.2),
			"feed_purchases": [
				{
					"purchase_date": add_days(today(), -38),
					"supplier": "Demo Feed Supplier",
					"feed_items": [
						{"feed_type": "Pre-Starter", "no_of_bags": 6, "pack_weight_kg": 50, "price_per_bag": 2300},
						{"feed_type": "C1 Grower", "no_of_bags": 8, "pack_weight_kg": 50, "price_per_bag": 2450},
					],
				},
				{
					"purchase_date": add_days(today(), -24),
					"supplier": "Demo Feed Supplier",
					"feed_items": [
						{"feed_type": "C2 Grower", "no_of_bags": 8, "pack_weight_kg": 50, "price_per_bag": 2550},
						{"feed_type": "C3 Grower", "no_of_bags": 10, "pack_weight_kg": 50, "price_per_bag": 2600},
					],
				},
				{
					"purchase_date": add_days(today(), -10),
					"supplier": "Demo Feed Supplier",
					"feed_items": [
						{"feed_type": "Finisher", "no_of_bags": 9, "pack_weight_kg": 50, "price_per_bag": 2700},
					],
				},
			],
			"collection_date": add_days(today(), -4),
			"collection_details": [
				{"weight_band": "Below 1.6 KG", "no_of_birds": 30, "average_weight_kg": 1.52, "price_per_kg": 178},
				{"weight_band": "1.6 to 1.8 KG", "no_of_birds": 70, "average_weight_kg": 1.73, "price_per_kg": 185},
				{"weight_band": "Above 1.8 KG", "no_of_birds": 120, "average_weight_kg": 1.96, "price_per_kg": 193},
			],
			"target_status": "Closed",
		},
	]

	for config in configs:
		if frappe.db.exists("Poultry Crop", {"crop_number": config["crop_number"], "farm_code": config["farm_code"]}):
			print(f"  Demo crop already exists: {config['farm_code']} / {config['crop_number']}")
			continue

		crop = frappe.get_doc(
			{
				"doctype": "Poultry Crop",
				"crop_number": config["crop_number"],
				"farm_name": config["farm_name"],
				"farm_code": config["farm_code"],
				"warehouse": config["warehouse"],
				"placement_date": config["placement_date"],
				"chicks_received": config["chicks_received"],
				"chick_cost_per_unit": config["chick_cost_per_unit"],
				"remarks": "Demo lifecycle seed data for Poultry workspace verification.",
			}
		)
		crop.insert(ignore_permissions=True)
		crop.activate_crop()
		print(f"  Created demo crop: {crop.name}")

		create_demo_daily_records(crop.name, config["placement_date"], config["daily_records"])
		refresh_crop_stats(crop.name)

		for purchase in config.get("feed_purchases", []):
			create_demo_feed_purchase(crop.name, purchase)

		if config["target_status"] in {"Slaughter", "Closed"}:
			crop.reload()
			crop.start_slaughter()
			create_demo_bird_collection(crop.name, config["collection_date"], config["collection_details"])

		if config["target_status"] == "Closed":
			crop.reload()
			crop.close_crop()
		else:
			refresh_crop_stats(crop.name)

	frappe.db.commit()
	print("  Demo lifecycle data ready.")


def build_daily_rows(days, opening_stock, default_feed):
	rows = []
	current_stock = opening_stock
	for day_age in range(1, days + 1):
		mortality = 2 if day_age % 9 == 0 else 1 if day_age % 4 == 0 else 0
		feed_in_kg = round(default_feed + (day_age * 0.35), 2)
		is_weigh_day = 1 if day_age in {7, 14, 21, 28, 35, 42} else 0
		bwt_actual_gms = 0
		if is_weigh_day:
			standards = frappe.get_attr(
				"poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.get_standards_for_day"
			)(day_age)
			bwt_actual_gms = (standards.get("bwt_std_gms") or 0) - 15

		rows.append(
			{
				"day_age": day_age,
				"opening_stock": current_stock,
				"mortality": mortality,
				"feed_in_kg": feed_in_kg,
				"is_weigh_day": is_weigh_day,
				"bwt_actual_gms": bwt_actual_gms,
			}
		)
		current_stock -= mortality

	return rows


def create_demo_daily_records(crop_name, placement_date, rows):
	get_standards = frappe.get_attr(
		"poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.get_standards_for_day"
	)
	for row in rows:
		record_date = add_days(placement_date, row["day_age"] - 1)
		if frappe.db.exists("Flock Daily Record", {"crop": crop_name, "day_age": row["day_age"]}):
			continue

		standards = get_standards(row["day_age"]) or {}
		doc = frappe.get_doc(
			{
				"doctype": "Flock Daily Record",
				"crop": crop_name,
				"date": record_date,
				"day_age": row["day_age"],
				"opening_stock": row["opening_stock"],
				"mortality": row["mortality"],
				"feed_std_gms": standards.get("feed_std_gms"),
				"feed_in_kg": row["feed_in_kg"],
				"is_weigh_day": row["is_weigh_day"],
				"bwt_std_gms": standards.get("bwt_std_gms") if row["is_weigh_day"] else 0,
				"bwt_actual_gms": row["bwt_actual_gms"] if row["is_weigh_day"] else 0,
			}
		)
		doc.insert(ignore_permissions=True)


def create_demo_feed_purchase(crop_name, payload):
	if frappe.db.exists(
		"Feed Purchase Entry",
		{"crop": crop_name, "purchase_date": payload["purchase_date"], "supplier": payload["supplier"]},
	):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Feed Purchase Entry",
			"crop": crop_name,
			"purchase_date": payload["purchase_date"],
			"supplier": payload["supplier"],
			"remarks": "Demo lifecycle seed",
			"feed_items": payload["feed_items"],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()


def create_demo_bird_collection(crop_name, collection_date, details):
	if frappe.db.exists("Bird Collection Entry", {"crop": crop_name, "collection_date": collection_date}):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Bird Collection Entry",
			"crop": crop_name,
			"collection_date": collection_date,
			"remarks": "Demo lifecycle seed",
			"collection_details": details,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()


def refresh_crop_stats(crop_name):
	frappe.get_attr(
		"poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.update_crop_stats"
	)(crop_name)
