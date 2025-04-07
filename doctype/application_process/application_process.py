import frappe
from frappe.model.document import Document

class ApplicationProcess(Document):
    def validate(self):
        self.validate_dates()
        self.validate_appeal_fields()
        
    def validate_dates(self):
        if self.expected_completion and self.start_date and self.expected_completion < self.start_date:
            frappe.throw("Expected completion date cannot be earlier than start date")
            
        if self.submission_date and self.start_date and self.submission_date < self.start_date:
            frappe.throw("Submission date cannot be earlier than start date")
            
        if self.decision_date and self.submission_date and self.decision_date < self.submission_date:
            frappe.throw("Decision date cannot be earlier than submission date")
            
        if self.visa_issue_date and self.decision_date and self.visa_issue_date < self.decision_date:
            frappe.throw("Visa issue date cannot be earlier than decision date")
            
    def validate_appeal_fields(self):
        if self.appeal_filed:
            if not self.decision_received:
                frappe.throw("Decision must be received before filing an appeal")
            if self.decision != "Rejected":
                frappe.throw("Appeal can only be filed for rejected applications")