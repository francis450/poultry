frappe.ui.form.on("Crop Consumable Sheet", {

	crop: function(frm) {
		if (!frm.doc.crop) return;

		// Auto-fetch warehouse from crop
		frappe.db.get_value("Poultry Crop", frm.doc.crop, "warehouse", function(r) {
			if (r && r.warehouse) {
				frm.set_value("warehouse", r.warehouse);
			}
		});

		// Auto-populate all catalogue rows on a new form when no real items exist yet
		// (Frappe auto-inserts one blank row into required child tables — ignore it)
		if (!frm.is_new()) return;
		let has_real_rows = (frm.doc.items || []).some(r => r.item);
		if (has_real_rows) return;

		frappe.call({
			method: "poultry_farm.poultry.doctype.crop_consumable_sheet.crop_consumable_sheet.get_catalogue_with_carryover",
			args: { crop: frm.doc.crop },
			callback: function(r) {
				if (!r.message || !r.message.length) return;
				r.message.forEach(function(ci) {
					let row = frm.add_child("items");
					row.item               = ci.item;
					row.item_name          = ci.item_name;
					row.unit               = ci.unit;
					row.qty_brought_forward = ci.qty_brought_forward;
				});
				frm.refresh_field("items");
				recalc_total(frm);

				let has_carryover = r.message.some(ci => ci.qty_brought_forward > 0);
				if (has_carryover) {
					frappe.show_alert({
						message: __("All items loaded. Brought Forward pulled from warehouse stock."),
						indicator: "green"
					});
				} else {
					frappe.show_alert({
						message: __("All items loaded. No prior stock found — Brought Forward set to zero."),
						indicator: "blue"
					});
				}
			}
		});
	},

	refresh: function(frm) {
		if (frm.doc.docstatus !== 0) return;

		// Button: add any catalogue items not yet in this sheet (e.g. newly added items)
		frm.add_custom_button(__("Add Missing Items from Catalogue"), function() {
			let existing = (frm.doc.items || []).map(r => r.item).filter(Boolean);
			frappe.call({
				method: "poultry_farm.poultry.doctype.crop_consumable_sheet.crop_consumable_sheet.get_missing_catalogue_items",
				args: { crop: frm.doc.crop, existing_items: JSON.stringify(existing) },
				callback: function(r) {
					if (!r.message || !r.message.length) {
						frappe.msgprint(__("All catalogue items are already in this sheet."));
						return;
					}
					r.message.forEach(function(ci) {
						let row = frm.add_child("items");
						row.item               = ci.item;
						row.unit               = ci.unit;
						row.qty_brought_forward = ci.qty_brought_forward;
					});
					frm.refresh_field("items");
					recalc_total(frm);
					frappe.show_alert({
						message: __("{0} new item(s) added.", [r.message.length]),
						indicator: "green"
					});
				}
			});
		});
	}
});

frappe.ui.form.on("Consumable Sheet Item", {
	qty_brought_forward: recalc_row,
	qty_purchased:       recalc_row,
	qty_used:            recalc_row,
	unit_cost:           recalc_row,
});

function recalc_row(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let in_store = (row.qty_brought_forward || 0) + (row.qty_purchased || 0);
	frappe.model.set_value(cdt, cdn, "qty_in_store",        in_store);
	frappe.model.set_value(cdt, cdn, "qty_balance",         in_store - (row.qty_used || 0));
	frappe.model.set_value(cdt, cdn, "total_purchase_cost", (row.qty_purchased || 0) * (row.unit_cost || 0));
	recalc_total(frm);
}

function recalc_total(frm) {
	let total = (frm.doc.items || []).reduce((sum, row) => sum + (row.total_purchase_cost || 0), 0);
	frm.set_value("total_cost", total);
}
