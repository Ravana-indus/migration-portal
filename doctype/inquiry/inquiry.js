// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Inquiry", {
	refresh: function(frm) {
		// Show link to client if converted
		if (frm.doc.linked_client) {
			frm.add_custom_button(__("View Client"), function() {
				frappe.set_route("Form", "Client", frm.doc.linked_client);
			}, "Go");
		} else {
            frm.remove_custom_button("View Client");
        }
        
        // Apply initial filters on load
        frm.trigger("destination_country");
	},

	inquiry_source: function(frm) {
		// No visibility toggles needed
	},

	service_type: function(frm) {
		// Show/hide relevant sections based on service type
		frm.toggle_display("study_options_section", frm.doc.service_type === "Study");
		frm.toggle_display("study_options", frm.doc.service_type === "Study");
		frm.toggle_display("preferred_field_of_study", frm.doc.service_type === "Study");
		frm.toggle_display("work_options_section", frm.doc.service_type === "Work");
		frm.toggle_display("work_options", frm.doc.service_type === "Work");
		frm.toggle_display("preferred_field_of_work", frm.doc.service_type === "Work");
		frm.toggle_display("length_of_work_experience", frm.doc.service_type === "Work");
	}
});

// Setup filters for child tables when a new row is added 
frappe.ui.form.on("Inquiry Study Option", {
    study_options_add: function(frm, cdt, cdn) {
        frm.trigger("destination_country"); 
    }
});

frappe.ui.form.on("Inquiry Work Option", {
    work_options_add: function(frm, cdt, cdn) {
        frm.trigger("destination_country");
    }
});

// Example for Child Table script (if needed later)
/*
frappe.ui.form.on("Inquiry Study Option", {
	field_to_validate(frm, cdt, cdn) {
		// Add validation for child table rows
	}
});
*/ 