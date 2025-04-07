app_name = "migration_portal"
app_title = "Migration Portal"
app_publisher = "RavanOS"
app_description = "Migration Services Portal with FlyOut Integration"
app_email = "info@example.com"
app_license = "MIT"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "migration_portal",
# 		"logo": "/assets/migration_portal/logo.png",
# 		"title": "Migration Portal",
# 		"route": "/migration_portal",
# 		"has_permission": "migration_portal.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/migration_portal/css/migration_portal.css"
app_include_js = "/assets/migration_portal/js/migration_portal.js"

# include js, css files in header of web template
# web_include_css = "/assets/migration_portal/css/migration_portal.css"
# web_include_js = "/assets/migration_portal/js/migration_portal.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "migration_portal/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "migration_portal/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "migration_portal.utils.jinja_methods",
# 	"filters": "migration_portal.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "migration_portal.install.before_install"
# after_install = "migration_portal.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "migration_portal.uninstall.before_uninstall"
# after_uninstall = "migration_portal.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "migration_portal.utils.before_app_install"
# after_app_install = "migration_portal.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "migration_portal.utils.before_app_uninstall"
# after_app_uninstall = "migration_portal.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "migration_portal.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "migration_portal.overrides.CustomToDo"
# }

# Document Events
doc_events = {
	"Inquiry": {
		# Commenting out sync hook temporarily
		# "on_update": "migration_portal.doctype.inquiry.inquiry.trigger_flyout_sync", 
	},
	"Client": {
	},
    "FlyOut Account Settings": {
        "on_update": "migration_portal.doctype.flyout_account_settings.flyout_account_settings.update_sync_status_on_save"
    }
}

# Fixtures 
# fixtures = [
#     {"dt": "Workflow", "filters": [["name", "in", ["Inquiry Workflow", "Client Workflow"]]]},
# ]

# Add Python type annotations (recommended)
export_python_type_annotations = True

# Other hooks commented out for simplicity during debug

