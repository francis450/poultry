"""
Installs the five Poultry Farm approval workflows.

Run once after bench migrate:
    bench --site mysite.local execute poultry_farm.fixtures.create_workflows.create
"""

import frappe

# ---------------------------------------------------------------------------
# Workflow State master records
# Each state needs a record in tabWorkflow State before any Workflow can use it
# ---------------------------------------------------------------------------

WORKFLOW_STATES = [
    {"state": "Draft",                "style": ""},
    {"state": "Pending Approval",     "style": "Warning"},
    {"state": "Pending Verification", "style": "Warning"},
    {"state": "Pending Sign-off",     "style": "Warning"},
    {"state": "Approved",             "style": "Success"},
    {"state": "Verified",             "style": "Success"},
    {"state": "Signed Off",           "style": "Success"},
    {"state": "Rejected",             "style": "Danger"},
]

WORKFLOW_ACTIONS = [
    "Submit for Approval",
    "Submit for Verification",
    "Submit for Sign-off",
    "Approve",
    "Verify & Confirm",
    "Sign Off",
    "Reject",
    "Revise",
]


def _ensure_workflow_states():
    """Create any missing Workflow State master records."""
    for entry in WORKFLOW_STATES:
        if not frappe.db.exists("Workflow State", entry["state"]):
            ws = frappe.new_doc("Workflow State")
            ws.workflow_state_name = entry["state"]
            ws.style = entry["style"]
            ws.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"  [state created]  {entry['state']}")


def _ensure_workflow_actions():
    """Create any missing Workflow Action Master records."""
    for action in WORKFLOW_ACTIONS:
        if not frappe.db.exists("Workflow Action Master", action):
            wa = frappe.new_doc("Workflow Action Master")
            wa.workflow_action_name = action
            wa.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"  [action created] {action}")


# ---------------------------------------------------------------------------
# Workflow definitions
# ---------------------------------------------------------------------------

WORKFLOWS = [
    # -----------------------------------------------------------------------
    # 1. Feed Purchase Approval
    #    Farm Manager creates → Store Manager / Farm Director approves
    #    Approval triggers on_submit (creates ERPNext Stock Entry)
    # -----------------------------------------------------------------------
    {
        "workflow_name": "Feed Purchase Approval",
        "document_type": "Feed Purchase Entry",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "send_email_alert": 0,
        "states": [
            {"state": "Draft",            "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Store Manager", "is_optional_state": 0},
            {"state": "Approved",         "doc_status": "1", "allow_edit": "Farm Director", "is_optional_state": 0},
            {"state": "Rejected",         "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
        ],
        "transitions": [
            # Farm Manager submits for approval
            {"state": "Draft",            "action": "Submit for Approval", "next_state": "Pending Approval", "allowed": "Farm Manager"},
            # Store Manager can approve or reject
            {"state": "Pending Approval", "action": "Approve",             "next_state": "Approved",         "allowed": "Store Manager"},
            {"state": "Pending Approval", "action": "Reject",              "next_state": "Rejected",         "allowed": "Store Manager"},
            # Farm Director can also approve or reject
            {"state": "Pending Approval", "action": "Approve",             "next_state": "Approved",         "allowed": "Farm Director"},
            {"state": "Pending Approval", "action": "Reject",              "next_state": "Rejected",         "allowed": "Farm Director"},
            # Farm Manager revises a rejection
            {"state": "Rejected",         "action": "Revise",              "next_state": "Draft",            "allowed": "Farm Manager"},
        ],
    },

    # -----------------------------------------------------------------------
    # 2. Bird Collection Verification
    #    Farm Manager records harvest → Farm Director verifies
    #    Verification triggers on_submit (creates / updates Crop Financial Summary)
    # -----------------------------------------------------------------------
    {
        "workflow_name": "Bird Collection Verification",
        "document_type": "Bird Collection Entry",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "send_email_alert": 0,
        "states": [
            {"state": "Draft",                "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Pending Verification", "doc_status": "0", "allow_edit": "Farm Director", "is_optional_state": 0},
            {"state": "Verified",             "doc_status": "1", "allow_edit": "Farm Director", "is_optional_state": 0},
            {"state": "Rejected",             "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
        ],
        "transitions": [
            {"state": "Draft",                "action": "Submit for Verification", "next_state": "Pending Verification", "allowed": "Farm Manager"},
            {"state": "Pending Verification", "action": "Verify & Confirm",        "next_state": "Verified",             "allowed": "Farm Director"},
            {"state": "Pending Verification", "action": "Reject",                  "next_state": "Rejected",             "allowed": "Farm Director"},
            {"state": "Rejected",             "action": "Revise",                  "next_state": "Draft",                "allowed": "Farm Manager"},
        ],
    },

    # -----------------------------------------------------------------------
    # 3. Treatment Medical Sign-off
    #    Farm Manager logs treatment → Farm Manager or Farm Director signs off
    #    Sign-off triggers on_submit (propagates cost to Crop Financial Summary)
    # -----------------------------------------------------------------------
    {
        "workflow_name": "Treatment Medical Sign-off",
        "document_type": "Crop Treatment Entry",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "send_email_alert": 0,
        "states": [
            {"state": "Draft",            "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Pending Sign-off", "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Signed Off",       "doc_status": "1", "allow_edit": "Farm Director", "is_optional_state": 0},
            {"state": "Rejected",         "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
        ],
        "transitions": [
            {"state": "Draft",            "action": "Submit for Sign-off", "next_state": "Pending Sign-off", "allowed": "Farm Manager"},
            {"state": "Pending Sign-off", "action": "Sign Off",            "next_state": "Signed Off",       "allowed": "Farm Manager"},
            {"state": "Pending Sign-off", "action": "Sign Off",            "next_state": "Signed Off",       "allowed": "Farm Director"},
            {"state": "Pending Sign-off", "action": "Reject",              "next_state": "Rejected",         "allowed": "Farm Manager"},
            {"state": "Pending Sign-off", "action": "Reject",              "next_state": "Rejected",         "allowed": "Farm Director"},
            {"state": "Rejected",         "action": "Revise",              "next_state": "Draft",            "allowed": "Farm Manager"},
        ],
    },

    # -----------------------------------------------------------------------
    # 4. Consumable Sheet Approval
    #    Store Manager creates → Farm Manager approves
    #    Approval triggers on_submit (updates Crop Financial Summary.consumable_cost)
    # -----------------------------------------------------------------------
    {
        "workflow_name": "Consumable Sheet Approval",
        "document_type": "Crop Consumable Sheet",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "send_email_alert": 0,
        "states": [
            {"state": "Draft",            "doc_status": "0", "allow_edit": "Store Manager", "is_optional_state": 0},
            {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Approved",         "doc_status": "1", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Rejected",         "doc_status": "0", "allow_edit": "Store Manager", "is_optional_state": 0},
        ],
        "transitions": [
            {"state": "Draft",            "action": "Submit for Approval", "next_state": "Pending Approval", "allowed": "Store Manager"},
            {"state": "Draft",            "action": "Submit for Approval", "next_state": "Pending Approval", "allowed": "Farm Manager"},
            {"state": "Pending Approval", "action": "Approve",             "next_state": "Approved",         "allowed": "Farm Manager"},
            {"state": "Pending Approval", "action": "Approve",             "next_state": "Approved",         "allowed": "Farm Director"},
            {"state": "Pending Approval", "action": "Reject",              "next_state": "Rejected",         "allowed": "Farm Manager"},
            {"state": "Pending Approval", "action": "Reject",              "next_state": "Rejected",         "allowed": "Farm Director"},
            {"state": "Rejected",         "action": "Revise",              "next_state": "Draft",            "allowed": "Store Manager"},
            {"state": "Rejected",         "action": "Revise",              "next_state": "Draft",            "allowed": "Farm Manager"},
        ],
    },

    # -----------------------------------------------------------------------
    # 5. Labor Entry Approval
    #    Farm Manager creates → Farm Director approves
    #    Approval triggers on_submit (updates Crop Financial Summary.labor_cost)
    # -----------------------------------------------------------------------
    {
        "workflow_name": "Labor Entry Approval",
        "document_type": "Crop Labor Entry",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "send_email_alert": 0,
        "states": [
            {"state": "Draft",            "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
            {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Farm Director", "is_optional_state": 0},
            {"state": "Approved",         "doc_status": "1", "allow_edit": "Farm Director", "is_optional_state": 0},
            {"state": "Rejected",         "doc_status": "0", "allow_edit": "Farm Manager",  "is_optional_state": 0},
        ],
        "transitions": [
            {"state": "Draft",            "action": "Submit for Approval", "next_state": "Pending Approval", "allowed": "Farm Manager"},
            {"state": "Pending Approval", "action": "Approve",             "next_state": "Approved",         "allowed": "Farm Director"},
            {"state": "Pending Approval", "action": "Reject",              "next_state": "Rejected",         "allowed": "Farm Director"},
            {"state": "Rejected",         "action": "Revise",              "next_state": "Draft",            "allowed": "Farm Manager"},
        ],
    },
]


# ---------------------------------------------------------------------------
# Installer
# ---------------------------------------------------------------------------

def create():
    """Create all Poultry Farm workflows. Safe to re-run (idempotent)."""
    _ensure_workflow_states()
    _ensure_workflow_actions()

    for wf_data in WORKFLOWS:
        name = wf_data["workflow_name"]

        if frappe.db.exists("Workflow", name):
            # Deactivate first so existing documents are not locked during delete
            frappe.db.set_value("Workflow", name, "is_active", 0)
            frappe.db.commit()
            frappe.delete_doc("Workflow", name, ignore_permissions=True, force=True)
            print(f"  [replaced] {name}")

        doc = frappe.new_doc("Workflow")
        doc.workflow_name       = name
        doc.document_type       = wf_data["document_type"]
        doc.workflow_state_field = wf_data["workflow_state_field"]
        doc.is_active           = wf_data["is_active"]
        doc.send_email_alert    = wf_data["send_email_alert"]

        for state in wf_data["states"]:
            doc.append("states", state)

        for transition in wf_data["transitions"]:
            doc.append("transitions", transition)

        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  [created]  {name}  →  {wf_data['document_type']}")

    print("\nDone. Run 'bench --site <site> migrate' if you have not already.")
