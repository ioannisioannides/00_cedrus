# Code Standards

**Version:** 1.0  
**Last Updated:** November 21, 2025  
**Status:** Active

---

## Overview

This document defines the coding standards, best practices, and conventions for the Cedrus project. All contributors should follow these guidelines to maintain code quality, consistency, and maintainability.

---

## Python Coding Standards

### PEP 8 Compliance

All Python code must follow [PEP 8](https://pep8.org/) style guidelines.

**Line Length:**

- **Soft limit:** 100 characters
- **Hard limit:** 120 characters (enforced by Black formatter)
- **Exceptions:** Long URLs, import statements

**Indentation:**

- Use **4 spaces** per indentation level
- Never use tabs
- Hanging indents should align with opening delimiter

**Imports:**

- Group imports in this order (enforced by isort):
  1. Future imports
  2. Standard library
  3. Django core
  4. Third-party packages
  5. First-party/local imports

- One import per line for `import` statements
- Multiple imports allowed for `from` statements
- Avoid wildcard imports (`from module import *`)

**Example:**

```python
from __future__ import annotations

import os
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from identity.adapters.models import Profile
from core.models import Organization
```

### Code Formatting

**Black** is the official code formatter for Cedrus.

- All Python files are formatted with Black (120-char line length)
- Auto-format on save is enabled in VS Code
- Run manually: `black .`

**isort** organizes imports:

- Profile: Black-compatible
- Django-aware import sections
- Run manually: `isort .`

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Modules** | `snake_case` | `audit_service.py`, `finding_forms.py` |
| **Classes** | `PascalCase` | `Audit`, `AuditCreateView`, `FindingService` |
| **Functions** | `snake_case` | `create_audit()`, `validate_transition()` |
| **Variables** | `snake_case` | `audit_type`, `user_profile` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE`, `DEFAULT_STATUS` |
| **Private** | `_leading_underscore` | `_validate_data()`, `_internal_method()` |

**Django-Specific:**

| Element | Convention | Example |
|---------|------------|---------|
| **Models** | `PascalCase` (singular) | `Audit`, `Nonconformity`, `Finding` |
| **Views (class)** | `PascalCase` + `View` suffix | `AuditListView`, `AuditCreateView` |
| **Views (function)** | `snake_case` | `audit_detail`, `finding_delete` |
| **URL names** | `snake_case` | `audit_list`, `finding_create` |
| **Templates** | `snake_case.html` | `audit_detail.html`, `finding_form.html` |

### Docstrings

All public modules, classes, and functions **must** have docstrings.

**Format:** Google-style docstrings

**Module Docstrings:**

```python
"""
Views for audit management.

This module provides CRUD views for audits, including role-based
access control and workflow management.
"""
```

**Class Docstrings:**

```python
class AuditCreateView(CreateView):
    """
    Create a new audit (CB Admin only).
    
    This view allows CB Admins to create audits and assign them to
    lead auditors. The audit is created in 'draft' status.
    
    Permissions:
        Requires CB Admin role
        
    Template:
        audits/audit_form.html
    """
```

**Function/Method Docstrings:**

```python
def create_audit(organization, certifications, sites, audit_data, created_by):
    """
    Create a new audit with proper validation.
    
    Args:
        organization (Organization): The organization being audited
        certifications (list[Certification]): Certifications in scope
        sites (list[Site]): Sites covered by the audit
        audit_data (dict): Additional audit fields
        created_by (User): User creating the audit
        
    Returns:
        Audit: The newly created audit instance
        
    Raises:
        ValidationError: If audit data is invalid
        
    Example:
        >>> audit = create_audit(
        ...     organization=org,
        ...     certifications=[cert1, cert2],
        ...     sites=[site1],
        ...     audit_data={'audit_type': 'stage1'},
        ...     created_by=request.user
        ... )
    """
```

**When to Skip Docstrings:**

- Private methods (starting with `_`) may have brief docstrings or none
- Django framework methods (`get_queryset`, `form_valid`) if behavior is obvious
- One-line utility functions if the name is self-explanatory

### Type Hints

**Strongly encouraged** but not required for existing code.

**Usage:**

```python
from typing import Optional, List
from django.contrib.auth.models import User

def get_user_audits(user: User, status: Optional[str] = None) -> List[Audit]:
    """Get all audits for a user, optionally filtered by status."""
    queryset = Audit.objects.filter(lead_auditor=user)
    if status:
        queryset = queryset.filter(status=status)
    return list(queryset)
```

**Import from `typing`:**

- Use `from __future__ import annotations` for forward references
- Prefer `list[Model]` over `List[Model]` (Python 3.9+)
- Use `Optional[Type]` for nullable parameters

---

## Django Best Practices

### Models

**Model Design:**

- One model per logical entity
- Use descriptive field names
- Add `help_text` for clarity
- Define `Meta` class for ordering, indexes, verbose names

**Model Methods:**

- Override `clean()` for validation logic
- Override `save()` for pre-save processing
- Add custom methods for business logic
- Use `@property` for computed fields

**Example:**

```python
class Audit(models.Model):
    """Audit record for an organization."""
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        help_text="Organization being audited"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current audit status"
    )
    
    class Meta:
        ordering = ['-total_audit_date_from']
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]
        verbose_name = "Audit"
        verbose_name_plural = "Audits"
    
    def clean(self):
        """Validate audit data."""
        if self.total_audit_date_to < self.total_audit_date_from:
            raise ValidationError("End date must be after start date")
    
    @property
    def is_overdue(self):
        """Check if audit is past its scheduled end date."""
        return self.total_audit_date_to < timezone.now().date()
```

### Views

**Prefer Class-Based Views (CBVs):**

- Use CBVs for CRUD operations
- Use function-based views for complex workflows or one-off actions
- Mixins for reusable behavior

**View Organization:**

```python
class AuditListView(LoginRequiredMixin, ListView):
    """List audits with role-based filtering."""
    
    model = Audit
    template_name = 'audits/audit_list.html'
    context_object_name = 'audits'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter audits by user role."""
        # Custom queryset logic
        pass
    
    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        # Add custom context
        return context
```

**Business Logic Location:**

- **Models:** Simple validation, computed properties
- **Services:** Complex business logic, multi-model operations
- **Views:** Request handling, permission checks, context preparation
- **Forms:** Field validation, form-specific logic

**Example:**

```python
# ❌ BAD: Business logic in view
class AuditCreateView(CreateView):
    def form_valid(self, form):
        audit = form.save(commit=False)
        audit.created_by = self.request.user
        audit.save()
        # ... 50 lines of business logic
        return redirect('audit_detail', pk=audit.pk)

# ✅ GOOD: Business logic in service
class AuditCreateView(CreateView):
    def form_valid(self, form):
        audit = AuditService.create_audit(
            organization=form.cleaned_data['organization'],
            created_by=self.request.user,
            audit_data=form.cleaned_data
        )
        return redirect('audit_detail', pk=audit.pk)
```

### Forms

**Form Design:**

- One form per model or logical grouping
- Use `ModelForm` for database-backed forms
- Add `clean_*` methods for field-specific validation
- Add `clean()` for cross-field validation

**Example:**

```python
class AuditForm(forms.ModelForm):
    """Form for creating/editing audits."""
    
    class Meta:
        model = Audit
        fields = ['organization', 'audit_type', 'total_audit_date_from']
        widgets = {
            'total_audit_date_from': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_total_audit_date_from(self):
        """Validate audit start date is not in the past."""
        date = self.cleaned_data['total_audit_date_from']
        if date < timezone.now().date():
            raise forms.ValidationError("Audit date cannot be in the past")
        return date
    
    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        start = cleaned_data.get('total_audit_date_from')
        end = cleaned_data.get('total_audit_date_to')
        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date")
        return cleaned_data
```

### Templates

**Template Structure:**

- Extend from `base.html`
- Use template blocks: `{% block content %}`
- Keep logic minimal (use template tags)
- Use Bootstrap 5 components

**Naming:**

- `model_list.html` - List view
- `model_detail.html` - Detail view
- `model_form.html` - Create/update form
- `model_confirm_delete.html` - Delete confirmation

**Example:**

```django
{% extends "base.html" %}

{% block title %}Audit List{% endblock %}

{% block content %}
<div class="container">
    <h1>Audits</h1>
    
    {% for audit in audits %}
    <div class="card mb-3">
        <div class="card-body">
            <h5>{{ audit.organization.name }}</h5>
            <p>Status: {{ audit.get_status_display }}</p>
        </div>
    </div>
    {% empty %}
    <p>No audits found.</p>
    {% endfor %}
    
    {% include "pagination.html" %}
</div>
{% endblock %}
```

### URLs

**URL Patterns:**

- Use descriptive names (not `url1`, `url2`)
- Use `app_name` for namespacing
- Use `path()` over `re_path()` when possible
- Order from most specific to least specific

**Example:**

```python
# audits/urls.py
from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    path('', views.AuditListView.as_view(), name='audit_list'),
    path('create/', views.AuditCreateView.as_view(), name='audit_create'),
    path('<int:pk>/', views.AuditDetailView.as_view(), name='audit_detail'),
    path('<int:pk>/edit/', views.AuditUpdateView.as_view(), name='audit_update'),
    path('<int:pk>/delete/', views.AuditDeleteView.as_view(), name='audit_delete'),
]
```

---

## Git Commit Conventions

### Commit Message Format

```
<type>(<scope>): <subject>

<body (optional)>

<footer (optional)>
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(audits): Add audit workflow status transitions` |
| `fix` | Bug fix | `fix(findings): Correct NC verification status logic` |
| `docs` | Documentation only | `docs: Update README with deployment instructions` |
| `style` | Code style (formatting, no logic change) | `style: Run Black formatter on all Python files` |
| `refactor` | Code refactoring | `refactor(services): Extract audit creation to service layer` |
| `test` | Add or update tests | `test(audits): Add test for Stage 2 validation` |
| `chore` | Maintenance tasks | `chore: Update dependencies to latest versions` |
| `perf` | Performance improvement | `perf(queries): Add select_related to audit list view` |

### Scopes

Common scopes in Cedrus:

- `audits` - Audit management
- `findings` - Finding management (NCs, observations, OFIs)
- `core` - Core entities (organizations, sites, standards)
- `accounts` - User management and authentication
- `permissions` - Access control and permissions
- `workflows` - Status workflow logic
- `api` - API endpoints
- `docs` - Documentation
- `tests` - Test suite

### Examples

**Good Commit Messages:**

```
feat(audits): Add evidence file upload to findings

- Allow users to attach evidence files to findings
- Validate file types and size (10MB max)
- Store files in media/evidence/ directory

Closes #123
```

```
fix(workflows): Prevent Stage 2 audit without completed Stage 1

The workflow was allowing Stage 2 audits to be created even when
no completed Stage 1 audit existed. Added validation in
Audit.clean() method.

Fixes #456
```

```
docs: Update API reference with new endpoints

Added documentation for:
- Audit recommendation endpoints
- Evidence file management endpoints
- Workflow state transitions

Related to #789
```

**Bad Commit Messages:**

```
❌ Fixed bug
❌ Update code
❌ WIP
❌ Stuff
```

### Branch Naming

**Format:** `<type>/<short-description>`

**Examples:**

- `feat/audit-workflow-status`
- `fix/nc-verification-bug`
- `docs/update-readme`
- `refactor/extract-audit-service`

**Rules:**

- Use lowercase
- Use hyphens (not underscores)
- Be descriptive but concise
- Delete branches after merge

---

## Code Review Checklist

### For Reviewers

**Functionality:**

- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs

**Code Quality:**

- [ ] Code is readable and maintainable
- [ ] Naming is clear and consistent
- [ ] No unnecessary complexity
- [ ] DRY principle followed (Don't Repeat Yourself)

**Django Best Practices:**

- [ ] Business logic is in appropriate layer (model/service/view)
- [ ] Queries are optimized (use `select_related`/`prefetch_related`)
- [ ] Forms have proper validation
- [ ] Templates are well-structured

**Security:**

- [ ] No SQL injection vulnerabilities
- [ ] Proper authentication and authorization
- [ ] CSRF protection on forms
- [ ] File uploads are validated
- [ ] No sensitive data in logs

**Testing:**

- [ ] New features have tests
- [ ] Tests pass locally
- [ ] Test coverage is adequate
- [ ] Edge cases are tested

**Documentation:**

- [ ] Docstrings are present
- [ ] Comments explain "why", not "what"
- [ ] README updated if needed
- [ ] API docs updated if needed

**Performance:**

- [ ] No N+1 query problems
- [ ] Database indexes considered
- [ ] Caching considered (if applicable)
- [ ] File uploads handled efficiently

### For Contributors

**Before Submitting PR:**

- [ ] Run Black formatter: `black .`
- [ ] Run isort: `isort .`
- [ ] Run tests: `python manage.py test`
- [ ] Check for lint errors
- [ ] Update documentation
- [ ] Write clear commit messages
- [ ] Squash or rebase commits if needed

---

## Testing Standards

### Test Structure

**Test Location:**

- Unit tests: `tests.py` in app directory
- Integration tests: `test_integration.py`
- Specific feature tests: `test_<feature>.py`

**Test Naming:**

```python
class AuditModelTest(TestCase):
    """Tests for Audit model."""
    
    def test_audit_creation(self):
        """Test creating a basic audit."""
        pass
    
    def test_audit_validation_future_date(self):
        """Test that audits >1 year in future are rejected."""
        pass
```

**Pattern:** `test_<what>_<condition>`

### Test Coverage

**Target:** 80%+ test coverage

**Priority:**

1. **Critical business logic** - 100% coverage required
2. **Models** - 90%+ coverage
3. **Services** - 90%+ coverage
4. **Views** - 70%+ coverage
5. **Forms** - 80%+ coverage

**Run Coverage:**

```bash
coverage run --source='.' manage.py test
coverage report
coverage html
open htmlcov/index.html
```

---

## Security Standards

### Input Validation

- ✅ Always validate user input
- ✅ Use Django forms for validation
- ✅ Add model-level validation in `clean()`
- ✅ Sanitize HTML input
- ❌ Never trust user input

### Authentication & Authorization

- ✅ Use `@login_required` on all non-public views
- ✅ Use permission mixins for role-based access
- ✅ Check permissions in views and templates
- ❌ Never hardcode credentials

### Database Security

- ✅ Always use Django ORM (parameterized queries)
- ✅ Use `select_related`/`prefetch_related` to avoid N+1
- ❌ Never use raw SQL unless absolutely necessary
- ❌ Never construct queries with string formatting

### File Uploads

- ✅ Validate file types (whitelist approach)
- ✅ Limit file sizes (10MB default)
- ✅ Store outside web root
- ✅ Use unique filenames
- ❌ Never trust file extensions

### Production Settings

- ✅ Set `DEBUG = False`
- ✅ Use strong `SECRET_KEY` from environment
- ✅ Configure `ALLOWED_HOSTS`
- ✅ Use HTTPS in production
- ✅ Enable security middleware

See `docs/SECURITY_AUDIT_REPORT.md` for complete security checklist.

---

## Performance Standards

### Database Optimization

**Use `select_related()` for ForeignKey:**

```python
# ❌ BAD: N+1 queries
audits = Audit.objects.all()
for audit in audits:
    print(audit.organization.name)  # Query per audit!

# ✅ GOOD: Single query
audits = Audit.objects.select_related('organization')
for audit in audits:
    print(audit.organization.name)  # No extra queries
```

**Use `prefetch_related()` for ManyToMany:**

```python
# ❌ BAD: N+1 queries
audits = Audit.objects.all()
for audit in audits:
    print(audit.sites.all())  # Query per audit!

# ✅ GOOD: Two queries total
audits = Audit.objects.prefetch_related('sites')
for audit in audits:
    print(audit.sites.all())  # No extra queries
```

### Query Optimization

- Use `only()` or `defer()` for large models
- Add database indexes on frequently queried fields
- Use `count()` instead of `len(queryset)`
- Use `exists()` instead of `if queryset:`
- Use `iterator()` for large querysets

---

## Documentation Standards

### Required Documentation

1. **README.md** - Project overview, setup, usage
2. **CONTRIBUTING.md** - Contribution guidelines
3. **docs/ARCHITECTURE.md** - System architecture
4. **docs/MODELS.md** - Data model documentation
5. **docs/API_REFERENCE.md** - API endpoints
6. **docs/DEPLOYMENT.md** - Deployment guide

### Documentation Format

- Use **Markdown** (.md) for all documentation
- Include table of contents for long documents
- Add code examples where applicable
- Keep docs in sync with code
- Add version/date stamps

---

## Continuous Improvement

### Code Quality Monitoring

- **Lint errors:** Track and reduce over time
- **Test coverage:** Maintain >80%
- **Security:** Run audits quarterly
- **Performance:** Monitor query counts, page load times

### Sprint Reviews

- Review code quality metrics
- Identify technical debt
- Plan refactoring sprints
- Update standards document

---

## References

- [PEP 8 Style Guide](https://pep8.org/)
- [Django Coding Style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)

---

**Version History:**

- **1.0** (2025-11-21): Initial version for Sprint 7 Quality Excellence

---

**Questions or Suggestions?**

This is a living document. If you have suggestions for improvements, please:

1. Open an issue in the project repository
2. Discuss with the team
3. Submit a PR with proposed changes

**Maintained by:** Cedrus Development Team
