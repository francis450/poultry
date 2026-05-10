frappe.query_reports["Vaccination Compliance Report"] = {
	filters: [
		{
			fieldname: "crop",
			label: __("Crop"),
			fieldtype: "Link",
			options: "Poultry Crop",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nPending\nDone\nOverdue\nSkipped",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};
