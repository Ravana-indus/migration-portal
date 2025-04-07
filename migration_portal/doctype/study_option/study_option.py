# Copyright (c) 2023, Migration Portal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StudyOption(Document):
    def validate(self):
        self.validate_dates()
    
    def validate_dates(self):
        if self.start_date and self.application_deadline:
            if self.start_date < self.application_deadline:
                frappe.throw("Start Date cannot be before Application Deadline") 