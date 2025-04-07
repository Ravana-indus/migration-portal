# Copyright (c) 2023, Migration Portal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WorkOption(Document):
    def validate(self):
        self.validate_salary_range()
    
    def validate_salary_range(self):
        if self.salary_range_min and self.salary_range_max:
            if float(self.salary_range_min) > float(self.salary_range_max):
                frappe.throw("Minimum Salary cannot be greater than Maximum Salary") 