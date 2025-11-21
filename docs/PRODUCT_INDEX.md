# Cedrus Product Documentation Index

**Product Owner:** Cedrus Product Owner Agent  
**Last Updated:** 2024

---

## Documentation Overview

This index provides quick access to all product documentation for the Cedrus platform Phase 1 (External Audit Module).

---

## Core Documents

### 1. [MVP_SCOPE.md](./MVP_SCOPE.md)

**Purpose:** Concise MVP scope definition  
**Audience:** Stakeholders, Product Team  
**Contents:**

- MVP in-scope and out-of-scope features
- Critical path to MVP
- Success criteria
- Definition of Done

**Use When:** You need a quick overview of what's included in MVP

---

### 2. [PRODUCT_REQUIREMENTS.md](./PRODUCT_REQUIREMENTS.md)

**Purpose:** Comprehensive product requirements with detailed user stories  
**Audience:** Development Team, QA, Product Team  
**Contents:**

- 8 Epics with detailed user stories
- Acceptance criteria (Given/When/Then format)
- Edge cases and business rules
- Dependencies and blockers
- ISO/IEC 17021 alignment

**Use When:** You need detailed requirements for implementation or testing

---

### 3. [BACKLOG.md](./BACKLOG.md)

**Purpose:** Structured backlog for sprint planning  
**Audience:** Scrum Master, Development Team, Product Owner  
**Contents:**

- All epics and user stories with priorities
- Story point estimates
- Dependencies and blockers
- Sprint planning recommendations
- Definition of Ready/Done

**Use When:** Planning sprints or prioritizing work

---

### 4. [USER_JOURNEYS.md](./USER_JOURNEYS.md)

**Purpose:** User journey maps for each role  
**Audience:** UX Team, Product Team, Stakeholders  
**Contents:**

- 6 primary user journeys
- Step-by-step workflows
- Pain points identification
- Success criteria
- Future improvements

**Use When:** Understanding user workflows or designing UX

---

## Quick Reference

### By Role

**CB Admin:**

- Journey: [USER_JOURNEYS.md#journey-1](./USER_JOURNEYS.md#journey-1-cb-admin---create-and-complete-audit)
- Stories: EPIC-001, EPIC-002, EPIC-007
- Key Features: Create audits, make decisions, manage organizations

**Lead Auditor:**

- Journey: [USER_JOURNEYS.md#journey-2](./USER_JOURNEYS.md#journey-2-lead-auditor---conduct-audit)
- Stories: EPIC-002, EPIC-003, EPIC-004, EPIC-005, EPIC-007
- Key Features: Edit audits, document findings, verify responses

**Auditor:**

- Journey: [USER_JOURNEYS.md#journey-3](./USER_JOURNEYS.md#journey-3-auditor---document-findings)
- Stories: EPIC-004
- Key Features: Document findings, verify responses

**Client Admin/User:**

- Journey: [USER_JOURNEYS.md#journey-4](./USER_JOURNEYS.md#journey-4-client-admin---respond-to-audit-findings)
- Stories: EPIC-004
- Key Features: Respond to nonconformities, upload evidence

### By Epic

**EPIC-001: Foundation & Core Entities** ✅ Done

- [PRODUCT_REQUIREMENTS.md#epic-1](./PRODUCT_REQUIREMENTS.md#epic-1-foundation--core-entities-management)
- Organizations, Sites, Standards, Certifications

**EPIC-002: Audit Creation & Lifecycle** 🟡 In Progress

- [PRODUCT_REQUIREMENTS.md#epic-2](./PRODUCT_REQUIREMENTS.md#epic-2-audit-creation--lifecycle-management)
- Create, view, edit audits, status workflow

**EPIC-003: Audit Team Management** 🟡 In Progress

- [PRODUCT_REQUIREMENTS.md#epic-3](./PRODUCT_REQUIREMENTS.md#epic-3-audit-team-management)
- Assign team members, view team

**EPIC-004: Findings Management** 🔴 Not Started - **BLOCKING**

- [PRODUCT_REQUIREMENTS.md#epic-4](./PRODUCT_REQUIREMENTS.md#epic-4-findings-management)
- NCs, Observations, OFIs, client responses, verification

**EPIC-005: Audit Documentation** 🟡 In Progress (Models exist)

- [PRODUCT_REQUIREMENTS.md#epic-5](./PRODUCT_REQUIREMENTS.md#epic-5-audit-documentation--metadata)
- Organization changes, plan review, summary

**EPIC-006: Evidence File Management** 🔴 Not Started

- [PRODUCT_REQUIREMENTS.md#epic-6](./PRODUCT_REQUIREMENTS.md#epic-6-evidence-file-management)
- Upload, view, download evidence files

**EPIC-007: Certification Decision** 🟡 In Progress (Model exists)

- [PRODUCT_REQUIREMENTS.md#epic-7](./PRODUCT_REQUIREMENTS.md#epic-7-certification-decision--recommendations)
- Recommendations, certification decisions

**EPIC-008: Print & Reporting** ✅ Done (Basic)

- [PRODUCT_REQUIREMENTS.md#epic-8](./PRODUCT_REQUIREMENTS.md#epic-8-print--reporting)
- Print-friendly audit reports

---

## Critical Blockers

### Must Fix for MVP

1. **EPIC-004: Findings Management** 🔴
   - All 6 user stories not implemented
   - **Impact:** Cannot complete audit workflow
   - **See:** [BACKLOG.md#epic-4](./BACKLOG.md#epic-4-findings-management)

2. **US-009: Status Workflow** 🔴
   - Status transition validation missing
   - **Impact:** Audits can skip required steps
   - **See:** [PRODUCT_REQUIREMENTS.md#us-009](./PRODUCT_REQUIREMENTS.md#us-009-audit-status-workflow-transitions)

3. **EPIC-007: Certification Decision** 🔴
   - Recommendations and decision UI missing
   - **Impact:** Cannot complete certification decision
   - **See:** [BACKLOG.md#epic-7](./BACKLOG.md#epic-7-certification-decision--recommendations)

4. **EPIC-005: Audit Documentation UI** 🔴
   - Forms missing for metadata sections
   - **Impact:** Cannot complete audit documentation
   - **See:** [BACKLOG.md#epic-5](./BACKLOG.md#epic-5-audit-documentation--metadata)

---

## Sprint Planning Quick Reference

### Recommended Sprint Sequence

**Sprint 1:** Findings Creation (US-012, US-013, US-014, US-017)  
**Sprint 2:** Client Response (US-015, US-016)  
**Sprint 3:** Status Workflow & Documentation (US-009, US-018, US-019)  
**Sprint 4:** Certification Decision (US-023, US-024, US-020)  
**Sprint 5:** Evidence & Polish (US-021, US-022, validation fixes)

**See:** [BACKLOG.md#sprint-planning-recommendations](./BACKLOG.md#sprint-planning-recommendations)

---

## ISO/IEC 17021 Alignment

All requirements align with ISO/IEC 17021:

- **Clause 9.2:** Audit Planning ✅
- **Clause 9.3:** Audit Conduct ✅
- **Clause 9.4:** Audit Reporting ✅
- **Clause 9.5:** Certification Decision ✅
- **Clause 9.6:** Nonconformity Management ✅

**See:** [PRODUCT_REQUIREMENTS.md#isoiec-17021-alignment](./PRODUCT_REQUIREMENTS.md#isoiec-17021-alignment)

---

## Acceptance Criteria Format

All user stories use Given/When/Then format:

```
**Given** [initial context/state]
**When** [action taken]
**Then** [expected outcome]
**And** [additional outcomes/validations]
```

**Example:** [PRODUCT_REQUIREMENTS.md#us-001](./PRODUCT_REQUIREMENTS.md#us-001-manage-organizations)

---

## Definition of Done

An audit is "MVP Complete" when:

- ✅ CB Admin can create an audit
- ✅ Lead Auditor can edit audit and add findings
- ✅ Client can respond to nonconformities
- ✅ Auditor can verify client responses
- ✅ CB Admin can make certification decision
- ✅ Audit can be printed as official report
- ✅ All status transitions are validated
- ✅ All data validation rules are enforced

**See:** [MVP_SCOPE.md#mvp-definition-of-done](./MVP_SCOPE.md#mvp-definition-of-done)

---

## Story Point Estimates

**Total MVP:** ~150+ story points  
**Completed:** ~45 story points (30%)  
**Remaining:** ~105 story points (70%)

**Breakdown:**

- EPIC-001: ✅ 15 points (Done)
- EPIC-002: 🟡 31 points (Partially done)
- EPIC-003: 🟡 7 points (Partially done)
- EPIC-004: 🔴 39 points (Not started - BLOCKING)
- EPIC-005: 🔴 18 points (Not started)
- EPIC-006: 🔴 13 points (Not started)
- EPIC-007: 🔴 21 points (Not started)
- EPIC-008: ✅ 5 points (Done)

**See:** [BACKLOG.md](./BACKLOG.md) for detailed breakdown

---

## Contact & Updates

**Product Owner:** Cedrus Product Owner Agent  
**Documentation Location:** `/docs/`  
**Last Review:** 2024

For questions or updates, refer to the specific document or contact the Product Owner.

---

**Quick Links:**

- [MVP Scope](./MVP_SCOPE.md)
- [Product Requirements](./PRODUCT_REQUIREMENTS.md)
- [Backlog](./BACKLOG.md)
- [User Journeys](./USER_JOURNEYS.md)
