frappe.ui.form.on("FlyOut Account Settings", {
	refresh: function(frm) {
		// Add buttons for testing connection or fetching account info?
		// Example:
		// frm.add_custom_button(__("Test API Connection"), function() {
		// 	frappe.call({
		// 		method: "migration_portal.migration_portal.api.flyout.test_connection", // Needs implementation
		// 		callback: function(r) {
		// 			if (r.message && r.message.success) {
		// 				frappe.msgprint(__("Connection Successful!"), { indicator: "green" });
		// 			} else {
		// 				frappe.msgprint(__("Connection Failed: {0}").format(r.message.error), { indicator: "red" });
		// 			}
		// 		}
		// 	});
		// });
	},

	enable_sync: function(frm) {
		// Toggle visibility of sync frequency
		frm.toggle_display("sync_frequency", frm.doc.enable_sync);
	}
}); 