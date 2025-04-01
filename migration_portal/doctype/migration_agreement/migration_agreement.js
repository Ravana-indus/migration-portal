frappe.ui.form.on("Migration Agreement", {
	refresh: function(frm) {
		// Set query for party based on party type
		frm.set_query("client", function() {
			return {
				filters: {
					// Add any relevant filters for selecting clients
				}
			};
		});
		frm.set_query("inquiry", function() {
			return {
				filters: {
					// Add any relevant filters for selecting inquiries
					status: ["!=", "Converted"] // Example: Don't link to converted inquiries
				}
			};
		});
	},

	party_type: function(frm) {
		// Clear the other party link when type changes
		if (frm.doc.party_type === "Client") {
			frm.set_value("inquiry", null);
		} else if (frm.doc.party_type === "Inquiry") {
			frm.set_value("client", null);
		}
		frm.refresh_field("client");
		frm.refresh_field("inquiry");
	},

	company_signatory: function(frm) {
		// Fetch designation when signatory changes (handled server-side in validate)
		// If you want immediate feedback, you could do a client-side call here too
		// but server-side validation ensures it happens on save.
		frm.set_value("signatory_designation", null); // Clear designation
	}
}); 