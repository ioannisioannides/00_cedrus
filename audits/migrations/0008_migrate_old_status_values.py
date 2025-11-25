# Generated manually for status migration

from django.db import migrations


def migrate_status_values(apps, _schema_editor):
    """Migrate old status values to new workflow statuses."""
    Audit = apps.get_model("audits", "Audit")

    # Map old statuses to new ones
    status_mapping = {
        "draft": "draft",  # No change
        "in_review": "report_draft",  # Maps to report being reviewed internally
        "submitted_to_cb": "submitted",  # Maps to submitted
        "returned_for_correction": "report_draft",  # Back to draft state
        "technical_review": "submitted",  # Technical review happens after submission
        "decision_pending": "submitted",  # Waiting for decision
        "closed": "decided",  # Final state
    }

    for old_status, new_status in status_mapping.items():
        Audit.objects.filter(status=old_status).update(status=new_status)


def reverse_migrate_status_values(apps, _schema_editor):
    """Reverse migration - map new statuses back to old ones."""
    Audit = apps.get_model("audits", "Audit")

    # Reverse mapping (best effort)
    reverse_mapping = {
        "draft": "draft",
        "scheduled": "draft",
        "in_progress": "draft",
        "report_draft": "in_review",
        "client_review": "in_review",
        "submitted": "submitted_to_cb",
        "decided": "closed",
        "cancelled": "draft",
    }

    for new_status, old_status in reverse_mapping.items():
        Audit.objects.filter(status=new_status).update(status=old_status)


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0007_update_status_choices"),
    ]

    operations = [
        migrations.RunPython(migrate_status_values, reverse_migrate_status_values),
    ]
