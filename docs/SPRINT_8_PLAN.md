# Sprint 8 - MVP Completion & Quality Enhancement

**Sprint Duration:** November 21 - December 5, 2025 (2 weeks)  
**Sprint Goal:** Complete MVP feature set with 90%+ test coverage and optimized performance  
**Total Story Points:** 50 SP  
**Status:** 🟡 PLANNING

---

## Sprint Objectives

### Primary Goals

1. ✅ **Complete MVP-blocking features** - Findings management, client workflow, status validation
2. ✅ **Achieve 90%+ test coverage** - Comprehensive integration and edge case testing
3. ✅ **Optimize performance** - Implement query optimizations from performance audit
4. ✅ **MVP feature-complete** - Full audit lifecycle from creation to certification decision

### Success Criteria

- [ ] All EPIC-004 user stories implemented (Findings Management)
- [ ] Audit status workflow enforced with validation
- [ ] Audit documentation forms fully functional
- [ ] Test coverage ≥ 90%
- [ ] All performance optimizations from PERFORMANCE_AUDIT_REPORT.md implemented
- [ ] Load testing completed with <200ms average response time
- [ ] Zero high-severity security issues
- [ ] All 347+ tests passing

---

## Sprint Backlog

### 🔴 HIGH PRIORITY (MVP Blocking) - 26 SP

#### Task 8.1: Findings Management - Complete CRUD (8 SP)

**Epic:** EPIC-004  
**User Stories:** US-013  
**Priority:** P0 (BLOCKING)

**Scope:**

- ✅ Models already exist (Nonconformity, Observation, OpportunityForImprovement)
- ✅ Forms already exist (finding_forms.py)
- 🔴 Complete view layer implementation
- 🔴 Add validation for audit status (can't add findings if status='decided')
- 🔴 Integrate with FindingService

**Deliverables:**

1. Nonconformity CRUD views (create, detail, update, delete)
2. Observation CRUD views
3. OpportunityForImprovement CRUD views
4. Finding listing within audit detail
5. Permission checks (can_add_finding, can_edit_finding)
6. Integration tests for all CRUD operations

**Acceptance Criteria:**

- Lead auditors can create/edit/delete findings on assigned audits
- Auditors can create/edit findings on assigned audits
- Clients cannot create findings
- Findings cannot be added/edited when audit status = 'decided'
- Standard selection limited to audit's certifications
- All findings display in audit detail view

---

#### Task 8.2: Client Response Workflow (5 SP)

**Epic:** EPIC-004  
**User Stories:** US-014  
**Priority:** P0 (BLOCKING)

**Scope:**

- ✅ NonconformityResponseForm exists
- 🔴 Implement client response view
- 🔴 Add response_date tracking
- 🔴 Email notification to lead auditor (optional)
- 🔴 Response history tracking

**Deliverables:**

1. NonconformityResponseView (client-only access)
2. Response form with root_cause_analysis, corrective_action, preventive_action
3. Permission check (can_respond_to_nc)
4. Response timestamp tracking
5. Success message and redirect
6. Integration tests for response workflow

**Acceptance Criteria:**

- Client admins/users can respond to NCs for their organization's audits
- Response form shows current NC details
- Response includes root cause, corrective action, preventive action, evidence
- Response_date set automatically
- Verification_status remains 'open' until auditor verifies
- Auditors cannot use client response form

---

#### Task 8.3: Auditor Verification Workflow (5 SP)

**Epic:** EPIC-004  
**User Stories:** US-015  
**Priority:** P0 (BLOCKING)

**Scope:**

- ✅ NonconformityVerificationForm exists
- 🔴 Implement auditor verification view
- 🔴 Add verification actions (accept/reject)
- 🔴 Track verification history
- 🔴 Update verification_status

**Deliverables:**

1. NonconformityVerifyView (auditor-only access)
2. Verification form with action (accept/reject) and notes
3. Permission check (can_verify_nc)
4. FindingService.verify_nonconformity integration
5. Verification history tracking
6. Integration tests for verification workflow

**Acceptance Criteria:**

- Lead auditors can verify NCs on assigned audits
- Verification actions: 'accept' (closes NC) or 'reject' (remains open)
- Verification notes required for reject action
- Verified_by and verified_date set automatically
- Verification_status updates: open → closed (accept) or remains open (reject)
- Clients cannot access verification form

---

#### Task 8.4: Audit Status Workflow Validation (8 SP)

**Epic:** EPIC-002  
**User Stories:** US-009  
**Priority:** P0 (BLOCKING)

**Scope:**

- 🔴 Implement AuditWorkflow class with state machine
- 🔴 Enforce valid status transitions
- 🔴 Add pre-transition validation rules
- 🔴 Track workflow history
- 🔴 Update audit_transition_status view

**Deliverables:**

1. `trunk/workflows/audit_workflow.py` - Workflow state machine
2. Valid transition matrix (draft → in_review → submitted_to_cb, etc.)
3. Pre-transition validation (e.g., can't submit without findings)
4. Workflow history model (AuditWorkflowHistory)
5. Updated audit_transition_status view with validation
6. Unit tests for all transitions and validation rules

**Acceptance Criteria:**

- Only valid transitions allowed (e.g., draft → in_review, not draft → closed)
- Pre-transition checks:
  - Can't submit to CB without at least 1 finding
  - Can't close without all NCs verified
  - Can't transition to decision_pending without technical review
- Transition history logged with user, timestamp, notes
- Invalid transitions return ValidationError with clear message
- Permission checks: only lead auditor or CB admin can transition

**Valid Transitions:**

```
draft → in_review
in_review → submitted_to_cb
in_review → returned_for_correction
submitted_to_cb → technical_review
technical_review → decision_pending
decision_pending → closed
returned_for_correction → in_review
```

---

### 🟡 MEDIUM PRIORITY (MVP Enhancement) - 9 SP

#### Task 8.5: Audit Documentation Forms (9 SP)

**Epic:** EPIC-005  
**User Stories:** US-016, US-017, US-018  
**Priority:** P1 (HIGH)

**Scope:**

- ✅ Models exist (AuditChanges, AuditPlanReview, AuditSummary)
- ✅ Forms exist (documentation_forms.py)
- ✅ Views exist (audit_changes_edit, audit_plan_review_edit, audit_summary_edit)
- 🔴 Complete view templates
- 🔴 Add to audit detail page
- 🔴 Integration tests

**Deliverables:**

1. Templates for all 3 documentation forms
2. Navigation links in audit detail page
3. Permission checks (lead auditor only)
4. Auto-create related records if not exist
5. Integration tests for all 3 forms

**Acceptance Criteria:**

- Lead auditors can edit organization changes, plan review, summary
- Forms pre-populated if data exists
- Forms accessible from audit detail page
- CB admins can also edit
- Changes saved successfully with success message

---

### 🟢 QUALITY & PERFORMANCE - 15 SP

#### Task 8.6: Test Coverage Enhancement (8 SP)

**Priority:** P1 (HIGH)  
**Goal:** Achieve 90%+ test coverage

**Scope:**

- Current: 76% coverage (347 tests)
- Target: 90%+ coverage
- Focus: Integration tests, edge cases, error handling

**Deliverables:**

1. Integration tests for findings workflow (create → respond → verify)
2. Integration tests for status transitions
3. Edge case tests:
   - Invalid date ranges
   - Cross-organization access attempts
   - Concurrent edit conflicts
   - Invalid status transitions
4. Error handling tests (ValidationError, PermissionDenied)
5. Form validation tests
6. Coverage report showing 90%+ coverage

**Test Areas:**

- `audits/views.py` - Increase from 60% to 90%
- `trunk/workflows/` - New code, need 95%+ coverage
- `trunk/services/finding_service.py` - Increase to 95%
- `audits/forms.py` - Edge case validation

---

#### Task 8.7: Performance Optimization (7 SP)

**Priority:** P1 (HIGH)  
**Goal:** Implement optimizations from PERFORMANCE_AUDIT_REPORT.md

**Scope:**

- Optimize query-heavy views
- Add database indexes
- Implement caching strategy
- Load testing

**Deliverables:**

1. **Query Optimization** (3 SP)
   - Finding views: Add select_related/prefetch_related (50 → 10 queries)
   - Team views: Optimize team member queries (30 → 5 queries)
   - Evidence views: Optimize file queries (25 → 8 queries)

2. **Database Indexing** (2 SP)
   - Add indexes to Audit model:
     - `(organization, status)`
     - `(lead_auditor, status)`
   - Add indexes to Finding models:
     - `(audit, verification_status)` for Nonconformity
     - `(audit, created_at)` for all findings

3. **Caching Implementation** (1 SP)
   - Session-based caching for user permissions
   - Template fragment caching for audit detail sections

4. **Load Testing** (1 SP)
   - Locust or Django Silk performance testing
   - Target: <200ms average response time
   - Test with 100 concurrent users

**Success Metrics:**

- 40% query reduction on key views
- 25% faster page load times
- <200ms average response time under load
- All Django Debug Toolbar recommendations addressed

---

## Sprint Schedule (2 weeks)

### Week 1: Core Features (26 SP)

**Days 1-3:** Tasks 8.1, 8.2, 8.3 (Findings & Client Workflow)

- Findings CRUD implementation
- Client response workflow
- Auditor verification workflow
- Integration testing

**Days 4-5:** Task 8.4 (Status Workflow)

- Workflow state machine
- Transition validation
- History tracking
- Unit testing

### Week 2: Enhancement & Quality (24 SP)

**Days 6-7:** Task 8.5 (Documentation Forms)

- Template creation
- Integration with audit detail
- Testing

**Days 8-9:** Task 8.6 (Test Coverage)

- Integration tests
- Edge case tests
- Coverage reporting

**Days 10:** Task 8.7 (Performance Optimization)

- Query optimization
- Indexing
- Load testing

---

## Definition of Done

### Feature Completion

- [ ] All user stories implemented and tested
- [ ] All acceptance criteria met
- [ ] Code reviewed and approved
- [ ] Documentation updated

### Quality Gates

- [ ] Test coverage ≥ 90%
- [ ] All tests passing (0 failures)
- [ ] No high-severity lint errors
- [ ] Security grade maintained (A-)
- [ ] Performance targets met (<200ms response time)

### Documentation

- [ ] CODE_STANDARDS.md followed (docstrings, formatting)
- [ ] API documentation updated
- [ ] User guide updated (if needed)
- [ ] CHANGELOG.md updated

---

## Risks & Mitigation

### Risk 1: Workflow Complexity

**Impact:** HIGH  
**Probability:** MEDIUM  
**Mitigation:** Start with simple state machine, iterate. Use existing workflow patterns from codebase.

### Risk 2: Test Coverage Time

**Impact:** MEDIUM  
**Probability:** MEDIUM  
**Mitigation:** Prioritize integration tests for critical paths. Use test generators where possible.

### Risk 3: Performance Regression

**Impact:** LOW  
**Probability:** LOW  
**Mitigation:** Django Debug Toolbar already installed. Monitor queries continuously.

---

## Dependencies

### Internal Dependencies

- Sprint 7 completion (DONE ✅)
- CODE_STANDARDS.md in place (DONE ✅)
- Test infrastructure ready (DONE ✅)
- Django Debug Toolbar configured (DONE ✅)

### External Dependencies

- None

---

## Sprint Outcome

### MVP Status After Sprint 8

✅ **FEATURE-COMPLETE MVP**

- Full audit lifecycle workflow
- Client-auditor collaboration
- Findings management (NC, Obs, OFI)
- Status workflow with validation
- Audit documentation
- Evidence file management (already exists)
- Certification decision (model exists)
- 90%+ test coverage
- Optimized performance

### Ready for Sprint 9: Production Deployment

After Sprint 8, the system will be ready for:

- Production environment setup
- CI/CD pipeline
- User acceptance testing
- Production deployment

---

**Sprint Planning Meeting:** November 21, 2025  
**Sprint Start:** November 21, 2025  
**Sprint Review:** December 5, 2025  
**Sprint Retrospective:** December 5, 2025
