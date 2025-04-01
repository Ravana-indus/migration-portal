# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

# Import actual sync functions
from migration_portal.migration_portal.api.flyout import log_sync_attempt
from migration_portal.migration_portal.utils.sync_utils import schedule_sync, push_client_updates

# Function potentially called by the 'on_update' hook in hooks.py (if uncommented later)
# def trigger_client_sync(doc, method):
# 	"""
# 	Wrapper function called by the doc_event hook `on_update` for Client.
# 	Calls a sync method if needed.
# 	"""
# 	if not frappe.flags.get("in_sync"):
# 		doc.sync_to_external_system() # Example method name

class Client(Document):
	# ----- Lifecycle Hooks -----
	def validate(self):
		# Example: Validate passport expiry date
		if self.passport_expiry and frappe.utils.date_diff(self.passport_expiry, frappe.utils.today()) < 0:
			frappe.msgprint("Passport has expired.", title="Validation Warning", indicator="orange")

	# Placeholder for potential future sync logic
	# def sync_to_external_system(self):
	# 	frappe.logger().info(f"Sync logic for Client {self.name} called.")
	# 	pass

	def before_save(self):
		# Populate client name from linked inquiry if empty (should be set during conversion)
		if not self.client_name and self.linked_inquiry:
			inquiry = frappe.get_cached_doc("Inquiry", self.linked_inquiry)
			self.client_name = inquiry.applicant_name
		
		# Update required document status based on submitted documents
		self.update_required_document_status()

	def on_update(self):
		# Sync updates to FlyOut if linked inquiry source was FlyOut
		if not frappe.flags.get("in_sync"):
			db_status = frappe.db.get_value(self.doctype, self.name, "status")
			if db_status and self.status != db_status:
				# Map Frappe status to FlyOut status (adjust mapping as needed)
				flyout_status_map = {
					"Active": "ACTIVE", 
					"In Progress": "IN_PROGRESS", # Example mapping
					"Completed": "COMPLETED",
					"Cancelled": "CANCELLED"
				}
				flyout_status = flyout_status_map.get(self.status, self.status.upper().replace(" ", "_")) 
				self.sync_client_to_flyout(flyout_status)

	def on_submit(self):
		# Sync status update (workflow state might be more reliable)
		self.sync_client_to_flyout("ACTIVE") # Assuming 'Submitted'/'Active' maps to 'ACTIVE' in FlyOut

	def on_cancel(self):
		# Sync status update
		self.sync_client_to_flyout("CANCELLED")

	def sync_client_to_flyout(self, flyout_status):
		"""Sends client updates to FlyOut if the original inquiry source was FlyOut."""
		if self.linked_inquiry:
			inquiry = frappe.get_cached_doc("Inquiry", self.linked_inquiry)
			if inquiry.inquiry_source == "FlyOut" and inquiry.flyout_inquiry_id:
				settings = frappe.get_cached_doc("FlyOut Account Settings")
				if settings.enable_sync:
					data = {
						"inquiry_id": inquiry.flyout_inquiry_id, # Still identifying by original FlyOut ID
						"status": flyout_status, 
						# Add other relevant fields if FlyOut needs them (e.g., if FlyOut has client-specific fields)
						"applicant_name": self.client_name,
						"email": self.email,
						"phone": self.phone,
						"updated_at": str(now_datetime())
					}
					
					# Use the specific function from sync_utils
					result = push_client_updates(data, settings)
					
					# Logging is handled within push_client_updates
					
					if not result.get("success"):
						frappe.msgprint(f"Failed to sync Client {self.name} update to FlyOut: {result.get('message')}", indicator='red', alert=True)
						# Schedule retry
						schedule_sync("Client", self.name)

	def update_required_document_status(self):
		"""Updates status in 'required_documents' table based on 'submitted_documents' table."""
		if not self.submitted_documents or not self.required_documents:
			return

		submitted_names = {d.document_name for d in self.submitted_documents if d.document_name}
		updated = False
		for req_doc in self.required_documents:
			if req_doc.document_name and req_doc.document_name in submitted_names and req_doc.status == "Pending":
				req_doc.status = "Received"
				updated = True
			# Consider case if a submitted document is deleted later
			# elif req_doc.document_name and req_doc.document_name not in submitted_names and req_doc.status == "Received":
			#    req_doc.status = "Pending"
			#    updated = True
		
		if updated:
			frappe.msgprint(_("Required document statuses updated based on submissions."), indicator="blue")
			# No need to explicitly save the child table row here, happens on main doc save 