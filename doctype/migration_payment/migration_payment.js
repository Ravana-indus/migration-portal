// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Migration Payment", {
	refresh(frm) {
		// Client-side logic for payments
	},

	reference_type(frm) {
		// Clear the reference name when type changes
		frm.set_value("reference_name", null);
	},

	payment_method(frm) {
		// Show/hide bank/cheque details based on method
		let show_bank = ['Bank Transfer', 'Cheque'].includes(frm.doc.payment_method);
		let show_cheque = frm.doc.payment_method === 'Cheque';
		frm.toggle_display("bank_name", show_bank);
		frm.toggle_display("cheque_number", show_cheque);
	}
}); 