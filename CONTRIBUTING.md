# Contributing to Cedrus

Thank you for your interest in contributing to Cedrus! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Testing](#testing)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

### Our Responsibilities

- Maintain a welcoming and safe environment
- Address conflicts professionally
- Clarify project standards and expectations

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of Django
- Familiarity with audit/compliance domain (helpful but not required)

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:

   ```bash
   git clone https://github.com/your-username/cedrus.git
   cd cedrus
   ```

3. **Install uv and sync dependencies**:

   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Sync dependencies (creates virtual environment automatically)
   uv sync
   ```

4. **Set up the database**:

   ```bash
   uv run manage.py makemigrations
   uv run manage.py migrate
   ```

5. **Create a superuser** (for testing):

   ```bash
   uv run manage.py createsuperuser
   ```

6. **Seed test data** (optional):

   ```bash
   uv run manage.py seed_data
   ```

7. **Run the development server**:

   ```bash
   uv run manage.py runserver
   ```

### Setting Up Your Development Branch

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

   Or for bug fixes:

   ```bash
   git checkout -b fix/bug-description
   ```

2. **Keep your branch updated**:

   ```bash
   git fetch upstream
   git rebase upstream/main  # or master, depending on default branch
   ```

---

## Development Workflow

### Before You Start

1. **Check existing issues** to see if your feature/bug is already being worked on
2. **Create an issue** if you're planning a significant change (discussion is welcome)
3. **Ask questions** if anything is unclear

### Making Changes

1. **Make your changes** following the coding standards below
2. **Test your changes** thoroughly
3. **Update documentation** if needed
4. **Commit your changes** with clear commit messages

### Testing Your Changes

- Test with different user roles (CB Admin, Lead Auditor, Auditor, Client Admin, Client User)
- Test edge cases and error conditions
- Verify that existing functionality still works
- Check that migrations work correctly (if you modified models)

---

## Coding Standards

### Python Style

- Follow **PEP 8** style guidelines
- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **100 characters** (soft limit, 120 hard limit)
- Use descriptive variable and function names
- Add docstrings to all classes and functions

### Django Conventions

- Use **class-based views** where appropriate (preferred over function views for CRUD)
- Follow Django's naming conventions:
  - Models: `PascalCase`
  - Views: `PascalCase` for classes, `snake_case` for functions
  - URLs: `snake_case`
  - Templates: `snake_case.html`
- Use Django's built-in features (Groups, Permissions) rather than custom solutions
- Keep business logic in models or separate service modules, not in views

### Code Organization

- **One app per domain**: Keep related functionality together
- **DRY (Don't Repeat Yourself)**: Extract common functionality
- **Clear over clever**: Favor readability
- **Document complex logic**: Add comments explaining "why", not "what"

### Example: Model Definition

```python
class Audit(models.Model):
    """
    Main audit record.
    
    An audit is performed on an organization, covers specific certifications
    and sites, and is managed by a lead auditor.
    """
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="audits"
    )
    # ... other fields
    
    class Meta:
        verbose_name = "Audit"
        verbose_name_plural = "Audits"
        ordering = ["-total_audit_date_from", "-created_at"]
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_audit_type_display()}"
```

### Example: View Definition

```python
class AuditDetailView(LoginRequiredMixin, DetailView):
    """View audit details with role-based access control."""
    model = Audit
    template_name = "audits/audit_detail.html"
    context_object_name = "audit"
    
    def get_queryset(self):
        # Role-based filtering logic
        ...
```

### Template Guidelines

- Use **Bootstrap 5** components for UI consistency
- Keep templates simple and readable
- Use template inheritance (`{% extends %}`)
- Minimize JavaScript (use vanilla JS only when needed)
- Ensure responsive design (mobile-friendly)

### Example: Template Structure

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Audit Details{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1>{{ audit.organization.name }}</h1>
    <!-- Content here -->
</div>
{% endblock %}
```

---

## Commit Messages

### Format

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat: Add risk management app

- Create risks app with Risk model
- Add risk assessment views
- Update navigation to include risks section

Closes #123
```

```
fix: Correct nonconformity verification workflow

The verification status was not updating correctly when
auditors accepted client responses. Fixed the state
transition logic.

Fixes #456
```

```
docs: Update README with deployment instructions

Added detailed production deployment guide including
database setup, static files configuration, and
security considerations.
```

---

## Pull Request Process

### Before Submitting

1. **Ensure your code follows** all coding standards
2. **Test thoroughly** with different user roles
3. **Update documentation** if you added features or changed behavior
4. **Check for linting errors** (if linting is set up)
5. **Rebase your branch** on the latest main/master branch

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass (if applicable)
```

### Review Process

1. **Automated checks** (if configured) must pass
2. **Code review** by maintainers
3. **Feedback addressed** (if any)
4. **Approval** from at least one maintainer
5. **Merge** by maintainers

### What to Expect

- **Constructive feedback**: We'll help improve your code
- **Questions**: Maintainers may ask for clarification
- **Iteration**: Multiple rounds of review are normal
- **Appreciation**: We value all contributions!

---

## Documentation

### When to Update Documentation

- **New features**: Document in README and relevant user guides
- **API changes**: Update API documentation
- **Workflow changes**: Update workflow diagrams
- **Configuration changes**: Update setup/deployment docs

### Documentation Standards

- Use **Markdown** format
- Include **Mermaid diagrams** for workflows and architecture
- Keep language **clear and professional**
- Provide **examples** where helpful
- Update **table of contents** when adding new sections

### Documentation Locations

- `README.md`: Main project documentation
- `CONTRIBUTING.md`: This file
- `docs/`: Additional documentation
  - `user-guides/`: Role-specific user guides
  - `API.md`: API documentation (when available)
  - `ARCHITECTURE.md`: System architecture details
  - `DEPLOYMENT.md`: Production deployment guide
  - `MODELS.md`: Complete model documentation

---

## Testing

### Current Testing Approach

- Manual testing with different user roles
- Django admin interface testing
- Workflow testing (audit lifecycle, NC management)

### Future Testing Goals

- Unit tests for models and business logic
- Integration tests for workflows
- View tests for permission checks
- API tests (when API is added)

### Running Tests (When Available)

```bash
DJANGO_SETTINGS_MODULE=cedrus.settings uv run pytest
```

### Writing Tests

- Test **happy paths** and **error cases**
- Test **permission checks** (role-based access)
- Test **workflow transitions** (audit status changes)
- Use **Django's TestCase** for database-backed tests
- Use **fixtures** for test data

---

## Areas for Contribution

### High Priority

- **Testing**: Comprehensive test suite
- **API**: REST API endpoints
- **Documentation**: User guides, API docs
- **Security**: Security audit and improvements

### Feature Development

- Risk management app (`risks/`)
- Internal audits app (`internal_audits/`)
- Email notifications
- PDF report generation
- Advanced reporting and analytics

### Improvements

- Performance optimization
- UI/UX enhancements
- Accessibility improvements
- Internationalization (i18n)
- Mobile responsiveness

---

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion (if enabled)
- **Documentation**: Check existing docs first

---

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md (if created)
- Acknowledged in release notes for significant contributions
- Appreciated by the community!

---

Thank you for contributing to Cedrus! 🎉
