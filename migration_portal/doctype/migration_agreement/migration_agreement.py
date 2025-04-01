# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MigrationAgreement(Document):
	def validate(self):
		# Fetch signatory designation if user is selected
		if self.company_signatory:
			# This assumes the designation is stored on the User doctype
			# Adjust if designation is stored elsewhere (e.g., Employee)
			designation = frappe.db.get_value("User", self.company_signatory, "designation")
			if designation:
				self.signatory_designation = designation
			else:
				# If designation not on User, clear it or fetch from Employee/other source
				self.signatory_designation = None # Or fetch logic

	def on_submit(self):
		# Add logic to update related Client/Inquiry if needed
		self.link_to_party("add")

	def on_cancel(self):
		# Add logic to update related Client/Inquiry if needed
		self.link_to_party("remove")

	def link_to_party(self, action="add"):
		"""Adds or removes this agreement from the child table in Client/Inquiry."""
		if self.party_type and (self.client or self.inquiry):
			party_doctype = self.party_type
			party_name = self.client if self.party_type == "Client" else self.inquiry
			child_table_field = "agreements" # Fieldname in Client/Inquiry
			child_doctype = "Client Agreement" if self.party_type == "Client" else "Inquiry Agreement" # Child DocType name
			link_field = "agreement" # Fieldname in the child table linking to this agreement

			try:
				party_doc = frappe.get_doc(party_doctype, party_name)
				
				if action == "add":
					# Check if already linked
					already_linked = any(d.get(link_field) == self.name for d in party_doc.get(child_table_field))
					if not already_linked:
						party_doc.append(child_table_field, {
							link_field: self.name,
							# status field in child table is fetched automatically based on Client Agreement doctype definition
						})
						party_doc.save(ignore_permissions=True)
						frappe.msgprint(f"Agreement linked to {party_doctype} {party_name}")
						
				elif action == "remove":
					# Find and remove the link
					updated_links = [d for d in party_doc.get(child_table_field) if d.get(link_field) != self.name]
					if len(updated_links) < len(party_doc.get(child_table_field)):
						party_doc.set(child_table_field, updated_links)
						party_doc.save(ignore_permissions=True)
						frappe.msgprint(f"Agreement link removed from {party_doctype} {party_name}")

			except Exception as e:
				frappe.log_error(f"Failed to update {party_doctype} {party_name} for agreement {self.name}. Error: {e}") 