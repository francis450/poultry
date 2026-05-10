frappe.ui.form.on("Crop Treatment Entry", {

	crop: function(frm) {
		calculate_day_age(frm);
	},

	treatment_date: function(frm) {
		calculate_day_age(frm);
	},

	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.follow_up_required && frm.doc.follow_up_date) {
			const days_until = frappe.datetime.get_diff(frm.doc.follow_up_date, frappe.datetime.get_today());
			if (days_until < 0) {
				frm.dashboard.add_indicator(__("Follow-up Overdue"), "red");
			} else if (days_until === 0) {
				frm.dashboard.add_indicator(__("Follow-up Due Today"), "orange");
			} else {
				frm.dashboard.add_indicator(__("Follow-up in {0} day(s)", [days_until]), "blue");
			}
		}

		if (frm.doc.outcome === "Mortality Increase") {
			frm.dashboard.add_indicator(__("Mortality Increase Reported"), "red");
		}
	}
});

frappe.ui.form.on("Treatment Item", {
	quantity_used: function(frm, cdt, cdn) {
		recalc_row(frm, cdt, cdn);
	},
	unit_cost: function(frm, cdt, cdn) {
		recalc_row(frm, cdt, cdn);
	},
	treatment_items_remove: function(frm) {
		recalc_total(frm);
	}
});

function recalc_row(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const total = (row.quantity_used || 0) * (row.unit_cost || 0);
	frappe.model.set_value(cdt, cdn, "total_cost", total);
	recalc_total(frm);
}

function recalc_total(frm) {
	let grand_total = 0;
	(frm.doc.treatment_items || []).forEach(row => {
		grand_total += row.total_cost || 0;
	});
	frm.set_value("treatment_cost", grand_total);
}

function calculate_day_age(frm) {
	if (!frm.doc.crop || !frm.doc.treatment_date) return;

	frappe.db.get_value("Poultry Crop", frm.doc.crop, "placement_date", function(d) {
		if (!d || !d.placement_date) return;
		const diff = frappe.datetime.get_diff(frm.doc.treatment_date, d.placement_date) + 1;
		frm.set_value("day_age", Math.max(diff, 1));
	});
}
