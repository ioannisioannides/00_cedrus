# Cedrus Refactoring Proposal

## Current State Analysis

### Strengths

1. **Clear Domain Separation**: `accounts`, `core`, `audits` apps are well-defined
2. **Good Model Design**: Proper use of foreign keys, relationships, and inheritance
3. **Role-Based Access**: Group-based RBAC is a solid foundation
4. **Template Organization**: Templates are well-organized by app

### Issues Identified

#### 1. Business Logic in Views

**Location**: `audits/views.py`, `core/views.py`

**Problem**: Views contain validation, business rules, and workflow logic

**Example**:

```python
# audits/views.py - Current
def audit_create(request):
    if request.method == 'POST':
        # Validation logic
        if not request.POST.get('organization'):
            messages.error(request, "Organization required")
            return redirect('audit_create')
        
        # Business logic
        organization = Organization.objects.get(id=request.POST['organization'])
        if organization.certifications.count() == 0:
            messages.error(request, "Organization has no certifications")
            return redirect('audit_create')
        
        # Create logic
        audit = Audit.objects.create(...)
        
        # Notification logic
        send_mail(...)
        
        return redirect('audit_detail', audit.id)
```

#### 2. Duplicated Permission Checks

**Location**: Multiple views across apps

**Problem**: Same permission logic repeated in multiple places

**Example**:

```python
# Repeated in multiple views
if not request.user.groups.filter(name="cb_admin").exists():
    return redirect("accounts:dashboard")
```

#### 3. No Service Layer

**Location**: All apps

**Problem**: Direct model manipulation in views, no abstraction layer

**Impact**:

- Hard to test business logic
- Logic not reusable
- Difficult to add API layer later

#### 4. Tight Coupling

**Location**: Views importing models from other apps

**Problem**: Direct imports create dependencies

**Example**:

```python
# accounts/views.py
from core.models import Organization, Certification
from audits.models import Audit
```

#### 5. Status Transitions in Views

**Location**: `audits/views.py`

**Problem**: Status transition logic scattered in views

**Example**:

```python
# In multiple views
if audit.status == 'draft' and new_status == 'client_review':
    if not request.user.groups.filter(name='lead_auditor').exists():
        return error("Permission denied")
    audit.status = new_status
    audit.save()
```

---

## Refactoring Plan

### Phase 1: Foundation (Weeks 1-4)

#### 1.1 Create Trunk Structure

**Goal**: Establish trunk foundation

**Steps**:

1. Create `trunk/` directory
2. Move shared models from `core/` to `trunk/models/`
3. Create `trunk/services/` for shared services
4. Create `trunk/permissions/` for permission system

**Files to Create**:

```
trunk/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── organization.py
│   ├── site.py
│   ├── standard.py
│   └── certification.py
├── services/
│   ├── __init__.py
│   └── organization_service.py
├── permissions/
│   ├── __init__.py
│   ├── mixins.py
│   ├── predicates.py
│   └── backends.py
└── events/
    ├── __init__.py
    └── dispatcher.py
```

**Migration Strategy**:

- Keep `core/` app temporarily
- Create `trunk/` models with same structure
- Use data migration to copy data
- Update foreign keys gradually
- Remove `core/` after migration complete

#### 1.2 Create Permission System

**Goal**: Centralize permission logic

**Files to Create**:

```python
# trunk/permissions/predicates.py
class PermissionPredicate:
    @staticmethod
    def is_cb_admin(user):
        return user.groups.filter(name='cb_admin').exists()
    
    @staticmethod
    def is_lead_auditor(user):
        return user.groups.filter(name='lead_auditor').exists()
    
    @staticmethod
    def is_auditor(user):
        return user.groups.filter(name__in=['lead_auditor', 'auditor']).exists()
    
    @staticmethod
    def is_client_user(user):
        return user.groups.filter(name__in=['client_admin', 'client_user']).exists()
    
    @staticmethod
    def can_view_audit(user, audit):
        """Composite permission check"""
        if PermissionPredicate.is_cb_admin(user):
            return True
        if audit.lead_auditor == user:
            return True
        if hasattr(user, 'profile') and user.profile.organization == audit.organization:
            return True
        return False

# trunk/permissions/mixins.py
class CBAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return PermissionPredicate.is_cb_admin(self.request.user)

class AuditorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return PermissionPredicate.is_auditor(self.request.user)

class ClientRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return PermissionPredicate.is_client_user(self.request.user)
```

**Refactoring**:

- Replace all permission checks in views with mixins
- Use predicates for complex permission logic

#### 1.3 Create Event System

**Goal**: Enable event-driven communication

**Files to Create**:

```python
# trunk/events/dispatcher.py
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class EventDispatcher:
    """Simple event dispatcher"""
    
    def __init__(self):
        self._handlers = defaultdict(list)
    
    def register(self, event_type, handler):
        """Register event handler"""
        self._handlers[event_type].append(handler)
    
    def emit(self, event_type, payload):
        """Emit event to all handlers"""
        for handler in self._handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

# Singleton instance
event_dispatcher = EventDispatcher()

# trunk/events/types.py
class EventType:
    AUDIT_CREATED = 'audit.created'
    AUDIT_STATUS_CHANGED = 'audit.status_changed'
    AUDIT_SUBMITTED = 'audit.submitted'
    CERTIFICATION_ISSUED = 'certification.issued'
    ORGANIZATION_UPDATED = 'organization.updated'
```

---

### Phase 2: Service Layer (Weeks 5-8)

#### 2.1 Create Audit Service

**Goal**: Extract business logic from views

**Files to Create**:

```python
# branches/audits/services/__init__.py
from .audit_service import AuditService
from .finding_service import FindingService

__all__ = ['AuditService', 'FindingService']

# branches/audits/services/audit_service.py
from django.core.exceptions import ValidationError
from ..models import Audit
from trunk.events.dispatcher import event_dispatcher
from trunk.events.types import EventType

class AuditService:
    """Business logic for audit operations"""
    
    def __init__(self):
        self.repository = AuditRepository()
    
    def create_audit(self, organization, certifications, sites, audit_data, created_by):
        """Create audit with validation"""
        # Validation
        self._validate_audit_data(audit_data)
        
        # Business rules
        if not certifications:
            raise ValidationError("At least one certification required")
        
        if not sites:
            raise ValidationError("At least one site required")
        
        # Create
        audit = Audit.objects.create(
            organization=organization,
            created_by=created_by,
            lead_auditor=audit_data.get('lead_auditor', created_by),
            **audit_data
        )
        
        audit.certifications.set(certifications)
        audit.sites.set(sites)
        
        # Emit event
        event_dispatcher.emit(EventType.AUDIT_CREATED, audit)
        
        return audit
    
    def transition_status(self, audit, new_status, user):
        """Handle status transitions"""
        from ..workflows.audit_workflow import AuditWorkflow
        
        workflow = AuditWorkflow(audit)
        if not workflow.can_transition(new_status, user):
            raise ValidationError("Invalid status transition")
        
        old_status = audit.status
        audit.status = new_status
        audit.save()
        
        # Emit event
        event_dispatcher.emit(EventType.AUDIT_STATUS_CHANGED, {
            'audit': audit,
            'old_status': old_status,
            'new_status': new_status,
            'user': user
        })
        
        return audit
    
    def _validate_audit_data(self, data):
        """Validate audit data"""
        required_fields = ['audit_type', 'total_audit_date_from', 'total_audit_date_to']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"{field} is required")
```

**Refactoring Views**:

```python
# branches/audits/views/audit_views.py - After refactoring
from django.views.generic import CreateView
from ..forms import AuditForm
from ..services import AuditService

class AuditCreateView(LoginRequiredMixin, AuditorRequiredMixin, CreateView):
    form_class = AuditForm
    template_name = 'audits/audit_form.html'
    
    def form_valid(self, form):
        service = AuditService()
        audit = service.create_audit(
            organization=form.cleaned_data['organization'],
            certifications=form.cleaned_data['certifications'],
            sites=form.cleaned_data['sites'],
            audit_data=form.cleaned_data,
            created_by=self.request.user
        )
        return redirect('audit_detail', audit.id)
```

#### 2.2 Create Finding Service

**Goal**: Extract finding business logic

**Files to Create**:

```python
# branches/audits/services/finding_service.py
class FindingService:
    """Business logic for findings"""
    
    def create_nonconformity(self, audit, standard, clause, data, created_by):
        """Create nonconformity"""
        from ..models import Nonconformity
        
        nc = Nonconformity.objects.create(
            audit=audit,
            standard=standard,
            clause=clause,
            created_by=created_by,
            **data
        )
        
        event_dispatcher.emit('finding.created', nc)
        return nc
    
    def update_client_response(self, nonconformity, response_data, user):
        """Update client response to NC"""
        # Permission check
        if not PermissionPredicate.can_respond_to_nc(user, nonconformity):
            raise PermissionDenied()
        
        nonconformity.client_root_cause = response_data.get('root_cause', '')
        nonconformity.client_correction = response_data.get('correction', '')
        nonconformity.client_corrective_action = response_data.get('corrective_action', '')
        nonconformity.verification_status = 'client_responded'
        nonconformity.save()
        
        event_dispatcher.emit('finding.client_responded', nonconformity)
        return nonconformity
```

#### 2.3 Create Workflow Layer

**Goal**: Centralize state transition logic

**Files to Create**:

```python
# branches/audits/workflows/__init__.py
from .audit_workflow import AuditWorkflow
from .finding_workflow import FindingWorkflow

__all__ = ['AuditWorkflow', 'FindingWorkflow']

# branches/audits/workflows/audit_workflow.py
class AuditWorkflow:
    """Manages audit state transitions"""
    
    TRANSITIONS = {
        'draft': ['client_review', 'submitted_to_cb'],
        'client_review': ['draft', 'submitted_to_cb'],
        'submitted_to_cb': ['decided'],
        'decided': []
    }
    
    PERMISSIONS = {
        ('draft', 'client_review'): ['audits.submit_audit'],
        ('client_review', 'submitted_to_cb'): ['audits.approve_audit'],
        ('submitted_to_cb', 'decided'): ['audits.decide_audit'],
    }
    
    def __init__(self, audit):
        self.audit = audit
    
    def can_transition(self, new_status, user):
        """Check if transition is allowed"""
        current_status = self.audit.status
        allowed = self.TRANSITIONS.get(current_status, [])
        
        if new_status not in allowed:
            return False
        
        # Check permissions
        required_perm = self.PERMISSIONS.get((current_status, new_status))
        if required_perm and not user.has_perm(required_perm):
            return False
        
        return True
    
    def transition(self, new_status, user):
        """Perform state transition"""
        if not self.can_transition(new_status, user):
            raise WorkflowError(f"Cannot transition from {self.audit.status} to {new_status}")
        
        old_status = self.audit.status
        self.audit.status = new_status
        self.audit.save()
        
        return {
            'old_status': old_status,
            'new_status': new_status
        }
```

---

### Phase 3: Repository Pattern (Weeks 9-12)

#### 3.1 Create Audit Repository

**Goal**: Abstract data access

**Files to Create**:

```python
# branches/audits/repositories/__init__.py
from .audit_repository import AuditRepository

__all__ = ['AuditRepository']

# branches/audits/repositories/audit_repository.py
class AuditRepository:
    """Data access for audits"""
    
    def get(self, audit_id):
        """Get audit by ID with optimizations"""
        return Audit.objects.select_related(
            'organization', 'lead_auditor', 'created_by'
        ).prefetch_related(
            'certifications', 'sites', 'team_members'
        ).get(id=audit_id)
    
    def list(self, filters=None, user=None):
        """List audits with optional filtering"""
        queryset = Audit.objects.select_related(
            'organization', 'lead_auditor'
        ).prefetch_related('certifications')
        
        # Apply user-based filtering
        if user:
            if not PermissionPredicate.is_cb_admin(user):
                if PermissionPredicate.is_auditor(user):
                    queryset = queryset.filter(lead_auditor=user)
                elif PermissionPredicate.is_client_user(user):
                    org = user.profile.organization
                    queryset = queryset.filter(organization=org)
        
        # Apply additional filters
        if filters:
            queryset = queryset.filter(**filters)
        
        return queryset
    
    def create(self, **data):
        """Create audit"""
        return Audit.objects.create(**data)
    
    def update(self, audit, **data):
        """Update audit"""
        for key, value in data.items():
            setattr(audit, key, value)
        audit.save()
        return audit
```

**Update Service**:

```python
# branches/audits/services/audit_service.py
class AuditService:
    def __init__(self, repository=None):
        self.repository = repository or AuditRepository()
    
    def get_audit(self, audit_id, user):
        """Get audit with permission check"""
        audit = self.repository.get(audit_id)
        if not PermissionPredicate.can_view_audit(user, audit):
            raise PermissionDenied()
        return audit
```

---

### Phase 4: Module Organization (Weeks 13-16)

#### 4.1 Reorganize Audits App

**Goal**: Move audits to branches structure

**New Structure**:

```
branches/
└── audits/
    ├── __init__.py
    ├── apps.py
    ├── models/
    │   ├── __init__.py
    │   ├── audit.py
    │   ├── finding.py
    │   └── recommendation.py
    ├── services/
    │   ├── __init__.py
    │   ├── audit_service.py
    │   └── finding_service.py
    ├── repositories/
    │   ├── __init__.py
    │   └── audit_repository.py
    ├── workflows/
    │   ├── __init__.py
    │   ├── audit_workflow.py
    │   └── finding_workflow.py
    ├── views/
    │   ├── __init__.py
    │   ├── audit_views.py
    │   └── finding_views.py
    ├── forms/
    │   ├── __init__.py
    │   └── audit_forms.py
    ├── permissions.py
    ├── urls.py
    ├── admin.py
    └── tests/
        ├── __init__.py
        ├── test_models.py
        ├── test_services.py
        └── test_workflows.py
```

**Migration Steps**:

1. Create `branches/audits/` directory
2. Move models to `models/` subdirectory
3. Create service layer
4. Create repository layer
5. Create workflow layer
6. Refactor views to use services
7. Update imports throughout codebase
8. Update `INSTALLED_APPS` in settings
9. Run tests to ensure nothing breaks

---

## Testing Strategy

### Service Layer Tests

```python
# branches/audits/tests/test_services.py
from django.test import TestCase
from ..services import AuditService
from trunk.models import Organization, Certification
from accounts.models import Profile

class AuditServiceTest(TestCase):
    def setUp(self):
        self.service = AuditService()
        self.organization = Organization.objects.create(...)
        self.certification = Certification.objects.create(...)
        self.user = User.objects.create_user(...)
    
    def test_create_audit(self):
        audit = self.service.create_audit(
            organization=self.organization,
            certifications=[self.certification],
            sites=[],
            audit_data={
                'audit_type': 'stage1',
                'total_audit_date_from': date.today(),
                'total_audit_date_to': date.today(),
            },
            created_by=self.user
        )
        
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, 'draft')
        self.assertEqual(audit.organization, self.organization)
```

### Workflow Tests

```python
# branches/audits/tests/test_workflows.py
class AuditWorkflowTest(TestCase):
    def test_can_transition_draft_to_client_review(self):
        audit = Audit.objects.create(status='draft', ...)
        workflow = AuditWorkflow(audit)
        user = User.objects.create_user(...)
        user.groups.add(Group.objects.get(name='lead_auditor'))
        
        self.assertTrue(workflow.can_transition('client_review', user))
    
    def test_cannot_transition_draft_to_decided(self):
        audit = Audit.objects.create(status='draft', ...)
        workflow = AuditWorkflow(audit)
        user = User.objects.create_user(...)
        
        self.assertFalse(workflow.can_transition('decided', user))
```

---

## Migration Checklist

### Pre-Migration

- [ ] Backup database
- [ ] Create feature branch
- [ ] Write tests for existing functionality
- [ ] Document current behavior

### During Migration

- [ ] Create trunk structure
- [ ] Create service layer
- [ ] Create repository layer
- [ ] Create workflow layer
- [ ] Refactor views
- [ ] Update imports
- [ ] Run tests continuously

### Post-Migration

- [ ] All tests passing
- [ ] Code review
- [ ] Update documentation
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Deploy to production

---

## Risk Mitigation

### Risks

1. **Breaking Changes**: Refactoring may break existing functionality
2. **Data Loss**: Migration may cause data issues
3. **Performance**: New layers may impact performance
4. **Timeline**: Refactoring may take longer than expected

### Mitigation Strategies

1. **Incremental Refactoring**: Do it in phases, not all at once
2. **Comprehensive Testing**: Write tests before refactoring
3. **Feature Flags**: Use feature flags to toggle new code
4. **Rollback Plan**: Keep old code until new code is proven
5. **Performance Monitoring**: Monitor performance during migration

---

## Success Metrics

### Code Quality

- [ ] Service layer covers all business logic
- [ ] No business logic in views
- [ ] Permission checks centralized
- [ ] Test coverage > 80%

### Maintainability

- [ ] Clear separation of concerns
- [ ] Easy to add new features
- [ ] Easy to test
- [ ] Documentation complete

### Performance

- [ ] No performance regression
- [ ] Query optimization in place
- [ ] Caching where appropriate

---

## Timeline Summary

- **Weeks 1-4**: Foundation (trunk, permissions, events)
- **Weeks 5-8**: Service layer
- **Weeks 9-12**: Repository pattern
- **Weeks 13-16**: Module reorganization

**Total**: 16 weeks (4 months)

This can be done incrementally alongside feature development, not as a separate project.
