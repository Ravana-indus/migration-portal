# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now

class SyncLog(Document):
	def before_insert(self):
		# Set timestamp for autoname if not set
		if not self.timestamp:
			self.timestamp = now().strftime("%Y%m%d%H%M%S")
		
		# Set sync datetime if not set
		if not self.sync_datetime:
			self.sync_datetime = frappe.utils.now_datetime()
	
	# Sync Logs are typically read-only after creation
	def before_save(self):
		if not self.is_new():
			# Allow updating retry_scheduled and retry_count fields
			if self.has_value_changed("retry_scheduled") or self.has_value_changed("retry_count"):
				pass # Allow save
			else:
				frappe.throw("Sync Logs cannot be modified after creation.", frappe.WriteError)

	def on_trash(self):
		# Prevent deletion by non-System Managers if needed
		if not frappe.has_permission("Sync Log", "delete"):
			frappe.throw("You do not have permission to delete Sync Logs.", frappe.PermissionError) 