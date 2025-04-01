# Workflow definition for Inquiry DocType
# This file will contain the Frappe Workflow definition
# Example structure (needs to be defined according to guide.txt or requirements):

'''
workflow_states = [
	{"state": "New", "doc_status": 0},
	{"state": "Under Review", "doc_status": 1},
	{"state": "Converted", "doc_status": 1},
	{"state": "Rejected", "doc_status": 2}
]

workflow_transitions = [
	{
		"state": "New", 
		"action": "Review", 
		"next_state": "Under Review", 
		"allowed": "Migration Manager"
	},
	{
		"state": "Under Review", 
		"action": "Convert", 
		"next_state": "Converted", 
		"allowed": "Migration Manager",
		# Add condition: link to Client must exist? or handled in code?
	},
	{
		"state": "Under Review", 
		"action": "Reject", 
		"next_state": "Rejected", 
		"allowed": "Migration Manager"
	}
]
''' 