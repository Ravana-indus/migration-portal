// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("FlyOut Account Settings", {
	refresh(frm) {
		// Logic specific to the settings page
	},

	enable_sync(frm) {
		// Show/hide sync frequency based on enable_sync checkbox
		frm.toggle_display("sync_frequency", frm.doc.enable_sync == 1);
	}
}); 