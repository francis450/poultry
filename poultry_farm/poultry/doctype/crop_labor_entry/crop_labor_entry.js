frappe.ui.form.on("Crop Labor Entry", {
	refresh: function(frm) {
		if (frm.doc.docstatus === 0) {
			frm.set_query("crop", function() {
				return { filters: { status: ["in", ["Active", "Slaughter"]] } };
			});
		}
	}
});

frappe.ui.form.on("Crop Labor Item", {
	num_workers: recalc_labor_row,
	num_days: recalc_labor_row,
	rate_per_day: recalc_labor_row,
});

function recalc_labor_row(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total = (row.num_workers || 0) * (row.num_days || 0) * (row.rate_per_day || 0);
	frappe.model.set_value(cdt, cdn, "total_cost", total);
	let grand_total = (frm.doc.labor_items || []).reduce((s, r) => s + (r.total_cost || 0), 0);
	frm.set_value("total_cost", grand_total);
}
