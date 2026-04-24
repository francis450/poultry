frappe.ui.form.on("Feed Purchase Entry", {

	crop: function(frm) {
		if (!frm.doc.crop) return;
		frappe.db.get_value("Poultry Crop", frm.doc.crop, "warehouse").then(r => {
			if (r.message && r.message.warehouse) {
				frm.set_value("warehouse", r.message.warehouse);
			}
		});
	},

	refresh: function(frm) {
		if (frm.doc.stock_entry_reference) {
			frm.dashboard.add_comment(
				`Feed purchase recorded. Reference: ${frm.doc.stock_entry_reference}`,
				"blue", false
			);
		}
	}
});

frappe.ui.form.on("Feed Purchase Item", {

	no_of_bags:     function(frm, cdt, cdn) { calculate_item_totals(frm, cdt, cdn); },
	pack_weight_kg: function(frm, cdt, cdn) { calculate_item_totals(frm, cdt, cdn); },
	price_per_bag:  function(frm, cdt, cdn) { calculate_item_totals(frm, cdt, cdn); },

	feed_items_remove: function(frm) { calculate_purchase_totals(frm); }
});

function calculate_item_totals(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total_kgs  = (row.no_of_bags || 0) * (row.pack_weight_kg || 0);
	let total_cost = (row.no_of_bags || 0) * (row.price_per_bag  || 0);

	frappe.model.set_value(cdt, cdn, "total_kgs",  total_kgs);
	frappe.model.set_value(cdt, cdn, "total_cost", total_cost);

	calculate_purchase_totals(frm);
}

function calculate_purchase_totals(frm) {
	let total_bags = 0, total_kgs = 0, total_cost = 0;

	(frm.doc.feed_items || []).forEach(row => {
		total_bags += (row.no_of_bags  || 0);
		total_kgs  += (row.total_kgs   || 0);
		total_cost += (row.total_cost  || 0);
	});

	frm.set_value("total_bags", total_bags);
	frm.set_value("total_kgs",  total_kgs);
	frm.set_value("total_cost", total_cost);
}
