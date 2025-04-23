# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FlyOutAccountSettings(Document):
	def validate(self):
		# Reset sync status if sync is disabled
		if not self.enable_sync:
			self.sync_status = "Not Configured"
			self.last_sync_datetime = None
		
		# Ensure Base URL and API key are provided if sync is enabled
		if self.enable_sync and (not self.flyout_base_url or not self.api_key):
			frappe.throw("FlyOut Base URL and API Key are required to enable synchronization.")

	# Method to securely get the password (API Key)
	def get_password(self, fieldname="api_key"):
		return self.get_password(fieldname) 