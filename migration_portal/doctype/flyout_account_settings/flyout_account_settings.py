# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FlyOutAccountSettings(Document):
	def validate(self):
		# Ensure base URL is valid format (basic check)
		if self.flyout_base_url and not self.flyout_base_url.startswith(("http://", "https://")):
			frappe.throw(_("FlyOut Base URL must start with http:// or https://"))
		
		# Reset sync status if sync is disabled
		if not self.enable_sync:
			self.sync_status = "Not Configured"
			self.last_sync_datetime = None
		
		# Add other validation as needed, e.g., check API key format if possible
		pass

	def on_update(self):
		"""Called automatically on save/update."""
		self.update_sync_status_on_save()

	def update_sync_status_on_save(self):
		"""
		Updates the read-only sync_status field based on other settings.
		This logic might need refinement based on actual sync health checks.
		"""
		if not self.enable_sync:
			self.sync_status = "Not Configured" # Or "Paused"?
		elif not self.api_key:
			self.sync_status = "Error" # Cannot sync without API key
			frappe.msgprint("API Key is missing. Synchronization cannot be enabled.", title="Configuration Error", indicator="red")
		elif self.sync_status in ["Not Configured", None]:
			# If sync is enabled and API key exists, but status is not set, mark as Active
			# This assumes initial setup is okay. Real status check might involve a test API call.
			self.sync_status = "Active"
		# NOTE: The actual 'Error' status should ideally be set by the sync utility 
		# when an API call fails, not directly here on save.
		# This method just ensures the status isn't misleadingly "Active" if config is bad.

		# Use db_set to avoid recursive on_update calls if only changing sync_status
		frappe.db.set_value(self.doctype, self.name, "sync_status", self.sync_status)

	# Example: Add a button or method to test API connection
	@frappe.whitelist()
	def test_api_connection(self):
		"""Attempts a simple API call to FlyOut to verify credentials and connectivity."""
		if not self.enable_sync or not self.api_key:
			frappe.throw("Sync must be enabled and API Key must be set to test connection.")

		try:
			# Replace with an actual simple GET endpoint from FlyOut API docs if available
			# Example: A '/ping' or '/me' endpoint
			test_endpoint = f"{self.flyout_base_url}/providers/me" # Placeholder endpoint
			headers = {
				"Authorization": f"Bearer {self.get_password('api_key')}"
			}
			
			from migration_portal.migration_portal.utils.sync_utils import make_api_request
			
			response = make_api_request("GET", test_endpoint, headers, max_retries=1) # Only try once for test
			
			frappe.msgprint("API Connection Successful!", title="Success", indicator="green")
			# Optionally update status to Active if it was in Error
			if self.sync_status == "Error":
				frappe.db.set_value(self.doctype, self.name, "sync_status", "Active")
			return True

		except Exception as e:
			frappe.log_error(f"FlyOut API Connection Test Failed: {e}", "FlyOut Settings Error")
			frappe.msgprint(f"API Connection Failed: {e}", title="Error", indicator="red")
			# Set status to Error
			frappe.db.set_value(self.doctype, self.name, "sync_status", "Error")
			return False

# Make settings available viafrappe.get_cached_doc
@frappe.whitelist()
def get_flyout_settings():
    return frappe.get_cached_doc("FlyOut Account Settings") 