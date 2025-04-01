# Workflow definition for Client DocType
# This file will contain the Frappe Workflow definition
# Example structure (needs to be defined according to guide.txt or requirements):

'''
workflow_states = [
	{"state": "Active", "doc_status": 1},
	{"state": "In Progress", "doc_status": 1},
	{"state": "Completed", "doc_status": 1},
	{"state": "Cancelled", "doc_status": 2}
]

workflow_transitions = [
	{
		"state": "Active", 
		"action": "Start Process", 
		"next_state": "In Progress", 
		"allowed": "Migration Consultant"
	},
	{
		"state": "In Progress", 
		"action": "Complete", 
		"next_state": "Completed", 
		"allowed": "Migration Consultant"
	},
	{
		"state": ["Active", "In Progress"], 
		"action": "Cancel", 
		"next_state": "Cancelled", 
		"allowed": "Migration Manager"
	}
]
''' 