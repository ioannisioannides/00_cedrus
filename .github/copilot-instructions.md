# GitHub Copilot Instructions for Cedrus

> Karpathy-Inspired AI Coding Guidelines — Django GRC Platform

---

## Project

**Cedrus** is a Django 6 GRC (Governance, Risk, Compliance) platform for ISO 17021 external audit management by Certification Bodies.

**Stack:** Python 3.13 · Django 6 · DRF · Celery · PostgreSQL · Redis · IBM Carbon Design System · uv · ruff · pytest-django

---

## Core Principles (Karpathy-Inspired)

1. **Read before write** — understand existing code before changing it
2. **Small changes** — make the minimum change that solves the problem
3. **No clever code** — boring, obvious code beats clever code
4. **Verify everything** — run `uv run ruff check .` and `uv run pytest -x -q` after every change
5. **Fail loudly** — validate at boundaries, log errors, never silently swallow exceptions
6. **One thing per function** — if you need "and" in a docstring, split the function
7. **Make impossible states impossible** — use model validators, serializer validation, type hints

---

## Django Patterns (Strict)

### Architecture Layers
```
adapters/models.py  → Models + business rules in clean()
api/views/          → Thin DRF ViewSets (no business logic)
api/serializers.py  → Input validation at API boundary
domain/             → Domain services
application/        → Use case orchestration
forms/              → Django forms for template views
templates/          → HTML — NO inline <script> blocks
static/js/          → ALL JavaScript (external files only)
```

### ORM Only — No Raw SQL
```python
# Always use the ORM
Audit.objects.filter(organization_id=org_id).select_related("organization")
```

### Thin Views
```python
# Views orchestrate — they do not contain business logic
def audit_close(request, pk):
    audit = get_object_or_404(Audit, pk=pk)
    AuditWorkflowService.close(audit, actor=request.user)
```

### Query Parameter Validation
```python
org_id = request.GET.get("organization")
if org_id:
    try:
        queryset = queryset.filter(organization_id=int(org_id))
    except (ValueError, TypeError):
        pass
```

---

## Security Rules (Non-Negotiable)

- `DEBUG = False` by default — requires `DJANGO_DEBUG=True` explicitly
- No `unsafe-inline` in `script-src` CSP — use external JS with `data-*` attributes
- No secrets in code — environment variables only
- File uploads: validate extension + MIME type + size
- Object-level permissions on every API endpoint
- Validate and cast all query parameters at boundaries
- Log errors with `logger.error()`, never swallow with bare `except: pass`

---

## Testing

Run before every commit:
```bash
uv run ruff check .
uv run ruff format --check .
uv run bandit -c pyproject.toml -r . -ll
uv run pytest -x -q
```

Coverage target: ≥ 75%

---

## What NOT To Do

- Don't add features not in scope (check `docs/BACKLOG.md`)
- Don't refactor working code unless asked
- Don't add docstrings/comments to unchanged code
- Don't use `print()` — use `logger.debug()`
- Don't write raw SQL — use the ORM
- Don't store secrets in code
- Don't add inline `<script>` in templates — use external JS with data attributes
- Don't catch and swallow exceptions silently
- Don't ship code without running the test suite

---

## Key Commands

```bash
uv sync --all-extras --dev           # Install deps
DJANGO_DEBUG=True uv run python manage.py runserver  # Dev server
uv run pytest -x -q                  # Fast tests
uv run ruff check .                  # Lint
uv run ruff format .                 # Format
uv run bandit -c pyproject.toml -r . -ll  # Security scan
```
