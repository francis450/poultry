frappe.ui.form.on("Poultry Crop", {

	onload: function(frm) {
		set_crop_title(frm);
	},

	farm_name:   function(frm) { set_crop_title(frm); },
	crop_number: function(frm) { set_crop_title(frm); },

	chicks_received:         function(frm) { calculate_chick_cost(frm); calculate_adjusted_stock(frm); },
	chick_cost_per_unit:     function(frm) { calculate_chick_cost(frm); },
	birds_dead_on_arrival:   function(frm) { calculate_adjusted_stock(frm); },

	refresh: function(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Activate Crop"), function() {
				frappe.confirm(
					`Activate Crop ${frm.doc.name}? Chicks have been received.`,
					() => frm.call("activate_crop").then(() => frm.reload_doc())
				);
			}, __("Actions")).addClass("btn-primary");
		}

		if (frm.doc.status === "Active") {
			frm.add_custom_button(__("New Daily Record"), function() {
				frappe.new_doc("Flock Daily Record", { crop: frm.doc.name });
			}, __("Create"));

			frm.add_custom_button(__("New Consumable Sheet"), function() {
				frappe.new_doc("Crop Consumable Sheet", { crop: frm.doc.name });
			}, __("Create"));

			frm.add_custom_button(__("New Labor Entry"), function() {
				frappe.new_doc("Crop Labor Entry", { crop: frm.doc.name });
			}, __("Create"));

			frm.add_custom_button(__("New Treatment Entry"), function() {
				frappe.new_doc("Crop Treatment Entry", { crop: frm.doc.name });
			}, __("Create"));

			frm.add_custom_button(__("Vaccination Log"), function() {
				frappe.set_route("List", "Crop Vaccination Log", { crop: frm.doc.name });
			}, __("View"));

			frm.add_custom_button(__("Treatment Log"), function() {
				frappe.set_route("List", "Crop Treatment Entry", { crop: frm.doc.name });
			}, __("View"));

			frm.add_custom_button(__("New Feed Purchase"), function() {
				frappe.new_doc("Feed Purchase Entry", {
					crop: frm.doc.name,
					warehouse: frm.doc.warehouse
				});
			}, __("Create"));

			frm.add_custom_button(__("Start Slaughter"), function() {
				frm.call("start_slaughter").then(() => frm.reload_doc());
			}, __("Actions"));
		}

		if (frm.doc.status === "Slaughter") {
			frm.add_custom_button(__("New Collection Entry"), function() {
				frappe.new_doc("Bird Collection Entry", { crop: frm.doc.name });
			}, __("Create")).addClass("btn-primary");

			frm.add_custom_button(__("Close Crop"), function() {
				frappe.confirm(
					"Close this crop? This will generate the Financial Summary and lock all records.",
					() => frm.call("close_crop").then(() => frm.reload_doc())
				);
			}, __("Actions"));
		}

		if (frm.doc.status === "Closed") {
			frm.add_custom_button(__("View P&L Summary"), function() {
				frappe.set_route("query-report", "Crop Profit Loss", { crop: frm.doc.name });
			}, __("Reports"));
		}

		// Performance indicators
		if (frm.doc.total_mortality > 0) {
			frm.dashboard.add_indicator(
				`Mortality: ${frm.doc.mortality_pct}%`,
				frm.doc.mortality_pct > 5 ? "red" : frm.doc.mortality_pct > 2 ? "orange" : "green"
			);
		}
		if (frm.doc.fcr) {
			frm.dashboard.add_indicator(
				`FCR: ${frm.doc.fcr}`,
				frm.doc.fcr > 2.2 ? "red" : frm.doc.fcr > 1.8 ? "orange" : "green"
			);
		}
	}
});

function set_crop_title(frm) {
	if (frm.doc.farm_name && frm.doc.crop_number) {
		frm.set_value("crop_title", `${frm.doc.farm_name} — Crop ${frm.doc.crop_number}`);
	}
}

function calculate_chick_cost(frm) {
	let total = (frm.doc.chicks_received || 0) * (frm.doc.chick_cost_per_unit || 0);
	frm.set_value("total_chick_cost", total);
}

function calculate_adjusted_stock(frm) {
	let adjusted = (frm.doc.chicks_received || 0) - (frm.doc.birds_dead_on_arrival || 0);
	frm.set_value("adjusted_opening_stock", adjusted);
}
