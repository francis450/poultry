frappe.ui.form.on("Flock Daily Record", {

	onload: function(frm) {
		if (frm.is_new()) {
			frm.set_value("date", frappe.datetime.get_today());
		}
	},

	crop: function(frm) {
		if (!frm.doc.crop) return;

		frappe.db.get_doc("Poultry Crop", frm.doc.crop).then(crop => {
			let placement = frappe.datetime.str_to_obj(crop.placement_date);
			let today     = frappe.datetime.str_to_obj(frm.doc.date || frappe.datetime.get_today());
			let day_age   = frappe.datetime.get_diff(today, placement) + 1;

			frm.set_value("day_age", day_age);
			frm.set_value("opening_stock", crop.current_stock || crop.chicks_received);
		});
	},

	date: function(frm) {
		if (!frm.doc.crop || !frm.doc.date) return;

		frappe.db.get_value("Poultry Crop", frm.doc.crop, "placement_date").then(r => {
			let placement = frappe.datetime.str_to_obj(r.message.placement_date);
			let selected  = frappe.datetime.str_to_obj(frm.doc.date);
			let day_age   = frappe.datetime.get_diff(selected, placement) + 1;
			frm.set_value("day_age", day_age);
		});
	},

	day_age: function(frm) {
		if (!frm.doc.day_age) return;

		let day  = frm.doc.day_age;
		let week = Math.ceil(day / 7);
		frm.set_value("week_number", week);

		// Auto-populate feed and body-weight standards for this day
		frappe.call({
			method: "poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.get_standards_for_day",
			args: { day_age: day },
			callback: function(r) {
				if (r.message) {
					frm.set_value("feed_std_gms", r.message.feed_std_gms);
					if (frm.doc.is_weigh_day) {
						frm.set_value("bwt_std_gms", r.message.bwt_std_gms);
					}
				}
			}
		});

		// Fetch previous day's closing stock as today's opening stock
		if (frm.doc.crop && day > 1) {
			frappe.call({
				method: "poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.get_previous_closing_stock",
				args: { crop: frm.doc.crop, day_age: day },
				callback: function(r) {
					if (r.message !== null && r.message !== undefined) {
						frm.set_value("opening_stock", r.message);
					}
				}
			});
		}
	},

	mortality:     function(frm) { calculate_stock(frm); },
	opening_stock: function(frm) { calculate_stock(frm); },

	feed_in_kg:   function(frm) { calculate_feed_variance(frm); },
	feed_std_gms: function(frm) { calculate_std_total(frm); },

	bwt_actual_gms: function(frm) {
		frm.set_value("bwt_variance_gms",
			(frm.doc.bwt_actual_gms || 0) - (frm.doc.bwt_std_gms || 0)
		);
	},
	bwt_std_gms: function(frm) {
		frm.set_value("bwt_variance_gms",
			(frm.doc.bwt_actual_gms || 0) - (frm.doc.bwt_std_gms || 0)
		);
	},

	is_weigh_day: function(frm) {
		if (!frm.doc.is_weigh_day) {
			frm.set_value("bwt_actual_gms", 0);
			frm.set_value("bwt_variance_gms", 0);
		}
	}
});

function calculate_stock(frm) {
	let closing = (frm.doc.opening_stock || 0) - (frm.doc.mortality || 0);
	frm.set_value("closing_stock", closing);

	if (frm.doc.opening_stock > 0) {
		let pct = ((frm.doc.mortality || 0) / frm.doc.opening_stock * 100).toFixed(2);
		frm.set_value("mortality_pct", parseFloat(pct));

		if (parseFloat(pct) > 1.0) {
			frm.dashboard.add_comment(
				`Mortality today is ${pct}% — above 1% threshold. Please investigate.`,
				"red", true
			);
		}
	}

	calculate_std_total(frm);
}

function calculate_std_total(frm) {
	if (frm.doc.feed_std_gms && frm.doc.closing_stock) {
		let std_kg = (frm.doc.feed_std_gms * frm.doc.closing_stock) / 1000;
		frm.set_value("std_total_kg", parseFloat(std_kg.toFixed(3)));
		calculate_feed_variance(frm);
	}
}

function calculate_feed_variance(frm) {
	let variance = (frm.doc.feed_in_kg || 0) - (frm.doc.std_total_kg || 0);
	frm.set_value("feed_variance_kg", parseFloat(variance.toFixed(3)));
}
