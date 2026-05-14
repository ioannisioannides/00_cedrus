---
applyTo: "**/test_*.py,**/tests.py,**/tests/**/*.py"
---

# pytest-django Testing Patterns — Cedrus

## Test Structure

```python
import pytest
from django.contrib.auth.models import Group

@pytest.mark.django_db
class TestAuditCreation:
    """Tests for audit creation business rules."""

    def test_draft_audit_requires_lead_auditor_on_submit(self, audit_factory, user_factory):
        """An audit cannot be submitted without a lead auditor."""
        lead = user_factory(groups=["lead_auditor"])
        audit = audit_factory(status="draft", lead_auditor=None)
        
        with pytest.raises(ValidationError, match="lead auditor"):
            AuditWorkflowService.submit(audit, actor=lead)
```

## Fixtures (conftest.py)

Use `pytest-factoryboy` or simple `@pytest.fixture` factories. Prefer minimal data — only create what the test needs.

```python
@pytest.fixture
def cb_admin(db):
    user = User.objects.create_user(username="admin", password="testpass")
    group = Group.objects.get_or_create(name="cb_admin")[0]
    user.groups.add(group)
    return user

@pytest.fixture
def audit(db, organization, cb_admin):
    return Audit.objects.create(
        organization=organization,
        title="Test Audit",
        status="draft",
        created_by=cb_admin,
    )
```

## Test Categories (use markers)

```python
@pytest.mark.unit          # Pure logic, no DB
@pytest.mark.django_db     # Requires database
@pytest.mark.integration   # Tests multiple layers together
@pytest.mark.security      # Permission/access control tests
```

## What to Test

1. **Model `clean()` validation** — invalid data raises `ValidationError`
2. **Status transitions** — valid and invalid paths
3. **Permissions** — each role can/cannot perform each action
4. **API endpoints** — create/read/update/delete with correct/incorrect roles
5. **Serializer validation** — boundary inputs, missing required fields
6. **Domain service rules** — business logic edge cases

## API Testing Pattern

```python
@pytest.mark.django_db
class TestAuditAPI:
    def test_client_cannot_create_audit(self, api_client, client_user):
        api_client.force_authenticate(user=client_user)
        response = api_client.post("/api/audits/", data={...})
        assert response.status_code == 403

    def test_cb_admin_can_create_audit(self, api_client, cb_admin, valid_audit_data):
        api_client.force_authenticate(user=cb_admin)
        response = api_client.post("/api/audits/", data=valid_audit_data)
        assert response.status_code == 201
```

## Running Tests

```bash
uv run pytest -x -q                  # Fast — stop at first failure
uv run pytest audit_management/ -v   # Verbose for a specific module
uv run pytest -k "test_audit"        # Filter by name
uv run pytest --cov --cov-report=html # Coverage report
```

## Coverage Target: ≥ 75%
