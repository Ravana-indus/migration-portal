// Script for Playbook Step child table

frappe.ui.form.on("Playbook Step", {
    status: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.status === "Completed") {
            // Set completion date to today if status is set to Completed
            frappe.model.set_value(cdt, cdn, "completion_date", frappe.datetime.now_date());
            frm.refresh_field("playbook_steps"); // Refresh the table to show the date
        } else {
            // Clear completion date if status is changed from Completed
            if (frappe.model.get_value(cdt, cdn, "completion_date")) {
                 frappe.model.set_value(cdt, cdn, "completion_date", null);
                 frm.refresh_field("playbook_steps");
            }
        }
    }
}); 