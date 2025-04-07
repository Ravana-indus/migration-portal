# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_url_to_form

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
		
		# Clear cache on update
		frappe.cache().delete_value("flyout_account_settings")
		
		# Consider syncing profile if relevant fields changed
		if self.has_value_changed("company_description") or \
		   self.has_value_changed("services_offered") or \
		   self.has_value_changed("contact_email") or \
		   self.has_value_changed("contact_phone") or \
		   self.has_value_changed("company_logo") or \
		   self.has_value_changed("website") or \
		   self.has_value_changed("supported_languages"):
		   
		   # Enqueue background job to sync profile data to avoid delays on save
		   # Check if sync is enabled before queuing
		   if self.enable_sync:
			   frappe.enqueue(
				   "migration_portal.migration_portal.doctype.flyout_account_settings.flyout_account_settings.sync_provider_profile_to_flyout", 
				   queue="short", 
				   timeout=300
			   )

	def update_sync_status_on_save(self):
		"""
		Updates the read-only sync_status field based on other settings.
		Called by on_update.
		"""
		new_status = self.sync_status # Start with current status
		if not self.enable_sync:
			new_status = "Not Configured"
		elif not self.api_key:
			new_status = "Error"
			frappe.msgprint("API Key is missing. Synchronization cannot be enabled.", title="Configuration Error", indicator="red")
		elif self.sync_status in ["Not Configured", None]:
			new_status = "Active"
		
		# Only update DB if status actually changed to avoid recursion
		if new_status != self.sync_status:
		    self.sync_status = new_status # Update field in memory
		    # Use db_set to save directly and avoid triggering on_update again
		    frappe.db.set_value(self.doctype, self.name, "sync_status", new_status)

	@frappe.whitelist()
	def test_api_connection(self):
		"""Attempts a simple API call to FlyOut to verify credentials and connectivity."""
		if not self.enable_sync or not self.get_password('api_key'):
			frappe.throw("Sync must be enabled and API Key must be set to test connection.")

		try:
			# Use a known, simple endpoint for testing (replace if needed)
			test_endpoint = f"{self.flyout_base_url}/providers/me" 
			headers = {
				"Authorization": f"Bearer {self.get_password('api_key')}",
                "Accept": "application/json"
			}
			
			from migration_portal.migration_portal.utils.sync_utils import make_api_request
			
			response = make_api_request("GET", test_endpoint, headers, max_retries=1) 
			
			# Basic check: Status code was 2xx (handled by raise_for_status in make_api_request)
			# Optional: Check response content for expected structure or data
			try:
				response_data = response.json()
				frappe.msgprint(f"API Connection Successful!<br>Response:<pre>{frappe.as_json(response_data)}</pre>", title="Success", indicator="green")
			except Exception:
				frappe.msgprint("API Connection Successful! (Could not parse JSON response)", title="Success", indicator="green")

			# Update status to Active if it was in Error
			if self.sync_status == "Error":
				frappe.db.set_value(self.doctype, self.name, "sync_status", "Active")
			return True

		except Exception as e:
			frappe.log_error(f"FlyOut API Connection Test Failed: {e}", "FlyOut Settings Error")
			response_text = getattr(e, 'response', None) and getattr(e.response, 'text', None)
			frappe.msgprint(f"API Connection Failed: {e}<br><pre>{response_text or 'No response body'}</pre>", title="Error", indicator="red", wide=True)
			# Set status to Error
			frappe.db.set_value(self.doctype, self.name, "sync_status", "Error")
			return False

# --- Background Job for Profile Sync --- 

def sync_provider_profile_to_flyout():
    """(Background Job) Syncs provider profile fields to FlyOut."""
    settings = frappe.get_doc("FlyOut Account Settings")
    if not settings.enable_sync or not settings.get_password('api_key'):
        frappe.logger().info("Skipping FlyOut profile sync: Sync disabled or API key missing.")
        return

    try:
        # 1. Prepare Payload (Map local fields to FlyOut API fields)
        # Example - adjust field names based on actual FlyOut API
        profile_data = {
            "provider_name": settings.provider_name,
            "description": settings.company_description,
            "website": settings.website,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            # Map Table MultiSelect fields appropriately (e.g., list of names/IDs)
            "services_offered": [s.service_name for s in settings.services_offered], 
            "supported_languages": [lang.language for lang in settings.supported_languages],
            # Handle logo - needs API endpoint for image upload or URL
            # "logo_url": frappe.utils.get_url(settings.company_logo) if settings.company_logo else None 
        }
        # Remove None values
        profile_data = {k: v for k, v in profile_data.items() if v is not None}

        # 2. Determine API Endpoint (e.g., /providers/profile)
        endpoint = f"{settings.flyout_base_url}/providers/profile" # Placeholder

        # 3. Set Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.get_password('api_key')}"
        }

        # 4. Make API Call (e.g., PUT or POST)
        from migration_portal.migration_portal.utils.sync_utils import make_api_request
        make_api_request("PUT", endpoint, headers, data=profile_data)

        frappe.logger().info("Successfully synced provider profile to FlyOut.")
        # Update sync status if needed
        if settings.sync_status == "Error":
             frappe.db.set_value(settings.doctype, settings.name, "sync_status", "Active")

    except Exception as e:
        frappe.log_error(f"Failed to sync provider profile to FlyOut: {e}", "FlyOut Profile Sync Error")
        # Set sync status to Error
        frappe.db.set_value(settings.doctype, settings.name, "sync_status", "Error")
        # Optionally, notify admin


# Make settings available via frappe.get_cached_doc
# (No need for a separate function, Frappe handles caching for Single DocTypes)
# @frappe.whitelist()
# def get_flyout_settings():
#    return frappe.get_cached_doc("FlyOut Account Settings") 