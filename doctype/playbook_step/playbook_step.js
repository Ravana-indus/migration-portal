// Copyright (c) 2024, RavanOS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Playbook Step", {
	status(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// Set completion date when status is 'Completed'
		if (row.status === 'Completed' && !row.completion_date) {
			frappe.model.set_value(cdt, cdn, 'completion_date', frappe.datetime.nowdate());
		} else if (row.status !== 'Completed') {
			frappe.model.set_value(cdt, cdn, 'completion_date', null);
		}
		
		// Show/hide completion date field based on status
		frappe.toggle_reqd(cdt, cdn, "completion_date", row.status === 'Completed');
		frappe.meta.get_docfield(cdt, "completion_date", cdn).hidden = (row.status !== 'Completed');
		frm.refresh_field("playbook_steps"); // Refresh the table to show/hide field
	},

	// Optional: Add validation for due date vs completion date
	completion_date(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.due_date && row.completion_date && row.completion_date > row.due_date) {
			frappe.show_alert({message: `Step "${row.title || row.idx}" completed after due date.`, indicator: 'orange'});
		}
	}
}); 