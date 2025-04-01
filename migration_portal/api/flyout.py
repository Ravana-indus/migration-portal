import frappe
import json
import requests
from frappe import _
from frappe.utils import now_datetime, get_datetime

@frappe.whitelist(allow_guest=True)
def receive_inquiry(data=None, token=None):
    """
    Endpoint to receive new inquiry data from FlyOut
    
    Expected JSON format:
    {
        "inquiry_id": "FL-12345",
        "applicant_name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "service_type": "Study",
        "destination_country": "Australia",
        "source_country": "India",
        "created_at": "2023-05-20T12:34:56",
        "notes": "Interested in CS programs"
    }
    """
    # Validate token
    validate_flyout_token(token)
    
    # Parse data if not already parsed
    if isinstance(data, str):
        data = json.loads(data)
    
    # Validate required fields
    required_fields = ["inquiry_id", "applicant_name", "email", "phone", "service_type"]
    for field in required_fields:
        if field not in data:
            # Corrected error message and logic
            frappe.throw(f"Missing required field: {field} for FlyOut Inquiry ID {data.get('inquiry_id', 'N/A')}")

    # Check if inquiry already exists
    existing = frappe.db.get_value("Inquiry", {"flyout_inquiry_id": data["inquiry_id"]})

    # Set the in_sync flag to prevent recursive sync
    frappe.flags.in_sync = True

    try:
        if existing:
            # Update existing inquiry
            doc = frappe.get_doc("Inquiry", existing)

            # Update fields (only if provided)
            if "applicant_name" in data:
                doc.applicant_name = data["applicant_name"]
            if "email" in data:
                doc.contact_email = data["email"]
            if "phone" in data:
                doc.contact_phone = data["phone"]
            if "service_type" in data:
                doc.service_type = data["service_type"]
            if "destination_country" in data:
                doc.destination_country = data["destination_country"]
            if "notes" in data and data["notes"]: # Added check for non-empty notes
                # Append to existing notes
                if doc.notes:
                    doc.notes += f"\n\nUpdate from FlyOut ({now_datetime()}):\n{data.get('notes', '')}"
                else:
                    doc.notes = f"Update from FlyOut ({now_datetime()}):\n{data.get('notes', '')}"

            # Save the document
            doc.save(ignore_permissions=True) # Consider permissions? For now ignore.

            # Create sync log
            create_sync_log("Inbound", "Success", "Inquiry", doc.name, data["inquiry_id"], data)

            return {
                "success": True,
                "message": "Inquiry updated successfully",
                "inquiry": doc.name
            }
        else:
            # Create new inquiry
            doc = frappe.new_doc("Inquiry")
            doc.inquiry_source = "FlyOut"
            doc.flyout_inquiry_id = data["inquiry_id"]
            doc.applicant_name = data["applicant_name"]
            doc.contact_email = data["email"]
            doc.contact_phone = data["phone"]
            doc.service_type = data["service_type"]
            doc.status = "New" # Default status for new inquiries
            doc.inquiry_date = get_datetime(data.get("created_at", now_datetime())).date()

            # Optional fields
            if "destination_country" in data:
                doc.destination_country = data["destination_country"]
            if "notes" in data and data["notes"]: # Added check for non-empty notes
                doc.notes = f"From FlyOut:\n{data['notes']}"

            # Insert the document
            doc.insert(ignore_permissions=True) # Consider permissions? For now ignore.

            # Create sync log
            create_sync_log("Inbound", "Success", "Inquiry", doc.name, data["inquiry_id"], data)

            return {
                "success": True,
                "message": "Inquiry created successfully",
                "inquiry": doc.name
            }
    except Exception as e:
        # Log the error
        frappe.log_error(f"FlyOut Inquiry Sync Error: {str(e)}\nData: {data}", "FlyOut API Error")

        # Create error sync log
        create_sync_log("Inbound", "Error", "Inquiry", None, data.get("inquiry_id"), data, error_message=str(e))

        # Return error response
        frappe.throw(_("Error processing FlyOut inquiry: {0}").format(str(e))) # Throw instead of returning JSON error
    finally:
        # Reset the in_sync flag
        frappe.flags.in_sync = False


@frappe.whitelist(allow_guest=True)
def update_inquiry_status(data=None, token=None):
    """
    Endpoint to receive inquiry status updates from FlyOut

    Expected JSON format:
    {
        "inquiry_id": "FL-12345",
        "status": "Cancelled", # e.g., Cancelled, Closed, Active
        "reason": "Client found another provider",
        "updated_at": "2023-05-20T12:34:56"
    }
    """
    # Validate token
    validate_flyout_token(token)

    # Parse data if not already parsed
    if isinstance(data, str):
        data = json.loads(data)

    # Validate required fields
    if "inquiry_id" not in data or "status" not in data:
        frappe.throw(_("Missing required fields: inquiry_id, status"))

    # Find the inquiry
    inquiry_name = frappe.db.get_value("Inquiry", {"flyout_inquiry_id": data["inquiry_id"]})
    if not inquiry_name:
         frappe.throw(_("Inquiry with FlyOut ID {0} not found").format(data['inquiry_id']))

    # Set the in_sync flag to prevent recursive sync
    frappe.flags.in_sync = True

    try:
        # Get the inquiry document
        doc = frappe.get_doc("Inquiry", inquiry_name)

        # Map FlyOut status to our status (Adjust as per actual FlyOut statuses)
        status_map = {
            "Cancelled": "Rejected",
            "Closed": "Rejected", # Assuming Closed means rejected from FlyOut perspective
            "Active": "Under Review" # Assuming Active maps to Under Review
            # Add more mappings as needed based on FlyOut's status lifecycle
        }

        new_status = status_map.get(data["status"])

        if new_status and new_status != doc.status:
            # Add a comment about the status change
            reason = data.get("reason", "No reason provided")
            doc.add_comment("Info", f"Status changed by FlyOut to {data['status']}. Reason: {reason}")

            # Update the status
            # Note: This might trigger workflows. Ensure workflows handle this external change.
            doc.status = new_status

            # Add notes if provided (optional, could be part of the reason)
            if "notes" in data and data["notes"]:
                 if doc.notes:
                     doc.notes += f"\n\nStatus Update Notes from FlyOut ({now_datetime()}):\n{data['notes']}"
                 else:
                     doc.notes = f"Status Update Notes from FlyOut ({now_datetime()}):\n{data['notes']}"

            # Save the document
            doc.save(ignore_permissions=True) # Consider permissions

            # Create sync log
            create_sync_log("Inbound", "Success", "Inquiry", doc.name, data["inquiry_id"], data)

            return {
                "success": True,
                "message": "Inquiry status updated successfully"
            }
        else:
            # If status doesn't map or hasn't changed, log info and return success
            if not new_status:
                 frappe.logger().info(f"FlyOut status '{data['status']}' for Inquiry {doc.name} has no defined mapping.")
            else: # Status hasn't changed
                 frappe.logger().info(f"FlyOut status update for Inquiry {doc.name} matches current status '{doc.status}'. No change applied.")

            # Create sync log for information even if no change applied
            create_sync_log("Inbound", "Success", "Inquiry", doc.name, data["inquiry_id"], data, response_data={"message": "No status change applied or mapping not found."})

            return {
                "success": True,
                "message": "Inquiry status update received, no change applied."
             }

    except Exception as e:
        # Log the error
        frappe.log_error(f"FlyOut Status Update Error: {str(e)}\nData: {data}", "FlyOut API Error")

        # Create error sync log
        create_sync_log("Inbound", "Error", "Inquiry", inquiry_name, data["inquiry_id"], data, error_message=str(e))

        # Return error response
        frappe.throw(_("Error updating inquiry status from FlyOut: {0}").format(str(e)))
    finally:
        # Reset the in_sync flag
        frappe.flags.in_sync = False


def validate_flyout_token(token):
    """Validate the API token from FlyOut"""
    if not token:
        frappe.throw(_("Authentication token is required"), frappe.AuthenticationError)

    # Get settings
    settings = frappe.get_cached_doc("FlyOut Account Settings")

    # Check if sync is enabled first
    if not settings.enable_sync:
        frappe.throw(_("Synchronization is disabled in FlyOut Account Settings"), frappe.ValidationError)

    # Check if token matches
    # Use get_password for secure retrieval
    api_key = settings.get_password('api_key')
    if not api_key or api_key != token:
        frappe.throw(_("Invalid authentication token"), frappe.AuthenticationError)


def create_sync_log(direction, status, doctype=None, docname=None, flyout_id=None, request_data=None, response_data=None, error_message=None):
    """Create a sync log entry"""
    try:
        log = frappe.new_doc("Sync Log")
        log.sync_datetime = now_datetime()
        log.direction = direction
        log.status = status

        if doctype:
            log.reference_doctype = doctype
        if docname:
            log.reference_name = docname
        if flyout_id:
            log.flyout_reference_id = flyout_id

        # Get endpoint from settings if possible, otherwise use placeholder
        try:
            settings = frappe.get_cached_doc("FlyOut Account Settings")
            # Make endpoint more specific based on function call if possible
            if direction == "Inbound" and "receive_inquiry" in frappe.request.path:
                 log.endpoint = f"{settings.flyout_base_url}/webhooks/inquiry" # Example
            elif direction == "Inbound" and "update_inquiry_status" in frappe.request.path:
                 log.endpoint = f"{settings.flyout_base_url}/webhooks/status" # Example
            elif direction == "Outbound":
                 # Determine outbound endpoint based on context if possible, e.g., passed in request_data
                 log.endpoint = "Outbound Endpoint TBD" # Placeholder
            else:
                 log.endpoint = "Unknown"
        except Exception:
            log.endpoint = "FlyOut Settings not found"


        # Method based on direction or request
        log.method = frappe.request.method if frappe.request else ("POST" if direction == "Outbound" else "Webhook")

        # Store request and response data safely
        try:
            if request_data:
                log.request_data = json.dumps(request_data, indent=2) if isinstance(request_data, (dict, list)) else str(request_data)
        except Exception as e:
            log.request_data = f"Error serializing request data: {e}"

        try:
            if response_data:
                log.response_data = json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)
        except Exception as e:
            log.response_data = f"Error serializing response data: {e}"


        # Store error details if any
        if status == "Error" and error_message:
            log.error_type = "API Error" # Or determine more specific type if possible
            log.error_message = str(error_message)
            log.stack_trace = frappe.get_traceback()

        # Insert the log
        log.insert(ignore_permissions=True)

        return log.name
    except Exception as e:
        # Log error in creating sync log itself
        frappe.log_error(f"Failed to create Sync Log: {str(e)}", "Sync Log Creation Error")
        return None # Indicate failure 