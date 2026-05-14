---
applyTo: "**/*.py,**/*.yml,**/*.yaml,Dockerfile*,docker-compose*.yml"
---

# Security Patterns — OWASP / Django Hardening

## Django Security Checklist

### Authentication & Authorization
- Every view requires `LoginRequiredMixin` or `@login_required`
- API endpoints require `IsAuthenticated` + role-specific permission class
- Object-level permissions: verify the user can access *this specific object*
- Use `get_object_or_404()` — prevents user enumeration via timing attacks

### Input Validation
```python
# At API boundary — DRF serializer
class AuditSerializer(serializers.ModelSerializer):
    def validate_organization(self, value):
        if not self.context['request'].user.can_access_organization(value):
            raise serializers.ValidationError("Access denied.")
        return value

# At query boundary — always cast numeric params
org_id = request.GET.get("organization")
if org_id:
    try:
        queryset = queryset.filter(organization_id=int(org_id))
    except (ValueError, TypeError):
        pass
```

### File Upload Security
```python
# In model clean() — validate extension AND check content is safe
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx'}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def clean(self):
    if self.file:
        ext = os.path.splitext(self.file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"File type {ext} not allowed.")
        if self.file.size > MAX_SIZE_BYTES:
            raise ValidationError("File exceeds 10 MB limit.")
```

### CSRF Protection
- `CsrfViewMiddleware` is enabled globally
- DRF `SessionAuthentication` enforces CSRF on all state-changing endpoints
- AJAX requests must include `X-CSRFToken` header

### Content Security Policy
- `script-src`: `'self'` + approved CDN domains — **no `unsafe-inline`**
- `style-src`: `'self' 'unsafe-inline'` (required for Carbon Design System)
- No inline scripts in templates — use external JS + data attributes

### Security Headers (all applied by `SecurityHeadersMiddleware`)
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://1.www.s81c.com; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Cross-Origin-Opener-Policy: same-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), ...
```

### Secrets Management
```python
# Good: environment variable
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

# Bad: hardcoded
SECRET_KEY = "my-hardcoded-secret"  # NEVER DO THIS
```

### Logging Security Events
```python
import logging
logger = logging.getLogger(__name__)

# Good: log security-relevant events
logger.warning("Permission denied: user=%s attempted to access audit=%s", user.pk, audit.pk)
logger.error("File upload rejected: invalid type %s from user=%s", ext, user.pk)

# Bad: swallow exceptions
try:
    do_something()
except Exception:
    pass  # NEVER DO THIS
```

## OWASP Top 10 Mitigations

| # | Risk | Mitigation in Cedrus |
|---|------|---------------------|
| A01 | Broken Access Control | Role-based permissions, object-level checks, queryset scoping |
| A02 | Cryptographic Failures | HTTPS enforced (HSTS), secrets in env vars, no sensitive data in logs |
| A03 | Injection | ORM only, parameterised queries, input validation |
| A04 | Insecure Design | Domain model validators, status machine enforcement |
| A05 | Security Misconfiguration | DEBUG=False default, security headers middleware |
| A06 | Vulnerable Components | pip-audit in CI, Dependabot weekly, version constraints |
| A07 | Auth Failures | django-axes (5 attempts, 1h lockout), session hardening |
| A08 | Data Integrity | CSRF, signed sessions, model validators |
| A09 | Security Logging | Structured logging, `django.security` logger configured |
| A10 | SSRF | No external HTTP calls from user-supplied URLs |

## Running Security Scans

```bash
# Static analysis
uv run bandit -c pyproject.toml -r . -ll

# Dependency vulnerabilities
pip freeze | pip-audit -r /dev/stdin

# Lint (includes flake8-bandit rules via ruff S-prefix)
uv run ruff check --select S .
```
