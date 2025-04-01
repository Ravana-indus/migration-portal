frappe.ui.form.on("Study Option", {
	refresh: function(frm) {
		// Add client-side logic if needed, e.g., dynamic filters for links
	},
	scholarship_available: function(frm) {
		// Show/hide scholarship details based on the checkbox
		frm.toggle_display("scholarship_details", frm.doc.scholarship_available);
	},
	estimated_living_cost: function(frm) {
		// Show/hide living cost period based on whether cost is entered
		frm.toggle_display("living_cost_period", frm.doc.estimated_living_cost > 0);
	}
}); 