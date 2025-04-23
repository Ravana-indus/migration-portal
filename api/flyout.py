# Copyright (c) 2024, RavanOS and contributors
# API endpoints for FlyOut Integration

import frappe
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True) # Allow access via webhook
def receive_inquiry_webhook(data):
    """Receives inquiry data from FlyOut via webhook."""
    # 1. Validate webhook source (e.g., using a shared secret or verifying IP)
    # settings = frappe.get_cached_doc("FlyOut Account Settings")
    # if not is_valid_webhook_source(frappe.request.headers, settings):
    #     frappe.log_error("Invalid webhook source", "FlyOut Webhook Error")
    #     return {"status": "error", "message": "Unauthorized"}

    # 2. Process the incoming data (example structure, adjust based on actual FlyOut payload)
    try:
        if not isinstance(data, dict):
            data = frappe.parse_json(data)

        flyout_inquiry_id = data.get('inquiry_id')
        applicant_name = data.get('applicant_name')
        contact_email = data.get('email')
        contact_phone = data.get('phone')
        service_type = data.get('service_type') # Map if needed
        destination_country = data.get('destination_country') # Map if needed
        # ... other fields ...
        
        if not flyout_inquiry_id or not applicant_name or not contact_email:
             raise ValueError("Missing required fields: inquiry_id, applicant_name, email")

        # 3. Log the incoming request
        log_sync_attempt(
            direction="Inbound",
            status="Received", # Initial status
            doctype=None, # No local doctype yet
            docname=None,
            flyout_id=flyout_inquiry_id,
            endpoint="/api/method/migration_portal.migration_portal.api.flyout.receive_inquiry_webhook", # Example endpoint
            method="POST",
            request_data=data,
            response_data=None, 
            error_message=None
        )

        # 4. Check if inquiry already exists
        existing_inquiry = frappe.db.exists("Inquiry", {"flyout_inquiry_id": flyout_inquiry_id})

        if existing_inquiry:
            # Update existing inquiry (handle status changes, etc.)
            inquiry_doc = frappe.get_doc("Inquiry", existing_inquiry)
            # Set flag to prevent sync loop
            frappe.flags.in_sync = True 
            # --- Update logic --- 
            # Example: Only update if FlyOut data is newer? Compare timestamps?
            # inquiry_doc.applicant_name = applicant_name # Update fields as needed
            # inquiry_doc.contact_email = contact_email
            # ...
            # inquiry_doc.save()
            frappe.flags.in_sync = False
            message = f"Inquiry {existing_inquiry} updated."
            log_id = log_sync_attempt(status="Success", message=message, flyout_id=flyout_inquiry_id)
        else:
            # Create new inquiry
            inquiry = frappe.new_doc("Inquiry")
            inquiry.inquiry_source = "FlyOut"
            inquiry.flyout_inquiry_id = flyout_inquiry_id
            inquiry.applicant_name = applicant_name
            inquiry.contact_email = contact_email
            inquiry.contact_phone = contact_phone
            inquiry.service_type = service_type # Make sure value exists in Select options
            inquiry.destination_country = destination_country # Make sure value exists as Country name
            inquiry.inquiry_date = frappe.utils.today() # Or get from webhook data if available
            inquiry.status = "New" # Or map from FlyOut status
            # ... map other fields ...
            
            # Set flag to prevent sync loop during save/submit
            frappe.flags.in_sync = True
            inquiry.insert()
            # Optional: Submit if needed, depending on workflow
            # inquiry.submit()
            frappe.flags.in_sync = False
            message = f"New Inquiry {inquiry.name} created."
            log_id = log_sync_attempt(status="Success", message=message, doctype="Inquiry", docname=inquiry.name, flyout_id=flyout_inquiry_id)

        return {"status": "success", "message": message, "log_id": log_id}

    except ValueError as ve:
        frappe.log_error(frappe.get_traceback(), f"Webhook Data Error: {str(ve)}")
        log_id = log_sync_attempt(status="Error", error_message=str(ve), request_data=data, flyout_id=data.get('inquiry_id') if isinstance(data, dict) else None)
        frappe.response.status_code = 400 # Bad Request
        return {"status": "error", "message": str(ve), "log_id": log_id}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Webhook Processing Error")
        log_id = log_sync_attempt(status="Error", error_message=str(e), request_data=data, flyout_id=data.get('inquiry_id') if isinstance(data, dict) else None)
        frappe.response.status_code = 500 # Internal Server Error
        return {"status": "error", "message": "Internal server error during processing.", "log_id": log_id}

# --- Sync Log Helper --- #
def log_sync_attempt(direction, status, doctype=None, docname=None, flyout_id=None, endpoint=None, method=None, request_data=None, response_data=None, error_message=None, message=None):
    """Helper function to create or update a Sync Log entry."""
    try:
        # If updating a received log with final status
        if direction == "Inbound" and status != "Received" and flyout_id:
             existing_log = frappe.db.get_value("Sync Log", {"flyout_reference_id": flyout_id, "direction": "Inbound", "status": "Received"}, "name")
             if existing_log:
                 log = frappe.get_doc("Sync Log", existing_log)
                 log.status = status
                 log.reference_doctype = doctype
                 log.reference_name = docname
                 log.response_data = frappe.as_json(response_data or message)
                 log.error_message = error_message
                 log.save(ignore_permissions=True)
                 return log.name
                 
        # Create new log entry
        log = frappe.new_doc("Sync Log")
        log.sync_datetime = now_datetime()
        log.direction = direction
        log.status = status
        log.reference_doctype = doctype
        log.reference_name = docname
        log.flyout_reference_id = flyout_id
        log.endpoint = endpoint
        log.method = method
        log.request_data = frappe.as_json(request_data)
        log.response_data = frappe.as_json(response_data or message)
        log.error_message = error_message
        
        log.insert(ignore_permissions=True)
        return log.name
    except Exception as e:
        frappe.log_error(f"Failed to create/update Sync Log: {e}", "Sync Log Error")
        return None

# --- Placeholder for webhook validation (Implement actual logic) --- #
def is_valid_webhook_source(headers, settings):
    # Example: Check for a secret token in headers
    # provided_secret = headers.get('X-FlyOut-Token')
    # expected_secret = settings.get_password('webhook_secret') # Add a 'webhook_secret' field to settings
    # if not provided_secret or not expected_secret or provided_secret != expected_secret:
    #     return False
    # Example: Check source IP address if FlyOut provides static IPs
    # source_ip = frappe.request.remote_addr
    # allowed_ips = settings.allowed_webhook_ips.split('\n') # Add field 'allowed_webhook_ips' (TextArea)
    # if source_ip not in allowed_ips:
    #    return False
    return True # Placeholder - Always true for now 