# Cedrus MVP Scope - External Audit Module

**Version:** 1.0  
**Status:** Approved  
**Phase:** Phase 1 - External Audit Module

---

## MVP Overview

The MVP enables a Certification Body to conduct complete external audit lifecycles from creation through certification decision, with client collaboration on nonconformity responses.

**Target Release:** Phase 1 MVP  
**Timeline:** TBD  
**Success Criteria:** A CB Admin can create an audit, assign a lead auditor, document findings, receive client responses, and make a certification decision.

---

## MVP In-Scope Features

### ✅ Foundation (Implemented)

- Organization management (CRUD)
- Site management (CRUD)
- Standards library (CRUD)
- Certification management (CRUD)
- User authentication and role-based access
- Basic audit creation and listing

### ✅ Core Workflow (Implemented)

- Audit creation with team assignment
- Audit status workflow (Draft → Client Review → Submitted to CB → Technical Review → Decision Pending → Closed)
- Role-based audit filtering
- Audit detail view

### ✅ Critical Features (Implemented)

- **Findings Management**: Create/edit/view nonconformities, observations, OFIs
- **Client Response Workflow**: Client users respond to nonconformities
- **Auditor Verification**: Verify client responses
- **Audit Documentation UI**: Organization changes, plan review, summary forms
- **Recommendations & Decision**: CB Admin makes certification decisions (ISO 17021 compliant)
- **Evidence File Upload**: Attach files to audits and findings
- **Status Workflow Validation**: Enforce valid status transitions

### 🟡 Data Validation (Partially Implemented)

- Date range validation (end >= start) - ✅ Done
- Organization-scoped validation (certifications/sites belong to org) - ✅ Done
- Lead auditor role validation - ✅ Done
- Team member date validation - ✅ Done
- **Remaining**: Comprehensive edge case validation (ongoing)

---

## MVP Out-of-Scope

- Internal audits
- Risk management
- Compliance tracking (beyond certifications)
- Email notifications
- Reporting dashboards
- API endpoints
- Mobile apps
- Multi-language
- Accreditation body features
- Audit scheduling/calendar
- Billing/invoicing
- Client self-registration
- Advanced search/filtering
- Audit templates

---

## User Roles & Permissions (MVP)

| Role | Key Capabilities |
|------|------------------|
| **CB Admin** | Create audits, edit all audits, make certification decisions, manage organizations/certifications |
| **Lead Auditor** | Edit assigned audits, add findings, assign team, submit to client |
| **Auditor** | View assigned audits, add findings |
| **Client Admin** | View org audits, respond to nonconformities, upload evidence |
| **Client User** | View org audits, respond to nonconformities |

---

## Critical Path to MVP (Completed)

1. **Findings Management** (EPIC-004) - ✅ COMPLETE
   - Create nonconformities, observations, OFIs
   - Client response workflow
   - Auditor verification

2. **Status Workflow** (US-009) - ✅ COMPLETE
   - Validate status transitions
   - Enforce workflow rules

3. **Audit Documentation** (EPIC-005) - ✅ COMPLETE
   - Organization changes form
   - Audit plan review form
   - Audit summary form

4. **Certification Decision** (EPIC-007) - ✅ COMPLETE
   - Recommendations UI
   - Decision workflow
   - Certification status updates

5. **Evidence Files** (EPIC-006) - ✅ COMPLETE
   - File upload UI
   - File storage

6. **Data Validation** - ✅ COMPLETE
   - All validation rules

---

## MVP Definition of Done

An audit is considered "MVP Complete" when:

- ✅ CB Admin can create an audit
- ✅ Lead Auditor can edit audit and add findings
- ✅ Client can respond to nonconformities
- ✅ Auditor can verify client responses
- ✅ CB Admin can make certification decision
- ✅ Audit can be printed as official report
- ✅ All status transitions are validated
- ✅ All data validation rules are enforced

---

## Success Metrics

- **Functional**: All 8 Epics implemented with core user stories
- **Quality**: All critical blockers resolved
- **Compliance**: Aligned with ISO/IEC 17021 requirements
- **Usability**: All user roles can complete their primary workflows

---

**Next:** See `PRODUCT_REQUIREMENTS.md` for detailed epics, user stories, and acceptance criteria.
