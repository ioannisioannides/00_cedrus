# Cedrus MVP - Test Execution Guide

**QA Lead:** Testing & Quality Assurance  
**Date:** 2024

---

## Quick Start

### 1. Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Run all tests
python manage.py test

# Run with verbose output
python manage.py test --verbosity=2

# Run specific app tests
python manage.py test accounts
python manage.py test core
python manage.py test audits

# Run specific test class
python manage.py test accounts.tests.ProfileModelTest

# Run specific test method
python manage.py test accounts.tests.ProfileModelTest.test_profile_auto_created
```

### 2. Run Tests with Coverage

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in browser
```

### 3. Run Tests in Parallel (Faster)

```bash
# Install pytest and pytest-django
pip install pytest pytest-django pytest-xdist

# Run tests in parallel (4 workers)
pytest --numprocesses=4
```

---

## Test Structure

### Accounts App Tests (`accounts/tests.py`)

- **ProfileModelTest:** Profile model methods and relationships
- **AuthenticationTest:** Login/logout functionality
- **DashboardAccessTest:** Role-based dashboard access
- **ProfileOrganizationTest:** Profile-organization relationships

**Key Tests:**

- Profile auto-creation
- Role checking methods
- Login with valid/invalid credentials
- Dashboard redirects by role
- Permission boundaries

### Core App Tests (`core/tests.py`)

- **OrganizationModelTest:** Organization model validation
- **SiteModelTest:** Site model and relationships
- **StandardModelTest:** Standard model validation
- **CertificationModelTest:** Certification model and relationships
- **OrganizationViewPermissionTest:** Organization view permissions
- **SiteViewPermissionTest:** Site view permissions
- **CertificationViewPermissionTest:** Certification view permissions

**Key Tests:**

- Unique constraints (customer_id, standard code)
- CASCADE vs PROTECT relationships
- CB Admin-only access
- Form validation

### Audits App Tests (`audits/tests.py`)

- **AuditModelTest:** Audit model validation
- **AuditViewPermissionTest:** Audit view permissions (comprehensive)
- **FindingModelTest:** Finding models (NC, Observation, OFI)
- **AuditTeamMemberTest:** Team member model
- **AuditMetadataTest:** Metadata models (Changes, PlanReview, Summary, Recommendation)

**Key Tests:**

- Audit creation and permissions
- Role-based audit list filtering
- Finding creation and relationships
- Team member validation
- One-to-one metadata relationships

---

## Test Data Setup

### Using Seed Data

```bash
# Create test data
python manage.py seed_data

# This creates:
# - User groups
# - Test users for each role
# - Sample organization, site, standard, certification
# - Sample audit
```

### Manual Test Data

For manual testing, create test users:

```python
# In Django shell: python manage.py shell
from django.contrib.auth.models import User, Group
from identity.adapters.models import Profile
from core.models import Organization

# Create groups
cb_group = Group.objects.create(name="cb_admin")
lead_group = Group.objects.create(name="lead_auditor")
auditor_group = Group.objects.create(name="auditor")
client_admin_group = Group.objects.create(name="client_admin")
client_user_group = Group.objects.create(name="client_user")

# Create CB Admin
cb_admin = User.objects.create_user(username="cbadmin", password="testpass123")
cb_admin.groups.add(cb_group)

# Create Lead Auditor
lead = User.objects.create_user(username="lead", password="testpass123")
lead.groups.add(lead_group)

# Create Client Admin with organization
org = Organization.objects.create(
    name="Test Client",
    registered_address="123 St",
    customer_id="CLIENT001",
    total_employee_count=10
)
client_admin = User.objects.create_user(username="clientadmin", password="testpass123")
client_admin.groups.add(client_admin_group)
client_admin.profile.organization = org
client_admin.profile.save()
```

---

## Running Specific Test Scenarios

### Test Authentication

```bash
python manage.py test accounts.tests.AuthenticationTest
```

### Test Permissions

```bash
# Test all permission tests
python manage.py test accounts.tests.DashboardAccessTest
python manage.py test core.tests.OrganizationViewPermissionTest
python manage.py test audits.tests.AuditViewPermissionTest
```

### Test Models

```bash
# Test all model tests
python manage.py test accounts.tests.ProfileModelTest
python manage.py test core.tests.OrganizationModelTest
python manage.py test audits.tests.AuditModelTest
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python manage.py test
      - name: Generate coverage
        run: |
          pip install coverage
          coverage run --source='.' manage.py test
          coverage report
```

---

## Test Maintenance

### Adding New Tests

1. **Follow naming convention:** `TestClassName` for test classes, `test_method_name` for test methods
2. **Use descriptive names:** Test names should describe what is being tested
3. **One assertion per test (when possible):** Makes failures easier to diagnose
4. **Use setUp():** Create test data in setUp() method
5. **Clean up:** Use tearDown() if needed (usually not necessary with Django TestCase)

### Example Test Template

```python
class MyFeatureTest(TestCase):
    """Test description."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
    
    def test_feature_behavior(self):
        """Test that feature behaves correctly."""
        # Arrange
        # Act
        # Assert
        self.assertEqual(expected, actual)
```

---

## Troubleshooting

### Tests Failing

1. **Check database:** Tests use separate test database, ensure migrations are up to date

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Check test data:** Ensure setUp() creates all necessary data

3. **Check permissions:** Verify user groups are created correctly

4. **Check URLs:** Ensure URL patterns are correct

### Common Issues

- **"No such table" errors:** Run migrations
- **"Permission denied" errors:** Check user groups and permissions
- **"404 Not Found" in tests:** Check URL patterns and view permissions
- **"403 Forbidden" in tests:** Check permission mixins and test_func methods

---

## Test Coverage Goals

- **Minimum:** 70% code coverage
- **Target:** 80% code coverage
- **Critical paths:** 100% coverage (authentication, permissions, workflows)

### Check Coverage

```bash
coverage run --source='.' manage.py test
coverage report --show-missing
```

---

## Performance Testing

### Load Testing (Future)

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run: locust
```

### Database Query Testing

```python
# In tests, check query count
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

class QueryTest(TestCase):
    def test_query_count(self):
        with self.assertNumQueries(5):  # Expect 5 queries
            # Your code here
            pass
```

---

## Sign-Off

**Test Execution Status:** \[ \] ALL TESTS PASSING \[ \] SOME FAILURES \[ \] BLOCKED

**Coverage:** _____%

**Notes:**

---
---

---

**END OF TEST EXECUTION GUIDE**
