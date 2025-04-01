# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

# Import sync utility
# Make sure the path is correct based on your app structure
from migration_portal.migration_portal.utils.sync_utils import push_inquiry_updates, schedule_sync

# Function called by the 'on_update' hook in hooks.py
def trigger_flyout_sync(doc, method):
	"""
	Wrapper function called by the doc_event hook `on_update`.
	Calls the sync_to_flyout method on the document instance.
	"""
	# `method` is passed by the hook but often not needed here directly
	# Check if sync is needed and call the instance method
	if doc.inquiry_source == "FlyOut" and doc.flyout_inquiry_id:
		# Check if it's not already being synced (to prevent loops)
		if not frappe.flags.get("in_sync"):
			doc.sync_to_flyout()


class Inquiry(Document):
	# ----- Lifecycle Hooks -----
	def validate(self):
		# Add validation logic here, e.g., check email format
		if self.contact_email and not frappe.utils.validate_email_address(self.contact_email):
			frappe.throw("Invalid Email Address format.")

	# on_update is now handled by the standalone trigger_flyout_sync function via hooks.py
	# def on_update(self):
	#     pass # Logic moved to trigger_flyout_sync

	def on_submit(self):
		# Actions to perform upon submission (if needed beyond workflow)
		# Example: Maybe send a confirmation email
		# self.sync_to_flyout() # Trigger sync on submit as well?
		pass

	def on_cancel(self):
		# Actions to perform upon cancellation
		# self.sync_to_flyout() # Trigger sync on cancel
		pass

	# ----- Custom Methods -----
	def sync_to_flyout(self, is_retry=False, originating_log=None):
		"""
		Sends inquiry data (or specific updates) to FlyOut if the source is FlyOut.
		Handles calling the push_inquiry_updates utility.

		Args:
			is_retry (bool): Indicates if this call is a retry attempt.
			originating_log (str): The name of the Sync Log that initiated the retry, if applicable.
		"""
		if self.inquiry_source != "FlyOut" or not self.flyout_inquiry_id:
			return # Don't sync if not a FlyOut inquiry or no ID

		# Check settings
		try:
			settings = frappe.get_cached_doc("FlyOut Account Settings")
			if not settings.enable_sync:
				frappe.logger().info(f"FlyOut sync skipped for Inquiry {self.name}: Sync is disabled in settings.")
				return
		except frappe.DoesNotExistError:
			frappe.log_error("FlyOut Account Settings not found. Cannot sync.", "FlyOut Sync Error")
			return

		# Call the push utility function
		# It handles the API call, logging, and retry scheduling
		result = push_inquiry_updates(self, settings) # Pass the document itself

		# Optionally, add UI feedback based on the result
		if is_retry:
			# If this was a retry, maybe update the original log based on the new result
			if originating_log:
				status = "Success" if result.get("success") else "Error"
				frappe.db.set_value("Sync Log", originating_log, "status", f"Retry {status}")
				frappe.db.set_value("Sync Log", originating_log, "response_data", result.get("message"))
		elif not result.get("success"):
			# Show message only for direct (non-retry) failures
			frappe.msgprint(
				f"Failed to sync Inquiry {self.name} to FlyOut: {result.get('message')}",
				title="Sync Error",
				indicator='red',
				alert=True
			)
			# Note: Retry scheduling is handled within push_inquiry_updates -> make_api_request -> schedule_sync


	# ----- Client Conversion (Called via Workflow Action) -----
	@frappe.whitelist()
	def convert_to_client(self):
		"""
		Converts this Inquiry document to a Client document.
		This method is intended to be called as a Workflow Action.
		The status transition (Inquiry -> Converted) should be part of the workflow transition definition.
		"""
		# Double-check status although workflow should manage this
		if self.status != "Under Review":
			frappe.throw("Inquiry must be 'Under Review' to be converted.")

		if self.linked_client:
			frappe.msgprint(f"Inquiry already linked to Client <a href='/app/client/{self.linked_client}'>{self.linked_client}</a>.", title="Already Converted", indicator="orange")
			return self.linked_client # Return existing client link

		try:
			# Create new Client document
			client = frappe.new_doc("Client")
			client.linked_inquiry = self.name
			client.client_name = self.applicant_name
			client.email = self.contact_email
			client.phone = self.contact_phone
			client.service_type = self.service_type
			client.destination_country = self.destination_country
			client.primary_consultant = self.assigned_to or frappe.session.user # Assign or default

			# Map address (simple example)
			if self.address:
				address_parts = self.address.split('\n')
				client.address_line1 = address_parts[0]
				if len(address_parts) > 1:
					client.address_line2 = address_parts[1]
				# TODO: Add more robust address parsing if needed (city, state, country, postal code)

			# Set initial Client status (assuming Workflow handles Inquiry status change)
			client.status = "Active"
			client.insert(ignore_permissions=True) # Ignore perms for automated creation

			# Update Inquiry link (status is handled by workflow)
			self.db_set("linked_client", client.name) # Use db_set to avoid triggering on_update again

			frappe.msgprint(f"Inquiry {self.name} converted to Client <a href='/app/client/{client.name}'>{client.name}</a>", alert=True, indicator='green', title="Conversion Successful")
			return client.name

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Client Conversion Error")
			frappe.throw(f"Error converting Inquiry to Client: {str(e)}")


# Standalone Whitelisted Function (potentially for button if workflow action isn't used)
# Kept for reference, but primary conversion should be via workflow action calling the instance method.
@frappe.whitelist()
def convert_inquiry_to_client_standalone(inquiry_name):
	"""Standalone function to convert inquiry, e.g., if called from a custom button."""
	doc = frappe.get_doc("Inquiry", inquiry_name)
	return doc.convert_to_client() 