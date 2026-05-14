---
applyTo: "**/*.py"
---

# Django & DRF Coding Patterns — Cedrus

## Model Layer (`adapters/models.py`)

- Use `models.TextChoices` for all enum-like fields
- Put business rules in `clean()` — called by forms, serializers, and `full_clean()`
- Use `save(update_fields=[...])` for targeted updates to avoid race conditions
- Always use `select_related()` / `prefetch_related()` in querysets returning lists
- Index foreign keys that are frequently filtered

```python
class AuditStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted to CB"

class Audit(models.Model):
    status = models.CharField(max_length=30, choices=AuditStatus.choices, default=AuditStatus.DRAFT)
    
    def clean(self):
        self._validate_status_transition()
        self._validate_organization_consistency()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

## API Layer (`api/views/`, `api/serializers.py`)

- ViewSets declare `permission_classes` and `authentication_classes` explicitly
- `get_queryset()` always scopes to the requesting user's accessible objects
- Serializer `validate_<field>` for field-level checks; `validate()` for cross-field
- Use `read_only_fields` in serializer Meta; never expose write access to auto-set fields
- Return 400 for validation errors, 403 for permission errors, 404 for not found

```python
class AuditViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAuditorOrAdmin]
    serializer_class = AuditSerializer
    
    def get_queryset(self):
        return AuditQueryService.for_user(self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
```

## Service Layer (`domain/`, `application/`)

- Services are stateless — pure functions or classes with no instance state
- Services raise `ValidationError` or `PermissionDenied` — never return None silently
- Services return domain objects, not HTTP responses

```python
class AuditWorkflowService:
    @staticmethod
    def close(audit: Audit, actor: User) -> Audit:
        if not actor.has_perm("audit_management.close_audit"):
            raise PermissionDenied("Only CB Admins can close audits.")
        if audit.findings.filter(status="open").exists():
            raise ValidationError("All findings must be resolved before closing.")
        audit.status = AuditStatus.CLOSED
        audit.save(update_fields=["status", "updated_at"])
        AuditClosedEvent.fire(audit=audit, actor=actor)
        return audit
```

## Forms Layer (`forms/`)

- Use `ModelForm` for all model-backed forms
- Override `__init__` to filter queryset choices by organization
- Always call `super().clean()` in form clean methods

## Query Parameter Validation

Always cast numeric parameters before filtering:

```python
org_id = request.GET.get("organization")
if org_id:
    try:
        queryset = queryset.filter(organization_id=int(org_id))
    except (ValueError, TypeError):
        pass
```

## Import Order

1. Standard library
2. Django
3. Third-party (DRF, Celery, etc.)
4. Local (`from audit_management.models import ...`)
