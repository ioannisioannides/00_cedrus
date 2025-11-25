# Changelog

All notable changes to the Cedrus platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

#### Sprint 8 (November 2025)

**Task 8.1: Findings Management CRUD Enhancement**
- Complete CRUD operations for all finding types (Nonconformities, Observations, OFIs)
- New detail views: `ObservationDetailView` and `OpportunityForImprovementDetailView`
- Standardized URL patterns across all finding types
- Added missing detail page templates: `observation_detail.html`, `ofi_detail.html`
- Clickable finding links in audit detail page
- Comprehensive test suite with 18 test cases (`test_findings_crud.py`)
- pytest framework integration

**Task 8.1: Code Improvements**
- Removed legacy function-based URLs (7 deprecated endpoints)
- Fixed field references in templates (`statement`→`objective_evidence`, `description`→`objective_evidence`)
- Enhanced audit detail integration with proper URL references
- Status validation: findings cannot be added/edited when audit status = "decided"
- Role-based access control for all finding operations

#### Sprint 8 (November 2025) - MVP Complete

**Task 8.4: Audit Workflow State Machine**
- Implemented `trunk/workflows/audit_workflow.py` - Robust state machine for audit lifecycle
- 8 audit statuses with validated transitions (draft → scheduled → in_progress → report_draft → client_review → submitted → decided)
- Pre-transition validation rules (e.g., can't submit without client responses to major NCs)
- Integration with `audit_transition_status` view
- Comprehensive workflow tests (8 test cases)

**Task 8.5: Audit Documentation (Verified Complete)**
- AuditChanges, AuditPlanReview, AuditSummary forms functional
- All templates exist and integrated with audit detail
- Lead auditor and CB admin access

**Task 8.6: Test Coverage Enhancement**
- Added 26 new test cases (workflow + CRUD + integration)
- pytest framework fully configured
- Test coverage for state transitions, permissions, edge cases

**Task 8.7: Performance Optimization**
- Added 7 database indexes for common query patterns
- Audit indexes: (organization, status), (lead_auditor, status), (status, date)
- Finding indexes: (audit, verification_status), (audit, category), (audit, created_at)
- Query optimization with select_related/prefetch_related in detail views

**Client Response & Verification Workflows (Verified Complete)**
- Task 8.2: `NonconformityResponseView` - Client response to NCs (already implemented)
- Task 8.3: `NonconformityVerifyView` - Auditor verification workflow (already implemented)
- Full integration with FindingService

**Sprint Achievements**
- ✅ 50/50 story points delivered
- ✅ MVP feature-complete
- ✅ All audit lifecycle workflows functional
- ✅ Performance optimized with strategic indexes
- ✅ Comprehensive test framework established

#### Sprint 7 (November 2025)

**Documentation & Code Quality**
- Added 85+ docstrings across codebase (95.5% coverage)
- Created `CODE_STANDARDS.md` (950 lines) - comprehensive coding guidelines
- Security audit: A- grade, 0 high-severity issues
- Performance optimization recommendations documented

### Planned

- Risk management app (`risks/`)
- Internal audits app (`internal_audits/`)
- Email notifications
- PDF report generation
- REST API endpoints
- Advanced reporting and analytics
- Multi-language support
- Audit scheduling and calendar integration

## 1.0.0 - TBD

### Added

- Initial release of Cedrus platform
- User authentication and role-based access control
- Organization, Site, Standard, and Certification management
- Complete audit lifecycle management
- Finding management (Nonconformities, Observations, Opportunities for Improvement)
- Audit team member assignment
- Evidence file uploads
- Audit workflow (Draft → Client Review → Submitted to CB → Decided)
- Nonconformity response workflow (Open → Client Responded → Accepted → Closed)
- Role-based dashboards for CB Admins, Auditors, and Clients
- Django admin interface integration
- Seed data management command
- Comprehensive documentation (README, CONTRIBUTING, Architecture, Deployment, Models)

### Security

- Django's built-in authentication and authorization
- CSRF protection
- XSS protection via template auto-escaping
- Role-based access control using Django Groups
- View-level and query-level permission enforcement

### Documentation

- Complete README with architecture diagrams
- Contributing guidelines
- Deployment guide
- Architecture documentation
- Models reference documentation

---

## Version History

- **1.0.0**: Initial release

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes
