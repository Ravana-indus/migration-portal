import frappe
import requests
import json
from frappe.utils import now_datetime, get_datetime
import time

def push_inquiry_updates(inquiry_doc, settings=None):
    """
    Push inquiry updates to FlyOut.
    Called from Inquiry hooks (e.g., on_update).
    
    Args:
        inquiry_doc (Document): The Inquiry document being updated.
        settings (Document, optional): FlyOut Account Settings document.
    
    Returns:
        dict: Result with success status and message.
    """
    if frappe.flags.in_sync: # Prevent sync loop
        return {"success": False, "message": "Sync currently in progress, skipping outbound."}

    if not settings:
        settings = frappe.get_cached_doc("FlyOut Account Settings")
    
    if not settings.enable_sync or inquiry_doc.inquiry_source != 'FlyOut':
        return {"success": False, "message": "Synchronization is disabled or inquiry is not from FlyOut"}
    
    if not inquiry_doc.flyout_inquiry_id:
        frappe.log_error(f"Cannot sync Inquiry {inquiry_doc.name}: Missing FlyOut Inquiry ID.", "FlyOut Sync Error")
        return {"success": False, "message": "Missing FlyOut Inquiry ID"}

    # Construct the endpoint URL
    endpoint = f"{settings.flyout_base_url}/providers/inquiries/{inquiry_doc.flyout_inquiry_id}" # Assume PUT updates existing
    
    # Prepare data payload (Map local fields to FlyOut fields)
    # This mapping depends on FlyOut's expected API structure
    payload = {
        "inquiry_id": inquiry_doc.flyout_inquiry_id,
        "applicant_name": inquiry_doc.applicant_name,
        "email": inquiry_doc.contact_email,
        "phone": inquiry_doc.contact_phone,
        "service_type": inquiry_doc.service_type,
        "destination_country": inquiry_doc.destination_country,
        "status": inquiry_doc.status, # Map local status to FlyOut status if necessary
        "notes": inquiry_doc.notes, # Send latest notes
        "updated_at": now_datetime().isoformat()
        # Add other fields FlyOut expects
    }

    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.get_password('api_key')}"
    }
    
    request_data_str = json.dumps(payload, indent=2)
    sync_log_name = None
    try:
        # Make the API call with retry logic
        response = make_api_request("PUT", endpoint, headers, payload, max_retries=3)
        response_data = response.json() if response.text else {}
        
        # Create success sync log
        sync_log_name = create_sync_log(
            "Outbound", "Success", "Inquiry", inquiry_doc.name, 
            inquiry_doc.flyout_inquiry_id, request_data_str, response_data, 
            endpoint=endpoint, method="PUT"
        )

        # Update last sync datetime in settings
        frappe.db.set_value("FlyOut Account Settings", settings.name, "last_sync_datetime", now_datetime())
        frappe.db.set_value("FlyOut Account Settings", settings.name, "sync_status", "Active")
        
        return {
            "success": True,
            "message": "Data synced successfully",
            "endpoint": endpoint,
            "response": response_data
        }
    except Exception as e:
        # Create error sync log
        sync_log_name = create_sync_log(
            "Outbound", "Error", "Inquiry", inquiry_doc.name, 
            inquiry_doc.flyout_inquiry_id, request_data_str, None, 
            error_message=str(e), endpoint=endpoint, method="PUT"
        )

        # Update sync status to error in settings
        frappe.db.set_value("FlyOut Account Settings", settings.name, "sync_status", "Error")
        
        # Schedule retry if applicable
        schedule_sync("Inquiry", inquiry_doc.name, sync_log=sync_log_name)

        return {
            "success": False,
            "message": str(e),
            "error_type": type(e).__name__,
            "endpoint": endpoint
        }

def make_api_request(method, url, headers, data=None, max_retries=3, retry_delay=2):
    """
    Make an API request with retry logic.
    
    Args:
        method (str): HTTP method (GET, POST, PUT, DELETE)
        url (str): API endpoint
        headers (dict): HTTP headers
        data (dict, optional): Data to send (will be JSON serialized for POST/PUT)
        max_retries (int, optional): Maximum number of retries
        retry_delay (int, optional): Delay between retries in seconds
    
    Returns:
        requests.Response: HTTP response object
    
    Raises:
        requests.exceptions.RequestException: If request fails after all retries.
    """
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            request_kwargs = {
                "headers": headers,
                "timeout": 30 # Standard timeout
            }
            if data is not None and method.upper() in ["POST", "PUT"]:
                 request_kwargs["json"] = data
            elif data is not None and method.upper() == "GET": # Params for GET
                 request_kwargs["params"] = data

            response = requests.request(method, url, **request_kwargs)
            
            # Check if the response indicates failure
            response.raise_for_status() # Raises HTTPError for 4xx/5xx
            
            return response # Return successful response

        except requests.exceptions.RequestException as e:
            last_exception = e
            retry_count += 1
            
            # Log the retry attempt
            frappe.log_error(
                f"API request to {url} failed (attempt {retry_count}/{max_retries}): {str(e)}",
                "FlyOut API Retry"
            )
            
            # Wait before retrying, unless it's the last attempt
            if retry_count < max_retries:
                time.sleep(retry_delay * (2 ** (retry_count - 1))) # Exponential backoff
            
    # If loop completes, all retries failed. Raise the last exception.
    if last_exception:
         raise last_exception
    else:
         # Should not happen if max_retries > 0, but handle defensively
         raise requests.exceptions.RequestException("API request failed after retries, but no exception was captured.")


def schedule_sync(doctype, docname, sync_log=None, retry_after=300):
    """
    Schedule a document for sync retry using Frappe's background jobs.
    
    Args:
        doctype (str): DocType name
        docname (str): Document name
        sync_log (str, optional): The name of the failed Sync Log entry.
        retry_after (int, optional): Retry after seconds.
    """
    if not sync_log:
        # Optionally, find the latest failed sync log if not provided
        latest_failed = frappe.get_all(
            "Sync Log",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname,
                "status": "Error",
                "direction": "Outbound", # Usually only retry outbound
                "retry_scheduled": 0
            },
            order_by="sync_datetime desc",
            limit=1
        )
        if not latest_failed:
            frappe.logger().info(f"No failed, unscheduled sync log found for {doctype} {docname}. Skipping retry schedule.")
            return
        sync_log = latest_failed[0].name

    try:
        # Mark the specific sync log for retry
        frappe.db.set_value("Sync Log", sync_log, "retry_scheduled", 1)
        
        # Enqueue the retry job
        frappe.enqueue(
            "migration_portal.migration_portal.utils.sync_utils.retry_sync",
            queue="short", # Or choose appropriate queue
            timeout=600,
            doctype=doctype,
            docname=docname,
            sync_log_name=sync_log,
            enqueue_after_commit=True,
            # Frappe < v14 might use `run_at` instead of `enqueue_after`
            # run_at = frappe.utils.add_to_date(None, seconds=retry_after)
            # For Frappe v14+, enqueue_after expects seconds delay
            enqueue_after=retry_after 
        )
        frappe.logger().info(f"Scheduled retry for {doctype} {docname} (Sync Log: {sync_log}) after {retry_after} seconds.")
    except Exception as e:
         frappe.log_error(f"Failed to schedule sync retry for {doctype} {docname}: {e}", "Sync Retry Schedule Error")
         # Optionally, unmark the sync log if enqueue fails
         frappe.db.set_value("Sync Log", sync_log, "retry_scheduled", 0)


def retry_sync(doctype, docname, sync_log_name):
    """
    Background job function to retry a failed sync operation.
    
    Args:
        doctype (str): DocType name.
        docname (str): Document name.
        sync_log_name (str): Sync Log document name that triggered the retry.
    """
    try:
        # Get the document
        doc = frappe.get_doc(doctype, docname)
        
        # Get the sync log
        log = frappe.get_doc("Sync Log", sync_log_name)
        
        # Increment retry count on the log
        log.db_set("retry_count", log.retry_count + 1)
        log.db_set("retry_scheduled", 0) # Mark as no longer scheduled for this attempt
        # No need for log.save() when using db_set
        
        # Call the appropriate sync method based on doctype
        # This needs to be implemented in the respective doctype controllers
        if hasattr(doc, 'sync_to_flyout') and callable(doc.sync_to_flyout):
            frappe.logger().info(f"Retrying sync for {doctype} {docname} (Log: {sync_log_name})")
            doc.sync_to_flyout(is_retry=True, originating_log=sync_log_name)
            # The sync_to_flyout method should handle creating new success/error logs
        else:
             frappe.log_error(f"Cannot retry sync for {doctype} {docname}: No sync_to_flyout method found.", "Sync Retry Error")
             # Update the original log to indicate permanent failure? Maybe not here.

    except Exception as e:
        frappe.log_error(f"Error during sync retry for {doctype} {docname} (Log: {sync_log_name}): {e}", "Sync Retry Execution Error")
        # Log the error in the original sync log? 
        try:
             log = frappe.get_doc("Sync Log", sync_log_name)
             log.db_set("error_message", f"Retry failed: {str(e)}\n{frappe.get_traceback()}")
             # Decide if we should reschedule again or mark as permanently failed after N retries
        except Exception as log_e:
             frappe.log_error(f"Failed to update sync log {sync_log_name} after retry error: {log_e}", "Sync Log Update Error")

# Add other utility functions as needed, e.g., for communication 