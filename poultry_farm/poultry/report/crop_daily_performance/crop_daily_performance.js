frappe.query_reports["Crop Daily Performance"] = {
	filters: [
		{
			fieldname: "crop",
			label: __("Poultry Crop"),
			fieldtype: "Link",
			options: "Poultry Crop",
			reqd: 1,
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
			default: frappe.datetime.get_today(),
		},
	],
};
