# CLAUDE.md — Karpathy-Inspired Coding Guidelines for Cedrus

> **Read this first.** These guidelines govern how Claude Code operates in this repository.
> Inspired by Andrej Karpathy's "vibe coding" philosophy — write code that is direct, honest, and verifiable.

---

## 1. Project Context

**Cedrus** is a Django 6 GRC (Governance, Risk, Compliance) platform used by Certification Bodies to conduct ISO external audits. It is a single-app Django project with DRF API, Celery workers, PostgreSQL, and Redis.

**Stack:**
- Python 3.13 · Django 6 · Django REST Framework · Celery · PostgreSQL
- IBM Carbon Design System (web components via CDN)
- uv for dependency management · ruff for linting · pytest-django for tests
- Deployed via Docker + Gunicorn + Nginx

**Domain:** Audit lifecycle management — from audit creation → team assignment → findings → client responses → certification decisions (ISO 17021 compliant).

---

## 2. Karpathy Principles Applied

### 2.1 Read Before Write
Always read the relevant files before changing them. Understand existing patterns. Do not guess.

```
# Good: read first
cat audit_management/models.py | grep "class Audit"
# Then write
```

### 2.2 Small, Verifiable Changes
Make the smallest change that solves the problem. Run tests after every non-trivial change.

```bash
uv run pytest -x -q  # fast fail, quiet
uv run ruff check .  # lint before commit
```

### 2.3 No Clever Code
Prefer boring, obvious code. If you need a comment to explain a line, simplify the line first.

```python
# Bad: clever
result = next((x for x in items if x.active), None)

# Good: obvious
result = None
for item in items:
    if item.active:
        result = item
        break
```

### 2.4 One Thing Per Function
Functions do one thing. If you find yourself writing "and" in a docstring, split the function.

### 2.5 Fail Loudly at Boundaries
Validate inputs at system boundaries (API endpoints, form submissions). Raise explicit errors. Never silently swallow exceptions.

```python
# Bad
try:
    result = do_something()
except Exception:
    pass

# Good
try:
    result = do_something()
except SpecificError as e:
    logger.error("Audit creation failed: %s", e)
    raise
```

### 2.6 Trust but Verify
After every AI-generated change, run the test suite. Never ship unverified code.

```bash
uv run pytest audit_management/tests/ -v
```

### 2.7 Make Impossible States Impossible
Use Django's field validators, model `clean()`, and DRF serializer `validate_*` to make invalid data structurally impossible to persist.

```python
# Good: invalid state cannot be saved
class Audit(models.Model):
    status = models.CharField(choices=AuditStatus.choices, ...)
    
    def clean(self):
        self._validate_status_transition()
        self._validate_organization_consistency()
```

---

## 3. Django Conventions (Strict)

### 3.1 Architecture Pattern
Follow the existing layered architecture:
```
adapters/models.py     → Domain models, business logic in clean()
api/views/             → DRF ViewSets, thin — no business logic
api/serializers.py     → Input validation at API boundary
domain/                → Domain services, workflow logic
application/           → Use cases (orchestrates domain services)
forms/                 → Django forms for template views
templates/             → HTML — no inline <script> blocks
```

### 3.2 ORM — Never Raw SQL
Use the Django ORM exclusively. If you think you need raw SQL, you probably need `annotate()` or `select_related()`.

```python
# Bad
cursor.execute("SELECT * FROM audits WHERE org_id = %s", [org_id])

# Good
Audit.objects.filter(organization_id=org_id).select_related("organization")
```

### 3.3 Thin Views
Views orchestrate. They do not contain business logic.

```python
# Bad: fat view
def audit_close(request, pk):
    audit = get_object_or_404(Audit, pk=pk)
    if audit.findings.filter(status="open").exists():
        audit.status = "closed"
        audit.save()
        send_notification(audit)

# Good: thin view
def audit_close(request, pk):
    audit = get_object_or_404(Audit, pk=pk)
    AuditWorkflowService.close(audit, actor=request.user)
```

### 3.4 Explicit Permissions
Every view must declare its permissions. No view should be accessible without explicit authentication and role checks.

```python
class AuditViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAuditorOrAdmin]
    
    def get_queryset(self):
        # Always scope to user's accessible audits
        return AuditQueryService.for_user(self.request.user)
```

### 3.5 Query Parameter Validation
Always cast numeric query parameters:

```python
org_id = request.GET.get("organization")
if org_id:
    try:
        queryset = queryset.filter(organization_id=int(org_id))
    except (ValueError, TypeError):
        pass
```

---

## 4. Security Rules (Non-Negotiable)

1. **DEBUG defaults to False** — requires explicit `DJANGO_DEBUG=True` in environment.
2. **No `unsafe-inline` in `script-src` CSP** — use external JS files with data attributes.
3. **No secrets in code** — all secrets via environment variables.
4. **File uploads**: validate extension AND MIME type, enforce size limits.
5. **Object-level permissions**: every API action must verify the user can access *that specific object*.
6. **CSRF**: DRF SessionAuthentication enforces CSRF on all state-changing endpoints.
7. **Rate limiting**: login endpoints protected by django-axes (5 attempts / 1 hour lockout).
8. **Input validation at boundaries**: validate all external data at API/form entry point.

---

## 5. Testing Discipline

### Required before every commit:
```bash
uv run ruff check .          # zero lint errors
uv run ruff format --check . # zero formatting errors
uv run bandit -c pyproject.toml -r . -ll  # zero security issues
uv run pytest -x -q          # all tests pass
```

### Test structure:
```python
# One test file per feature area
# audit_management/tests/test_audit_workflow.py

class TestAuditStatusTransitions:
    """Test that audit status machine enforces valid transitions."""
    
    def test_draft_to_client_review_requires_lead_auditor(self, audit_factory):
        audit = audit_factory(status="draft", lead_auditor=None)
        with pytest.raises(ValidationError, match="lead auditor"):
            audit.transition_to("client_review")
```

### Coverage target: ≥ 75% (enforced by CI)

---

## 6. Development Commands

```bash
# Install dependencies
uv sync --all-extras --dev

# Run development server
DJANGO_DEBUG=True uv run python manage.py runserver

# Run tests (fast)
uv run pytest -x -q

# Run tests with coverage
uv run pytest --cov --cov-report=html

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Security scan
uv run bandit -c pyproject.toml -r . -ll

# Vulnerability audit
pip freeze | pip-audit -r /dev/stdin

# Database migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser
```

---

## 7. Git Workflow

- Branch from `main` via feature branches: `feature/`, `fix/`, `chore/`
- Commit messages: conventional commits — `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `security:`
- Every PR requires CI to pass (lint + tests + security scan)
- Squash merge to keep `main` clean

---

## 8. What NOT to Do

| Don't | Do Instead |
|-------|-----------|
| Add features not in scope | Check BACKLOG.md, get approval |
| Refactor working code | Focus on the task |
| Add docstrings to unchanged code | Leave existing code alone |
| Use `print()` for debugging | Use `logger.debug()` |
| Import `*` | Explicit imports only |
| Write raw SQL | Use the ORM |
| Store secrets in code | Use environment variables |
| Add inline `<script>` in templates | Use external JS with data attributes |
| Catch and swallow exceptions | Log and re-raise or return error |
| Ship code without running tests | Always verify with the test suite |

---

## 9. Agent Roles

This repository uses a multi-agent system. Agents are defined in `.agents/`:

| Agent | Responsibility |
|-------|---------------|
| `orchestrator` | Strategic coordination, breaks down work |
| `engineer` | Implementation, bug fixes |
| `qa` | Test writing, quality verification |
| `security` | Security review, vulnerability assessment |
| `product_owner` | Backlog prioritisation, acceptance criteria |
| `architect` | Architecture decisions, patterns |
| `devops` | CI/CD, Docker, deployment |

---

## 10. File Location Map

```
cedrus/settings.py           → Development settings (DEBUG=False by default)
cedrus/settings_production.py→ Production overrides
cedrus/urls.py               → Root URL configuration
core/                        → Shared models: Organization, Site, Certification
identity/                    → Authentication, users, roles
audit_management/            → Core audit domain (the main application)
  adapters/models.py         → All Django models
  api/                       → DRF API layer
  domain/                    → Business logic services
  application/               → Use case orchestration
  templates/audits/          → Django templates
certification/               → Certification management
reporting/                   → PDF report generation
trunk/                       → Shared utilities, base classes
static/js/                   → External JavaScript (no inline scripts)
templates/                   → Base templates + app templates
docs/                        → Architecture, backlog, sprint docs
.agents/                     → AI agent role definitions
```
