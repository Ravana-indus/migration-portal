frappe.ui.form.on("Migration Payment", {
	refresh: function(frm) {
		// Set query for reference name based on reference type
		frm.set_query("reference_name", function() {
			return {
				query: "frappe.client.query",
				filters: {
					doctype: frm.doc.reference_type
					// Add more filters if needed, e.g., status != 'Cancelled'
				}
			};
		});
	},

	reference_type: function(frm) {
		// Clear reference name when type changes
		frm.set_value("reference_name", null);
		frm.refresh_field("reference_name");
	},

	payment_method: function(frm) {
		// Show/hide fields based on payment method
		frm.toggle_display("bank_name", ["Bank Transfer", "Cheque"].includes(frm.doc.payment_method));
		frm.toggle_display("cheque_number", frm.doc.payment_method === "Cheque");
	}
}); 