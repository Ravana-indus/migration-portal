frappe.ui.form.on("Inquiry", {
	refresh: function(frm) {
		// Button logic is now handled by Workflow Actions
		// We can remove the old button adding logic if it exists.
		// if (frm.doc.status == "Under Review" && !frm.doc.linked_client && !frm.is_new()) {
		// 	frm.add_custom_button(__("Convert to Client"), function() {
		// 		frappe.call({
		// 			method: "migration_portal.migration_portal.doctype.inquiry.inquiry.convert_to_client",
		// 			args: {
		// 				inquiry_name: frm.doc.name
		// 			},
		// 			callback: function(r) {
		// 				if (r.message) {
		// 					frm.reload_doc();
		// 					frappe.set_route("Form", "Client", r.message);
		// 				}
		// 			}
		// 		});
		// 	});
		// } else {
        //     // Clear button if status is not 'Under Review' or already converted
        //     frm.remove_custom_button("Convert to Client");
        // }

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
		// Make FlyOut ID mandatory if source is FlyOut
		frm.toggle_reqd("flyout_inquiry_id", frm.doc.inquiry_source === "FlyOut");
	},

	service_type: function(frm) {
		// Show/hide relevant sections based on service type
		frm.toggle_display("study_options_section", frm.doc.service_type === "Study");
		frm.toggle_display("study_options", frm.doc.service_type === "Study");
		frm.toggle_display("work_options_section", frm.doc.service_type === "Work");
		frm.toggle_display("work_options", frm.doc.service_type === "Work");
	},
    
    destination_country: function(frm) {
        // Clear child tables if country changes?
        // frm.clear_table("study_options");
        // frm.clear_table("work_options");
        // frm.refresh_field("study_options");
        // frm.refresh_field("work_options");
        
        // Apply filters to child table link fields
        // Note: This relies on the child table fields being rendered. 
        // It might need adjustment if tables are initially hidden.
        frm.set_query("study_option", "study_options", function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            let filters = {};
            if (doc.destination_country) {
                filters.country = doc.destination_country;
            }
            // Add other filters if needed
            // filters.level = ["in", ["Bachelor's Degree", "Master's Degree"]]; 
            return {
                filters: filters
            };
        });
        
        frm.set_query("work_option", "work_options", function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            let filters = {};
            if (doc.destination_country) {
                filters.country = doc.destination_country;
            }
            // Add other filters if needed
            // filters.required_experience_years = ["<=", 5];
            return {
                filters: filters
            };
        });
    }
});

// Setup filters for child tables when a new row is added 
// (needed because set_query on parent field only affects existing rows initially)
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