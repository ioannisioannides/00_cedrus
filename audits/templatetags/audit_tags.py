from django import template

register = template.Library()


@register.simple_tag
def get_audit_progress(audit):
    """
    Returns the progress state of an audit for the progress tracker.
    """
    status = audit.status

    steps = [
        {"id": 1, "label": "Planning", "statuses": ["draft", "scheduled"]},
        {"id": 2, "label": "Field Audit", "statuses": ["in_progress"]},
        {"id": 3, "label": "Reporting", "statuses": ["report_draft", "client_review"]},
        {"id": 4, "label": "Tech Review", "statuses": ["submitted", "technical_review"]},
        {"id": 5, "label": "Decision", "statuses": ["decision_pending", "decided", "closed"]},
    ]

    current_step_index = 1  # Default to 1
    found = False

    for step in steps:
        if status in step["statuses"]:
            current_step_index = step["id"]
            found = True
            break

    if not found and status == "cancelled":
        current_step_index = -1

    # Calculate progress percentage (0 to 100)
    # We have 4 intervals between 5 steps.
    # If we are at step 1, progress is 0.
    # If we are at step 5, progress is 100.
    if current_step_index > 0:
        progress_percent = (current_step_index - 1) * 25
    else:
        progress_percent = 0

    return {"steps": steps, "current_step": current_step_index, "progress_percent": progress_percent, "status": status}
