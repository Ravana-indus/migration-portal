# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PlaybookStep(Document):
	# This is a child table DocType, so server-side logic is usually minimal
	# Logic like setting completion_date is handled client-side
	pass 