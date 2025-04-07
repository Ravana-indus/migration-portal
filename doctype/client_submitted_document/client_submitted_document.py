# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ClientSubmittedDocument(Document):
	def validate(self):
		# Attempt to automatically fill document name from attachment filename
		if self.attachment and not self.document_name:
			self.document_name = self.attachment.split('/')[-1]

	def on_update(self):
		# Trigger update on parent Client doc after save
		if self.parenttype == "Client" and self.parent:
			try:
				client_doc = frappe.get_doc(self.parenttype, self.parent)
				client_doc.update_required_document_status() # Call the method we added earlier
				client_doc.save(ignore_permissions=True) # Save the client doc to persist changes in required_documents
			except Exception as e:
				frappe.log_error(f"Failed to update Client status on ClientSubmittedDocument update: {e}")

	def on_trash(self):
		# Trigger update on parent Client doc after delete
		if self.parenttype == "Client" and self.parent:
			try:
				client_doc = frappe.get_doc(self.parenttype, self.parent)
				# Optionally reset status in required_documents here if a submitted doc is deleted
				# client_doc.reset_required_document_status(self.document_name) 
				# client_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Failed to update Client status on ClientSubmittedDocument delete: {e}") 