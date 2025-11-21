# Cedrus Architecture Vision: Trunk & Branches

## Executive Summary

Cedrus is architected as a **scalable Django monolith** using a **trunk-and-branches** metaphor:

- **Trunk (Core)**: Foundation services, shared infrastructure, and domain-agnostic utilities
- **Branches (Modules)**: Domain-specific applications that extend the trunk

This document outlines the ideal long-term architecture, design principles, and evolution path.

---

## The Trunk: Core Foundation

### Purpose

The trunk provides:

1. **Shared Infrastructure**: Authentication, permissions, file storage, notifications
2. **Domain Models**: Core entities used across all modules (Organization, Site, Standard, Certification)
3. **Cross-Cutting Concerns**: Logging, auditing, caching, messaging
4. **Integration Points**: APIs, webhooks, event system

### Trunk Components

```
cedrus/
├── trunk/                          # Core foundation (rename from 'core')
│   ├── models/
│   │   ├── __init__.py
│   │   ├── organization.py        # Organization, Site
│   │   ├── standards.py            # Standard, Certification
│   │   └── base.py                 # Abstract base models
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── organization_service.py
│   │   ├── certification_service.py
│   │   └── notification_service.py
│   ├── permissions/                # Permission system
│   │   ├── __init__.py
│   │   ├── mixins.py               # View permission mixins
│   │   ├── decorators.py           # Function decorators
│   │   ├── backends.py             # Custom permission backends
│   │   └── predicates.py           # Reusable permission checks
│   ├── events/                     # Event system
│   │   ├── __init__.py
│   │   ├── signals.py              # Django signals
│   │   ├── handlers.py             # Event handlers
│   │   └── types.py                # Event type definitions
│   ├── storage/                    # File storage abstraction
│   │   ├── __init__.py
│   │   ├── backends.py             # Storage backends (local, S3, etc.)
│   │   └── validators.py           # File validation
│   ├── api/                        # Shared API utilities
│   │   ├── __init__.py
│   │   ├── serializers.py          # Base serializers
│   │   ├── viewsets.py             # Base viewsets
│   │   └── permissions.py          # API permissions
│   └── utils/                      # Shared utilities
│       ├── __init__.py
│       ├── validators.py
│       ├── formatters.py
│       └── helpers.py
│
├── accounts/                       # Authentication & user management
│   ├── models/
│   │   └── profile.py
│   ├── services/
│   │   └── user_service.py
│   └── ...
│
└── branches/                       # Domain modules (branches)
    ├── audits/                     # External audit management
    ├── internal_audits/            # Internal audit module (future)
    ├── risk/                       # Risk management (future)
    ├── documents/                  # Document control (future)
    └── compliance/                 # Compliance tracking (future)
```

### Trunk Design Principles

1. **No Business Logic**: Trunk contains infrastructure, not domain logic
2. **Dependency Direction**: Branches depend on trunk, trunk never depends on branches
3. **Stable API**: Trunk interfaces must be stable and versioned
4. **Minimal Coupling**: Branches communicate through trunk events, not direct imports

---

## The Branches: Domain Modules

### Purpose

Branches are **self-contained domain modules** that:

1. Own their domain models and business logic
2. Extend trunk models through composition or foreign keys
3. Implement domain-specific workflows
4. Can be enabled/disabled via configuration

### Branch Structure Template

```
branches/audits/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── audit.py
│   ├── finding.py
│   └── recommendation.py
├── services/
│   ├── __init__.py
│   ├── audit_service.py           # Business logic
│   └── finding_service.py
├── workflows/
│   ├── __init__.py
│   ├── audit_workflow.py          # State machine logic
│   └── finding_workflow.py
├── views/
│   ├── __init__.py
│   ├── audit_views.py
│   └── finding_views.py
├── forms/
│   ├── __init__.py
│   └── audit_forms.py
├── permissions.py                 # Module-specific permissions
├── urls.py
├── admin.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_workflows.py
```

### Branch Design Principles

1. **Domain Ownership**: Each branch owns its domain models
2. **Service Layer**: Business logic in services, not views or models
3. **Workflow Separation**: State machines/workflows in dedicated modules
4. **Event-Driven**: Communicate with other branches via trunk events
5. **Testability**: Services are easily unit-testable

---

## Domain Modeling Strategy

### Current State Analysis

**Strengths:**

- Clear separation of concerns (accounts, core, audits)
- Good use of foreign keys and relationships
- Abstract base model for findings (good inheritance pattern)

**Areas for Improvement:**

- `core` app mixes infrastructure with domain models
- Business logic scattered in views
- No service layer abstraction
- Permission checks duplicated across views

### Proposed Domain Model

#### Trunk Models (Foundation)

```python
# trunk/models/organization.py
class Organization(BaseModel):
    """Core entity - used by all branches"""
    # ... existing fields ...
    
    class Meta:
        app_label = 'trunk'
        db_table = 'trunk_organization'

# trunk/models/standards.py
class Standard(BaseModel):
    """Reference data - used by audits, compliance, etc."""
    # ... existing fields ...

class Certification(BaseModel):
    """Certification lifecycle - shared across modules"""
    # ... existing fields ...
```

#### Branch Models (Domain-Specific)

```python
# branches/audits/models/audit.py
class Audit(BaseModel):
    """Audit domain model - extends trunk concepts"""
    organization = models.ForeignKey(
        'trunk.Organization',
        on_delete=models.CASCADE,
        related_name='audits'
    )
    certifications = models.ManyToManyField(
        'trunk.Certification',
        related_name='audits'
    )
    # ... audit-specific fields ...
```

### Model Relationships

```
┌─────────────────────────────────────────────────────────┐
│                    TRUNK (Foundation)                    │
├─────────────────────────────────────────────────────────┤
│  Organization  │  Site  │  Standard  │  Certification   │
└────────┬───────┴────────┴────────────┴──────────────────┘
         │
         │ Foreign Key References
         │
    ┌────┴────┬──────────────┬──────────────┬─────────────┐
    │         │              │              │             │
┌───▼───┐ ┌──▼──────┐ ┌──────▼──────┐ ┌────▼──────┐ ┌───▼────┐
│Audits │ │Internal │ │    Risk     │ │Documents  │ │Comply  │
│Branch │ │Audits   │ │  Branch     │ │  Branch   │ │Branch  │
└───────┘ └─────────┘ └─────────────┘ └───────────┘ └────────┘
```

---

## Separation of Concerns

### Current Issues

1. **Views contain business logic**: Status transitions, validations in views
2. **Models are anemic**: Business rules not in models
3. **Permission checks duplicated**: Same logic in multiple views
4. **No service layer**: Direct model manipulation in views

### Proposed Architecture Layers

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer                  │
│  Views (HTTP handlers) │ Templates │ Forms      │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Service Layer                       │
│  Business Logic │ Workflows │ Validations       │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Domain Layer                        │
│  Models │ Managers │ Querysets                   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Infrastructure Layer                 │
│  Storage │ Events │ Permissions │ Notifications │
└──────────────────────────────────────────────────┘
```

### Service Layer Pattern

```python
# branches/audits/services/audit_service.py
class AuditService:
    """Business logic for audit operations"""
    
    def __init__(self, audit_repository, event_dispatcher):
        self.audit_repository = audit_repository
        self.event_dispatcher = event_dispatcher
    
    def create_audit(self, organization, certifications, audit_data, created_by):
        """Create audit with validation and event emission"""
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
        self.event_dispatcher.emit('audit.created', audit)
        
        return audit
    
    def transition_status(self, audit, new_status, user):
        """Handle status transitions with workflow validation"""
        workflow = AuditWorkflow(audit)
        if not workflow.can_transition(new_status, user):
            raise WorkflowError("Invalid status transition")
        
        old_status = audit.status
        audit.status = new_status
        audit.save()
        
        self.event_dispatcher.emit('audit.status_changed', {
            'audit': audit,
            'old_status': old_status,
            'new_status': new_status,
            'user': user
        })
```

---

## Security & Permission Architecture

### Current State

- Group-based RBAC (good foundation)
- Permission checks in views (duplicated)
- No object-level permissions framework
- No permission caching

### Proposed Permission System

#### Permission Hierarchy

```
┌─────────────────────────────────────────┐
│         Permission System                │
├─────────────────────────────────────────┤
│                                         │
│  Role-Based (Groups)                    │
│  ├── cb_admin                           │
│  ├── lead_auditor                       │
│  ├── auditor                            │
│  ├── client_admin                       │
│  └── client_user                        │
│                                         │
│  Permission-Based (Django Permissions) │
│  ├── audits.view_audit                  │
│  ├── audits.create_audit                │
│  ├── audits.edit_audit                  │
│  └── audits.delete_audit                │
│                                         │
│  Object-Level (Custom)                  │
│  ├── audits.view_own_organization_audits│
│  ├── audits.edit_assigned_audits        │
│  └── audits.approve_audit               │
└─────────────────────────────────────────┘
```

#### Permission Backend

```python
# trunk/permissions/backends.py
class CedrusPermissionBackend(ModelBackend):
    """Custom permission backend with object-level checks"""
    
    def has_perm(self, user_obj, perm, obj=None):
        # Check Django permissions
        if super().has_perm(user_obj, perm, obj):
            return True
        
        # Check object-level permissions
        if obj is not None:
            return self._check_object_permission(user_obj, perm, obj)
        
        return False
    
    def _check_object_permission(self, user, perm, obj):
        """Object-level permission checks"""
        # Organization-based permissions
        if isinstance(obj, Organization):
            return self._check_organization_permission(user, perm, obj)
        
        # Audit-based permissions
        if isinstance(obj, Audit):
            return self._check_audit_permission(user, perm, obj)
        
        return False
```

#### Permission Predicates

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
        """Check if user is lead auditor for audit"""
        return audit.lead_auditor == user
    
    @staticmethod
    def is_audit_team_member(user, audit):
        """Check if user is team member"""
        return audit.team_members.filter(user=user).exists()
```

---

## Scalability Architecture

### Current Limitations

1. **Single Database**: All modules share one database
2. **No Caching**: No Redis/Memcached
3. **Local File Storage**: Not scalable
4. **Synchronous Processing**: No background tasks

### Scalability Strategy

#### Database Strategy

```
┌─────────────────────────────────────────┐
│         Database Architecture            │
├─────────────────────────────────────────┤
│                                         │
│  Primary Database (PostgreSQL)          │
│  ├── Trunk tables                      │
│  ├── Accounts tables                   │
│  └── All branch tables                 │
│                                         │
│  Read Replicas (Future)                 │
│  └── Reporting queries                 │
│                                         │
│  Connection Pooling (pgBouncer)         │
│  └── Efficient connection management    │
└─────────────────────────────────────────┘
```

#### Caching Strategy

```python
# trunk/cache/__init__.py
from django.core.cache import cache

class CacheKeys:
    """Centralized cache key management"""
    ORGANIZATION = "org:{id}"
    CERTIFICATION = "cert:{id}"
    USER_PERMISSIONS = "user:{id}:perms"
    
    @classmethod
    def organization(cls, org_id):
        return cls.ORGANIZATION.format(id=org_id)
```

#### File Storage Strategy

```python
# trunk/storage/backends.py
class StorageBackend(ABC):
    """Abstract storage backend"""
    
    @abstractmethod
    def save(self, file, path):
        pass
    
    @abstractmethod
    def delete(self, path):
        pass
    
    @abstractmethod
    def url(self, path):
        pass

class LocalStorageBackend(StorageBackend):
    """Local filesystem storage"""
    # ... implementation ...

class S3StorageBackend(StorageBackend):
    """AWS S3 storage"""
    # ... implementation ...

class AzureBlobStorageBackend(StorageBackend):
    """Azure Blob storage"""
    # ... implementation ...
```

#### Background Tasks (Future)

```python
# trunk/tasks/__init__.py
from celery import shared_task

@shared_task
def send_audit_notification(audit_id, event_type):
    """Background task for notifications"""
    # ... implementation ...
```

---

## Naming Conventions

### App Naming

- **Trunk apps**: `trunk`, `accounts` (infrastructure)
- **Branch apps**: `audits`, `internal_audits`, `risk`, `documents`, `compliance`
- **Utility apps**: `common`, `utils` (if needed)

### Model Naming

- **Singular nouns**: `Organization`, `Audit`, `Finding`
- **Clear, descriptive**: `AuditTeamMember` not `TeamMember`
- **Consistent suffixes**: `*Service`, `*Repository`, `*Workflow`

### Service Naming

- **Domain + Service**: `AuditService`, `CertificationService`
- **Action-based methods**: `create_audit()`, `transition_status()`
- **Query methods**: `get_audit()`, `list_audits()`

### File Naming

- **Snake_case**: `audit_service.py`, `finding_workflow.py`
- **Grouped by type**: `models/`, `services/`, `workflows/`
- **Clear purpose**: `audit_views.py` not `views.py`

---

## Folder Layout Evolution

### Current Structure

```
cedrus/
├── accounts/
├── core/
├── audits/
└── cedrus/
```

### Proposed Structure

```
cedrus/
├── trunk/                          # Core foundation
│   ├── models/
│   ├── services/
│   ├── permissions/
│   ├── events/
│   ├── storage/
│   ├── api/
│   └── utils/
│
├── accounts/                       # Authentication (trunk-adjacent)
│   ├── models/
│   ├── services/
│   └── ...
│
├── branches/                       # Domain modules
│   ├── audits/
│   │   ├── models/
│   │   ├── services/
│   │   ├── workflows/
│   │   ├── views/
│   │   └── ...
│   ├── internal_audits/            # Future
│   ├── risk/                       # Future
│   ├── documents/                  # Future
│   └── compliance/                 # Future
│
├── cedrus/                         # Project config
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
│   ├── trunk/
│   ├── accounts/
│   └── branches/
│       └── audits/
│
├── static/
│   ├── trunk/                      # Shared CSS/JS
│   └── branches/                   # Module-specific
│
└── tests/
    ├── trunk/
    ├── accounts/
    └── branches/
        └── audits/
```

---

## Future Module Blueprints

### Internal Audits Module

**Purpose**: Manage internal audits (first-party audits)

**Key Models:**

- `InternalAudit`
- `InternalAuditPlan`
- `InternalAuditFinding`

**Integration Points:**

- Uses `trunk.Organization`
- Shares `trunk.Standard`
- Different workflow than external audits

**File Structure:**

```
branches/internal_audits/
├── models/
│   ├── internal_audit.py
│   └── internal_finding.py
├── services/
│   └── internal_audit_service.py
└── workflows/
    └── internal_audit_workflow.py
```

### Risk Management Module

**Purpose**: Risk assessment, risk registers, risk treatment

**Key Models:**

- `Risk`
- `RiskRegister`
- `RiskTreatment`
- `RiskAssessment`

**Integration Points:**

- Links to `trunk.Organization`
- Can link to `audits.Audit` (risks identified in audits)
- Uses `trunk.Standard` (risk framework)

**File Structure:**

```
branches/risk/
├── models/
│   ├── risk.py
│   ├── risk_register.py
│   └── risk_treatment.py
├── services/
│   └── risk_service.py
└── workflows/
    └── risk_assessment_workflow.py
```

### Document Control Module

**Purpose**: Document management, version control, approval workflows

**Key Models:**

- `Document`
- `DocumentVersion`
- `DocumentCategory`
- `DocumentApproval`

**Integration Points:**

- Links to `trunk.Organization`
- Can attach to `audits.Audit` (evidence documents)
- Uses `trunk.storage` for file management

**File Structure:**

```
branches/documents/
├── models/
│   ├── document.py
│   ├── document_version.py
│   └── document_approval.py
├── services/
│   └── document_service.py
└── workflows/
    └── document_approval_workflow.py
```

### Compliance Module

**Purpose**: Compliance tracking, regulatory requirements, compliance assessments

**Key Models:**

- `ComplianceRequirement`
- `ComplianceAssessment`
- `ComplianceEvidence`
- `RegulatoryFramework`

**Integration Points:**

- Links to `trunk.Organization`
- Uses `trunk.Standard` (regulatory standards)
- Can link to `audits.Audit` (compliance audits)

**File Structure:**

```
branches/compliance/
├── models/
│   ├── compliance_requirement.py
│   ├── compliance_assessment.py
│   └── regulatory_framework.py
├── services/
│   └── compliance_service.py
└── workflows/
    └── compliance_assessment_workflow.py
```

---

## Technical Debt Prevention

### Code Quality Standards

1. **Type Hints**: Use Python type hints for all functions
2. **Docstrings**: Comprehensive docstrings for all public APIs
3. **Tests**: Minimum 80% code coverage
4. **Linting**: Use `ruff` or `black` for code formatting
5. **Pre-commit Hooks**: Automated checks before commits

### Architecture Decision Records (ADRs)

Document all major architectural decisions:

```
docs/adr/
├── 0001-trunk-and-branches-architecture.md
├── 0002-service-layer-pattern.md
├── 0003-permission-system-design.md
└── 0004-event-driven-communication.md
```

### Dependency Management

1. **Pin Versions**: Use `requirements.txt` with pinned versions
2. **Separate Dev/Prod**: `requirements-dev.txt` for development tools
3. **Security Scanning**: Regular dependency vulnerability scans
4. **Upgrade Path**: Document upgrade procedures

### Database Migration Strategy

1. **Backward Compatible**: Migrations should be reversible
2. **Data Migrations**: Separate data migrations from schema migrations
3. **Zero-Downtime**: Design migrations for zero-downtime deployments
4. **Testing**: Test migrations on staging before production

---

## Upgrade Paths

### Phase 1: Foundation (Current → 6 months)

**Goals:**

- Refactor `core` → `trunk`
- Introduce service layer
- Centralize permissions
- Add event system

**Steps:**

1. Create `trunk/` directory structure
2. Move shared models to `trunk/models/`
3. Create service layer for existing functionality
4. Refactor views to use services
5. Add permission backend

### Phase 2: Modularization (6-12 months)

**Goals:**

- Move `audits` to `branches/audits/`
- Establish branch patterns
- Add workflow layer
- Implement event-driven communication

**Steps:**

1. Create `branches/` directory
2. Move `audits/` to `branches/audits/`
3. Refactor to use trunk services
4. Add workflow state machines
5. Implement event system

### Phase 3: Expansion (12-18 months)

**Goals:**

- Add new modules (internal audits, risk, documents)
- API layer
- Background tasks
- Caching layer

**Steps:**

1. Implement new branch modules
2. Add Django REST Framework
3. Add Celery for background tasks
4. Add Redis for caching
5. Optimize database queries

### Phase 4: Scale (18-24 months)

**Goals:**

- Horizontal scaling
- Cloud storage
- CDN integration
- Performance optimization

**Steps:**

1. Move file storage to cloud (S3/Azure)
2. Add CDN for static files
3. Database read replicas
4. Load balancing
5. Performance monitoring

---

## Performance Considerations

### Database Optimization

1. **Indexes**: Add indexes on foreign keys and frequently queried fields
2. **Query Optimization**: Use `select_related()` and `prefetch_related()`
3. **Connection Pooling**: Use pgBouncer for PostgreSQL
4. **Query Analysis**: Regular query profiling and optimization

### Caching Strategy

1. **Template Caching**: Cache expensive template fragments
2. **Query Caching**: Cache frequently accessed data
3. **Permission Caching**: Cache user permissions
4. **CDN**: Use CDN for static assets

### Background Processing

1. **Celery**: For long-running tasks
2. **Email Sending**: Async email delivery
3. **File Processing**: Async file upload/processing
4. **Report Generation**: Background report generation

---

## Integration Points

### Event System

```python
# trunk/events/types.py
class EventType:
    AUDIT_CREATED = 'audit.created'
    AUDIT_STATUS_CHANGED = 'audit.status_changed'
    CERTIFICATION_ISSUED = 'certification.issued'
    ORGANIZATION_UPDATED = 'organization.updated'

# trunk/events/handlers.py
@event_handler(EventType.AUDIT_CREATED)
def send_audit_notification(event):
    """Send notification when audit is created"""
    # ... implementation ...
```

### API Layer

```python
# trunk/api/viewsets.py
class TrunkViewSet(viewsets.ModelViewSet):
    """Base viewset with common functionality"""
    permission_classes = [CedrusPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = StandardResultsSetPagination
```

### Webhook System (Future)

```python
# trunk/webhooks/__init__.py
class WebhookDispatcher:
    """Dispatch events to external webhooks"""
    def dispatch(self, event_type, payload):
        # ... implementation ...
```

---

## Conclusion

The trunk-and-branches architecture provides:

1. **Clear Separation**: Infrastructure vs. domain logic
2. **Scalability**: Easy to add new modules
3. **Maintainability**: Clear structure and patterns
4. **Testability**: Service layer enables unit testing
5. **Flexibility**: Modules can evolve independently

This architecture supports Cedrus's growth from a simple audit management system to a comprehensive compliance and risk management platform.
