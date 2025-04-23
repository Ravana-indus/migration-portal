# Copyright (c) 2024, RavanOS and contributors
# Utility functions for FlyOut synchronization

import frappe
import requests
from frappe.integrations.utils import make_post_request
from frappe.utils import now_datetime

# Assuming log_sync_attempt is in api/flyout.py
from migration_portal.migration_portal.api.flyout import log_sync_attempt

# --- Outbound Sync Functions --- #

def push_inquiry_updates(data, settings):
    """Pushes inquiry updates to FlyOut API."""
    endpoint = f"{settings.flyout_base_url}/inquiries/{data.get('inquiry_id')}" # Assuming RESTful endpoint
    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    method = "PUT" # Or PATCH
    
    # Log attempt before sending
    log_id = log_sync_attempt(
        direction="Outbound", status="Attempting", doctype="Inquiry", 
        docname=frappe.db.get_value("Inquiry", {"flyout_inquiry_id": data.get('inquiry_id')}),
        flyout_id=data.get('inquiry_id'), endpoint=endpoint, method=method, request_data=data
    )

    try:
        response = requests.put(endpoint, headers=headers, json=data, timeout=15)
        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
        
        response_data = response.json()
        # Update log with success
        log_sync_attempt(log_id=log_id, status="Success", response_data=response_data)
        return {"success": True, "response": response_data}
        
    except requests.exceptions.RequestException as e:
        error_message = f"Connection Error: {e}"
        # Update log with error
        log_sync_attempt(log_id=log_id, status="Error", error_message=error_message)
        return {"success": False, "message": error_message}
    except Exception as e:
        error_message = f"API Error: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f" | Response: {e.response.text}"
        # Update log with error
        log_sync_attempt(log_id=log_id, status="Error", error_message=error_message, response_data=getattr(e.response, 'text', None))
        return {"success": False, "message": error_message}

def push_client_updates(data, settings):
    """Pushes client-related updates to FlyOut API.
    Note: This might use the same endpoint as inquiries or a different one.
    Adjust endpoint and payload based on FlyOut's API design.
    """
    # For now, reuse the inquiry push function
    # Replace with dedicated logic if FlyOut has a separate client endpoint/payload
    return push_inquiry_updates(data, settings) 

# --- Sync Scheduling & Retry --- #

@frappe.whitelist()
def schedule_sync(doctype, docname):
    """Schedules a background job to attempt sync later."""
    # This requires setting up background workers and potentially RQ scheduler
    # For simplicity, we'll just log it for now.
    frappe.log_info(f"Sync retry requested for {doctype} {docname}", "Sync Scheduler")
    # Real implementation would use frappe.enqueue:
    # frappe.enqueue("migration_portal.migration_portal.utils.sync_utils.retry_sync_job", 
    #                queue="short", timeout=300, doctype=doctype, docname=docname)
    # Mark log as retry scheduled if possible
    log = frappe.db.get_value("Sync Log", {"reference_doctype": doctype, "reference_name": docname, "status": "Error"}, "name")
    if log:
        try:
            sync_log = frappe.get_doc("Sync Log", log)
            sync_log.retry_scheduled = 1
            sync_log.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to mark Sync Log {log} as retry scheduled: {e}")

# Example background job function (would need RQ setup)
# def retry_sync_job(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)
#     if hasattr(doc, "sync_to_flyout"):
#         # Determine the correct status to send based on current state
#         current_status = doc.status.upper().replace(" ", "_") # Example mapping
#         doc.sync_to_flyout(current_status)
#         # Increment retry count in log
#         log = frappe.db.get_value("Sync Log", {"reference_doctype": doctype, "reference_name": docname, "status": "Error"}, "name")
#         if log:
#              sync_log = frappe.get_doc("Sync Log", log)
#              sync_log.retry_count = (sync_log.retry_count or 0) + 1
#              sync_log.retry_scheduled = 0 # Reset flag
#              sync_log.save(ignore_permissions=True)

@frappe.whitelist()
def retry_sync_from_log(sync_log_name):
    """Triggers a retry based on a specific Sync Log entry."""
    try:
        log = frappe.get_doc("Sync Log", sync_log_name)
        if log.status == "Error" and log.reference_doctype and log.reference_name:
            schedule_sync(log.reference_doctype, log.reference_name)
            return {"status": "success", "message": "Retry scheduled."}
        else:
             return {"status": "error", "message": "Log is not in error state or reference is missing."}
    except Exception as e:
        frappe.log_error(f"Error scheduling retry from log {sync_log_name}: {e}")
        return {"status": "error", "message": f"Error scheduling retry: {e}"}


# --- Helper for updating Sync Log (potentially move to api/flyout.py) ---
# Simplified update function for outbound calls within this file
def update_sync_log(log_id, status, response_data=None, error_message=None):
    if not log_id:
        return
    try:
        log = frappe.get_doc("Sync Log", log_id)
        log.status = status
        log.response_data = frappe.as_json(response_data)
        log.error_message = error_message
        log.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Failed to update Sync Log {log_id}: {e}", "Sync Log Update Error")

# Add this import line to the api/flyout.py file:
# from migration_portal.migration_portal.utils.sync_utils import schedule_sync, push_inquiry_updates, push_client_updates 

# Add this import line to the doctype py files (e.g., inquiry.py, client.py)
# from migration_portal.migration_portal.api.flyout import log_sync_attempt
# from migration_portal.migration_portal.utils.sync_utils import schedule_sync, push_inquiry_updates, push_client_updates 