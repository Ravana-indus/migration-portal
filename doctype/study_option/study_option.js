// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Study Option", {
	refresh(frm) {
		// Client-side logic for Study Option form
	},

	estimated_living_cost(frm) {
		// Show/hide living cost period if cost is entered
		frm.toggle_display("living_cost_period", frm.doc.estimated_living_cost > 0);
		frm.toggle_reqd("living_cost_period", frm.doc.estimated_living_cost > 0);
	},

	scholarship_available(frm) {
		// Show/hide scholarship details based on checkbox
		frm.toggle_display("scholarship_details", frm.doc.scholarship_available == 1);
	}
});

// Child Table Script (Study Option Image)
/*
frappe.ui.form.on("Study Option Image", {
	image(frm, cdt, cdn) {
		// Maybe set a caption based on filename?
	}
});
*/ 