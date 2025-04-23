# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MigrationAgreement(Document):
	def validate(self):
		# Ensure either Client or Inquiry is linked, but not both
		if self.party_type == "Client" and not self.client:
			frappe.throw("Client must be selected for Party Type 'Client'")
		if self.party_type == "Inquiry" and not self.inquiry:
			frappe.throw("Inquiry must be selected for Party Type 'Inquiry'")
		if self.client and self.inquiry:
			frappe.throw("Cannot link both Client and Inquiry to the same agreement.")
		
		# Validate dates
		if self.start_date and self.end_date and self.start_date > self.end_date:
			frappe.throw("Agreement End Date cannot be before Start Date")
		if self.signed_date and self.agreement_date and self.signed_date < self.agreement_date:
			frappe.throw("Signed Date cannot be before Agreement Date")

	def before_submit(self):
		if self.status != "Signed":
			frappe.throw("Only Signed agreements can be submitted.")
		if not self.signed_date:
			self.signed_date = frappe.utils.today() # Default signed date to today if submitted

	def on_submit(self):
		# Actions after submission (e.g., notify parties, update linked records)
		pass

	def on_cancel(self):
		# Actions after cancellation
		self.status = "Cancelled"
		pass 