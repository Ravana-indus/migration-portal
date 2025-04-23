// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Client", {
	refresh(frm) {
		// Client-side logic for the Client form
		// Example: Add custom buttons, filter linked documents, etc.
	},

	service_type(frm) {
		// Maybe filter playbook steps based on service type?
	},

	linked_inquiry(frm) {
		// Fetch additional details from linked inquiry if needed when it changes
		if (frm.doc.linked_inquiry) {
			// Example: frappe.db.get_value(...)
		}
	}
});

// Child table scripts if needed later (e.g., Client Document, Client Milestone)
/*
frappe.ui.form.on("Client Document", {
	status(frm, cdt, cdn) {
		// Update something based on document status change
	}
});
*/ 