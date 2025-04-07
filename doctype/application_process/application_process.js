frappe.ui.form.on('Application Process', {
    refresh: function(frm) {
        // Update statuses based on document collection
        frm.add_custom_button(__('Update Document Status'), function() {
            update_document_status(frm);
        });
        
        // Show/hide appeal section based on decision
        if(frm.doc.decision === 'Rejected') {
            frm.toggle_display('appeal_section', true);
        } else {
            frm.toggle_display('appeal_section', false);
        }
    },
    
    decision: function(frm) {
        // Show/hide appeal section when decision changes
        if(frm.doc.decision === 'Rejected') {
            frm.toggle_display('appeal_section', true);
        } else {
            frm.toggle_display('appeal_section', false);
            frm.set_value('appeal_filed', 0);
        }
    },
    
    application_fees_paid: function(frm) {
        if(!frm.doc.application_fees_paid) {
            frm.set_value('application_fee_date', '');
            frm.set_value('application_fee_amount', '');
        }
    },
    
    biometrics_required: function(frm) {
        if(!frm.doc.biometrics_required) {
            frm.set_value('biometrics_appointment', '');
            frm.set_value('biometrics_completed', 0);
        }
    },
    
    interview_required: function(frm) {
        if(!frm.doc.interview_required) {
            frm.set_value('interview_date', '');
            frm.set_value('interview_completed', 0);
            frm.set_value('interview_notes', '');
        }
    }
});

function update_document_status(frm) {
    let total = 0;
    let completed = 0;
    
    // Count total and completed documents
    frm.doc.document_checklist.forEach(function(doc) {
        if(doc.status !== 'Not Required') {
            total += 1;
            if(doc.status === 'Verified') {
                completed += 1;
            }
        }
    });
    
    // Update document collection status
    if(total === 0) {
        frm.set_value('document_collection_status', 'Not Started');
    } else if(completed === total) {
        frm.set_value('document_collection_status', 'Completed');
    } else if(completed > 0) {
        frm.set_value('document_collection_status', 'In Progress');
    }
    
    frm.refresh_field('document_collection_status');
}