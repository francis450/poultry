import datetime

import frappe
from frappe.model.document import Document


class CropVaccinationLog(Document):
    pass


def create_vaccination_log(crop_name):
	"""Auto-create Crop Vaccination Log from Vaccination Schedule Template when crop is activated."""
	if frappe.db.exists("Crop Vaccination Log", {"crop": crop_name}):
		return

	crop = frappe.get_doc("Poultry Crop", crop_name)
	placement_date = frappe.utils.getdate(crop.placement_date)

	if not frappe.db.exists("DocType", "Vaccination Schedule Template"):
		return

	template = frappe.get_doc("Vaccination Schedule Template")
	if not template.schedule_rows:
		return

	log = frappe.new_doc("Crop Vaccination Log")
	log.crop = crop_name
	log.placement_date = placement_date

	for row in template.schedule_rows:
		scheduled_date = placement_date + datetime.timedelta(days=row.day_number - 1)
		log.append("vaccinations", {
			"day_number": row.day_number,
			"vaccine_name": row.vaccine_name,
			"scheduled_date": scheduled_date,
			"status": "Pending",
		})

	log.insert(ignore_permissions=True)
	frappe.msgprint(
		f"Vaccination Schedule created for {crop_name}.",
		alert=True
	)
