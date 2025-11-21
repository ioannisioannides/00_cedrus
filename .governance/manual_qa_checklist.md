# Cedrus MVP - Manual QA Checklist

**QA Lead:** Testing & Quality Assurance  
**Date:** 2024  
**Status:** Pre-Release Manual Testing

---

## Instructions

1. **Test Environment:** Use a clean database with seeded test data
2. **Test Users:** Use the seed_data command to create test users
3. **Browser:** Test in Chrome, Firefox, and Safari
4. **Documentation:** Document any bugs found with screenshots and steps to reproduce
5. **Sign-off:** Each section must be signed off before release

---

## 1. Authentication & Login

### 1.1 Login Functionality
- [ ] **TEST-001:** Login with valid credentials (all roles)
  - [ ] CB Admin login
  - [ ] Lead Auditor login
  - [ ] Auditor login
  - [ ] Client Admin login
  - [ ] Client User login
  - **Expected:** Redirect to appropriate dashboard
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-002:** Login with invalid credentials
  - [ ] Wrong username
  - [ ] Wrong password
  - [ ] Empty fields
  - **Expected:** Error message, stay on login page
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-003:** Access protected URL without login
  - [ ] Try to access `/audits/`
  - [ ] Try to access `/dashboard/`
  - **Expected:** Redirect to login page with `next` parameter
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-004:** Logout functionality
  - [ ] Click logout button
  - [ ] Try to access protected URL after logout
  - **Expected:** Redirect to login, cannot access protected URLs
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-005:** Session persistence
  - [ ] Login, close browser, reopen
  - [ ] Check if still logged in
  - **Expected:** Session expired, must login again
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 2. Role-Based Dashboards

### 2.1 CB Admin Dashboard
- [ ] **TEST-006:** CB Admin dashboard access
  - [ ] Login as CB Admin
  - [ ] Verify redirect to `/dashboard/cb/`
  - [ ] Check statistics displayed (organizations, certifications, audits)
  - [ ] Check recent audits list
  - **Expected:** Dashboard shows all stats and recent audits
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-007:** CB Admin cannot access other dashboards
  - [ ] Try to access `/dashboard/auditor/`
  - [ ] Try to access `/dashboard/client/`
  - **Expected:** Redirect to CB dashboard
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 2.2 Auditor Dashboard
- [ ] **TEST-008:** Lead Auditor dashboard access
  - [ ] Login as Lead Auditor
  - [ ] Verify redirect to `/dashboard/auditor/`
  - [ ] Check audits list (only assigned audits)
  - **Expected:** Shows only audits where user is lead auditor or team member
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-009:** Auditor dashboard access
  - [ ] Login as regular Auditor
  - [ ] Verify redirect to `/dashboard/auditor/`
  - [ ] Check audits list (only assigned audits)
  - **Expected:** Shows only audits where user is team member
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 2.3 Client Dashboard
- [ ] **TEST-010:** Client Admin dashboard access
  - [ ] Login as Client Admin (with organization)
  - [ ] Verify redirect to `/dashboard/client/`
  - [ ] Check audits list (only their organization's audits)
  - **Expected:** Shows only audits for user's organization
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-011:** Client User dashboard access
  - [ ] Login as Client User (with organization)
  - [ ] Verify redirect to `/dashboard/client/`
  - [ ] Check audits list
  - **Expected:** Shows only audits for user's organization
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-012:** Client without organization
  - [ ] Login as Client User (no organization in profile)
  - [ ] Check dashboard
  - **Expected:** Shows no audits, clear message
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 3. Organization Management (CB Admin Only)

### 3.1 Organization List
- [ ] **TEST-013:** View organization list
  - [ ] Login as CB Admin
  - [ ] Navigate to `/core/organizations/`
  - [ ] Verify all organizations are listed
  - [ ] Check pagination (if >20 organizations)
  - **Expected:** All organizations displayed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-014:** Other roles cannot access
  - [ ] Login as Lead Auditor, try to access
  - [ ] Login as Client Admin, try to access
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 3.2 Create Organization
- [ ] **TEST-015:** Create organization (valid data)
  - [ ] Fill all required fields
  - [ ] Submit form
  - **Expected:** Organization created, redirect to list
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-016:** Create organization (missing required fields)
  - [ ] Try to submit without name
  - [ ] Try to submit without customer_id
  - [ ] Try to submit without registered_address
  - **Expected:** Form errors, stay on form
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-017:** Create organization (duplicate customer_id)
  - [ ] Create org with customer_id "TEST001"
  - [ ] Try to create another with same customer_id
  - **Expected:** Form error, duplicate not allowed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-018:** Create organization (invalid email)
  - [ ] Enter invalid email format
  - **Expected:** Form error
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-019:** Create organization (invalid URL)
  - [ ] Enter invalid website URL
  - **Expected:** Form error
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-020:** Create organization (negative employee count)
  - [ ] Enter employee_count < 1
  - **Expected:** Form error
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 3.3 Update Organization
- [ ] **TEST-021:** Update organization
  - [ ] Edit existing organization
  - [ ] Change name, employee count
  - [ ] Submit form
  - **Expected:** Changes saved, redirect to list
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 3.4 View Organization Detail
- [ ] **TEST-022:** View organization detail
  - [ ] Click on organization from list
  - [ ] Verify all details displayed
  - **Expected:** All organization fields shown
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 4. Site Management (CB Admin Only)

### 4.1 Site List
- [ ] **TEST-023:** View site list
  - [ ] Navigate to `/core/sites/`
  - [ ] Verify all sites listed
  - **Expected:** All sites displayed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-024:** Filter sites by organization
  - [ ] Select organization from filter
  - [ ] Submit filter
  - **Expected:** Only sites for selected organization shown
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 4.2 Create Site
- [ ] **TEST-025:** Create site (valid data)
  - [ ] Select organization
  - [ ] Enter site name and address
  - [ ] Submit form
  - **Expected:** Site created, redirect to list
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-026:** Create site (missing required fields)
  - [ ] Try without organization
  - [ ] Try without site_name
  - **Expected:** Form errors
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 4.3 Update Site
- [ ] **TEST-027:** Update site
  - [ ] Edit existing site
  - [ ] Change site name, deactivate site
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 5. Standard & Certification Management (CB Admin Only)

### 5.1 Standard Management
- [ ] **TEST-028:** Create standard
  - [ ] Enter code and title
  - [ ] Submit form
  - **Expected:** Standard created
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-029:** Create standard (duplicate code)
  - [ ] Try to create duplicate code
  - **Expected:** Form error
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 5.2 Certification Management
- [ ] **TEST-030:** Create certification
  - [ ] Select organization and standard
  - [ ] Enter scope and status
  - [ ] Submit form
  - **Expected:** Certification created
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-031:** Create certification (duplicate org+standard)
  - [ ] Try to create duplicate combination
  - **Expected:** Form error
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-032:** Update certification status
  - [ ] Change status (draft → active)
  - **Expected:** Status updated
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 6. Audit Management

### 6.1 Create Audit (CB Admin Only)
- [ ] **TEST-033:** Create audit (valid data)
  - [ ] Select organization
  - [ ] Select certifications (must belong to org)
  - [ ] Select sites (must belong to org)
  - [ ] Enter dates, duration, lead auditor
  - [ ] Submit form
  - **Expected:** Audit created, redirect to detail page
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-034:** Create audit (missing required fields)
  - [ ] Try without organization
  - [ ] Try without dates
  - [ ] Try without lead auditor
  - **Expected:** Form errors
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-035:** Create audit (invalid date range)
  - [ ] Enter end_date < start_date
  - **Expected:** Form error (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-036:** Create audit (negative duration)
  - [ ] Enter duration < 0
  - **Expected:** Form error
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-037:** Create audit (certification from wrong org)
  - [ ] Select certification from different organization
  - **Expected:** Form error (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-038:** Create audit (site from wrong org)
  - [ ] Select site from different organization
  - **Expected:** Form error (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-039:** Other roles cannot create audit
  - [ ] Login as Lead Auditor, try to create
  - [ ] Login as Client Admin, try to create
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 6.2 Audit List
- [ ] **TEST-040:** CB Admin sees all audits
  - [ ] Login as CB Admin
  - [ ] Navigate to `/audits/`
  - **Expected:** All audits displayed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-041:** Lead Auditor sees only assigned audits
  - [ ] Login as Lead Auditor
  - [ ] Navigate to `/audits/`
  - **Expected:** Only audits where user is lead auditor or team member
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-042:** Client sees only their org's audits
  - [ ] Login as Client Admin
  - [ ] Navigate to `/audits/`
  - **Expected:** Only audits for user's organization
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-043:** Filter audits by organization
  - [ ] Select organization filter
  - **Expected:** Only matching audits shown
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-044:** Filter audits by status
  - [ ] Select status filter
  - **Expected:** Only matching audits shown
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-045:** Filter audits by type
  - [ ] Select audit type filter
  - **Expected:** Only matching audits shown
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 6.3 Audit Detail View
- [ ] **TEST-046:** View audit detail (CB Admin)
  - [ ] Click on audit from list
  - [ ] Verify all information displayed
  - [ ] Check nonconformities, observations, OFIs sections
  - **Expected:** All audit details shown
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-047:** View audit detail (Lead Auditor, own audit)
  - [ ] Login as Lead Auditor
  - [ ] View audit where user is lead auditor
  - **Expected:** Can view audit
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-048:** View audit detail (Lead Auditor, other's audit)
  - [ ] Login as Lead Auditor
  - [ ] Try to view audit where user is NOT lead auditor
  - **Expected:** 404 Not Found
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-049:** View audit detail (Client, own org)
  - [ ] Login as Client Admin
  - [ ] View audit for user's organization
  - **Expected:** Can view audit
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-050:** View audit detail (Client, other org)
  - [ ] Login as Client Admin
  - [ ] Try to view audit for different organization
  - **Expected:** 404 Not Found
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 6.4 Edit Audit
- [ ] **TEST-051:** Edit audit (CB Admin)
  - [ ] Login as CB Admin
  - [ ] Edit any audit
  - [ ] Change dates, duration, status
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-052:** Edit audit (Lead Auditor, own audit)
  - [ ] Login as Lead Auditor
  - [ ] Edit audit where user is lead auditor
  - **Expected:** Can edit, changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-053:** Edit audit (Lead Auditor, other's audit)
  - [ ] Login as Lead Auditor
  - [ ] Try to edit audit where user is NOT lead auditor
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-054:** Edit audit (Client)
  - [ ] Login as Client Admin
  - [ ] Try to edit audit
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 6.5 Print Audit
- [ ] **TEST-055:** Print audit (all permitted roles)
  - [ ] Login as CB Admin, print audit
  - [ ] Login as Lead Auditor (own audit), print audit
  - [ ] Login as Client Admin (own org), print audit
  - **Expected:** Print-friendly view displayed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-056:** Print audit (unauthorized)
  - [ ] Login as Lead Auditor, try to print other's audit
  - [ ] Login as Client Admin, try to print other org's audit
  - **Expected:** Redirect to audit list
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 7. Findings Management (NOT IMPLEMENTED - BLOCKING)

### 7.1 Create Nonconformity
- [ ] **TEST-057:** Create NC (Auditor)
  - [ ] Navigate to audit detail
  - [ ] Click "Add Nonconformity"
  - [ ] Fill all required fields (clause, category, evidence, statement, explanation)
  - [ ] Submit form
  - **Expected:** NC created, appears in audit detail
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-058:** Create NC (Client)
  - [ ] Login as Client Admin
  - [ ] Try to create NC
  - **Expected:** 403 Forbidden or button not visible
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-059:** Create NC (missing required fields)
  - [ ] Try to submit without clause
  - [ ] Try to submit without category
  - **Expected:** Form errors
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 7.2 Create Observation
- [ ] **TEST-060:** Create observation (Auditor)
  - [ ] Add observation to audit
  - [ ] Fill clause and statement
  - **Expected:** Observation created
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 7.3 Create Opportunity for Improvement
- [ ] **TEST-061:** Create OFI (Auditor)
  - [ ] Add OFI to audit
  - [ ] Fill clause and description
  - **Expected:** OFI created
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 7.4 Edit Findings
- [ ] **TEST-062:** Edit finding (Auditor, own finding)
  - [ ] Edit finding created by current user
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-063:** Delete finding (Auditor)
  - [ ] Delete finding
  - **Expected:** Finding deleted
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 8. Nonconformity Response Workflow (NOT IMPLEMENTED - BLOCKING)

### 8.1 Client Response
- [ ] **TEST-064:** Client respond to NC (own org)
  - [ ] Login as Client Admin
  - [ ] View NC in audit detail
  - [ ] Click "Respond" button
  - [ ] Fill root cause, correction, corrective action
  - [ ] Set due date
  - [ ] Submit response
  - **Expected:** Response saved, status = "client_responded"
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-065:** Client respond to NC (other org)
  - [ ] Login as Client Admin
  - [ ] Try to respond to NC from different organization
  - **Expected:** 403 Forbidden or button not visible
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-066:** Client set due date
  - [ ] Set due date in response form
  - **Expected:** Due date saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 8.2 Auditor Verification
- [ ] **TEST-067:** Auditor verify response (accept)
  - [ ] Login as Lead Auditor
  - [ ] View NC with client response
  - [ ] Click "Accept" or "Verify"
  - [ ] Add verification comments if needed
  - **Expected:** Status = "accepted", verified_by and verified_at set
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-068:** Auditor verify response (reject)
  - [ ] Reject client response
  - [ ] Add comments
  - **Expected:** Status = "open", comments saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-069:** Auditor verify (not assigned)
  - [ ] Login as Auditor not on audit team
  - [ ] Try to verify NC
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-070:** NC status workflow
  - [ ] Open → Client Responded → Accepted → Closed
  - [ ] Verify each transition
  - **Expected:** Valid transitions work, invalid transitions rejected
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 9. File Upload (NOT IMPLEMENTED - BLOCKING)

### 9.1 Upload Evidence File
- [ ] **TEST-071:** Upload file to audit (Auditor)
  - [ ] Navigate to audit detail
  - [ ] Click "Upload Evidence"
  - [ ] Select file (PDF, image, document)
  - [ ] Submit
  - **Expected:** File uploaded, appears in evidence list
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-072:** Upload file to NC
  - [ ] Upload file linked to specific nonconformity
  - **Expected:** File linked to NC
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-073:** Upload file (too large)
  - [ ] Try to upload file >10MB
  - **Expected:** Error message (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-074:** Upload file (wrong type)
  - [ ] Try to upload executable (.exe, .sh)
  - **Expected:** Error message (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 9.2 Download/View Files
- [ ] **TEST-075:** Download file (permission check)
  - [ ] Login as different roles
  - [ ] Try to download evidence files
  - **Expected:** Only permitted users can download
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 9.3 Delete Files
- [ ] **TEST-076:** Delete file (permission check)
  - [ ] Try to delete file as uploader
  - [ ] Try to delete file as CB Admin
  - [ ] Try to delete file as other user
  - **Expected:** Only uploader or admin can delete
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 10. Audit Workflow & Status Transitions (NOT IMPLEMENTED - BLOCKING)

### 10.1 Status Transitions
- [ ] **TEST-077:** Move audit to Client Review
  - [ ] Change status from "draft" to "client_review"
  - **Expected:** Status updated, client can now view
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-078:** Move audit to Submitted
  - [ ] Change status from "client_review" to "submitted_to_cb"
  - **Expected:** Status updated
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-079:** Move audit to Decided
  - [ ] Change status from "submitted_to_cb" to "decided"
  - **Expected:** Status updated
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-080:** Invalid transition (skip step)
  - [ ] Try to go from "draft" directly to "submitted_to_cb"
  - **Expected:** Rejected (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-081:** Invalid transition (backward)
  - [ ] Try to go from "submitted_to_cb" back to "draft"
  - **Expected:** Rejected or allowed (business decision)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 10.2 Workflow Restrictions
- [ ] **TEST-082:** Edit audit in Client Review
  - [ ] Try to edit audit in "client_review" status
  - **Expected:** Allowed or restricted (business decision)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-083:** Add findings after Submitted
  - [ ] Try to add NC after audit is "submitted_to_cb"
  - **Expected:** Allowed or restricted (business decision)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 11. Audit Metadata Management (NOT IMPLEMENTED - BLOCKING)

### 11.1 Audit Changes
- [ ] **TEST-084:** Edit AuditChanges (Auditor)
  - [ ] Navigate to audit detail
  - [ ] Edit changes section
  - [ ] Mark various change flags
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 11.2 Audit Plan Review
- [ ] **TEST-085:** Edit AuditPlanReview (Auditor)
  - [ ] Edit plan review section
  - [ ] Mark deviations, issues
  - [ ] Set next audit dates
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 11.3 Audit Summary
- [ ] **TEST-086:** Edit AuditSummary (Auditor)
  - [ ] Edit summary section
  - [ ] Answer evaluation questions
  - [ ] Add comments
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 11.4 Audit Recommendation
- [ ] **TEST-087:** Edit AuditRecommendation (CB Admin)
  - [ ] Login as CB Admin
  - [ ] Edit recommendation section
  - [ ] Mark special audit, suspension, revocation
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-088:** Edit AuditRecommendation (Auditor)
  - [ ] Login as Lead Auditor
  - [ ] Try to edit recommendation
  - **Expected:** 403 Forbidden or button not visible
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 12. Team Member Management (NOT IMPLEMENTED - BLOCKING)

### 12.1 Add Team Member
- [ ] **TEST-089:** Add team member (user)
  - [ ] Navigate to audit detail
  - [ ] Click "Add Team Member"
  - [ ] Select user from dropdown
  - [ ] Set role and dates
  - **Expected:** Team member added
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-090:** Add team member (external)
  - [ ] Add external expert (no user account)
  - [ ] Enter name, title, role, dates
  - **Expected:** Team member added
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-091:** Add team member (invalid dates)
  - [ ] Set dates outside audit date range
  - **Expected:** Form error (if validation implemented)
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

### 12.2 Edit/Remove Team Member
- [ ] **TEST-092:** Edit team member
  - [ ] Edit existing team member
  - [ ] Change role or dates
  - **Expected:** Changes saved
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

- [ ] **TEST-093:** Remove team member
  - [ ] Delete team member
  - **Expected:** Team member removed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 13. Edge Cases & Error Handling

### 13.1 Invalid URLs
- [ ] **TEST-094:** Access non-existent audit
  - [ ] Try to access `/audits/999/`
  - **Expected:** 404 Not Found
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-095:** Access audit with invalid PK
  - [ ] Try to access `/audits/abc/`
  - **Expected:** 404 Not Found
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 13.2 Empty Lists
- [ ] **TEST-096:** Empty audit list
  - [ ] View audit list with no audits
  - **Expected:** Empty list message, no errors
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-097:** Empty organization list
  - [ ] View organization list with no organizations
  - **Expected:** Empty list message
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 13.3 Special Characters
- [ ] **TEST-098:** XSS prevention
  - [ ] Enter `<script>alert('XSS')</script>` in text fields
  - [ ] Submit form, view output
  - **Expected:** Script tags escaped, not executed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-099:** SQL injection prevention
  - [ ] Enter SQL in form fields (e.g., `'; DROP TABLE--`)
  - **Expected:** Treated as literal text, no SQL executed
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 13.4 Long Text Fields
- [ ] **TEST-100:** Very long text
  - [ ] Enter >10,000 characters in text fields
  - **Expected:** Handled gracefully, no errors
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## 14. Security Testing

### 14.1 CSRF Protection
- [ ] **TEST-101:** CSRF token required
  - [ ] Submit form without CSRF token (using curl/Postman)
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 14.2 Permission Escalation
- [ ] **TEST-102:** Direct URL access (unauthorized)
  - [ ] Login as Client Admin
  - [ ] Try to access `/audits/create/` directly
  - **Expected:** 403 Forbidden
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

- [ ] **TEST-103:** Access other organization's data
  - [ ] Login as Client Admin (Org A)
  - [ ] Try to access audit for Org B (via URL manipulation)
  - **Expected:** 404 Not Found
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 14.3 File Upload Security
- [ ] **TEST-104:** Path traversal prevention
  - [ ] Try to upload file with name `../../../etc/passwd`
  - **Expected:** Filename sanitized, file saved safely
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED [ ] NOT IMPLEMENTED

**Tester:** _________________ **Date:** _________________

---

## 15. Usability & UI Testing

### 15.1 Navigation
- [ ] **TEST-105:** Navigation menu
  - [ ] Check all navigation links work
  - [ ] Verify active page highlighted
  - **Expected:** All links functional
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 15.2 Forms
- [ ] **TEST-106:** Form validation messages
  - [ ] Submit invalid forms
  - [ ] Check error messages are clear and helpful
  - **Expected:** Clear, user-friendly error messages
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 15.3 Responsive Design
- [ ] **TEST-107:** Mobile view
  - [ ] Test on mobile device or browser resize
  - [ ] Check forms and tables are usable
  - **Expected:** Layout adapts, all features accessible
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

### 15.4 Performance
- [ ] **TEST-108:** Page load times
  - [ ] Measure page load times
  - [ ] Check with large datasets (100+ audits)
  - **Expected:** Pages load in <2 seconds
  - **Status:** [ ] PASS [ ] FAIL [ ] BLOCKED

**Tester:** _________________ **Date:** _________________

---

## Final Sign-Off

**QA Lead:** _________________  
**Date:** _________________  
**Overall Status:** [ ] APPROVED [ ] REJECTED [ ] CONDITIONAL

**Blocking Issues:**
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

**Notes:**
_________________________________________________
_________________________________________________
_________________________________________________

---

**END OF MANUAL QA CHECKLIST**

