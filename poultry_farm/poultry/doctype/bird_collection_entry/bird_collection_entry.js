frappe.ui.form.on("Bird Collection Entry", {

	crop: function(frm) {
		if (!frm.doc.crop) return;
		frappe.db.get_value("Poultry Crop", frm.doc.crop, "placement_date").then(r => {
			if (r.message && r.message.placement_date) {
				let placement = frappe.datetime.str_to_obj(r.message.placement_date);
				let today     = frappe.datetime.str_to_obj(
					frm.doc.collection_date || frappe.datetime.get_today()
				);
				frm.set_value("bird_age_days", frappe.datetime.get_diff(today, placement) + 1);
			}
		});
	},

	collection_date: function(frm) {
		if (frm.doc.crop) {
			frappe.ui.form.trigger.call(frm, frm.doctype, "crop");
		}
	}
});

frappe.ui.form.on("Bird Collection Detail", {
	no_of_birds:       function(frm, cdt, cdn) { calculate_band_totals(frm, cdt, cdn); },
	average_weight_kg: function(frm, cdt, cdn) { calculate_band_totals(frm, cdt, cdn); },
	price_per_kg:      function(frm, cdt, cdn) { calculate_band_totals(frm, cdt, cdn); },
	collection_details_remove: function(frm)   { calculate_collection_summary(frm); }
});

function calculate_band_totals(frm, cdt, cdn) {
	let row          = locals[cdt][cdn];
	let total_weight = (row.no_of_birds || 0) * (row.average_weight_kg || 0);
	let total_amount = total_weight * (row.price_per_kg || 0);

	frappe.model.set_value(cdt, cdn, "total_weight_kg", parseFloat(total_weight.toFixed(2)));
	frappe.model.set_value(cdt, cdn, "total_amount",    parseFloat(total_amount.toFixed(2)));

	calculate_collection_summary(frm);
}

function calculate_collection_summary(frm) {
	let total_birds = 0, total_weight = 0, total_revenue = 0;

	(frm.doc.collection_details || []).forEach(row => {
		total_birds   += (row.no_of_birds     || 0);
		total_weight  += (row.total_weight_kg || 0);
		total_revenue += (row.total_amount    || 0);
	});

	let avg_weight    = total_birds > 0 ? total_weight  / total_birds : 0;
	let rev_per_bird  = total_birds > 0 ? total_revenue / total_birds : 0;

	frm.set_value("total_birds",       total_birds);
	frm.set_value("total_weight_kg",   parseFloat(total_weight.toFixed(2)));
	frm.set_value("average_weight_kg", parseFloat(avg_weight.toFixed(3)));
	frm.set_value("total_revenue",     parseFloat(total_revenue.toFixed(2)));
	frm.set_value("revenue_per_bird",  parseFloat(rev_per_bird.toFixed(2)));
}
