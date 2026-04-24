app_name = "poultry_farm"
app_title = "Poultry Farm"
app_publisher = "Njoroge Francis"
app_description = "Poultry Farm Management"
app_email = "franciskamande2001@gmail.com"
app_license = "mit"

# Document Events
doc_events = {
	"Flock Daily Record": {
		"after_save": "poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.after_save",
		"on_submit":  "poultry_farm.poultry.doctype.flock_daily_record.flock_daily_record.on_submit",
	},
	"Feed Purchase Entry": {
		"on_submit": "poultry_farm.poultry.doctype.feed_purchase_entry.feed_purchase_entry.on_submit",
		"on_cancel": "poultry_farm.poultry.doctype.feed_purchase_entry.feed_purchase_entry.on_cancel",
	},
	"Bird Collection Entry": {
		"on_submit": "poultry_farm.poultry.doctype.bird_collection_entry.bird_collection_entry.on_submit",
		"on_cancel": "poultry_farm.poultry.doctype.bird_collection_entry.bird_collection_entry.on_cancel",
	},
}

# Scheduled Tasks
scheduler_events = {
	"daily": [
		"poultry_farm.poultry.scheduled.create_daily_records",
	],
	"weekly": [
		"poultry_farm.poultry.scheduled.send_weekly_summary",
	],
}

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "poultry_farm",
# 		"logo": "/assets/poultry_farm/logo.png",
# 		"title": "Poultry Farm",
# 		"route": "/poultry_farm",
# 		"has_permission": "poultry_farm.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/poultry_farm/css/poultry_farm.css"
# app_include_js = "/assets/poultry_farm/js/poultry_farm.js"

# include js, css files in header of web template
# web_include_css = "/assets/poultry_farm/css/poultry_farm.css"
# web_include_js = "/assets/poultry_farm/js/poultry_farm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "poultry_farm/public/scss/website"

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
# app_include_icons = "poultry_farm/public/icons.svg"

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
# 	"methods": "poultry_farm.utils.jinja_methods",
# 	"filters": "poultry_farm.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "poultry_farm.install.before_install"
# after_install = "poultry_farm.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "poultry_farm.uninstall.before_uninstall"
# after_uninstall = "poultry_farm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "poultry_farm.utils.before_app_install"
# after_app_install = "poultry_farm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "poultry_farm.utils.before_app_uninstall"
# after_app_uninstall = "poultry_farm.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "poultry_farm.notifications.get_notification_config"

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
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"poultry_farm.tasks.all"
# 	],
# 	"daily": [
# 		"poultry_farm.tasks.daily"
# 	],
# 	"hourly": [
# 		"poultry_farm.tasks.hourly"
# 	],
# 	"weekly": [
# 		"poultry_farm.tasks.weekly"
# 	],
# 	"monthly": [
# 		"poultry_farm.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "poultry_farm.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "poultry_farm.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "poultry_farm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["poultry_farm.utils.before_request"]
# after_request = ["poultry_farm.utils.after_request"]

# Job Events
# ----------
# before_job = ["poultry_farm.utils.before_job"]
# after_job = ["poultry_farm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"poultry_farm.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

