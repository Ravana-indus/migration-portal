import frappe
import requests
import json
from frappe.utils import now_datetime, get_datetime
import time

def push_inquiry_updates(data, settings=None):
    """
    Stub function for pushing inquiry updates to FlyOut
    
    Args:
        data (dict or Document): Data to push
        settings (Document, optional): FlyOut Account Settings document
    
    Returns:
        dict: Result with success status and message
    """
    try:
        # Just log the call for now
        frappe.logger().info(f"push_inquiry_updates called with data: {data}")
        
        # Mock successful response
        return {
            "success": True,
            "message": "Data sync simulated successfully"
        }
    except Exception as e:
        frappe.logger().error(f"Error in push_inquiry_updates: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

def push_client_updates(data, settings=None):
    """
    Stub function for pushing client updates to FlyOut
    
    Args:
        data (dict): Client data to push
        settings (Document, optional): FlyOut Account Settings document
    
    Returns:
        dict: Result with success status and message
    """
    try:
        # Just log the call for now
        frappe.logger().info(f"push_client_updates called with data: {data}")
        
        # Log the sync attempt
        from migration_portal.migration_portal.api.flyout import log_sync_attempt
        log_sync_attempt("Client", data.get("inquiry_id"), "PUSH", data, {"success": True, "message": "Simulated success"})
        
        # Mock successful response
        return {
            "success": True,
            "message": "Client data sync simulated successfully"
        }
    except Exception as e:
        frappe.logger().error(f"Error in push_client_updates: {str(e)}")
        return {
            "success": False,
            "message": str(e)
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
                 # Use json parameter for requests library to handle serialization and content-type
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
                # Exponential backoff: 2s, 4s, 8s, ...
                time.sleep(retry_delay * (2 ** (retry_count - 1))) 
            
    # If loop completes, all retries failed. Raise the last exception.
    if last_exception:
         raise last_exception
    else:
         # Should not happen if max_retries > 0, but handle defensively
         raise requests.exceptions.RequestException("API request failed after retries, but no exception was captured.")


def schedule_sync(doctype, docname, retry_after=300):
    """
    Stub function for scheduling a document for sync retry
    
    Args:
        doctype (str): DocType name
        docname (str): Document name
        retry_after (int, optional): Retry after seconds
    """
    frappe.logger().info(f"schedule_sync called for {doctype} {docname}")
    
    # For now, just log the call without actual scheduling
    pass


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
        
        # Call the appropriate sync method based on doctype
        if hasattr(doc, 'sync_to_flyout') and callable(doc.sync_to_flyout):
            frappe.logger().info(f"Retrying sync for {doctype} {docname} (Log: {sync_log_name})")
            doc.sync_to_flyout(is_retry=True, originating_log=sync_log_name)
        else:
             frappe.log_error(f"Cannot retry sync for {doctype} {docname}: No sync_to_flyout method found.", "Sync Retry Error")

    except Exception as e:
        frappe.log_error(f"Error during sync retry for {doctype} {docname} (Log: {sync_log_name}): {e}", "Sync Retry Execution Error")
        # Log the error in the original sync log 
        try:
             log = frappe.get_doc("Sync Log", sync_log_name)
             # Append to error message to avoid overwriting original failure reason
             current_error = log.error_message or ""
             log.db_set("error_message", f"{current_error}\nRETRY FAILED: {str(e)}\n{frappe.get_traceback()}")
             # Decide if we should stop retrying after N attempts based on log.retry_count
        except Exception as log_e:
             frappe.log_error(f"Failed to update sync log {sync_log_name} after retry error: {log_e}", "Sync Log Update Error")

# Add other utility functions as needed, e.g., for communication 