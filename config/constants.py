# Page Configuration
PAGE_CONFIG = {
    "page_title": "Timesheet App",
    "layout": "wide",
    "page_icon": "⏱️"
}

# Shared Mappings
PHASE_MAP = {
    "Analysis": "1",
    "Design": "2",
    "Development": "3",
    "Testing": "4",
    "Deployement": "5"
}

REV_PHASE_MAP = {v: k for k, v in PHASE_MAP.items()}

PHASE_OPTIONS = ["Analysis", "Design", "Development", "Testing", "Deployement"]

# Roles
ROLES = {
    "ADMIN": "admin",
    "EMPLOYEE": "employee"
}

# Navigation Menu Items
def get_nav_items(user_role):
    items = ["Timesheet", "Projects"]
    if user_role == "admin":
        items.extend(["Employees", "Reports", "Import Data"])
    return items
