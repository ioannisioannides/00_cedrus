# Cedrus User Journey Maps - Phase 1

**Version:** 1.0  
**Product Owner:** Cedrus Product Owner Agent

---

## Overview

This document maps the primary user journeys for each role in the Cedrus platform during Phase 1 (External Audit Module). Each journey represents a complete workflow from start to finish.

---

## Journey 1: CB Admin - Create and Complete Audit

**Actor:** Certification Body Administrator  
**Goal:** Create a new audit, assign a lead auditor, and make the final certification decision

### Journey Steps

1. **Login** → Dashboard (CB Admin view)
2. **Create Organization** (if new client)
   - Navigate to `/core/organizations/`
   - Create organization with all required fields
   - Create sites for the organization
   - Create certifications for the organization
3. **Create Audit**
   - Navigate to `/audits/create/`
   - Select organization
   - Select certifications (filtered to org)
   - Select sites (filtered to org)
   - Choose audit type (Stage 1, Stage 2, Surveillance, etc.)
   - Set date range and duration
   - Assign lead auditor
   - Save audit (status: "draft")
4. **Assign Team** (optional, can be done by lead auditor)
   - View audit details
   - Add team members (auditors, technical experts)
5. **Wait for Lead Auditor** to complete audit and submit
6. **Review Audit** (when status = "submitted_to_cb")
   - View audit details
   - Review findings
   - Review recommendations
   - Edit recommendations if needed
7. **Make Certification Decision**
   - Review all information
   - Make decision (approve, suspend, revoke, require special audit)
   - Update certification statuses
   - Audit status → "decided"

### Pain Points

- Cannot edit recommendations before decision (should be editable)
- No notification when audit is submitted
- No bulk operations for multiple certifications

### Success Criteria

- Audit created successfully
- Lead auditor can access audit
- Decision made and certifications updated

---

## Journey 2: Lead Auditor - Conduct Audit

**Actor:** Lead Auditor  
**Goal:** Complete audit documentation, document findings, and submit to client

### Journey Steps

1. **Login** → Dashboard (Auditor view)
2. **View Assigned Audits**
   - Navigate to `/audits/`
   - See audits where I am lead auditor or team member
3. **Open Audit**
   - Click on audit to view details
   - Verify audit information (organization, certifications, sites, dates)
4. **Edit Audit Details** (if needed)
   - Navigate to `/audits/<id>/edit/`
   - Update certifications, sites, dates, duration
   - Assign/adjust team members
5. **Complete Audit Documentation**
   - Track organization changes (if any)
   - Review audit plan and document deviations
   - Complete audit summary evaluation
6. **Document Findings**
   - Add nonconformities (major/minor)
   - Add observations
   - Add opportunities for improvement
   - Link findings to standard clauses
7. **Upload Evidence Files**
   - Attach files to audit
   - Attach files to specific findings
8. **Submit to Client**
   - Review all documentation
   - Click "Submit to Client"
   - Audit status → "client_review"
9. **Wait for Client Response**
10. **Verify Client Responses** (when client responds)
    - Review client responses to nonconformities
    - Accept or request changes
    - Close nonconformities when verified
11. **Create Recommendations** (if status allows)
    - Specify special audit requirements
    - Recommend suspension/revocation if needed
    - Add decision notes
12. **Submit to CB** (if workflow allows)
    - Audit status → "submitted_to_cb"

### Pain Points

- No audit checklist/template
- Cannot save draft findings
- No offline mode for field audits
- No mobile access for on-site documentation

### Success Criteria

- All findings documented
- Client can respond to nonconformities
- Audit submitted to CB for decision

---

## Journey 3: Auditor - Document Findings

**Actor:** Auditor (Team Member)  
**Goal:** Document findings during audit execution

### Journey Steps

1. **Login** → Dashboard (Auditor view)
2. **View Assigned Audits**
   - Navigate to `/audits/`
   - See audits where I am a team member
3. **Open Audit**
   - Click on audit to view details
   - Review audit scope and team
4. **Document Findings**
   - Add nonconformities with:
     - Standard and clause
     - Category (major/minor)
     - Objective evidence
     - Statement of NC
     - Explanation
   - Add observations
   - Add opportunities for improvement
5. **Upload Evidence**
   - Attach files to findings
   - Attach files to audit
6. **Verify Client Responses** (if assigned)
   - Review client responses to nonconformities
   - Accept or request changes
   - Close when verified

### Pain Points

- Cannot edit audit details (only lead auditor can)
- No real-time collaboration with team
- No finding templates

### Success Criteria

- Findings documented accurately
- Evidence attached
- Client responses verified

---

## Journey 4: Client Admin - Respond to Audit Findings

**Actor:** Client Organization Administrator  
**Goal:** Review audit findings and respond to nonconformities

### Journey Steps

1. **Login** → Dashboard (Client view)
2. **View Organization Audits**
   - Navigate to `/audits/`
   - See all audits for my organization
3. **Open Audit** (status: "client_review")
   - Click on audit to view details
   - Review audit information
   - Review all findings (NCs, Observations, OFIs)
4. **Review Nonconformities**
   - See all nonconformities (major and minor)
   - Review objective evidence
   - Review auditor explanation
   - Check due dates
5. **Respond to Nonconformity**
   - Click on a nonconformity
   - Fill in:
     - Root cause analysis
     - Correction (immediate action)
     - Corrective action (prevention plan)
   - Update due date if needed
   - Save response
   - Status → "client_responded"
6. **Upload Evidence**
   - Attach files supporting corrective actions
   - Link files to specific nonconformities
7. **Wait for Auditor Verification**
8. **Address Auditor Feedback** (if changes requested)
   - Update response if needed
   - Re-submit
9. **Track Status**
   - Monitor nonconformity status (open → client_responded → accepted → closed)
   - View certification decision when available

### Pain Points

- No notification when audit is submitted for review
- Cannot see audit until status = "client_review"
- No collaboration tools for internal team
- No templates for responses

### Success Criteria

- All nonconformities responded to
- Responses accepted by auditor
- Audit moves to CB decision

---

## Journey 5: Client User - View Audit and Respond

**Actor:** Client User  
**Goal:** View audit information and respond to nonconformities

### Journey Steps

1. **Login** → Dashboard (Client view)
2. **View Organization Audits**
   - Navigate to `/audits/`
   - See audits for my organization
3. **Open Audit**
   - View audit details
   - Review findings
4. **Respond to Nonconformities**
   - Same as Client Admin (US-015)
   - Can respond to nonconformities
   - Can upload evidence
5. **View Certification Decision** (when available)
   - See final decision
   - See updated certification statuses

### Pain Points

- Limited permissions (cannot manage users)
- No audit creation capabilities

### Success Criteria

- Nonconformities responded to
- Evidence submitted

---

## Journey 6: Complete Audit Lifecycle (End-to-End)

**Actor:** Multiple roles (CB Admin, Lead Auditor, Client)  
**Goal:** Complete full audit from creation to certification decision

### Journey Flow

```
CB Admin creates audit (draft)
    ↓
Lead Auditor edits audit, adds team
    ↓
Lead Auditor documents findings
    ↓
Lead Auditor submits to client (client_review)
    ↓
Client Admin responds to nonconformities
    ↓
Lead Auditor verifies responses
    ↓
Lead Auditor creates recommendations
    ↓
Lead Auditor submits to CB (submitted_to_cb)
    ↓
CB Admin reviews and makes decision (decided)
    ↓
Certifications updated
```

### Key Decision Points

1. **Audit Creation**: CB Admin selects organization, certifications, sites, lead auditor
2. **Findings Documentation**: Lead Auditor documents all findings
3. **Client Response**: Client responds to all nonconformities
4. **Verification**: Lead Auditor verifies responses
5. **Recommendation**: Lead Auditor provides recommendations
6. **Decision**: CB Admin makes final certification decision

### Success Metrics

- Time from audit creation to decision: < 30 days (target)
- All major NCs responded to: 100%
- All NCs verified: 100%
- Decision made: Yes/No

---

## User Journey Pain Points Summary

### Common Pain Points Across Roles

1. **No Notifications**
   - Users don't know when actions are required
   - No email/SMS notifications
   - No in-app notifications

2. **Limited Collaboration**
   - No real-time collaboration
   - No comments/threads
   - No @mentions

3. **No Templates**
   - No audit templates
   - No finding templates
   - No response templates

4. **Limited Mobile Access**
   - No mobile app
   - Limited mobile web experience
   - No offline mode

5. **No Reporting**
   - No dashboards
   - No analytics
   - Limited export capabilities

### Role-Specific Pain Points

**CB Admin:**

- Cannot bulk edit certifications
- No audit scheduling/calendar
- Limited reporting

**Lead Auditor:**

- Cannot delegate tasks
- No audit checklist
- Limited team collaboration tools

**Auditor:**

- Cannot edit audit details
- Limited permissions

**Client:**

- Cannot see audit until "client_review"
- No internal collaboration tools
- Limited visibility into process

---

## Journey Improvements (Future Phases)

### Phase 2 Enhancements

1. **Notifications System**
   - Email notifications for status changes
   - In-app notifications
   - SMS for critical actions

2. **Collaboration Features**
   - Comments on audits/findings
   - @mentions
   - Real-time updates

3. **Templates & Checklists**
   - Audit templates
   - Finding templates
   - Response templates
   - Audit checklists

4. **Mobile App**
   - Native mobile app
   - Offline mode
   - Photo capture for evidence

5. **Reporting & Analytics**
   - Dashboards
   - Audit metrics
   - Compliance reports
   - Export capabilities

---

## Journey Validation Checklist

For each user journey, validate:

- ✅ All steps are achievable with current features
- ✅ No dead ends or broken flows
- ✅ Permissions are correct for each role
- ✅ Status transitions are logical
- ✅ Error handling is clear
- ✅ Success feedback is provided
- ✅ Data validation prevents errors

---

**See `PRODUCT_REQUIREMENTS.md` for detailed acceptance criteria for each step.**
