# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MigrationPayment(Document):
	def on_submit(self):
		# Update payment status in linked document
		self.update_linked_document_payment_status(reverse=False)

	def on_cancel(self):
		# Reverse payment status update in linked document
		self.update_linked_document_payment_status(reverse=True)

	def update_linked_document_payment_status(self, reverse=False):
		"""Updates the payment child table in the linked Client or Inquiry document."""
		if self.reference_type and self.reference_name:
			party_doctype = self.reference_type
			party_name = self.reference_name
			child_table_field = "payments" # Fieldname in Client/Inquiry
			child_doctype = "Migration Payment Reference" # Child DocType name
			link_field = "payment" # Fieldname in the child table linking to this payment

			try:
				party_doc = frappe.get_doc(party_doctype, party_name)
				
				if not reverse: # On Submit
					# Check if already linked
					already_linked = any(d.get(link_field) == self.name for d in party_doc.get(child_table_field))
					if not already_linked:
						party_doc.append(child_table_field, {
							link_field: self.name,
							# Other fields (payment_date, amount, status) are fetched automatically
						})
						party_doc.save(ignore_permissions=True)
						frappe.msgprint(f"Payment linked to {party_doctype} {party_name}")
					# Log for potential further action (e.g., update overall payment status)
					frappe.log_info(f"Payment {self.name} submitted. Linked to {party_doctype} {party_name}.", "Payment Linking Update")

				else: # On Cancel
					# Find and remove the link
					updated_links = [d for d in party_doc.get(child_table_field) if d.get(link_field) != self.name]
					if len(updated_links) < len(party_doc.get(child_table_field)):
						party_doc.set(child_table_field, updated_links)
						party_doc.save(ignore_permissions=True)
						frappe.msgprint(f"Payment link removed from {party_doctype} {party_name}")
					# Log for potential further action
					frappe.log_info(f"Payment {self.name} cancelled. Link removed from {party_doctype} {party_name}.", "Payment Linking Update")

			except Exception as e:
				frappe.log_error(f"Failed to update {party_doctype} {party_name} for payment {self.name}. Error: {e}") 