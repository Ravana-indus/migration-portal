// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Migration Agreement", {
	refresh(frm) {
		// Add logic related to agreement status changes or template loading
	},

	agreement_template(frm) {
		// Load terms from template if selected
		if (frm.doc.agreement_template && !frm.doc.terms_and_conditions) {
			frappe.db.get_doc("Agreement Template", frm.doc.agreement_template)
				.then(template => {
					frm.set_value("terms_and_conditions", template.terms);
				});
		}
	},

	party_type(frm) {
		// Toggle visibility of client/inquiry links
		frm.toggle_display("client", frm.doc.party_type === 'Client');
		frm.toggle_display("inquiry", frm.doc.party_type === 'Inquiry');
		// Clear the other field when type changes
		if (frm.doc.party_type === 'Client') {
			frm.set_value('inquiry', null);
		} else if (frm.doc.party_type === 'Inquiry') {
			frm.set_value('client', null);
		}
	},

	status(frm) {
		// Show/hide signed date based on status
		frm.toggle_display("signed_date", frm.doc.status === 'Signed');
	}
}); 