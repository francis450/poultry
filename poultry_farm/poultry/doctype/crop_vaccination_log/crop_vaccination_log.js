frappe.ui.form.on("Crop Vaccination Log", {
	refresh: function(frm) {
		(frm.doc.vaccinations || []).forEach(function(row) {
			if (row.status === "Overdue") {
				frm.dashboard.add_indicator(
					__("Day {0} {1}: Overdue", [row.day_number, row.vaccine_name]),
					"red"
				);
			}
		});
	}
});
