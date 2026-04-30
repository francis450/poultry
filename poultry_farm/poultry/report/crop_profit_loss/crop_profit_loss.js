frappe.query_reports["Crop Profit Loss"] = {
	filters: [
		{
			fieldname: "farm_name",
			label: __("Farm"),
			fieldtype: "Data",
		},
		{
			fieldname: "status",
			label: __("Crop Status"),
			fieldtype: "Select",
			options: "\nActive\nSlaughter\nClosed",
		},
		{
			fieldname: "from_date",
			label: __("Placement From"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Placement To"),
			fieldtype: "Date",
		},
		{
			fieldname: "crop",
			label: __("Poultry Crop"),
			fieldtype: "Link",
			options: "Poultry Crop",
		},
	],
};
