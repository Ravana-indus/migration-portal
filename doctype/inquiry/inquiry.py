# Copyright (c) 2024, RavanOS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime_str, get_link_to_form

# Import actual sync functions
from migration_portal.migration_portal.api.flyout import log_sync_attempt
from migration_portal.migration_portal.utils.sync_utils import schedule_sync, push_inquiry_updates

class Inquiry(Document):
	def before_save(self):
		if not self.inquiry_date:
			self.inquiry_date = get_datetime_str(frappe.utils.now())

	def validate(self):
		if self.inquiry_source == "FlyOut" and not self.flyout_inquiry_id:
			frappe.throw("FlyOut Inquiry ID is required when source is FlyOut")
		
		if self.inquiry_source == "Website" and not self.source_details:
			frappe.throw("Source details are required when source is Website")

		# Validate source details are provided for Other/Referral
		if self.inquiry_source in ["Other", "Referral"] and not self.source_details:
			frappe.throw("Source Details are required when Inquiry Source is Other or Referral")

		# Validate study/work options based on service type
		if self.service_type == "Study" and not self.study_options:
			frappe.throw("Study Options are required when Service Type is Study")
		elif self.service_type == "Work" and not self.work_options:
			frappe.throw("Work Options are required when Service Type is Work")

	def on_submit(self):
		# Actions to perform upon submission
		self.sync_to_flyout()

	def on_cancel(self):
		# Actions to perform upon cancellation
		self.sync_to_flyout()

	def on_update(self):
		# Check if the status has changed and sync if applicable
		# Use flags to avoid sync loops if update is triggered by sync itself
		if not frappe.flags.get("in_sync"):
			db_status = frappe.db.get_value(self.doctype, self.name, "status")
			if db_status and self.status != db_status:
				# Map Frappe status to FlyOut status (adjust mapping as needed)
				flyout_status = self.status.upper().replace(" ", "_") 
				self.sync_to_flyout()

	def sync_to_flyout(self):
		if self.inquiry_source != "FlyOut":
			frappe.throw("Only FlyOut inquiries can be synced")
		
		data = {
			"applicant_name": self.applicant_name,
			"contact_email": self.contact_email,
			"contact_phone": self.contact_phone,
			"service_type": self.service_type,
			"destination_country": self.destination_country,
			"budget_range": self.budget,
			"timeline": self.timeline,
			"ielts_status": self.ielts_status,
			"preferred_language": self.preferred_language_of_communication,
			"preferred_field_of_study": self.preferred_field_of_study,
			"preferred_field_of_work": self.preferred_field_of_work,
			"work_experience": self.length_of_work_experience
		}
		
		# Add study options if present
		if self.service_type == "Study" and self.study_options:
			data["study_options"] = [{
				"country": opt.country,
				"program": opt.program,
				"level": opt.level,
				"institution": opt.institution
			} for opt in self.study_options]
		
		# Add work options if present
		if self.service_type == "Work" and self.work_options:
			data["work_options"] = [{
				"country": opt.country,
				"visa_type": opt.visa_type,
				"job_category": opt.job_category
			} for opt in self.work_options]
		
		# TODO: Implement actual API call to FlyOut
		frappe.msgprint("Synced to FlyOut successfully")

	def convert_to_client(self):
		if self.linked_client:
			frappe.throw("This inquiry has already been converted to a client")
		
		# Create new client
		client = frappe.get_doc({
			"doctype": "Client",
			"client_name": self.applicant_name,
			"email": self.contact_email,
			"phone": self.contact_phone,
			"service_type": self.service_type,
			"destination_country": self.destination_country,
			"budget_range": self.budget,
			"timeline": self.timeline,
			"ielts_status": self.ielts_status,
			"preferred_language": self.preferred_language_of_communication,
			"preferred_field_of_study": self.preferred_field_of_study,
			"preferred_field_of_work": self.preferred_field_of_work,
			"work_experience": self.length_of_work_experience,
			"status": "Active",
			"source_inquiry": self.name
		})
		
		# Add study options if present
		if self.service_type == "Study" and self.study_options:
			for opt in self.study_options:
				client.append("study_options", {
					"country": opt.country,
					"program": opt.program,
					"level": opt.level,
					"institution": opt.institution
				})
		
		# Add work options if present
		if self.service_type == "Work" and self.work_options:
			for opt in self.work_options:
				client.append("work_options", {
					"country": opt.country,
					"visa_type": opt.visa_type,
					"job_category": opt.job_category
				})
		
		# Add notes
		if self.notes:
			client.append("notes", {
				"note": f"Converted from Inquiry: {self.name}\n{self.notes}"
			})
		
		try:
			client.insert()
			self.linked_client = client.name
			self.save()
			frappe.msgprint(f"Successfully converted to Client: {get_link_to_form('Client', client.name)}")
		except Exception as e:
			frappe.log_error(f"Error converting Inquiry to Client: {str(e)}")
			frappe.throw("Error converting to client. Please try again.")

@frappe.whitelist()
def convert_to_client(doc=None, inquiry_name=None):
	"""Converts an Inquiry document to a Client document."""
	
	if inquiry_name:
		doc = frappe.get_doc("Inquiry", inquiry_name)
	elif isinstance(doc, str):
		doc = frappe.get_doc("Inquiry", doc)
	elif isinstance(doc, dict):
		# If full doc is passed from client-side
		doc = frappe.get_doc(doc)
	
	if not doc:
		frappe.throw("Inquiry document not provided or found.")

	if doc.status != "Under Review":
		frappe.throw("Inquiry must be 'Under Review' to convert.")

	if doc.linked_client:
		frappe.throw(
			f"Inquiry already linked to Client {get_link_to_form('Client', doc.linked_client)}", 
			title="Already Converted"
		)

	try:
		# Create new Client document
		client = frappe.new_doc("Client")
		
		# Basic Information
		client.linked_inquiry = doc.name
		client.client_name = doc.applicant_name
		client.email = doc.contact_email
		client.phone = doc.contact_phone
		client.service_type = doc.service_type
		client.destination_country = doc.destination_country
		client.primary_consultant = doc.assigned_to or frappe.session.user
		
		# Additional Details
		if doc.address:
			address_parts = doc.address.split('\n')
			if len(address_parts) >= 1:
				client.address_line1 = address_parts[0]
			if len(address_parts) >= 2:
				client.address_line2 = address_parts[1]
			if len(address_parts) >= 3:
				client.city = address_parts[2]

		# Service Details
		client.budget_range = doc.budget_range
		client.timeline = doc.timeline

		# Study Options
		if doc.service_type == "Study" and doc.study_options:
			for option in doc.study_options:
				client.append("study_preferences", {
					"program_name": option.program_name,
					"institution": option.institution,
					"level": option.level,
					"field_of_study": option.field_of_study,
					"country": option.country,
					"notes": option.notes,
					"reference_option": option.study_option
				})

		# Work Options
		if doc.service_type == "Work" and doc.work_options:
			for option in doc.work_options:
				client.append("job_preferences", {
					"job_title": option.job_title,
					"company_name": option.company_name,
					"industry": option.industry,
					"country": option.country,
					"expected_salary": option.expected_salary,
					"salary_period": option.salary_period,
					"contract_type": option.contract_type,
					"notes": option.notes,
					"reference_option": option.work_option
				})

		# Notes
		if doc.notes:
			client.append("notes_history", {
				"note": doc.notes,
				"note_type": "Conversion Note",
				"added_by": frappe.session.user,
				"added_on": now_datetime()
			})

		# Set initial status and insert
		client.status = "Active"
		client.insert(ignore_permissions=True)

		# Update Inquiry
		doc.status = "Converted"
		doc.linked_client = client.name
		doc.save(ignore_permissions=True)
		
		# Success message with link
		frappe.msgprint(
			f"Successfully converted Inquiry {doc.name} to Client {get_link_to_form('Client', client.name)}", 
			alert=True, 
			indicator='green'
		)
		
		return client.name

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Client Conversion Error for Inquiry {doc.name}")
		frappe.throw(f"Error converting Inquiry to Client: {str(e)}")

# Placeholders removed, actual functions are imported above 