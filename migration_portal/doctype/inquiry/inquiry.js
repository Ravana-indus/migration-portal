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
	}
}); 