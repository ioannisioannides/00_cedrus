# Cedrus Architectural Patterns & Anti-Patterns

## Design Patterns to Follow

### 1. Service Layer Pattern

**Purpose**: Separate business logic from views and models

**Implementation**:

```python
# branches/audits/services/audit_service.py
class AuditService:
    """Business logic for audit operations"""
    
    def __init__(self, audit_repository=None):
        self.audit_repository = audit_repository or AuditRepository()
    
    def create_audit(self, organization, certifications, audit_data, created_by):
        # Validation
        self._validate_audit_data(audit_data)
        
        # Business rules
        if not self._can_create_audit(organization, certifications):
            raise ValidationError("Cannot create audit")
        
        # Create
        audit = self.audit_repository.create(
            organization=organization,
            certifications=certifications,
            **audit_data,
            created_by=created_by
        )
        
        # Emit event
        event_dispatcher.emit('audit.created', audit)
        
        return audit
```

**Benefits**:

- Testable business logic
- Reusable across views and API
- Clear separation of concerns

### 2. Repository Pattern

**Purpose**: Abstract data access layer

**Implementation**:

```python
# branches/audits/repositories/audit_repository.py
class AuditRepository:
    """Data access for audits"""
    
    def get(self, audit_id):
        return Audit.objects.select_related(
            'organization', 'lead_auditor'
        ).prefetch_related(
            'certifications', 'sites', 'team_members'
        ).get(id=audit_id)
    
    def list(self, filters=None):
        queryset = Audit.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset
    
    def create(self, **data):
        return Audit.objects.create(**data)
    
    def update(self, audit, **data):
        for key, value in data.items():
            setattr(audit, key, value)
        audit.save()
        return audit
```

**Benefits**:

- Centralized query logic
- Easy to mock in tests
- Can swap data sources

### 3. Workflow Pattern

**Purpose**: Manage state transitions and business rules

**Implementation**:

```python
# branches/audits/workflows/audit_workflow.py
class AuditWorkflow:
    """Manages audit state transitions"""
    
    TRANSITIONS = {
        'draft': ['client_review', 'submitted_to_cb'],
        'client_review': ['draft', 'submitted_to_cb'],
        'submitted_to_cb': ['decided'],
        'decided': []
    }
    
    REQUIRED_PERMISSIONS = {
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
        required_perm = self.REQUIRED_PERMISSIONS.get(
            (current_status, new_status)
        )
        if required_perm and not user.has_perm(required_perm):
            return False
        
        return True
    
    def transition(self, new_status, user):
        """Perform state transition"""
        if not self.can_transition(new_status, user):
            raise WorkflowError("Invalid transition")
        
        old_status = self.audit.status
        self.audit.status = new_status
        self.audit.save()
        
        event_dispatcher.emit('audit.status_changed', {
            'audit': self.audit,
            'old_status': old_status,
            'new_status': new_status,
            'user': user
        })
```

**Benefits**:

- Centralized state management
- Clear business rules
- Easy to test

### 4. Event-Driven Pattern

**Purpose**: Decouple modules through events

**Implementation**:

```python
# trunk/events/dispatcher.py
class EventDispatcher:
    """Central event dispatcher"""
    
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
                logger.error(f"Error in event handler: {e}")

# Usage
event_dispatcher = EventDispatcher()

# Register handler
@event_handler('audit.created')
def send_notification(payload):
    audit = payload
    # Send notification
```

**Benefits**:

- Loose coupling between modules
- Easy to add new behaviors
- Testable in isolation

### 5. Permission Predicate Pattern

**Purpose**: Reusable permission checks

**Implementation**:

```python
# trunk/permissions/predicates.py
class PermissionPredicate:
    """Reusable permission checks"""
    
    @staticmethod
    def is_organization_member(user, organization):
        """Check if user belongs to organization"""
        return (
            hasattr(user, 'profile') and
            user.profile.organization == organization
        )
    
    @staticmethod
    def is_audit_lead_auditor(user, audit):
        """Check if user is lead auditor"""
        return audit.lead_auditor == user
    
    @staticmethod
    def can_view_audit(user, audit):
        """Composite permission check"""
        # CB admins can view all
        if user.groups.filter(name='cb_admin').exists():
            return True
        
        # Lead auditor can view assigned audits
        if PermissionPredicate.is_audit_lead_auditor(user, audit):
            return True
        
        # Organization members can view their audits
        if PermissionPredicate.is_organization_member(user, audit.organization):
            return True
        
        return False
```

**Benefits**:

- Reusable permission logic
- Easy to test
- Clear and readable

---

## Anti-Patterns to Avoid

### 1. Fat Views (Business Logic in Views)

**❌ Anti-Pattern**:

```python
def create_audit(request):
    # Validation
    if not request.POST.get('organization'):
        return error("Organization required")
    
    # Business logic
    organization = Organization.objects.get(id=request.POST['organization'])
    if organization.certifications.count() == 0:
        return error("Organization has no certifications")
    
    # Create
    audit = Audit.objects.create(
        organization=organization,
        # ... many fields ...
    )
    
    # Send email
    send_mail(...)
    
    return redirect('audit_detail', audit.id)
```

**✅ Correct Pattern**:

```python
def create_audit(request):
    form = AuditForm(request.POST)
    if form.is_valid():
        service = AuditService()
        audit = service.create_audit(
            organization=form.cleaned_data['organization'],
            certifications=form.cleaned_data['certifications'],
            audit_data=form.cleaned_data,
            created_by=request.user
        )
        return redirect('audit_detail', audit.id)
    return render(request, 'audit_form.html', {'form': form})
```

### 2. Anemic Domain Models

**❌ Anti-Pattern**:

```python
class Audit(models.Model):
    status = models.CharField(...)
    # No business logic methods

# Business logic in views/services
def transition_status(audit, new_status):
    if audit.status == 'draft' and new_status == 'client_review':
        audit.status = new_status
        audit.save()
```

**✅ Correct Pattern**:

```python
class Audit(models.Model):
    status = models.CharField(...)
    
    def can_transition_to(self, new_status, user):
        """Business logic in model"""
        workflow = AuditWorkflow(self)
        return workflow.can_transition(new_status, user)
    
    def transition_to(self, new_status, user):
        """Encapsulated state transition"""
        workflow = AuditWorkflow(self)
        workflow.transition(new_status, user)
```

### 3. Direct Model Queries in Views

**❌ Anti-Pattern**:

```python
def audit_list(request):
    audits = Audit.objects.filter(
        organization__in=request.user.profile.organization.sites.all()
    ).select_related('organization', 'lead_auditor')
    # Complex query logic in view
```

**✅ Correct Pattern**:

```python
def audit_list(request):
    repository = AuditRepository()
    audits = repository.list_for_user(request.user)
    return render(request, 'audit_list.html', {'audits': audits})

# In repository
def list_for_user(self, user):
    if user.groups.filter(name='cb_admin').exists():
        return self.list()
    elif user.groups.filter(name='auditor').exists():
        return self.list(lead_auditor=user)
    else:
        org = user.profile.organization
        return self.list(organization=org)
```

### 4. Duplicated Permission Checks

**❌ Anti-Pattern**:

```python
def audit_detail(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    
    # Duplicated permission logic
    if not (request.user.groups.filter(name='cb_admin').exists() or
            audit.lead_auditor == request.user or
            (hasattr(request.user, 'profile') and
             request.user.profile.organization == audit.organization)):
        return HttpResponseForbidden()
    
    return render(request, 'audit_detail.html', {'audit': audit})

def audit_edit(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    
    # Same permission logic duplicated
    if not (request.user.groups.filter(name='cb_admin').exists() or
            audit.lead_auditor == request.user):
        return HttpResponseForbidden()
    # ...
```

**✅ Correct Pattern**:

```python
# Use permission mixin
class AuditDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Audit
    permission_required = 'audits.view_audit'
    
    def has_permission(self):
        audit = self.get_object()
        return PermissionPredicate.can_view_audit(self.request.user, audit)
```

### 5. Tight Coupling Between Modules

**❌ Anti-Pattern**:

```python
# In audits/views.py
from risk.models import Risk  # Direct import from another module

def audit_detail(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    risks = Risk.objects.filter(organization=audit.organization)  # Tight coupling
    # ...
```

**✅ Correct Pattern**:

```python
# Use events or service layer
def audit_detail(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    
    # Emit event to get related data
    event_dispatcher.emit('audit.viewed', {'audit': audit})
    
    # Or use a service that coordinates
    service = AuditService()
    context = service.get_audit_context(audit)
    # ...
```

### 6. Magic Strings and Numbers

**❌ Anti-Pattern**:

```python
if audit.status == 'draft':  # Magic string
    # ...

if audit.audit_type == 'stage1':  # Magic string
    # ...
```

**✅ Correct Pattern**:

```python
# Use constants or enums
class AuditStatus:
    DRAFT = 'draft'
    CLIENT_REVIEW = 'client_review'
    SUBMITTED_TO_CB = 'submitted_to_cb'
    DECIDED = 'decided'

if audit.status == AuditStatus.DRAFT:
    # ...

# Or use Django choices with constants
AUDIT_STATUS_CHOICES = [
    (AuditStatus.DRAFT, 'Draft'),
    (AuditStatus.CLIENT_REVIEW, 'Client Review'),
    # ...
]
```

### 7. God Objects

**❌ Anti-Pattern**:

```python
# One massive service with all methods
class AuditService:
    def create_audit(...)
    def update_audit(...)
    def delete_audit(...)
    def create_finding(...)
    def update_finding(...)
    def create_recommendation(...)
    def send_notification(...)
    def generate_report(...)
    # 50+ methods
```

**✅ Correct Pattern**:

```python
# Split into focused services
class AuditService:
    def create_audit(...)
    def update_audit(...)
    def get_audit(...)

class FindingService:
    def create_finding(...)
    def update_finding(...)

class NotificationService:
    def send_audit_notification(...)

class ReportService:
    def generate_audit_report(...)
```

---

## Refactoring Recommendations

### Current Code Issues

1. **Views contain business logic** (`audits/views.py`)
2. **Permission checks duplicated** (multiple views)
3. **No service layer** (direct model manipulation)
4. **Tight coupling** (direct imports between apps)

### Refactoring Plan

#### Step 1: Create Service Layer

```python
# branches/audits/services/__init__.py
from .audit_service import AuditService
from .finding_service import FindingService

# branches/audits/services/audit_service.py
class AuditService:
    def __init__(self):
        self.repository = AuditRepository()
        self.workflow = AuditWorkflow
    
    def create_audit(self, organization, certifications, audit_data, created_by):
        # Move logic from views
        pass
```

#### Step 2: Extract Permission Logic

```python
# trunk/permissions/predicates.py
class AuditPermissions:
    @staticmethod
    def can_view_audit(user, audit):
        # Centralized permission logic
        pass
```

#### Step 3: Refactor Views

```python
# branches/audits/views/audit_views.py
class AuditCreateView(LoginRequiredMixin, CreateView):
    def form_valid(self, form):
        service = AuditService()
        audit = service.create_audit(
            organization=form.cleaned_data['organization'],
            # ...
            created_by=self.request.user
        )
        return redirect('audit_detail', audit.id)
```

---

## Testing Patterns

### Service Layer Testing

```python
# tests/services/test_audit_service.py
class TestAuditService(TestCase):
    def setUp(self):
        self.service = AuditService()
        self.organization = Organization.objects.create(...)
    
    def test_create_audit(self):
        audit = self.service.create_audit(
            organization=self.organization,
            # ...
        )
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, AuditStatus.DRAFT)
```

### Permission Testing

```python
# tests/permissions/test_audit_permissions.py
class TestAuditPermissions(TestCase):
    def test_cb_admin_can_view_all_audits(self):
        user = User.objects.create_user(...)
        user.groups.add(Group.objects.get(name='cb_admin'))
        
        audit = Audit.objects.create(...)
        
        self.assertTrue(
            PermissionPredicate.can_view_audit(user, audit)
        )
```

---

## Summary

**Follow These Patterns**:

- ✅ Service Layer for business logic
- ✅ Repository Pattern for data access
- ✅ Workflow Pattern for state management
- ✅ Event-Driven for module communication
- ✅ Permission Predicates for reusable checks

**Avoid These Anti-Patterns**:

- ❌ Fat Views (business logic in views)
- ❌ Anemic Models (no business logic)
- ❌ Direct queries in views
- ❌ Duplicated permission checks
- ❌ Tight coupling between modules
- ❌ Magic strings/numbers
- ❌ God objects
