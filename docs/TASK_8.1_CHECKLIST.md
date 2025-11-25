# Task 8.1: Findings Management - Complete CRUD

**Sprint:** 8 - MVP Completion & Quality Enhancement  
**Priority:** P0 (BLOCKING)  
**Story Points:** 8  
**Estimated Time:** 12-16 hours  
**Status:** 🔴 Ready to Start

---

## Task Overview

Complete the findings management CRUD functionality for Nonconformities, Observations, and Opportunities for Improvement. The models, forms, and base views already exist - this task focuses on completing the view layer, templates, URL routing, and integration testing.

---

## Current State Analysis

### ✅ Already Implemented

**Models (100% Complete):**

- ✅ `Nonconformity` model with all fields
- ✅ `Observation` model with all fields  
- ✅ `OpportunityForImprovement` model with all fields
- ✅ Base `Finding` abstract model

**Forms (100% Complete):**

- ✅ `NonconformityForm` in `finding_forms.py`
- ✅ `ObservationForm` in `finding_forms.py`
- ✅ `OpportunityForImprovementForm` in `finding_forms.py`
- ✅ Form validation (standard limited to audit certifications)

**Services (100% Complete):**

- ✅ `FindingService.create_nonconformity()`
- ✅ `FindingService.create_observation()`
- ✅ `FindingService.create_ofi()`
- ✅ Event dispatching for finding creation

**Permission Helpers (100% Complete):**

- ✅ `can_add_finding(user, audit)` - Check if user can add findings
- ✅ `can_edit_finding(user, finding)` - Check if user can edit findings

**Base Views (80% Complete):**

- ✅ `NonconformityCreateView` - Class-based create view
- ✅ `NonconformityDetailView` - Detail view with permissions
- ✅ `NonconformityUpdateView` - Update view with permissions
- ✅ `NonconformityDeleteView` - Delete view with permissions
- ✅ `ObservationCreateView` - Class-based create view
- ✅ `ObservationUpdateView` - Update view
- ✅ `ObservationDeleteView` - Delete view
- ✅ `OpportunityForImprovementCreateView` - Create view
- ✅ `OpportunityForImprovementUpdateView` - Update view
- ✅ `OpportunityForImprovementDeleteView` - Delete view

**Templates (80% Complete):**

- ✅ `nonconformity_form.html` - NC create/edit form
- ✅ `nonconformity_detail.html` - NC detail view
- ✅ `observation_form.html` - Observation form
- ✅ `ofi_form.html` - OFI form
- ✅ `finding_confirm_delete.html` - Delete confirmation

**URLs (Partial - Mixed):**

- ✅ Class-based view URLs exist (nonconformity_create, nonconformity_detail)
- ⚠️ Legacy function-based URLs exist but views not implemented
- ⚠️ Missing observation and OFI detail/update/delete URLs

### 🔴 Missing / Incomplete

**View Integration:**

- 🔴 Observation detail view not exposed via URL
- 🔴 OFI detail view not exposed via URL
- 🔴 Findings not displaying in audit detail page
- 🔴 Add finding buttons missing from audit detail
- 🔴 Audit status validation (prevent adding findings when status='decided')

**URL Routing:**

- 🔴 Clean up duplicate/legacy URLs
- 🔴 Add missing observation detail/update/delete URLs
- 🔴 Add missing OFI detail/update/delete URLs
- 🔴 Standardize URL patterns

**Templates:**

- 🔴 Observation detail template missing
- 🔴 OFI detail template missing
- 🔴 Findings list section in audit_detail.html incomplete
- 🔴 "Add Finding" action buttons in audit detail

**Testing:**

- 🔴 Integration tests for complete CRUD workflow
- 🔴 Permission tests (auditor can create, client cannot)
- 🔴 Status validation tests (can't add when decided)
- 🔴 Edge case tests

---

## Implementation Checklist

### Phase 1: URL Cleanup & Standardization (2 hours)

**Goal:** Clean up URLs and establish consistent patterns

- [ ] **1.1** Review current URLs in `audits/urls.py`
  - Identify duplicate URLs (function-based vs class-based)
  - Document which URLs are in use vs legacy
  
- [ ] **1.2** Standardize URL patterns

  ```python
  # Nonconformity URLs
  path('audit/<int:audit_pk>/nc/create/', ...)  # Create
  path('nc/<int:pk>/', ...)                      # Detail
  path('nc/<int:pk>/edit/', ...)                 # Update
  path('nc/<int:pk>/delete/', ...)               # Delete
  
  # Observation URLs (add missing)
  path('audit/<int:audit_pk>/observation/create/', ...)
  path('observation/<int:pk>/', ...)
  path('observation/<int:pk>/edit/', ...)
  path('observation/<int:pk>/delete/', ...)
  
  # OFI URLs (add missing)
  path('audit/<int:audit_pk>/ofi/create/', ...)
  path('ofi/<int:pk>/', ...)
  path('ofi/<int:pk>/edit/', ...)
  path('ofi/<int:pk>/delete/', ...)
  ```

- [ ] **1.3** Remove or comment out legacy function-based URLs
  - Keep class-based view URLs only
  - Update any template references to old URLs

- [ ] **1.4** Test URL routing

  ```bash
  python manage.py show_urls | grep -E "nonconformity|observation|ofi"
  ```

**Deliverable:** Clean, consistent URL structure for all finding types

---

### Phase 2: Complete Detail Views (3 hours)

**Goal:** Ensure all finding types have detail views with proper permissions

#### 2.1 Observation Detail View

- [ ] **2.1.1** Create `ObservationDetailView` (copy pattern from NonconformityDetailView)

  ```python
  class ObservationDetailView(LoginRequiredMixin, DetailView):
      """View observation details."""
      model = Observation
      template_name = "audits/observation_detail.html"
      context_object_name = "observation"
  ```

- [ ] **2.1.2** Add role-based queryset filtering
  - CB Admin: sees all
  - Auditor: sees observations in assigned audits
  - Client: sees observations in their org's audits

- [ ] **2.1.3** Add context data with permissions
  - `can_edit` - Can user edit this observation?
  - `audit` - Link to parent audit

- [ ] **2.1.4** Create `observation_detail.html` template
  - Display: standard, clause, statement, explanation
  - Show audit info and created_by
  - Edit/Delete buttons if user has permission
  - "Back to Audit" link

#### 2.2 OFI Detail View

- [ ] **2.2.1** Create `OpportunityForImprovementDetailView`

  ```python
  class OpportunityForImprovementDetailView(LoginRequiredMixin, DetailView):
      """View opportunity for improvement details."""
      model = OpportunityForImprovement
      template_name = "audits/ofi_detail.html"
      context_object_name = "ofi"
  ```

- [ ] **2.2.2** Add role-based queryset filtering (same as observation)

- [ ] **2.2.3** Add context data with permissions

- [ ] **2.2.4** Create `ofi_detail.html` template
  - Display: standard, clause, improvement_area, suggestion
  - Show audit info and created_by
  - Edit/Delete buttons if user has permission
  - "Back to Audit" link

#### 2.3 Register Detail Views in URLs

- [ ] **2.3.1** Add observation_detail URL

  ```python
  path('observation/<int:pk>/', 
       views.ObservationDetailView.as_view(), 
       name='observation_detail'),
  ```

- [ ] **2.3.2** Add ofi_detail URL

  ```python
  path('ofi/<int:pk>/', 
       views.OpportunityForImprovementDetailView.as_view(), 
       name='ofi_detail'),
  ```

**Deliverable:** All 3 finding types have working detail views

---

### Phase 3: Audit Detail Integration (3 hours)

**Goal:** Display all findings in audit detail page with add/edit/delete actions

#### 3.1 Update Audit Detail View

- [ ] **3.1.1** Update `AuditDetailView.get_context_data()`
  - Already includes: `nonconformities`, `observations`, `ofis`
  - Verify counts are correct
  - Add `can_add_findings` permission flag

- [ ] **3.1.2** Update permission context

  ```python
  context['can_add_findings'] = (
      can_add_finding(user, audit) and 
      audit.status != 'decided'
  )
  ```

#### 3.2 Update Audit Detail Template

- [ ] **3.2.1** Add "Findings" section to `audit_detail.html`
  - Create collapsible/tabbed section for findings
  - Separate tabs/sections for: Nonconformities, Observations, OFIs

- [ ] **3.2.2** Add "Add Finding" buttons (if `can_add_findings`)

  ```html
  {% if can_add_findings %}
  <div class="btn-group">
    <a href="{% url 'audits:nonconformity_create' audit.pk %}" 
       class="btn btn-primary">
      Add Nonconformity
    </a>
    <a href="{% url 'audits:observation_create' audit.pk %}" 
       class="btn btn-info">
      Add Observation
    </a>
    <a href="{% url 'audits:ofi_create' audit.pk %}" 
       class="btn btn-success">
      Add OFI
    </a>
  </div>
  {% endif %}
  ```

- [ ] **3.2.3** Add Nonconformities table
  - Display: NC number, category, clause, statement, status, actions
  - Link NC number to detail page
  - Show verification status badge
  - Edit/Delete buttons if permitted
  - "No nonconformities" message if empty

- [ ] **3.2.4** Add Observations table
  - Display: Obs number, clause, statement, actions
  - Link to detail page
  - Edit/Delete buttons if permitted
  - "No observations" message if empty

- [ ] **3.2.5** Add OFI table
  - Display: OFI number, clause, improvement area, actions
  - Link to detail page
  - Edit/Delete buttons if permitted
  - "No opportunities" message if empty

- [ ] **3.2.6** Add finding counts summary

  ```html
  <div class="findings-summary">
    <span class="badge bg-danger">{{ nonconformities.count }} NCs</span>
    <span class="badge bg-warning">{{ observations.count }} Observations</span>
    <span class="badge bg-info">{{ ofis.count }} OFIs</span>
  </div>
  ```

**Deliverable:** Audit detail page displays all findings with CRUD actions

---

### Phase 4: Status Validation (2 hours)

**Goal:** Enforce business rule - no findings can be added/edited when audit status = 'decided'

#### 4.1 View-Level Validation

- [ ] **4.1.1** Update all create views' `test_func()`

  ```python
  def test_func(self):
      audit = get_object_or_404(Audit, pk=self.kwargs['audit_pk'])
      if audit.status == 'decided':
          return False  # Cannot add findings to decided audits
      return can_add_finding(self.request.user, audit)
  ```

  - ✅ NonconformityCreateView (already has this)
  - ✅ ObservationCreateView (already has this)
  - ✅ OpportunityForImprovementCreateView (already has this)
  - Verify all are consistent

- [ ] **4.1.2** Update all update views' `test_func()`

  ```python
  def test_func(self):
      finding = self.get_object()
      if finding.audit.status == 'decided':
          return False  # Cannot edit findings in decided audits
      return can_edit_finding(self.request.user, finding)
  ```

  - Check NonconformityUpdateView
  - Check ObservationUpdateView
  - Check OpportunityForImprovementUpdateView

- [ ] **4.1.3** Update all delete views' `test_func()`
  - Same logic as update views

#### 4.2 Template-Level Validation

- [ ] **4.2.1** Hide "Add Finding" buttons when status='decided'

  ```html
  {% if can_add_findings and audit.status != 'decided' %}
    <!-- Add buttons -->
  {% endif %}
  ```

- [ ] **4.2.2** Hide Edit/Delete buttons when status='decided'

  ```html
  {% if can_edit and audit.status != 'decided' %}
    <a href="..." class="btn btn-sm btn-secondary">Edit</a>
  {% endif %}
  ```

- [ ] **4.2.3** Add informational message when status='decided'

  ```html
  {% if audit.status == 'decided' %}
  <div class="alert alert-info">
    This audit has been closed. Findings cannot be modified.
  </div>
  {% endif %}
  ```

**Deliverable:** Findings cannot be modified after audit is decided

---

### Phase 5: Integration Testing (4 hours)

**Goal:** Comprehensive test coverage for findings CRUD workflow

#### 5.1 Create Test File Structure

- [ ] **5.1.1** Create `audits/test_findings_crud.py`
- [ ] **5.1.2** Set up test fixtures (users, audit, standards)

#### 5.2 Nonconformity CRUD Tests

- [ ] **5.2.1** `test_nc_create_as_lead_auditor_success`
  - Lead auditor creates NC on assigned audit
  - Verify NC created in database
  - Verify redirect to audit detail

- [ ] **5.2.2** `test_nc_create_as_auditor_success`
  - Team auditor creates NC on assigned audit
  - Verify success

- [ ] **5.2.3** `test_nc_create_as_client_fails`
  - Client attempts to create NC
  - Verify 403 Forbidden

- [ ] **5.2.4** `test_nc_create_when_decided_fails`
  - Auditor attempts to create NC on decided audit
  - Verify 403 Forbidden

- [ ] **5.2.5** `test_nc_detail_view_permissions`
  - Auditor can view NCs in assigned audits
  - Client can view NCs in their org's audits
  - Other users cannot view

- [ ] **5.2.6** `test_nc_update_as_creator_success`
  - Creator updates their NC
  - Verify changes saved

- [ ] **5.2.7** `test_nc_update_when_decided_fails`
  - Attempt to update NC on decided audit
  - Verify 403 Forbidden

- [ ] **5.2.8** `test_nc_delete_as_lead_auditor_success`
  - Lead auditor deletes NC
  - Verify NC removed from database

- [ ] **5.2.9** `test_nc_delete_when_decided_fails`
  - Attempt to delete NC on decided audit
  - Verify 403 Forbidden

#### 5.3 Observation CRUD Tests

- [ ] **5.3.1** `test_observation_create_success`
- [ ] **5.3.2** `test_observation_create_as_client_fails`
- [ ] **5.3.3** `test_observation_detail_view`
- [ ] **5.3.4** `test_observation_update_success`
- [ ] **5.3.5** `test_observation_delete_success`
- [ ] **5.3.6** `test_observation_crud_when_decided_fails`

#### 5.4 OFI CRUD Tests

- [ ] **5.4.1** `test_ofi_create_success`
- [ ] **5.4.2** `test_ofi_create_as_client_fails`
- [ ] **5.4.3** `test_ofi_detail_view`
- [ ] **5.4.4** `test_ofi_update_success`
- [ ] **5.4.5** `test_ofi_delete_success`
- [ ] **5.4.6** `test_ofi_crud_when_decided_fails`

#### 5.5 Audit Detail Integration Tests

- [ ] **5.5.1** `test_audit_detail_shows_all_findings`
  - Create 2 NCs, 1 Obs, 1 OFI
  - Verify all displayed in audit detail
  - Verify counts are correct

- [ ] **5.5.2** `test_add_finding_buttons_visible_for_auditor`
  - Auditor views audit detail
  - Verify "Add Finding" buttons present

- [ ] **5.5.3** `test_add_finding_buttons_hidden_for_client`
  - Client views audit detail
  - Verify "Add Finding" buttons absent

- [ ] **5.5.4** `test_add_finding_buttons_hidden_when_decided`
  - Set audit status to 'decided'
  - Verify "Add Finding" buttons absent even for auditor

#### 5.6 Edge Case Tests

- [ ] **5.6.1** `test_standard_limited_to_audit_certifications`
  - Attempt to create finding with standard not in audit
  - Verify validation error

- [ ] **5.6.2** `test_finding_service_event_dispatched`
  - Create NC/Obs/OFI
  - Verify FINDING_CREATED event dispatched

- [ ] **5.6.3** `test_concurrent_finding_creation`
  - Test race conditions

- [ ] **5.6.4** `test_finding_deletion_cascade`
  - Delete audit
  - Verify findings deleted

#### 5.7 Run Test Suite

- [ ] **5.7.1** Run tests with coverage

  ```bash
  python manage.py test audits.test_findings_crud --keepdb --verbosity=2
  ```

- [ ] **5.7.2** Verify all tests pass (aim for 100%)

- [ ] **5.7.3** Generate coverage report

  ```bash
  coverage run --source='.' manage.py test audits.test_findings_crud
  coverage html
  ```

- [ ] **5.7.4** Verify findings views coverage >90%

**Deliverable:** Comprehensive test suite with >90% coverage

---

### Phase 6: Code Quality & Documentation (2 hours)

#### 6.1 Code Quality

- [ ] **6.1.1** Run Black formatter

  ```bash
  black audits/views.py templates/audits/
  ```

- [ ] **6.1.2** Run isort

  ```bash
  isort audits/views.py
  ```

- [ ] **6.1.3** Run pylint

  ```bash
  pylint audits/views.py --disable=C0301,C0103
  ```

- [ ] **6.1.4** Fix any critical linting issues

#### 6.2 Documentation

- [ ] **6.2.1** Verify all views have docstrings (CODE_STANDARDS.md compliance)
  - Class docstrings
  - Method docstrings (get_queryset, get_context_data, etc.)

- [ ] **6.2.2** Add inline comments for complex logic

- [ ] **6.2.3** Update CHANGELOG.md

  ```markdown
  ## [Unreleased]
  
  ### Added
  - Complete CRUD functionality for Nonconformities
  - Complete CRUD functionality for Observations
  - Complete CRUD functionality for Opportunities for Improvement
  - Findings display in audit detail page
  - Status validation (findings locked when audit decided)
  ```

- [ ] **6.2.4** Update API_REFERENCE.md (if it exists)
  - Document new views
  - Document URL patterns

**Deliverable:** Clean, well-documented code following CODE_STANDARDS.md

---

### Phase 7: Manual QA & User Testing (1 hour)

#### 7.1 Manual Testing Checklist

- [ ] **7.1.1** Test as Lead Auditor
  - [ ] Create audit
  - [ ] Add nonconformity (verify form works, success message)
  - [ ] View NC detail (verify all fields displayed)
  - [ ] Edit NC (verify changes saved)
  - [ ] Add observation (verify success)
  - [ ] Add OFI (verify success)
  - [ ] View audit detail (verify all 3 findings displayed)
  - [ ] Delete a finding (verify removed)
  - [ ] Transition audit to 'decided'
  - [ ] Verify cannot add/edit findings after decided

- [ ] **7.1.2** Test as Team Auditor
  - [ ] View assigned audit
  - [ ] Add findings (verify success)
  - [ ] Cannot edit other auditor's findings (verify)

- [ ] **7.1.3** Test as Client
  - [ ] View audit for my organization
  - [ ] See findings (verify visible)
  - [ ] Cannot add findings (verify buttons hidden)
  - [ ] Cannot edit findings (verify no edit button)

- [ ] **7.1.4** Test as CB Admin
  - [ ] View any audit
  - [ ] Add findings to any audit (verify success)
  - [ ] Edit any finding (verify success)

#### 7.2 Browser Testing

- [ ] **7.2.1** Test in Chrome (latest)
- [ ] **7.2.2** Test in Firefox (latest)
- [ ] **7.2.3** Test in Safari (if on Mac)
- [ ] **7.2.4** Mobile responsive (verify forms work on mobile)

#### 7.3 Django Debug Toolbar

- [ ] **7.3.1** Check query counts
  - Audit detail with findings: Should be <30 queries
  - Finding detail: Should be <10 queries

- [ ] **7.3.2** Identify any N+1 query issues
- [ ] **7.3.3** Add select_related/prefetch_related if needed

**Deliverable:** Manually verified working functionality

---

## Acceptance Criteria Validation

### Must Pass

- [ ] ✅ Lead auditors can create/edit/delete findings on assigned audits
- [ ] ✅ Auditors can create/edit findings on assigned audits
- [ ] ✅ Clients cannot create findings
- [ ] ✅ Findings cannot be added/edited when audit status = 'decided'
- [ ] ✅ Standard selection limited to audit's certifications
- [ ] ✅ All findings display in audit detail view
- [ ] ✅ All CRUD operations work for NC, Observation, OFI
- [ ] ✅ Permission checks work correctly
- [ ] ✅ Integration tests pass with >90% coverage
- [ ] ✅ Code follows CODE_STANDARDS.md
- [ ] ✅ All docstrings present
- [ ] ✅ Manual QA completed

---

## Definition of Done

- [ ] All checklist items completed
- [ ] All tests pass (0 failures)
- [ ] Test coverage for findings views ≥90%
- [ ] Code formatted with Black
- [ ] Imports organized with isort
- [ ] No critical pylint errors
- [ ] All views have docstrings
- [ ] CHANGELOG.md updated
- [ ] Manual QA completed
- [ ] Code reviewed (self-review minimum)
- [ ] Task board updated (move to "Done")

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| 1. URL Cleanup | 2h | | |
| 2. Detail Views | 3h | | |
| 3. Audit Integration | 3h | | |
| 4. Status Validation | 2h | | |
| 5. Integration Testing | 4h | | |
| 6. Code Quality | 2h | | |
| 7. Manual QA | 1h | | |
| **TOTAL** | **17h** | | |

**Note:** Initial estimate was 12-16h, actual detailed breakdown is 17h. This is within acceptable range for P0 task.

---

## Risks & Mitigation

### Risk 1: URL routing conflicts

**Mitigation:** Review all URLs first, remove legacy patterns before adding new

### Risk 2: Template inconsistencies

**Mitigation:** Use existing nonconformity templates as reference pattern

### Risk 3: Permission logic complexity

**Mitigation:** Reuse existing permission helpers (can_add_finding, can_edit_finding)

### Risk 4: Test coverage time

**Mitigation:** Use test fixtures, focus on critical paths first

---

## Dependencies

- ✅ Sprint 7 complete (docstrings, CODE_STANDARDS.md)
- ✅ Models exist
- ✅ Forms exist
- ✅ Base views exist
- ✅ FindingService exists
- ✅ Permission helpers exist

---

## Next Steps After Completion

Once Task 8.1 is complete, proceed to:

1. **Task 8.2:** Client Response Workflow (depends on NC CRUD being complete)
2. **Task 8.3:** Auditor Verification (depends on Task 8.2)

---

**Ready to Start:** YES ✅  
**All dependencies met:** YES ✅  
**Clear acceptance criteria:** YES ✅  
**Estimated completion:** 2-3 days (with testing)
