# 04_CLIENT_SCRIPTS.md — JavaScript Client Scripts

Create each script via ERPNext UI: **Settings → Customize Form → Client Script**
OR place in the corresponding `{doctype}.js` file in the doctype folder.

---

## 1. Flock Daily Record — `flock_daily_record.js`

```javascript
frappe.ui.form.on("Flock Daily Record", {

    // ── On form load ────────────────────────────────────────────────────────
    onload: function(frm) {
        if (frm.is_new()) {
            frm.set_value("date", frappe.datetime.get_today());
        }
    },

    // ── Crop selected: fetch opening stock and placement date ───────────────
    crop: function(frm) {
        if (!frm.doc.crop) return;

        frappe.db.get_doc("Poultry Crop", frm.doc.crop).then(crop => {
            // Calculate day age from placement date
            let placement = frappe.datetime.str_to_obj(crop.placement_date);
            let today     = frappe.datetime.str_to_obj(frm.doc.date || frappe.datetime.get_today());
            let day_age   = frappe.datetime.get_diff(today, placement) + 1;

            frm.set_value("day_age", day_age);
            frm.set_value("opening_stock", crop.current_stock || crop.chicks_received);
        });
    },

    // ── Date changed: recalculate day age ──────────────────────────────────
    date: function(frm) {
        if (!frm.doc.crop || !frm.doc.date) return;

        frappe.db.get_value("Poultry Crop", frm.doc.crop, "placement_date").then(r => {
            let placement = frappe.datetime.str_to_obj(r.message.placement_date);
            let selected  = frappe.datetime.str_to_obj(frm.doc.date);
            let day_age   = frappe.datetime.get_diff(selected, placement) + 1;
            frm.set_value("day_age", day_age);
        });
    },

    // ── Day age changed: set week number and auto-populate standards ────────
    day_age: function(frm) {
        if (!frm.doc.day_age) return;

        let day  = frm.doc.day_age;
        let week = Math.ceil(day / 7);
        frm.set_value("week_number", week);

        // Fetch feed standard for this day from Feed Standard Config
        frappe.call({
            method: "anirita_poultry.poultry.doctype.flock_daily_record.flock_daily_record.get_standards_for_day",
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

        // Fetch previous day's closing stock as opening stock
        if (frm.doc.crop && day > 1) {
            frappe.call({
                method: "anirita_poultry.poultry.doctype.flock_daily_record.flock_daily_record.get_previous_closing_stock",
                args: { crop: frm.doc.crop, day_age: day },
                callback: function(r) {
                    if (r.message !== null) {
                        frm.set_value("opening_stock", r.message);
                    }
                }
            });
        }
    },

    // ── Mortality entered: recalculate closing stock and mortality % ────────
    mortality: function(frm) {
        calculate_stock(frm);
    },

    opening_stock: function(frm) {
        calculate_stock(frm);
    },

    // ── Feed in KG entered: calculate variance ──────────────────────────────
    feed_in_kg: function(frm) {
        calculate_feed_variance(frm);
    },

    feed_std_gms: function(frm) {
        calculate_std_total(frm);
    },

    // ── Body weight entered: calculate variance ─────────────────────────────
    bwt_actual_gms: function(frm) {
        let variance = (frm.doc.bwt_actual_gms || 0) - (frm.doc.bwt_std_gms || 0);
        frm.set_value("bwt_variance_gms", variance);
    },

    bwt_std_gms: function(frm) {
        let variance = (frm.doc.bwt_actual_gms || 0) - (frm.doc.bwt_std_gms || 0);
        frm.set_value("bwt_variance_gms", variance);
    },

    // ── Weigh day toggle ────────────────────────────────────────────────────
    is_weigh_day: function(frm) {
        if (!frm.doc.is_weigh_day) {
            frm.set_value("bwt_actual_gms", 0);
            frm.set_value("bwt_variance_gms", 0);
        }
    }
});

// ── Helpers ─────────────────────────────────────────────────────────────────

function calculate_stock(frm) {
    let closing = (frm.doc.opening_stock || 0) - (frm.doc.mortality || 0);
    frm.set_value("closing_stock", closing);

    if (frm.doc.opening_stock > 0) {
        let pct = ((frm.doc.mortality || 0) / frm.doc.opening_stock * 100).toFixed(2);
        frm.set_value("mortality_pct", parseFloat(pct));

        // Visual alert if mortality % exceeds 1%
        if (parseFloat(pct) > 1.0) {
            frm.dashboard.add_comment(
                `⚠️ Mortality today is ${pct}% — above 1% threshold. Please investigate.`,
                "red", true
            );
        }
    }

    calculate_std_total(frm);
}

function calculate_std_total(frm) {
    if (frm.doc.feed_std_gms && frm.doc.closing_stock) {
        let std_kg = (frm.doc.feed_std_gms * frm.doc.closing_stock) / 1000;
        frm.set_value("std_total_kg", std_kg.toFixed(2));
        calculate_feed_variance(frm);
    }
}

function calculate_feed_variance(frm) {
    let variance = (frm.doc.feed_in_kg || 0) - (frm.doc.std_total_kg || 0);
    frm.set_value("feed_variance_kg", parseFloat(variance.toFixed(2)));
}
```

---

## 2. Feed Purchase Entry — `feed_purchase_entry.js`

```javascript
frappe.ui.form.on("Feed Purchase Entry", {

    crop: function(frm) {
        if (!frm.doc.crop) return;
        frappe.db.get_value("Poultry Crop", frm.doc.crop, "warehouse").then(r => {
            frm.set_value("warehouse", r.message.warehouse);
        });
    },

    refresh: function(frm) {
        if (frm.doc.stock_entry_reference) {
            frm.add_custom_button("View Stock Entry", function() {
                frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry_reference);
            }, "Links");
        }
    }
});

frappe.ui.form.on("Feed Purchase Item", {

    no_of_bags: function(frm, cdt, cdn) {
        calculate_item_totals(frm, cdt, cdn);
    },

    pack_weight_kg: function(frm, cdt, cdn) {
        calculate_item_totals(frm, cdt, cdn);
    },

    price_per_bag: function(frm, cdt, cdn) {
        calculate_item_totals(frm, cdt, cdn);
    },

    feed_items_remove: function(frm) {
        calculate_purchase_totals(frm);
    }
});

function calculate_item_totals(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let total_kgs  = (row.no_of_bags || 0) * (row.pack_weight_kg || 0);
    let total_cost = (row.no_of_bags || 0) * (row.price_per_bag || 0);

    frappe.model.set_value(cdt, cdn, "total_kgs",  total_kgs);
    frappe.model.set_value(cdt, cdn, "total_cost", total_cost);

    calculate_purchase_totals(frm);
}

function calculate_purchase_totals(frm) {
    let total_bags = 0, total_kgs = 0, total_cost = 0;

    (frm.doc.feed_items || []).forEach(row => {
        total_bags += (row.no_of_bags  || 0);
        total_kgs  += (row.total_kgs   || 0);
        total_cost += (row.total_cost  || 0);
    });

    frm.set_value("total_bags", total_bags);
    frm.set_value("total_kgs",  total_kgs);
    frm.set_value("total_cost", total_cost);
}
```

---

## 3. Bird Collection Entry — `bird_collection_entry.js`

```javascript
frappe.ui.form.on("Bird Collection Entry", {

    crop: function(frm) {
        if (!frm.doc.crop) return;
        frappe.db.get_value("Poultry Crop", frm.doc.crop, "placement_date").then(r => {
            if (r.message.placement_date) {
                let placement = frappe.datetime.str_to_obj(r.message.placement_date);
                let today     = frappe.datetime.str_to_obj(frm.doc.collection_date || frappe.datetime.get_today());
                let age       = frappe.datetime.get_diff(today, placement) + 1;
                frm.set_value("bird_age_days", age);
            }
        });
    },

    collection_date: function(frm) {
        // Recalculate bird age if crop and date both set
        if (frm.doc.crop) frappe.ui.form.trigger.call(frm, frm.doctype, "crop");
    }
});

frappe.ui.form.on("Bird Collection Detail", {

    no_of_birds: function(frm, cdt, cdn) { calculate_band_totals(frm, cdt, cdn); },
    average_weight_kg: function(frm, cdt, cdn) { calculate_band_totals(frm, cdt, cdn); },
    price_per_kg: function(frm, cdt, cdn) { calculate_band_totals(frm, cdt, cdn); },
    collection_details_remove: function(frm) { calculate_collection_summary(frm); }
});

function calculate_band_totals(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let total_weight = (row.no_of_birds || 0) * (row.average_weight_kg || 0);
    let total_amount = total_weight * (row.price_per_kg || 0);

    frappe.model.set_value(cdt, cdn, "total_weight_kg", parseFloat(total_weight.toFixed(2)));
    frappe.model.set_value(cdt, cdn, "total_amount",    parseFloat(total_amount.toFixed(2)));

    calculate_collection_summary(frm);
}

function calculate_collection_summary(frm) {
    let total_birds = 0, total_weight = 0, total_revenue = 0;

    (frm.doc.collection_details || []).forEach(row => {
        total_birds   += (row.no_of_birds    || 0);
        total_weight  += (row.total_weight_kg || 0);
        total_revenue += (row.total_amount    || 0);
    });

    let avg_weight     = total_birds > 0 ? total_weight / total_birds : 0;
    let revenue_p_bird = total_birds > 0 ? total_revenue / total_birds : 0;

    frm.set_value("total_birds",      total_birds);
    frm.set_value("total_weight_kg",  parseFloat(total_weight.toFixed(2)));
    frm.set_value("average_weight_kg",parseFloat(avg_weight.toFixed(3)));
    frm.set_value("total_revenue",    parseFloat(total_revenue.toFixed(2)));
    frm.set_value("revenue_per_bird", parseFloat(revenue_p_bird.toFixed(2)));
}
```

---

## 4. Poultry Crop — `poultry_crop.js`

```javascript
frappe.ui.form.on("Poultry Crop", {

    onload: function(frm) {
        // Auto-set crop title
        set_crop_title(frm);
    },

    farm_name: function(frm) { set_crop_title(frm); },
    crop_number: function(frm) { set_crop_title(frm); },

    chicks_received: function(frm) { calculate_chick_cost(frm); },
    chick_cost_per_unit: function(frm) { calculate_chick_cost(frm); },

    refresh: function(frm) {
        // Action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === "Draft") {
                frm.add_custom_button("Activate Crop", function() {
                    frappe.confirm(
                        `Activate Crop ${frm.doc.name}? Chicks have been received.`,
                        () => {
                            frm.call("activate_crop").then(() => frm.reload_doc());
                        }
                    );
                }, "Actions").addClass("btn-primary");
            }

            if (frm.doc.status === "Active") {
                frm.add_custom_button("New Daily Record", function() {
                    frappe.new_doc("Flock Daily Record", { crop: frm.doc.name });
                }, "Create");

                frm.add_custom_button("New Feed Purchase", function() {
                    frappe.new_doc("Feed Purchase Entry", {
                        crop: frm.doc.name,
                        warehouse: frm.doc.warehouse
                    });
                }, "Create");

                frm.add_custom_button("Start Slaughter", function() {
                    frm.call("start_slaughter").then(() => frm.reload_doc());
                }, "Actions");
            }

            if (frm.doc.status === "Slaughter") {
                frm.add_custom_button("New Collection Entry", function() {
                    frappe.new_doc("Bird Collection Entry", { crop: frm.doc.name });
                }, "Create").addClass("btn-primary");

                frm.add_custom_button("Close Crop", function() {
                    frappe.confirm(
                        "Close this crop? This will generate the Financial Summary and lock all records.",
                        () => {
                            frm.call("close_crop").then(() => frm.reload_doc());
                        }
                    );
                }, "Actions");
            }

            if (frm.doc.status === "Closed") {
                frm.add_custom_button("View P&L Summary", function() {
                    frappe.set_route("query-report", "Crop Profit Loss", {
                        crop: frm.doc.name
                    });
                }, "Reports");
            }

            // Performance indicators dashboard
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
```
