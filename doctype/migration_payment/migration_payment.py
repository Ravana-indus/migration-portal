# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MigrationPayment(Document):
	def validate(self):
		# Ensure reference is set
		if not self.reference_type or not self.reference_name:
			frappe.throw("Reference Type and Reference Name are required.")
		
		# Validate amount
		if self.amount <= 0:
			frappe.throw("Payment Amount must be positive.")
		
		# Set default currency if not set (can also fetch from company settings)
		if not self.currency:
			self.currency = frappe.get_cached_value('Company', frappe.defaults.get_user_default("company"), "default_currency") or "USD"

	def before_submit(self):
		# Payment must be in 'Paid' status to be submitted
		if self.payment_status != "Paid":
			frappe.throw("Payment must be marked as 'Paid' before submitting.")

	def on_submit(self):
		# Actions after submitting a payment (e.g., update Client/Inquiry status or totals)
		self.update_linked_document_payment_status()

	def on_cancel(self):
		# Actions after cancelling a payment
		self.payment_status = "Cancelled"
		# Potentially reverse the status update on the linked document
		# self.update_linked_document_payment_status(reverse=True)
		pass

	def update_linked_document_payment_status(self, reverse=False):
		"""Placeholder function to update payment status/totals on the linked Client or Inquiry."""
		if self.reference_type and self.reference_name:
			try:
				linked_doc = frappe.get_doc(self.reference_type, self.reference_name)
				# --- Add logic here to update payment summaries or status on Client/Inquiry --- 
				# Example: Calculate total paid amount, check if fully paid, etc.
				# if hasattr(linked_doc, "total_paid"): 
				# 	 linked_doc.calculate_totals()
				# 	 linked_doc.save()
				
				# Log the event instead of just printing
				frappe.log_info(
					f"Payment {self.name} {'cancelled' if reverse else 'submitted'}. "
					f"Linked document {self.reference_type} {self.reference_name} status can be updated here.", 
					"Payment Linking Update"
				)
				# Optional: Display message to user if needed
				# frappe.msgprint(f"Linked document {self.reference_type} {self.reference_name} needs payment status update.")
			except Exception as e:
				frappe.log_error(f"Failed to update linked document {self.reference_type} {self.reference_name} on payment {self.name} submit/cancel. Error: {e}") 