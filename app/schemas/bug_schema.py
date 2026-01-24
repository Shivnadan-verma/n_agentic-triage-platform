# AI assisted development
"""
Bug Schema - Defines required fields for bug payloads.

Required fields:
- bug_id: Unique identifier for the bug
- severity: Bug severity level (e.g., "High", "Critical", "Medium", "Low")
- product: Product name (e.g., "Checkout", "Orders")
- description: Description of the bug
- required_skills: List of skill names needed for the bug (e.g. ["Payments", "Java"])
"""

REQUIRED_BUG_FIELDS = [
    "bug_id",
    "severity",
    "product",
    "description",
    "required_skills"
]