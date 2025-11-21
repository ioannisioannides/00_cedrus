# Audit Workflow User Guide

**Version:** 1.0  
**Last Updated:** 20 November 2025  
**Audience:** Lead Auditors, Auditors, CB Administrators, Client Users

---

## Table of Contents

1. [Overview](#overview)
2. [Audit Status Lifecycle](#audit-status-lifecycle)
3. [Role-Based Permissions](#role-based-permissions)
4. [Step-by-Step Workflows](#step-by-step-workflows)
5. [Documentation Requirements](#documentation-requirements)
6. [Evidence File Management](#evidence-file-management)
7. [Recommendations & Decisions](#recommendations--decisions)
8. [Common Scenarios](#common-scenarios)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Cedrus audit workflow system manages the complete lifecycle of certification audits from initial planning through final certification decision. The system enforces ISO certification standards, ensures proper documentation, and maintains compliance with certification body requirements.

### Key Features

- **Status-driven workflow** with automatic validation
- **Role-based permissions** ensuring proper authority
- **Documentation requirements** at each stage
- **Evidence file management** with NC linkage
- **Recommendation and decision tracking**
- **Audit trail** for all status changes

---

## Audit Status Lifecycle

```
draft → client_review → submitted_to_cb → decided
```

### Status Definitions

| Status | Description | Who Can Set | Next Status |
|--------|-------------|-------------|-------------|
| **draft** | Initial audit creation and planning | System (on creation) | client_review |
| **client_review** | Audit submitted to client for review | Lead Auditor | submitted_to_cb |
| **submitted_to_cb** | Audit submitted to CB for decision | Lead Auditor, CB Admin | decided |
| **decided** | Final certification decision made | CB Admin | *Final - no changes* |

### Status Rules

- ✅ Forward progression only (no backward transitions except draft ↔ client_review)
- ✅ Major nonconformities must be responded to before submission to CB
- ✅ Recommendations required before final decision
- ✅ Decided status is permanent and cannot be changed

---

## Role-Based Permissions

### CB Administrator

**Full system access**

- Create and manage audits
- Assign lead auditors and team members
- Override status transitions
- Make final certification decisions
- Access all documentation and files

### Lead Auditor

**Audit execution authority**

- Complete audit documentation
- Upload evidence files
- Create and manage nonconformities
- Submit audit for client review
- Submit audit to CB (own audits only)
- Create recommendations for certification

### Auditor

**Team member execution**

- View assigned audits
- Upload evidence files
- Document findings
- Cannot change audit status
- Cannot create recommendations

### Client User

**Read-only access**

- View audit details for their organization
- Download evidence files
- View nonconformities
- Respond to nonconformities
- Cannot upload files or change status

---

## Step-by-Step Workflows

### 1. Creating a New Audit (CB Admin)

1. Navigate to **Audits** → **Create New Audit**
2. Complete required fields:
   - Organization
   - Audit Type (Stage 1, Stage 2, Surveillance, etc.)
   - Certifications being audited
   - Lead Auditor assignment
   - Audit dates and duration
3. Click **Save**
4. Audit is created in **draft** status

**Initial Status:** `draft`

---

### 2. Planning and Executing the Audit (Lead Auditor)

#### Step 2.1: Complete Audit Plan Documentation

1. Open the audit from your dashboard
2. Click **Edit Audit Plan Review**
3. Complete the form:
   - Organization changes assessment
   - Audit plan adequacy review
   - Team qualification verification
   - Audit plan approval
4. Click **Save**

#### Step 2.2: Document Organization Changes

1. Click **Edit Organization Changes**
2. Document any relevant changes:
   - Products/services changes
   - Process modifications
   - Key personnel changes
   - Facility changes
3. Click **Save**

#### Step 2.3: Conduct Audit and Upload Evidence

1. During the audit, upload evidence files:
   - Click **Upload Evidence File**
   - Select file (PDF, Word, Excel, or images)
   - Add description
   - Optionally link to nonconformity
   - Click **Upload**

2. Create nonconformities as needed:
   - Click **Add Nonconformity**
   - Select severity (minor/major)
   - Document the finding
   - Reference standard clause
   - Upload supporting evidence

#### Step 2.4: Submit to Client for Review

1. Review all documentation
2. Ensure all findings are documented
3. Click **Change Status** → **Submit to Client Review**
4. System validates:
   - ✅ All required documentation complete
   - ✅ Evidence files uploaded
5. Audit status changes to **client_review**

**Status Changes:** `draft` → `client_review`

---

### 3. Client Review Period (Client User)

1. Client receives notification (future enhancement)
2. Client logs in and views audit
3. Client reviews:
   - Nonconformities
   - Evidence files
   - Audit findings
4. Client responds to major nonconformities:
   - Click on major NC
   - Click **Respond to Nonconformity**
   - Complete:
     - Root cause analysis
     - Correction taken
     - Corrective action plan
     - Evidence of correction
   - Click **Submit Response**

**Client Action Required:** All major NCs must have responses before audit can proceed

---

### 4. Submitting to CB for Decision (Lead Auditor)

#### Prerequisites

- Audit must be in **client_review** status
- All major nonconformities must have client responses
- All documentation must be complete

#### Steps

1. Verify all major NCs have responses:
   - Check NC list for response status
   - Review client corrections
2. Complete audit summary:
   - Click **Edit Audit Summary**
   - Document audit conclusions
   - Summarize findings
   - Note any outstanding items
   - Click **Save**
3. Submit to CB:
   - Click **Change Status** → **Submit to CB**
   - System validates all requirements
   - Audit status changes to **submitted_to_cb**

**Status Changes:** `client_review` → `submitted_to_cb`

**Validation Errors:**

- ❌ "Major nonconformity (Clause X.X) has not been responded to" - Client must respond to all major NCs first
- ❌ "You do not have permission" - Only Lead Auditor or CB Admin can submit

---

### 5. Creating Recommendations (Lead Auditor)

#### Prerequisites

- Audit must be in **submitted_to_cb** status
- You must be the assigned Lead Auditor

#### Steps

1. Click **Create/Edit Recommendation**
2. Complete the recommendation form:
   - **Recommendation:** Select one
     - ✅ Recommend Certification
     - ✅ Recommend Certification with Conditions
     - ❌ Do Not Recommend Certification
   - **Stage 2 Date:** If Stage 1 audit, specify Stage 2 date
   - **Justification:** Detailed reasoning for recommendation
   - **Conditions:** If conditional, specify what must be met
3. Review all audit information displayed on form
4. Click **Save Recommendation**

**Requirements:**

- One recommendation required per audit
- Recommendations can be edited until CB makes decision
- Only Lead Auditor can create/edit recommendations

---

### 6. Making Certification Decision (CB Admin)

#### Prerequisites

- Audit must be in **submitted_to_cb** status
- Lead Auditor recommendation must exist
- You must be CB Administrator

#### Steps

1. Navigate to audit detail page
2. Review complete audit package:
   - All documentation
   - Nonconformities and responses
   - Evidence files
   - Lead Auditor recommendation
3. Click **Make Decision**
4. Review recommendation summary displayed
5. Complete decision form:
   - **Decision:** Select one
     - ✅ Certify
     - ✅ Certify with Conditions
     - ❌ Deny Certification
   - **Certification Date:** Date of decision
   - **Certificate Number:** If certifying
   - **Validity Period:** Certification validity (typically 3 years)
   - **Special Conditions:** Any conditions or limitations
   - **Internal Notes:** CB internal documentation
6. Click **Save Decision**
7. Audit status automatically changes to **decided**

**Status Changes:** `submitted_to_cb` → `decided`

**Important Notes:**

- Decision is final and permanent
- Status cannot be changed after decision
- Certificate is automatically generated (if certifying)
- Client is notified (future enhancement)

---

## Documentation Requirements

### At Draft Stage

- Audit plan
- Team assignments
- Audit schedule
- Initial risk assessment

### Before Client Review

- ✅ Organization changes documented
- ✅ Audit plan review completed
- ✅ All findings documented
- ✅ Evidence files uploaded
- ✅ Nonconformities created

### Before CB Submission

- ✅ All major NCs have client responses
- ✅ Audit summary completed
- ✅ All evidence reviewed
- ✅ Lead Auditor sign-off

### Before Decision

- ✅ Lead Auditor recommendation submitted
- ✅ All documentation reviewed
- ✅ Nonconformity verification complete

---

## Evidence File Management

### Uploading Files

1. **Navigate to Audit** → Click **Upload Evidence File**
2. **Select File:**
   - Maximum size: 10 MB
   - Allowed types: PDF, Word, Excel, Images (JPEG, PNG)
3. **Add Description:** Brief description of evidence
4. **Link to NC (Optional):** Select related nonconformity
5. **Click Upload**

### File Validation

- ❌ "File size exceeds 10MB" - Compress or split file
- ❌ "File type not allowed" - Convert to PDF or allowed format
- ❌ "You do not have permission" - Only auditors can upload

### Downloading Files

- **Who Can Download:** Auditors, Lead Auditors, CB Admin
- **How:** Click download icon next to file name
- **Access Control:** Files are audit-specific and permission-protected

### Deleting Files

- **Who Can Delete:** File uploader or CB Admin
- **Process:** Click delete icon → Confirm deletion
- **Warning:** Deletion is permanent and cannot be undone

---

## Recommendations & Decisions

### Recommendation Types

#### 1. Recommend Certification

**When to use:** Audit successful, all requirements met

- No major nonconformities outstanding
- Minor NCs have correction plans
- Organization demonstrates competence
- System effectiveness verified

#### 2. Recommend Certification with Conditions

**When to use:** Certifiable with specific conditions

- Minor issues require verification
- Documentation gaps need closure
- Follow-up evidence required
- Timeline for condition resolution specified

#### 3. Do Not Recommend Certification

**When to use:** Audit unsuccessful

- Major nonconformities not adequately addressed
- System not effective
- Critical requirements not met
- Re-audit required

### Decision Types

#### 1. Certify

**Final action:** Issue certificate

- Certificate number assigned
- Validity period set (typically 3 years)
- Surveillance schedule established
- Client notified

#### 2. Certify with Conditions

**Final action:** Issue conditional certificate

- Special conditions documented
- Timeline for condition clearance
- Follow-up verification scheduled
- Conditions tracked for closure

#### 3. Deny Certification

**Final action:** No certificate issued

- Detailed reasons documented
- Re-audit requirements specified
- Client appeal process available
- Future application not prevented

---

## Common Scenarios

### Scenario 1: Client Needs More Time for NC Responses

**Problem:** Audit in client_review but client needs more time

**Solution:**

1. CB Admin can temporarily move audit back to draft
2. Client completes responses
3. Lead Auditor resubmits to client_review
4. Process continues normally

**Note:** This is an exception process requiring CB Admin intervention

---

### Scenario 2: Lead Auditor Discovers Issues After Submission

**Problem:** Audit submitted to CB but new findings discovered

**Solution:**

1. Contact CB Admin immediately
2. CB Admin can move audit back to client_review
3. Lead Auditor adds new findings
4. Process restarts from client review stage

**Best Practice:** Thorough review before submission prevents this

---

### Scenario 3: Multiple Major NCs During Audit

**Problem:** Several major nonconformities found

**Solution:**

1. Document each NC separately with clear evidence
2. Ensure each NC links to specific standard clause
3. Submit to client review even with multiple majors
4. Client must respond to each major NC individually
5. System validates all responses before allowing CB submission

**Timeline:** Extended client review period may be needed

---

### Scenario 4: Recommendation Disagrees with Client Expectation

**Problem:** Lead Auditor recommends denial, client expected certification

**Solution:**

1. Lead Auditor documents clear justification
2. Evidence supports recommendation
3. CB Admin reviews complete package
4. CB Admin makes independent decision
5. Client has appeal process (outside system)

**Note:** Recommendation ≠ Decision. CB Admin makes final call.

---

### Scenario 5: Evidence File Too Large

**Problem:** Important evidence file exceeds 10MB limit

**Solution:**

- **PDFs:** Compress using online tools or Adobe Acrobat
- **Images:** Reduce resolution or convert to optimized JPEG
- **Documents:** Remove unnecessary formatting or split into multiple files
- **Videos:** Extract key frames as images

**Alternative:** Upload to external system and reference in notes

---

## Troubleshooting

### Cannot Submit to Client Review

**Error:** "Invalid transition from 'draft' to 'client_review'"

**Causes & Solutions:**

- ❌ Not logged in as Lead Auditor → Log in with correct account
- ❌ Documentation incomplete → Complete all required forms
- ❌ System validation failing → Check browser console for errors

---

### Cannot Submit to CB

**Error:** "Major nonconformity (Clause X.X) has not been responded to"

**Causes & Solutions:**

- ❌ Client hasn't responded to major NC → Wait for client response
- ❌ Response incomplete → Ensure client filled all required fields
- ❌ Response not saved → Verify response in database

**Verification Steps:**

1. Open each major NC
2. Check for "Responded" or "Client Responded" status
3. Verify all response fields completed
4. Refresh page and try again

---

### Cannot Make Decision

**Error:** "You do not have permission to perform this transition"

**Causes & Solutions:**

- ❌ Not logged in as CB Admin → Only CB Admin can make decisions
- ❌ No recommendation exists → Lead Auditor must create recommendation first
- ❌ Audit in wrong status → Audit must be in "submitted_to_cb" status

---

### File Upload Fails

**Error:** "File type not allowed" or "File size exceeds 10MB"

**Causes & Solutions:**

- ❌ Wrong file type → Convert to PDF, Word, Excel, or image format
- ❌ File too large → Compress or split file
- ❌ Network timeout → Try uploading on stable connection
- ❌ Browser issue → Try different browser or clear cache

---

### Changes Not Saving

**General troubleshooting:**

1. Check for error messages at top of page
2. Verify all required fields completed
3. Check browser console (F12) for JavaScript errors
4. Ensure stable internet connection
5. Try logging out and back in
6. Contact CB Admin if issue persists

---

## Additional Resources

- **Technical Documentation:** See `docs/ARCHITECTURE.md`
- **Workflow Diagrams:** See `docs/user-guides/WORKFLOW_DIAGRAMS.md`
- **API Reference:** See `docs/API_REFERENCE.md` (for developers)
- **Security Guidelines:** See `SECURITY_TESTING.md`

---

## Support

For technical issues or questions:

- **Email:** <support@cedrus-cert.example.com> (update with actual)
- **Help Desk:** [Help Desk Link] (update with actual)
- **Training:** Contact your CB Admin for workflow training

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-20 | Documentation Agent | Initial creation for Priority 2 features |

---

*This guide covers Priority 2 features implemented in November 2025. Additional features and enhancements are planned for future releases.*
