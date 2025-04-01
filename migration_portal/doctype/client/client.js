// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Client", {
	refresh: function(frm) {
		// Custom logic for the Client form refresh event
		console.log("Client form refreshed for:", frm.doc.name);

		// Example: Add a button to view the linked Inquiry
		if (frm.doc.linked_inquiry) {
			frm.add_custom_button(__("View Inquiry"), function() {
				frappe.set_route("Form", "Inquiry", frm.doc.linked_inquiry);
			}, "Go");
		} else {
            frm.remove_custom_button("View Inquiry");
        }

		// Add other refresh logic here, e.g., filtering child table fields
	},

	validate: function(frm) {
		// Example validation: Check if passport expiry is before date of birth
		if (frm.doc.date_of_birth && frm.doc.passport_expiry) {
			if (frappe.datetime.get_diff(frm.doc.passport_expiry, frm.doc.date_of_birth) < 0) {
				frappe.throw(__("Passport expiry date cannot be before Date of Birth"));
			}
		}
	},

	// Example: Trigger on field change
	// primary_consultant: function(frm) {
	// 	 if(frm.doc.primary_consultant) {
	// 		 frappe.msgprint(`Primary consultant changed to ${frm.doc.primary_consultant}`)
	// 	 }
	// }

	// Add more event handlers as needed (e.g., validate, onload)
}); 