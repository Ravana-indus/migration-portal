// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sync Log", {
	refresh(frm) {
		// Make fields read-only as logs should generally not be edited
		frm.disable_save();

		// Maybe add a button to retry failed syncs?
		if(frm.doc.status == "Error" && !frm.doc.retry_scheduled) {
			frm.add_custom_button(__("Retry Sync"), function(){
				frappe.call({
					method: "migration_portal.migration_portal.utils.sync_utils.retry_sync_from_log",
					args: {
						sync_log_name: frm.doc.name
					},
					callback: function(r){
						if(!r.exc){
							frappe.show_alert({message: __("Retry scheduled successfully"), indicator: "green"});
							frm.reload_doc();
						}
					},
					freeze: true,
					freeze_message: __("Scheduling retry...")
				})
			}).addClass("btn-primary");
		}
	},

	status(frm) {
		// Show/hide error details section based on status
		frm.toggle_display("error_section", frm.doc.status === 'Error');
		frm.toggle_display("column_break_3", frm.doc.status === 'Error'); // Assuming stack trace is in 3rd column
	}
}); 