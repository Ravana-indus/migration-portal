# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ClientMilestone(Document):
	pass

    # Set completion date on status change (handled client-side too for responsiveness)
    def on_update(self):
        if self.status == 'Completed' and not self.completion_date:
            self.completion_date = frappe.utils.today()
        elif self.status != 'Completed' and self.completion_date:
             self.completion_date = None 