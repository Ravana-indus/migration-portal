# Communication utilities init file 

import frappe
from frappe.utils import now_datetime, validate_email_address

@frappe.whitelist()
def log_communication(doctype, docname, communication_type, direction, subject, content, user=None):
    """Creates a Communication Log entry linked to a reference document.

    Args:
        doctype (str): Reference DocType (e.g., "Client", "Inquiry")
        docname (str): Reference Document Name
        communication_type (str): Type like "Email", "Phone Call", "Meeting"
        direction (str): "Incoming" or "Outgoing"
        subject (str): Subject line or topic
        content (str): Details of the communication
        user (str, optional): User involved. Defaults to session user.

    Returns:
        Document: The newly created Communication Log document.
    """
    try:
        comm_log = frappe.new_doc("Communication Log")
        comm_log.communication_date = now_datetime()
        comm_log.communication_type = communication_type
        comm_log.direction = direction
        comm_log.subject = subject
        comm_log.content = content
        comm_log.user = user or frappe.session.user
        comm_log.reference_doctype = doctype
        comm_log.reference_name = docname
        
        # If this Communication Log is part of a child table 
        # (e.g., within Client), set parent linkage.
        # This assumes it's being called where parent context is available, 
        # which isn't true for a generic utility function like this.
        # Instead, the calling function should add it to the parent's child table.
        # comm_log.parent = docname 
        # comm_log.parenttype = doctype
        # comm_log.parentfield = "communication_logs" # Check actual parent field name
        
        comm_log.insert(ignore_permissions=True) # Assuming system should log regardless of user role
        return comm_log

    except Exception as e:
        frappe.log_error(f"Failed to log communication for {doctype} {docname}: {e}", "Communication Util Error")
        return None

@frappe.whitelist()
def send_and_log_email(recipients, subject, message, reference_doctype=None, reference_name=None, attachments=None, send_real_email=True, add_to_reference_child_table=True):
    """Sends an email using Frappe's email queue and logs it.
    Optionally adds the log to the reference document's child table if it's a Client.

    Args:
        recipients (list or str): List of email addresses or comma-separated string.
        subject (str): Email subject.
        message (str): Email content (HTML or plain text).
        reference_doctype (str, optional): DocType to link the communication log to.
        reference_name (str, optional): Document name to link the communication log to.
        attachments (list, optional): List of dicts with {"fname": "...", "fcontent": "..."} or file paths.
        send_real_email (bool): Set to False for testing to prevent actual email sending.
        add_to_reference_child_table (bool): If True and reference is Client, add log to Client.communication_logs.

    Returns:
        dict: Result containing success status, email status, and optionally log name.
    """
    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(",") if validate_email_address(r.strip())]
    
    if not recipients:
        frappe.throw("No valid recipients provided for email.")
        
    comm_log_doc = None # Initialize
    email_status = "Unknown"
    success = False
    error_message = None

    try:
        # Prepare arguments for frappe.sendmail
        sendmail_args = {
            "recipients": recipients,
            "subject": subject,
            "message": message,
            "now": not send_real_email, # If False, send immediately for testing, else queue
            "attachments": attachments,
            "reference_doctype": reference_doctype, # Link email in Communication doctype
            "reference_name": reference_name
        }

        if send_real_email:
            frappe.sendmail(**sendmail_args)
            email_status = "Sent (Queued)"
            frappe.msgprint(f"Email to {', '.join(recipients)} queued for sending.", indicator="green")
        else:
            # If not sending real email, maybe just log it?
            email_status = "Not Sent (Test Mode)"
            frappe.msgprint(f"Email to {', '.join(recipients)} would be sent (Test Mode).", indicator="blue")
            # You might still want to log it even if not sent

        success = True

        # Log the communication if reference is provided
        if reference_doctype and reference_name:
            comm_log_doc = log_communication(
                doctype=reference_doctype,
                docname=reference_name,
                communication_type="Email",
                direction="Outgoing",
                subject=subject,
                content=message, # Or a summary?
                user=frappe.session.user
            )
            
            # --- Add Log to Client Child Table --- 
            if comm_log_doc and add_to_reference_child_table and reference_doctype == "Client":
                try:
                    client_doc = frappe.get_doc(reference_doctype, reference_name)
                    # Check if the field exists before appending
                    if hasattr(client_doc, "communication_logs"):
                         # Avoid duplicates if somehow called multiple times for same log
                        if not any(log.communication_log == comm_log_doc.name for log in client_doc.communication_logs):
                            client_doc.append("communication_logs", {
                                "communication_log": comm_log_doc.name 
                                # Add other fields here if the child table contains more than just the link
                            })
                            client_doc.save(ignore_permissions=True) # Save the client doc to persist the child table addition
                            frappe.msgprint(f"Email logged and linked to Client {reference_name}.", indicator="green")
                    else:
                         frappe.logger().warning(f"Child table 'communication_logs' not found on Client {reference_name}.")
                except Exception as e_link:
                    frappe.log_error(f"Failed to link Communication Log {comm_log_doc.name} to Client {reference_name}: {e_link}", "Communication Link Error")
                    frappe.msgprint(f"Email logged, but failed to link to Client: {e_link}", indicator="orange")
            # --- End Add Log --- 

    except Exception as e:
        error_message = str(e)
        success = False
        email_status = "Failed"
        frappe.log_error(frappe.get_traceback(), "Email Sending/Logging Error")
        frappe.msgprint(f"Failed to send/log email: {e}", indicator="red")
        # Log a failed attempt
        if reference_doctype and reference_name:
             # Still try to log the failure, but don't try to link it to child table
             comm_log_doc = log_communication(
                doctype=reference_doctype,
                docname=reference_name,
                communication_type="Email",
                direction="Outgoing",
                subject=f"[FAILED] {subject}",
                content=f"Attempt to send email failed.\nError: {e}\n\nMessage:\n{message}",
                user=frappe.session.user
            )
        
    return {
        "success": success, 
        "status": email_status, 
        "log_name": comm_log_doc.name if comm_log_doc else None, 
        "error": error_message
    } 