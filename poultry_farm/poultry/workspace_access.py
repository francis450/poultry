import json
from pathlib import Path

import frappe


POULTRY_WORKSPACE = "Poultry"
POULTRY_ROLES = ["System Manager", "Farm Manager", "Store Manager", "Farm Director"]
ADMIN_ONLY_ROLE = ["System Manager"]


def sync_workspace_roles():
	"""Keep this dedicated site focused on the Poultry workspace for poultry roles."""
	sync_poultry_report_json()
	sync_poultry_dashboard_components()
	sync_poultry_workspace_layout()

	for workspace_name in frappe.get_all("Workspace", pluck="name"):
		workspace = frappe.get_doc("Workspace", workspace_name)
		target_roles = POULTRY_ROLES if workspace.name == POULTRY_WORKSPACE else ADMIN_ONLY_ROLE

		current_roles = sorted(role.role for role in workspace.roles)
		if current_roles == sorted(target_roles):
			continue

		workspace.roles = []
		for role in target_roles:
			workspace.append("roles", {"role": role})
		workspace.save(ignore_permissions=True)

	frappe.db.commit()


def sync_poultry_workspace_layout():
	workspace_file = Path(
		frappe.get_app_path("poultry_farm", "poultry", "workspace", "poultry", "poultry.json")
	)
	data = json.loads(workspace_file.read_text())

	workspace = frappe.get_doc("Workspace", POULTRY_WORKSPACE)
	workspace.content = data.get("content", "[]")
	workspace.public = data.get("public", 1)
	workspace.is_hidden = data.get("is_hidden", 0)
	workspace.icon = data.get("icon")
	workspace.title = data.get("title")
	workspace.label = data.get("label")

	workspace.links = []
	for link in data.get("links", []):
		workspace.append("links", link)

	workspace.shortcuts = []
	for shortcut in data.get("shortcuts", []):
		workspace.append("shortcuts", shortcut)

	workspace.charts = []
	for chart in data.get("charts", []):
		workspace.append("charts", chart)

	workspace.number_cards = []
	for number_card in data.get("number_cards", []):
		workspace.append("number_cards", number_card)

	workspace.save(ignore_permissions=True)


def sync_poultry_report_json():
	report_root = Path(frappe.get_app_path("poultry_farm", "poultry", "report"))
	for report_file in report_root.glob("*/*.json"):
		data = json.loads(report_file.read_text())
		report_name = data.get("name") or data.get("report_name")
		if not report_name or not frappe.db.exists("Report", report_name):
			continue

		frappe.db.set_value("Report", report_name, "json", report_file.read_text(), update_modified=False)


def sync_poultry_dashboard_components():
	_sync_json_backed_docs("number_card", "Number Card", "name")
	_sync_json_backed_docs("dashboard_chart", "Dashboard Chart", "name")


def _sync_json_backed_docs(folder, doctype, name_key):
	root = Path(frappe.get_app_path("poultry_farm", "poultry", folder))
	if not root.exists():
		return
	columns = set(frappe.db.get_table_columns(doctype))

	for json_file in root.glob("*/*.json"):
		data = json.loads(json_file.read_text())
		docname = data.get(name_key)
		if not docname or not frappe.db.exists(doctype, docname):
			continue

		for fieldname, value in data.items():
			if fieldname in {"doctype", "docstatus", "modified", "modified_by", "creation", "owner"}:
				continue
			if fieldname == "roles":
				continue
			if fieldname not in columns:
				continue

			if isinstance(value, (dict, list)):
				value = json.dumps(value)

			frappe.db.set_value(doctype, docname, fieldname, value, update_modified=False)
