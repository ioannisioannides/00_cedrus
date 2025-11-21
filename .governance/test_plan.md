# Cedrus MVP - Comprehensive Test Plan

**QA Lead:** Testing & Quality Assurance  
**Date:** 2024  
**Status:** DRAFT - Pre-Release Testing  
**Severity Levels:** Critical, High, Medium, Low

---

## Executive Summary

This test plan covers all aspects of the Cedrus audit management platform MVP. The system manages multi-role workflows, audit lifecycle, findings management, and client responses. **Critical gaps identified** must be addressed before release.

---

## 1. CRITICAL GAPS IDENTIFIED

### 1.1 Missing Functionality (BLOCKING)

1. **Finding Management Views** - NO views exist for:
   - Creating Nonconformities (NC)
   - Creating Observations
   - Creating Opportunities for Improvement (OFI)
   - Editing findings
   - Deleting findings

2. **Client Response Workflow** - NO views exist for:
   - Clients responding to nonconformities (root cause, correction, corrective action)
   - Clients setting due dates
   - Clients uploading evidence files

3. **Audit Status Workflow** - NO views exist for:
   - Changing audit status (draft → client_review → submitted_to_cb → decided)
   - Status transition validation
   - Workflow enforcement

4. **Audit Metadata Management** - NO views exist for:
   - Editing AuditChanges
   - Editing AuditPlanReview
   - Editing AuditSummary
   - Editing AuditRecommendation (only CB Admin should edit)

5. **File Upload** - NO views exist for:
   - Uploading EvidenceFile
   - Viewing/downloading uploaded files
   - File deletion

6. **Team Member Management** - NO views exist for:
   - Adding team members to audits
   - Editing team members
   - Removing team members

### 1.2 Security & Permission Issues

1. **Missing Permission Checks:**
   - `audit_print` view has manual permission check but should use mixin
   - No permission checks on finding creation (when implemented)
   - No validation that clients can only respond to their organization's audits

2. **Data Leakage Risks:**
   - Client users without organization profile can see no audits (good), but error handling unclear
   - No explicit check that auditors can only see assigned audits

3. **CSRF Protection:**
   - Forms use `{% csrf_token %}` (good)
   - But no explicit CSRF testing in place

### 1.3 Validation Gaps

1. **Date Validation:**
   - No validation that `total_audit_date_to >= total_audit_date_from`
   - No validation that team member dates fall within audit dates
   - No validation that certification expiry dates are logical

2. **Business Logic:**
   - No validation that certifications belong to the audit's organization
   - No validation that sites belong to the audit's organization
   - No validation that lead_auditor is in lead_auditor group
   - No validation that audit status transitions are valid

3. **Required Fields:**
   - Many models have required fields but no form-level validation beyond Django defaults
   - No custom validation messages

### 1.4 Model Integrity Issues

1. **AuditTeamMember:**
   - `clean()` method exists but not called automatically (needs `full_clean()` in forms)
   - Validation: either `user` OR `name` must be provided

2. **Nonconformity Workflow:**
   - `verification_status` can be changed by anyone (no permission check)
   - No validation that `verified_by` is an auditor
   - No automatic timestamp on `verified_at` when status changes

3. **EvidenceFile:**
   - No file size limits
   - No file type restrictions
   - No validation that `finding` belongs to the same `audit`

---

## 2. TEST MATRIX

### 2.1 Authentication & Authorization

| Test ID | Test Case | Roles to Test | Expected Result | Priority |
|---------|-----------|---------------|-----------------|----------|
| AUTH-001 | Login with valid credentials | All roles | Redirect to appropriate dashboard | Critical |
| AUTH-002 | Login with invalid credentials | All roles | Error message, stay on login page | Critical |
| AUTH-003 | Access protected URL without login | Anonymous | Redirect to login page | Critical |
| AUTH-004 | Access URL after logout | All roles | Redirect to login page | Critical |
| AUTH-005 | Session timeout | All roles | Redirect to login after timeout | High |
| AUTH-006 | Access dashboard with no role | User with no group | Show "No role assigned" message | Medium |

### 2.2 Role-Based Access Control (RBAC)

| Test ID | Test Case | Role | URL/Feature | Expected Result | Priority |
|---------|-----------|------|-------------|-----------------|----------|
| RBAC-001 | CB Admin access CB dashboard | cb_admin | `/dashboard/cb/` | Access granted | Critical |
| RBAC-002 | CB Admin access auditor dashboard | cb_admin | `/dashboard/auditor/` | Redirect to CB dashboard | High |
| RBAC-003 | CB Admin access client dashboard | cb_admin | `/dashboard/client/` | Redirect to CB dashboard | High |
| RBAC-004 | Lead Auditor access auditor dashboard | lead_auditor | `/dashboard/auditor/` | Access granted | Critical |
| RBAC-005 | Auditor access auditor dashboard | auditor | `/dashboard/auditor/` | Access granted | Critical |
| RBAC-006 | Client Admin access client dashboard | client_admin | `/dashboard/client/` | Access granted | Critical |
| RBAC-007 | Client User access client dashboard | client_user | `/dashboard/client/` | Access granted | Critical |
| RBAC-008 | CB Admin create audit | cb_admin | `/audits/create/` | Access granted | Critical |
| RBAC-009 | Lead Auditor create audit | lead_auditor | `/audits/create/` | 403 Forbidden | Critical |
| RBAC-010 | Auditor create audit | auditor | `/audits/create/` | 403 Forbidden | Critical |
| RBAC-011 | Client create audit | client_admin | `/audits/create/` | 403 Forbidden | Critical |
| RBAC-012 | CB Admin view all audits | cb_admin | `/audits/` | See all audits | Critical |
| RBAC-013 | Lead Auditor view audits | lead_auditor | `/audits/` | See only assigned audits | Critical |
| RBAC-014 | Auditor view audits | auditor | `/audits/` | See only assigned audits | Critical |
| RBAC-015 | Client view audits | client_admin | `/audits/` | See only their org's audits | Critical |
| RBAC-016 | CB Admin edit any audit | cb_admin | `/audits/<pk>/edit/` | Access granted | Critical |
| RBAC-017 | Lead Auditor edit own audit | lead_auditor | `/audits/<pk>/edit/` | Access granted (if lead_auditor) | Critical |
| RBAC-018 | Lead Auditor edit other audit | lead_auditor | `/audits/<pk>/edit/` | 403 Forbidden | Critical |
| RBAC-019 | Auditor edit audit | auditor | `/audits/<pk>/edit/` | 403 Forbidden | Critical |
| RBAC-020 | Client edit audit | client_admin | `/audits/<pk>/edit/` | 403 Forbidden | Critical |
| RBAC-021 | CB Admin manage organizations | cb_admin | `/core/organizations/` | Access granted | Critical |
| RBAC-022 | Lead Auditor manage organizations | lead_auditor | `/core/organizations/` | 403 Forbidden | Critical |
| RBAC-023 | Client manage organizations | client_admin | `/core/organizations/` | 403 Forbidden | Critical |

### 2.3 Organization Management

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| ORG-001 | Create organization (CB Admin) | Create with all fields | Organization created, redirect to list | Critical |
| ORG-002 | Create organization (missing required) | Create without name | Form error, stay on form | Critical |
| ORG-003 | Create organization (duplicate customer_id) | Create with existing customer_id | Form error (unique constraint) | Critical |
| ORG-004 | Create organization (invalid email) | Create with invalid email format | Form error | High |
| ORG-005 | Create organization (invalid URL) | Create with invalid website | Form error | Medium |
| ORG-006 | Create organization (negative employee count) | Create with employee_count < 1 | Form error | High |
| ORG-007 | Update organization | Edit existing organization | Changes saved | Critical |
| ORG-008 | View organization list | List all organizations | All organizations shown | Critical |
| ORG-009 | View organization detail | View single organization | All details shown | Critical |
| ORG-010 | Delete organization (via admin) | Delete organization with audits | Protected (CASCADE) | Critical |

### 2.4 Site Management

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| SITE-001 | Create site (CB Admin) | Create with all fields | Site created | Critical |
| SITE-002 | Create site (missing organization) | Create without organization | Form error | Critical |
| SITE-003 | Create site (missing site_name) | Create without name | Form error | Critical |
| SITE-004 | Create site (negative employee count) | Create with employee_count < 1 | Form error | High |
| SITE-005 | Filter sites by organization | Filter list | Only matching sites shown | Medium |
| SITE-006 | Update site | Edit existing site | Changes saved | Critical |
| SITE-007 | Deactivate site | Set active=False | Site marked inactive | Medium |

### 2.5 Standard & Certification Management

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| STD-001 | Create standard (CB Admin) | Create with code and title | Standard created | Critical |
| STD-002 | Create standard (duplicate code) | Create with existing code | Form error (unique constraint) | Critical |
| STD-003 | Create certification (CB Admin) | Create for organization | Certification created | Critical |
| STD-004 | Create certification (duplicate org+standard) | Create duplicate | Form error (unique_together) | Critical |
| STD-005 | Create certification (invalid dates) | Issue date > expiry date | Should validate (NOT IMPLEMENTED) | High |
| STD-006 | Update certification status | Change status | Status updated | Critical |
| STD-007 | Filter certifications by organization | Filter list | Only matching certs shown | Medium |

### 2.6 Audit Creation & Management

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| AUDIT-001 | Create audit (CB Admin) | Create with all fields | Audit created | Critical |
| AUDIT-002 | Create audit (missing organization) | Create without organization | Form error | Critical |
| AUDIT-003 | Create audit (missing dates) | Create without dates | Form error | Critical |
| AUDIT-004 | Create audit (invalid date range) | End date < start date | Should validate (NOT IMPLEMENTED) | Critical |
| AUDIT-005 | Create audit (negative duration) | Duration < 0 | Form error | High |
| AUDIT-006 | Create audit (certification from different org) | Select cert from wrong org | Should validate (NOT IMPLEMENTED) | Critical |
| AUDIT-007 | Create audit (site from different org) | Select site from wrong org | Should validate (NOT IMPLEMENTED) | Critical |
| AUDIT-008 | Create audit (non-auditor as lead) | Select user not in lead_auditor group | Should validate (NOT IMPLEMENTED) | Critical |
| AUDIT-009 | Update audit (Lead Auditor, own audit) | Edit own audit | Changes saved | Critical |
| AUDIT-010 | Update audit (Lead Auditor, other audit) | Edit other's audit | 403 Forbidden | Critical |
| AUDIT-011 | View audit list (filtered by role) | List audits | Only permitted audits shown | Critical |
| AUDIT-012 | View audit detail (permission check) | View audit | Only if permitted | Critical |
| AUDIT-013 | Print audit (permission check) | Print audit | Only if permitted | Critical |
| AUDIT-014 | Change audit status (workflow) | Change status | Should validate transitions (NOT IMPLEMENTED) | Critical |

### 2.7 Findings Management (NOT IMPLEMENTED - BLOCKING)

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| FIND-001 | Create Nonconformity (Auditor) | Add NC to audit | NC created | Critical |
| FIND-002 | Create Nonconformity (Client) | Client tries to add NC | 403 Forbidden | Critical |
| FIND-003 | Create Nonconformity (missing clause) | Add NC without clause | Form error | Critical |
| FIND-004 | Create Nonconformity (missing category) | Add NC without category | Form error | Critical |
| FIND-005 | Create Observation (Auditor) | Add observation | Observation created | Critical |
| FIND-006 | Create OFI (Auditor) | Add OFI | OFI created | Critical |
| FIND-007 | Edit finding (Auditor, own finding) | Edit own finding | Changes saved | Critical |
| FIND-008 | Edit finding (Auditor, other's finding) | Edit other's finding | Should allow (team member) | High |
| FIND-009 | Delete finding (Auditor) | Delete finding | Finding deleted | High |
| FIND-010 | View findings (Client) | View audit findings | Can view, cannot edit | Critical |

### 2.8 Nonconformity Response Workflow (NOT IMPLEMENTED - BLOCKING)

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| NC-001 | Client respond to NC (own org) | Add root cause, correction, CA | Response saved | Critical |
| NC-002 | Client respond to NC (other org) | Client tries to respond | 403 Forbidden | Critical |
| NC-003 | Client set due date | Set due date | Due date saved | Critical |
| NC-004 | Client respond (missing fields) | Submit without root cause | Form error or allow | High |
| NC-005 | Auditor verify response (accept) | Mark as accepted | Status = accepted, verified_by set | Critical |
| NC-006 | Auditor verify response (reject) | Mark as open | Status = open, comments added | Critical |
| NC-007 | Auditor verify (not assigned) | Auditor not on audit team | 403 Forbidden | Critical |
| NC-008 | NC status workflow | Open → Responded → Accepted → Closed | Status transitions validated | Critical |
| NC-009 | NC verification timestamp | Verify NC | verified_at automatically set | High |

### 2.9 File Upload (NOT IMPLEMENTED - BLOCKING)

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| FILE-001 | Upload evidence file (Auditor) | Upload file to audit | File uploaded | Critical |
| FILE-002 | Upload evidence file (Client) | Client uploads file | File uploaded (if permitted) | High |
| FILE-003 | Upload file (too large) | Upload >10MB file | Error message (NOT IMPLEMENTED) | High |
| FILE-004 | Upload file (wrong type) | Upload executable | Error message (NOT IMPLEMENTED) | High |
| FILE-005 | Upload file to NC | Link file to nonconformity | File linked to NC | Critical |
| FILE-006 | Upload file (wrong audit) | Link file to NC from different audit | Should validate (NOT IMPLEMENTED) | Critical |
| FILE-007 | Download file (permission check) | Download evidence | Only if permitted | Critical |
| FILE-008 | Delete file (permission check) | Delete file | Only uploader or admin | High |

### 2.10 Audit Workflow & Status Transitions (NOT IMPLEMENTED - BLOCKING)

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| WF-001 | Move audit to Client Review | Change status draft → client_review | Status updated | Critical |
| WF-002 | Move audit to Submitted | Change status client_review → submitted_to_cb | Status updated | Critical |
| WF-003 | Move audit to Decided | Change status submitted_to_cb → decided | Status updated | Critical |
| WF-004 | Invalid transition (skip step) | draft → submitted_to_cb | Should reject (NOT IMPLEMENTED) | Critical |
| WF-005 | Invalid transition (backward) | submitted_to_cb → draft | Should reject or allow? | High |
| WF-006 | Edit audit in Client Review | Edit audit in client_review | Should allow or restrict? | High |
| WF-007 | Add findings after Submitted | Add NC after submitted | Should allow or restrict? | High |
| WF-008 | Client respond in Draft | Client respond when draft | Should allow or restrict? | High |

### 2.11 Audit Metadata Management (NOT IMPLEMENTED - BLOCKING)

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| META-001 | Edit AuditChanges (Auditor) | Edit changes record | Changes saved | Critical |
| META-002 | Edit AuditPlanReview (Auditor) | Edit plan review | Changes saved | Critical |
| META-003 | Edit AuditSummary (Auditor) | Edit summary | Changes saved | Critical |
| META-004 | Edit AuditRecommendation (CB Admin) | Edit recommendation | Changes saved | Critical |
| META-005 | Edit AuditRecommendation (Auditor) | Auditor tries to edit | 403 Forbidden | Critical |
| META-006 | Auto-create metadata | Create audit | Related records auto-created | High |

### 2.12 Team Member Management (NOT IMPLEMENTED - BLOCKING)

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| TEAM-001 | Add team member (user) | Add user to audit team | Member added | Critical |
| TEAM-002 | Add team member (external) | Add external expert | Member added | Critical |
| TEAM-003 | Add team member (missing name) | Add without name or user | Form error | Critical |
| TEAM-004 | Add team member (invalid dates) | Dates outside audit dates | Should validate (NOT IMPLEMENTED) | High |
| TEAM-005 | Edit team member | Edit member details | Changes saved | High |
| TEAM-006 | Remove team member | Delete member | Member removed | High |

### 2.13 Data Integrity & Relationships

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| DATA-001 | Delete organization with audits | Delete org | CASCADE deletes audits | Critical |
| DATA-002 | Delete organization with sites | Delete org | CASCADE deletes sites | Critical |
| DATA-003 | Delete audit with findings | Delete audit | CASCADE deletes findings | Critical |
| DATA-004 | Delete standard with certifications | Delete standard | PROTECT (error) | Critical |
| DATA-005 | Delete user with profile | Delete user | CASCADE deletes profile | Critical |
| DATA-006 | Delete user who created audit | Delete user | PROTECT (error) | Critical |

### 2.14 Edge Cases & Error Handling

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| EDGE-001 | Access non-existent audit | View audit/<999>/ | 404 Not Found | High |
| EDGE-002 | Access audit with invalid PK | View audit/abc/ | 404 Not Found | High |
| EDGE-003 | Client without organization | Client with no org profile | See no audits | High |
| EDGE-004 | Auditor not assigned to audit | Auditor views unassigned audit | 403 or 404 | High |
| EDGE-005 | Empty audit list | List with no audits | Empty list message | Low |
| EDGE-006 | Very long text fields | Enter >10,000 chars | Should handle gracefully | Medium |
| EDGE-007 | Special characters in names | Enter <script> tags | Should escape in templates | Critical |
| EDGE-008 | Concurrent edits | Two users edit same audit | Last save wins (expected) | Medium |

### 2.15 Security Testing

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| SEC-001 | CSRF token missing | Submit form without token | 403 Forbidden | Critical |
| SEC-002 | SQL Injection attempt | Enter SQL in form fields | Escaped/sanitized | Critical |
| SEC-003 | XSS attempt | Enter <script> tags | Escaped in output | Critical |
| SEC-004 | Direct URL access (unauthorized) | Access URL directly | 403 Forbidden | Critical |
| SEC-005 | Permission escalation | Client tries to access CB admin URL | 403 Forbidden | Critical |
| SEC-006 | Session hijacking | Use another user's session | Should be prevented | High |
| SEC-007 | File upload path traversal | Upload ../../../etc/passwd | Should be sanitized | Critical |
| SEC-008 | Mass assignment | POST extra fields | Should ignore extra fields | High |

---

## 3. TEST ENVIRONMENT SETUP

### 3.1 Test Database
- Use separate test database (SQLite for speed)
- Reset between test runs
- Seed with test data

### 3.2 Test Users
Create test users for each role:
- `test_cb_admin` (cb_admin group)
- `test_lead_auditor` (lead_auditor group)
- `test_auditor` (auditor group)
- `test_client_admin` (client_admin group, with org)
- `test_client_user` (client_user group, with org)
- `test_no_role` (no groups)

### 3.3 Test Data
- At least 3 organizations
- At least 5 sites (across orgs)
- At least 3 standards
- At least 5 certifications
- At least 5 audits (various statuses, assigned to different auditors)
- At least 10 findings (NCs, Observations, OFIs)
- At least 5 evidence files

---

## 4. AUTOMATED TEST COVERAGE

### 4.1 Unit Tests
- Model validation
- Model methods
- Form validation
- Utility functions

### 4.2 Integration Tests
- View permissions
- Workflow transitions
- Data relationships
- Queryset filtering

### 4.3 End-to-End Tests
- Complete audit creation flow
- Complete finding workflow
- Complete client response workflow

---

## 5. MANUAL TESTING CHECKLIST

See `MANUAL_QA_CHECKLIST.md` for detailed manual testing procedures.

---

## 6. BUG TRACKING

### 6.1 Bug Severity
- **Critical:** Blocks release, security issue, data loss
- **High:** Major functionality broken, workflow blocked
- **Medium:** Minor functionality issue, UX problem
- **Low:** Cosmetic, documentation, nice-to-have

### 6.2 Bug Report Template
```
BUG-XXX: [Title]
Severity: [Critical/High/Medium/Low]
Component: [accounts/audits/core]
Steps to Reproduce:
1. ...
2. ...
Expected Result:
Actual Result:
Screenshots/Logs:
```

---

## 7. RELEASE CRITERIA

### 7.1 Must Have (Blocking)
- [ ] All Critical and High priority tests pass
- [ ] All missing functionality implemented (Findings, Client Response, Workflow, Files, Team Members)
- [ ] All security tests pass
- [ ] No data integrity issues
- [ ] All permission checks in place
- [ ] Date validation implemented
- [ ] Business logic validation implemented

### 7.2 Should Have
- [ ] All Medium priority tests pass
- [ ] Manual QA checklist completed
- [ ] Performance acceptable (<2s page load)
- [ ] Error messages user-friendly

### 7.3 Nice to Have
- [ ] All Low priority tests pass
- [ ] Documentation complete
- [ ] Code coverage >80%

---

## 8. RISK ASSESSMENT

### 8.1 High Risk Areas
1. **Permission System** - Complex role-based access, easy to miss edge cases
2. **Workflow Transitions** - Status changes must be validated
3. **Data Relationships** - CASCADE vs PROTECT must be correct
4. **File Uploads** - Security and validation critical
5. **Client Response Workflow** - Complex state machine

### 8.2 Mitigation
- Comprehensive automated tests for permissions
- Explicit workflow state machine
- Careful review of model relationships
- File upload validation and security
- Extensive manual testing of client workflow

---

## 9. TEST EXECUTION PLAN

### Phase 1: Unit Tests (Week 1)
- Model tests
- Form tests
- Utility function tests

### Phase 2: Integration Tests (Week 1-2)
- View permission tests
- Workflow tests
- Relationship tests

### Phase 3: Security Tests (Week 2)
- Permission escalation tests
- CSRF tests
- XSS/SQL injection tests

### Phase 4: Manual Testing (Week 2-3)
- Role-based workflows
- End-to-end scenarios
- Edge cases

### Phase 5: Bug Fixes & Retest (Week 3-4)
- Fix identified bugs
- Retest affected areas
- Regression testing

---

## 10. SIGN-OFF

**QA Lead:** _________________  
**Date:** _________________  
**Status:** [ ] APPROVED [ ] REJECTED [ ] CONDITIONAL

**Conditions for Conditional Approval:**
- [ ] List of blocking issues
- [ ] Timeline for fixes
- [ ] Retest plan

---

**END OF TEST PLAN**

