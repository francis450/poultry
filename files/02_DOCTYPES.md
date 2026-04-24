# 02_DOCTYPES.md — Complete Doctype Specifications

All doctypes belong to module `Poultry` inside app `anirita_poultry`.
Create each as a JSON file in its folder then run `bench migrate`.

---

## 1. Feed Purchase Item (Child Table)

**File:** `poultry/doctype/feed_purchase_item/feed_purchase_item.json`

```json
{
  "name": "Feed Purchase Item",
  "doctype": "DocType",
  "module": "Poultry",
  "istable": 1,
  "editable_grid": 1,
  "fields": [
    {
      "fieldname": "feed_type",
      "fieldtype": "Link",
      "label": "Feed Type",
      "options": "Item",
      "in_list_view": 1,
      "reqd": 1,
      "get_query": "return { filters: { item_group: 'Poultry Feed' } }"
    },
    {
      "fieldname": "no_of_bags",
      "fieldtype": "Int",
      "label": "No. of Bags",
      "in_list_view": 1,
      "reqd": 1
    },
    {
      "fieldname": "pack_weight_kg",
      "fieldtype": "Float",
      "label": "Pack Weight (KG)",
      "in_list_view": 1,
      "default": "50",
      "description": "Weight per bag in KG"
    },
    {
      "fieldname": "total_kgs",
      "fieldtype": "Float",
      "label": "Total KGs",
      "in_list_view": 1,
      "read_only": 1,
      "description": "Auto-calculated: No. of Bags × Pack Weight"
    },
    {
      "fieldname": "price_per_bag",
      "fieldtype": "Currency",
      "label": "Price per Bag (KES)",
      "options": "KES"
    },
    {
      "fieldname": "total_cost",
      "fieldtype": "Currency",
      "label": "Total Cost (KES)",
      "options": "KES",
      "read_only": 1,
      "description": "Auto-calculated: No. of Bags × Price per Bag"
    }
  ]
}
```

---

## 2. Bird Collection Detail (Child Table)

**File:** `poultry/doctype/bird_collection_detail/bird_collection_detail.json`

```json
{
  "name": "Bird Collection Detail",
  "doctype": "DocType",
  "module": "Poultry",
  "istable": 1,
  "editable_grid": 1,
  "fields": [
    {
      "fieldname": "weight_band",
      "fieldtype": "Select",
      "label": "Weight Band",
      "options": "Below 1.6 KG\n1.6 to 1.8 KG\nAbove 1.8 KG",
      "in_list_view": 1,
      "reqd": 1
    },
    {
      "fieldname": "no_of_birds",
      "fieldtype": "Int",
      "label": "No. of Birds",
      "in_list_view": 1,
      "reqd": 1
    },
    {
      "fieldname": "average_weight_kg",
      "fieldtype": "Float",
      "label": "Avg Weight (KG)",
      "in_list_view": 1
    },
    {
      "fieldname": "price_per_kg",
      "fieldtype": "Currency",
      "label": "Price/KG (KES)",
      "options": "KES",
      "in_list_view": 1
    },
    {
      "fieldname": "total_weight_kg",
      "fieldtype": "Float",
      "label": "Total Weight (KG)",
      "read_only": 1
    },
    {
      "fieldname": "total_amount",
      "fieldtype": "Currency",
      "label": "Total Amount (KES)",
      "options": "KES",
      "read_only": 1
    }
  ]
}
```

---

## 3. Poultry Crop (Master)

**File:** `poultry/doctype/poultry_crop/poultry_crop.json`

```json
{
  "name": "Poultry Crop",
  "doctype": "DocType",
  "module": "Poultry",
  "naming_rule": "Expression",
  "autoname": "format:CROP-{farm_code}-{placement_date}-{####}",
  "title_field": "crop_title",
  "track_changes": 1,
  "fields": [
    {
      "fieldname": "crop_title",
      "fieldtype": "Data",
      "label": "Crop Title",
      "read_only": 1,
      "description": "Auto-set: Farm + Crop Number"
    },
    {
      "fieldname": "crop_number",
      "fieldtype": "Int",
      "label": "Crop Number",
      "reqd": 1,
      "description": "Sequential crop number for this farm e.g. 14"
    },
    {
      "fieldname": "col_break_1",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "status",
      "fieldtype": "Select",
      "label": "Status",
      "options": "Draft\nActive\nSlaughter\nClosed",
      "default": "Draft",
      "reqd": 1,
      "in_list_view": 1
    },
    {
      "fieldname": "section_farm",
      "fieldtype": "Section Break",
      "label": "Farm Details"
    },
    {
      "fieldname": "farm_name",
      "fieldtype": "Data",
      "label": "Farm Name",
      "reqd": 1,
      "description": "e.g. Paul Farm Belmonte"
    },
    {
      "fieldname": "farm_code",
      "fieldtype": "Data",
      "label": "Farm Code",
      "reqd": 1,
      "description": "Short code used in naming e.g. PAUL"
    },
    {
      "fieldname": "col_break_2",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "warehouse",
      "fieldtype": "Link",
      "label": "Farm Warehouse",
      "options": "Warehouse",
      "reqd": 1,
      "description": "Feed stock will be received and issued from this warehouse"
    },
    {
      "fieldname": "contract_farmer",
      "fieldtype": "Link",
      "label": "Contract Farmer",
      "options": "Supplier",
      "description": "The farmer running this crop under contract"
    },
    {
      "fieldname": "section_chick",
      "fieldtype": "Section Break",
      "label": "Chick Details"
    },
    {
      "fieldname": "placement_date",
      "fieldtype": "Date",
      "label": "Placement Date",
      "reqd": 1,
      "description": "Date chicks were received. Day 1 of the crop."
    },
    {
      "fieldname": "chicks_received",
      "fieldtype": "Int",
      "label": "Chicks Received",
      "reqd": 1
    },
    {
      "fieldname": "col_break_3",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "chick_supplier",
      "fieldtype": "Link",
      "label": "Chick Supplier",
      "options": "Supplier"
    },
    {
      "fieldname": "chick_cost_per_unit",
      "fieldtype": "Currency",
      "label": "Chick Cost / Unit (KES)",
      "options": "KES"
    },
    {
      "fieldname": "total_chick_cost",
      "fieldtype": "Currency",
      "label": "Total Chick Cost (KES)",
      "options": "KES",
      "read_only": 1,
      "description": "Chicks Received × Cost per Unit"
    },
    {
      "fieldname": "section_targets",
      "fieldtype": "Section Break",
      "label": "Target & Performance (Auto-updated)"
    },
    {
      "fieldname": "current_stock",
      "fieldtype": "Int",
      "label": "Current Stock",
      "read_only": 1,
      "description": "Live birds as of last Flock Daily Record"
    },
    {
      "fieldname": "total_mortality",
      "fieldtype": "Int",
      "label": "Total Mortality",
      "read_only": 1
    },
    {
      "fieldname": "mortality_pct",
      "fieldtype": "Percent",
      "label": "Mortality %",
      "read_only": 1
    },
    {
      "fieldname": "col_break_4",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "total_feed_consumed_kg",
      "fieldtype": "Float",
      "label": "Total Feed Consumed (KG)",
      "read_only": 1
    },
    {
      "fieldname": "fcr",
      "fieldtype": "Float",
      "label": "FCR (Feed Conversion Ratio)",
      "read_only": 1,
      "description": "Total Feed KG ÷ Total Live Weight KG"
    },
    {
      "fieldname": "last_recorded_weight_gms",
      "fieldtype": "Float",
      "label": "Last Recorded Weight (GMS)",
      "read_only": 1
    },
    {
      "fieldname": "section_closure",
      "fieldtype": "Section Break",
      "label": "Closure"
    },
    {
      "fieldname": "expected_slaughter_date",
      "fieldtype": "Date",
      "label": "Expected Slaughter Date"
    },
    {
      "fieldname": "actual_slaughter_date",
      "fieldtype": "Date",
      "label": "Actual Slaughter Date",
      "read_only": 1
    },
    {
      "fieldname": "col_break_5",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "total_birds_collected",
      "fieldtype": "Int",
      "label": "Total Birds Collected",
      "read_only": 1
    },
    {
      "fieldname": "total_revenue",
      "fieldtype": "Currency",
      "label": "Total Revenue (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "remarks",
      "fieldtype": "Small Text",
      "label": "Remarks"
    }
  ],
  "actions": [
    {
      "action": "Activate Crop",
      "action_label": "Activate Crop"
    },
    {
      "action": "Close Crop",
      "action_label": "Close Crop"
    }
  ]
}
```

---

## 4. Flock Daily Record

**File:** `poultry/doctype/flock_daily_record/flock_daily_record.json`

```json
{
  "name": "Flock Daily Record",
  "doctype": "DocType",
  "module": "Poultry",
  "naming_rule": "Expression",
  "autoname": "format:FDR-{crop}-{day_age:03d}",
  "title_field": "crop",
  "track_changes": 1,
  "fields": [
    {
      "fieldname": "crop",
      "fieldtype": "Link",
      "label": "Poultry Crop",
      "options": "Poultry Crop",
      "reqd": 1,
      "in_list_view": 1,
      "get_query": "return { filters: { status: ['in', ['Active', 'Slaughter']] } }"
    },
    {
      "fieldname": "date",
      "fieldtype": "Date",
      "label": "Date",
      "reqd": 1,
      "default": "Today",
      "in_list_view": 1
    },
    {
      "fieldname": "day_age",
      "fieldtype": "Int",
      "label": "Day Age",
      "reqd": 1,
      "in_list_view": 1,
      "description": "Day 1 = placement day"
    },
    {
      "fieldname": "col_break_1",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "week_number",
      "fieldtype": "Int",
      "label": "Week Number",
      "read_only": 1,
      "description": "Auto-calculated from day_age"
    },
    {
      "fieldname": "section_stock",
      "fieldtype": "Section Break",
      "label": "Stock"
    },
    {
      "fieldname": "opening_stock",
      "fieldtype": "Int",
      "label": "Opening Stock",
      "reqd": 1,
      "description": "Auto-fetched from previous day closing stock"
    },
    {
      "fieldname": "mortality",
      "fieldtype": "Int",
      "label": "Mortality",
      "default": 0
    },
    {
      "fieldname": "col_break_2",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "closing_stock",
      "fieldtype": "Int",
      "label": "Closing Stock",
      "read_only": 1,
      "description": "Opening Stock − Mortality"
    },
    {
      "fieldname": "mortality_pct",
      "fieldtype": "Percent",
      "label": "Mortality %",
      "read_only": 1
    },
    {
      "fieldname": "section_feed",
      "fieldtype": "Section Break",
      "label": "Feed"
    },
    {
      "fieldname": "feed_std_gms",
      "fieldtype": "Float",
      "label": "Feed Std (GMS/bird)",
      "description": "Standard feed per bird for this age — auto-populated from Feed Standard table"
    },
    {
      "fieldname": "feed_in_kg",
      "fieldtype": "Float",
      "label": "Feed In (KG)",
      "description": "Actual feed given today in KG"
    },
    {
      "fieldname": "col_break_3",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "std_total_kg",
      "fieldtype": "Float",
      "label": "Std Total (KG)",
      "read_only": 1,
      "description": "Feed Std GMS × Closing Stock ÷ 1000"
    },
    {
      "fieldname": "feed_variance_kg",
      "fieldtype": "Float",
      "label": "Feed Variance (KG)",
      "read_only": 1,
      "description": "Feed In KG − Std Total KG. Negative = under-fed."
    },
    {
      "fieldname": "section_weight",
      "fieldtype": "Section Break",
      "label": "Body Weight"
    },
    {
      "fieldname": "is_weigh_day",
      "fieldtype": "Check",
      "label": "Weigh Day?",
      "default": 0
    },
    {
      "fieldname": "bwt_actual_gms",
      "fieldtype": "Float",
      "label": "Actual Body Weight (GMS)",
      "depends_on": "eval: doc.is_weigh_day == 1",
      "description": "Average weight of sampled birds in grams"
    },
    {
      "fieldname": "col_break_4",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "bwt_std_gms",
      "fieldtype": "Float",
      "label": "B.Wt Std (GMS)",
      "depends_on": "eval: doc.is_weigh_day == 1",
      "description": "Standard body weight for this week — auto-populated"
    },
    {
      "fieldname": "bwt_variance_gms",
      "fieldtype": "Float",
      "label": "B.Wt Variance (GMS)",
      "read_only": 1,
      "depends_on": "eval: doc.is_weigh_day == 1",
      "description": "Actual − Standard. Negative = below target."
    },
    {
      "fieldname": "section_remarks",
      "fieldtype": "Section Break",
      "label": "Remarks & Events"
    },
    {
      "fieldname": "vaccination",
      "fieldtype": "Check",
      "label": "Vaccination Given?",
      "default": 0
    },
    {
      "fieldname": "vaccination_details",
      "fieldtype": "Data",
      "label": "Vaccination Details",
      "depends_on": "eval: doc.vaccination == 1"
    },
    {
      "fieldname": "remarks",
      "fieldtype": "Small Text",
      "label": "Remarks"
    },
    {
      "fieldname": "alert_sent",
      "fieldtype": "Check",
      "label": "Mortality Alert Sent",
      "read_only": 1,
      "hidden": 1
    }
  ]
}
```

---

## 5. Feed Purchase Entry

**File:** `poultry/doctype/feed_purchase_entry/feed_purchase_entry.json`

```json
{
  "name": "Feed Purchase Entry",
  "doctype": "DocType",
  "module": "Poultry",
  "naming_rule": "Expression",
  "autoname": "format:FPE-{crop}-{####}",
  "is_submittable": 1,
  "track_changes": 1,
  "fields": [
    {
      "fieldname": "crop",
      "fieldtype": "Link",
      "label": "Poultry Crop",
      "options": "Poultry Crop",
      "reqd": 1,
      "get_query": "return { filters: { status: ['in', ['Active', 'Slaughter']] } }"
    },
    {
      "fieldname": "purchase_date",
      "fieldtype": "Date",
      "label": "Purchase Date",
      "reqd": 1,
      "default": "Today"
    },
    {
      "fieldname": "col_break_1",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "supplier",
      "fieldtype": "Link",
      "label": "Feed Supplier",
      "options": "Supplier"
    },
    {
      "fieldname": "warehouse",
      "fieldtype": "Link",
      "label": "Destination Warehouse",
      "options": "Warehouse",
      "reqd": 1,
      "description": "Auto-fetched from Poultry Crop"
    },
    {
      "fieldname": "section_items",
      "fieldtype": "Section Break",
      "label": "Feed Items"
    },
    {
      "fieldname": "feed_items",
      "fieldtype": "Table",
      "label": "Feed Items",
      "options": "Feed Purchase Item",
      "reqd": 1
    },
    {
      "fieldname": "section_totals",
      "fieldtype": "Section Break",
      "label": "Totals"
    },
    {
      "fieldname": "total_bags",
      "fieldtype": "Int",
      "label": "Total Bags",
      "read_only": 1
    },
    {
      "fieldname": "total_kgs",
      "fieldtype": "Float",
      "label": "Total KGs",
      "read_only": 1
    },
    {
      "fieldname": "col_break_totals",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "total_cost",
      "fieldtype": "Currency",
      "label": "Total Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "stock_entry_reference",
      "fieldtype": "Link",
      "label": "Stock Entry",
      "options": "Stock Entry",
      "read_only": 1,
      "description": "Auto-created on submit"
    },
    {
      "fieldname": "remarks",
      "fieldtype": "Small Text",
      "label": "Remarks"
    }
  ]
}
```

---

## 6. Bird Collection Entry

**File:** `poultry/doctype/bird_collection_entry/bird_collection_entry.json`

```json
{
  "name": "Bird Collection Entry",
  "doctype": "DocType",
  "module": "Poultry",
  "naming_rule": "Expression",
  "autoname": "format:BCE-{crop}-{####}",
  "is_submittable": 1,
  "track_changes": 1,
  "fields": [
    {
      "fieldname": "crop",
      "fieldtype": "Link",
      "label": "Poultry Crop",
      "options": "Poultry Crop",
      "reqd": 1
    },
    {
      "fieldname": "collection_date",
      "fieldtype": "Date",
      "label": "Collection Date",
      "reqd": 1,
      "default": "Today"
    },
    {
      "fieldname": "col_break_1",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "bird_age_days",
      "fieldtype": "Int",
      "label": "Bird Age (Days)",
      "description": "Auto-calculated from crop placement date"
    },
    {
      "fieldname": "collection_details",
      "fieldtype": "Table",
      "label": "Collection by Weight Band",
      "options": "Bird Collection Detail",
      "reqd": 1
    },
    {
      "fieldname": "section_summary",
      "fieldtype": "Section Break",
      "label": "Summary"
    },
    {
      "fieldname": "total_birds",
      "fieldtype": "Int",
      "label": "Total Birds Collected",
      "read_only": 1
    },
    {
      "fieldname": "total_weight_kg",
      "fieldtype": "Float",
      "label": "Total Weight (KG)",
      "read_only": 1
    },
    {
      "fieldname": "col_break_summary",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "average_weight_kg",
      "fieldtype": "Float",
      "label": "Average Weight (KG)",
      "read_only": 1
    },
    {
      "fieldname": "total_revenue",
      "fieldtype": "Currency",
      "label": "Total Revenue (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "revenue_per_bird",
      "fieldtype": "Currency",
      "label": "Revenue / Bird (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "remarks",
      "fieldtype": "Small Text",
      "label": "Remarks"
    }
  ]
}
```

---

## 7. Crop Financial Summary

**File:** `poultry/doctype/crop_financial_summary/crop_financial_summary.json`

```json
{
  "name": "Crop Financial Summary",
  "doctype": "DocType",
  "module": "Poultry",
  "naming_rule": "Expression",
  "autoname": "format:CFS-{crop}",
  "read_only_on_submit": 1,
  "fields": [
    {
      "fieldname": "crop",
      "fieldtype": "Link",
      "label": "Poultry Crop",
      "options": "Poultry Crop",
      "reqd": 1,
      "read_only": 1
    },
    {
      "fieldname": "generated_date",
      "fieldtype": "Date",
      "label": "Generated On",
      "read_only": 1
    },
    {
      "fieldname": "section_input_costs",
      "fieldtype": "Section Break",
      "label": "Input Costs"
    },
    {
      "fieldname": "chick_cost",
      "fieldtype": "Currency",
      "label": "Total Chick Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "feed_cost_prestarter",
      "fieldtype": "Currency",
      "label": "Pre-Starter Feed Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "feed_cost_c1",
      "fieldtype": "Currency",
      "label": "C1 Grower Feed Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "feed_cost_c2",
      "fieldtype": "Currency",
      "label": "C2 Grower Feed Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "feed_cost_c3",
      "fieldtype": "Currency",
      "label": "C3 Grower Feed Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "feed_cost_finisher",
      "fieldtype": "Currency",
      "label": "Finisher Feed Cost (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "total_feed_cost",
      "fieldtype": "Currency",
      "label": "Total Feed Cost (KES)",
      "options": "KES",
      "read_only": 1,
      "bold": 1
    },
    {
      "fieldname": "col_break_costs",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "total_mortality_birds",
      "fieldtype": "Int",
      "label": "Total Mortality (Birds)",
      "read_only": 1
    },
    {
      "fieldname": "mortality_loss_value",
      "fieldtype": "Currency",
      "label": "Mortality Loss Value (KES)",
      "options": "KES",
      "read_only": 1,
      "description": "Dead birds × chick cost per unit"
    },
    {
      "fieldname": "other_costs",
      "fieldtype": "Currency",
      "label": "Other Costs (KES)",
      "options": "KES",
      "description": "Medication, labour, utilities — enter manually"
    },
    {
      "fieldname": "cumulative_cost",
      "fieldtype": "Currency",
      "label": "Cumulative / Total Cost (KES)",
      "options": "KES",
      "read_only": 1,
      "bold": 1
    },
    {
      "fieldname": "section_revenue",
      "fieldtype": "Section Break",
      "label": "Revenue"
    },
    {
      "fieldname": "total_birds_slaughtered",
      "fieldtype": "Int",
      "label": "Total Birds Slaughtered",
      "read_only": 1
    },
    {
      "fieldname": "total_revenue",
      "fieldtype": "Currency",
      "label": "Total Revenue (KES)",
      "options": "KES",
      "read_only": 1,
      "bold": 1
    },
    {
      "fieldname": "col_break_rev",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "gross_profit",
      "fieldtype": "Currency",
      "label": "Gross Profit (KES)",
      "options": "KES",
      "read_only": 1,
      "bold": 1
    },
    {
      "fieldname": "net_profit",
      "fieldtype": "Currency",
      "label": "Net Profit (KES)",
      "options": "KES",
      "read_only": 1,
      "bold": 1
    },
    {
      "fieldname": "profit_margin_pct",
      "fieldtype": "Percent",
      "label": "Profit Margin %",
      "read_only": 1
    },
    {
      "fieldname": "section_per_bird",
      "fieldtype": "Section Break",
      "label": "Per Bird Analysis"
    },
    {
      "fieldname": "cost_per_bird",
      "fieldtype": "Currency",
      "label": "Cost / Bird (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "revenue_per_bird",
      "fieldtype": "Currency",
      "label": "Revenue / Bird (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "col_break_per_bird",
      "fieldtype": "Column Break"
    },
    {
      "fieldname": "feed_cost_per_bird",
      "fieldtype": "Currency",
      "label": "Feed Cost / Bird (KES)",
      "options": "KES",
      "read_only": 1
    },
    {
      "fieldname": "fcr",
      "fieldtype": "Float",
      "label": "FCR",
      "read_only": 1,
      "description": "Feed Conversion Ratio"
    }
  ]
}
```

---

## 8. Feed Standard (Configuration Doctype)

This is a **Single** doctype used to store the age-to-feed-standard mapping.
It is read by client scripts to auto-populate `Feed Std GMS` on Flock Daily Records.

**File:** `poultry/doctype/feed_standard_config/feed_standard_config.json`

```json
{
  "name": "Feed Standard Config",
  "doctype": "DocType",
  "module": "Poultry",
  "issingle": 1,
  "fields": [
    {
      "fieldname": "standards",
      "fieldtype": "Table",
      "label": "Daily Feed Standards",
      "options": "Feed Standard Row"
    }
  ]
}
```

**Child table: Feed Standard Row**

```json
{
  "name": "Feed Standard Row",
  "doctype": "DocType",
  "module": "Poultry",
  "istable": 1,
  "fields": [
    { "fieldname": "day_from", "fieldtype": "Int", "label": "Day From", "in_list_view": 1, "reqd": 1 },
    { "fieldname": "day_to", "fieldtype": "Int", "label": "Day To", "in_list_view": 1, "reqd": 1 },
    { "fieldname": "feed_std_gms", "fieldtype": "Float", "label": "Feed Std (GMS/bird)", "in_list_view": 1, "reqd": 1 },
    { "fieldname": "bwt_std_gms", "fieldtype": "Float", "label": "B.Wt Std (GMS)", "in_list_view": 1 },
    { "fieldname": "feed_type", "fieldtype": "Link", "label": "Expected Feed Type", "options": "Item", "in_list_view": 1 }
  ]
}
```
