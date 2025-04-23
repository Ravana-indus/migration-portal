# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class StudyOption(Document):
	# Basic validation or logic can go here if needed
	def validate(self):
		# Example: Validate start date vs application deadline?
		pass 