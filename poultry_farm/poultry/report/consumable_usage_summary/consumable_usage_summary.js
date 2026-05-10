frappe.query_reports["Consumable Usage Summary"] = {
	filters: [
		{
			fieldname: "crop",
			label: __("Crop"),
			fieldtype: "Link",
			options: "Poultry Crop",
		},
		{
			fieldname: "category",
			label: __("Category"),
			fieldtype: "Select",
			options: "\nVeterinary\nBiosecurity\nWater Treatment\nFuel & Heating\nBedding\nCleaning\nMiscellaneous",
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
