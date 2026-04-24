frappe.query_reports["Feed Consumption Report"] = {
	filters: [
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
		{
			fieldname: "crop",
			label: __("Poultry Crop"),
			fieldtype: "Link",
			options: "Poultry Crop",
		},
		{
			fieldname: "status",
			label: __("Crop Status"),
			fieldtype: "Select",
			options: ["", "Active", "Slaughter", "Closed"],
		},
		{
			fieldname: "week_number",
			label: __("Week Number"),
			fieldtype: "Int",
		},
	],
};
