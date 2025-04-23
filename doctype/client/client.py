# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

# Import actual sync functions
from migration_portal.migration_portal.api.flyout import log_sync_attempt
from migration_portal.migration_portal.utils.sync_utils import schedule_sync, push_client_updates

class Client(Document):
	def before_save(self):
		# Example: Validate passport expiry date
		if self.passport_expiry and frappe.utils.getdate(self.passport_expiry) < frappe.utils.today():
			frappe.msgprint("Warning: Passport has expired.", indicator='orange')
		
		# Populate client name from linked inquiry if empty (should generally be set during conversion)
		if not self.client_name and self.linked_inquiry:
			inquiry = frappe.get_cached_doc("Inquiry", self.linked_inquiry)
			self.client_name = inquiry.applicant_name
		
		# Ensure required fields populated from inquiry are present
		# Note: These fields are now set during conversion in Inquiry.py
		# required_fields = ["email", "phone", "service_type", "destination_country", "primary_consultant"]
		# for field in required_fields:
		# 	if not self.get(field):
		# 		frappe.throw(f"Missing required field copied from Inquiry: {self.meta.get_label(field)}")

		# Attempt to parse city/country (highly dependent on format)
		# client.city = ... 
		# client.country = ...
		pass # Add address parsing logic if needed
		
		# Sync submitted documents with required documents status
		self.update_required_document_status()

	def on_update(self):
		# Sync updates to FlyOut if linked inquiry source was FlyOut
		if not frappe.flags.get("in_sync"):
			db_status = frappe.db.get_value(self.doctype, self.name, "status")
			if db_status and self.status != db_status:
				# Map Frappe status to FlyOut status (adjust mapping as needed)
				flyout_status = self.status.upper().replace(" ", "_") 
				self.sync_client_to_flyout(flyout_status)

	def on_submit(self):
		# Potentially sync status update
		self.sync_client_to_flyout("ACTIVE") # Assuming 'Submitted' maps to 'Active' in FlyOut

	def on_cancel(self):
		# Potentially sync status update
		self.sync_client_to_flyout("CANCELLED")

	def sync_client_to_flyout(self, flyout_status):
		"""Sends client updates to FlyOut if the original inquiry source was FlyOut."""
		if self.linked_inquiry:
			inquiry = frappe.get_cached_doc("Inquiry", self.linked_inquiry)
			if inquiry.inquiry_source == "FlyOut" and inquiry.flyout_inquiry_id:
				settings = frappe.get_cached_doc("FlyOut Account Settings")
				if settings.enable_sync:
					# Note: FlyOut might have a different endpoint or payload structure for *client* updates
					# vs inquiry updates. This assumes using the inquiry endpoint for status updates for simplicity.
					# Adjust the data payload and endpoint logic based on FlyOut's actual API.
					data = {
						"inquiry_id": inquiry.flyout_inquiry_id, # Still identifying by original FlyOut ID
						"status": flyout_status, # Map internal Client status to FlyOut's expected status
						# Add other relevant fields if FlyOut needs them
						"applicant_name": self.client_name,
						"email": self.email,
						"phone": self.phone,
						"updated_at": str(now_datetime())
					}
					
					# This function needs to be defined in sync_utils.py
					result = push_client_updates(data, settings)
					
					# Logging is now handled within push_client_updates
					
					if not result.get("success"):
						frappe.msgprint(f"Failed to sync Client {self.name} update to FlyOut: {result.get('message')}", indicator='red', alert=True)
						# Schedule retry
						schedule_sync("Client", self.name)

	def update_required_document_status(self):
		"""Updates status in 'required_documents' table based on 'submitted_documents' table."""
		if not self.submitted_documents or not self.required_documents:
			return

		submitted_names = {d.document_name for d in self.submitted_documents}
		updated = False
		for req_doc in self.required_documents:
			# If the required document is found in submitted documents and its status is Pending
			if req_doc.document_name in submitted_names and req_doc.status == "Pending":
				req_doc.status = "Received"
				updated = True
			# Optional: Handle if a submitted doc is removed? Reset status to Pending?
			# elif req_doc.document_name not in submitted_names and req_doc.status == "Received":
			#    req_doc.status = "Pending"
			#    updated = True
		
		if updated:
			frappe.msgprint("Required document statuses updated based on submissions.", indicator="blue")
			# No need to save here, as this is called within before_save/validate


# Placeholders removed, actual functions are imported above 