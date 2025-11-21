# Cedrus Governance Board Meeting  
### Meeting #001 — External Audit Module Design  
### Date: 21 November 2025

---

## 1. Attendance

### Core Execution Agents
- **Orchestrator** (Chair)
- **Product Owner** (Requirements)
- **Business Analyst** (Process Mapping)
- **Architecture** (System Design)
- **Data Modeling** (Schema Design)
- **Security** (InfoSec)
- **Compliance** (Internal QA)
- **UI/UX** (User Experience)
- **QA** (Testing Strategy)

### Standards Experts
- **ISO 17021** (Conformity Assessment Requirements)
- **ISO 19011** (Guidelines for Auditing)
- **ISO 9001** (QMS Expert)
- **ISO 27001** (ISMS Expert)
- **ISO 37301** (Compliance Expert)

### Accreditation & CB Experts
- **IAF Expert** (Mandatory Documents)
- **Accreditation Assessor** (External View)
- **CB Operations** (Internal Workflow)
- **Lead Auditor Competence** (Resource Mgmt)

### Advisory Board
- **CISO** (Enterprise Security)
- **CRO** (Risk Management)
- **GDPR/Privacy** (Data Protection)
- **Legal** (Contractual Obligations)
- **Customer Council** (Client Perspective)

---

## 2. Opening Summary (Orchestrator)

This meeting is convened to formally define the functional and non-functional requirements for the **External Audit Module**. This module is the core operational engine of Cedrus, handling the lifecycle of third-party certification audits. It must strictly adhere to **ISO/IEC 17021-1:2015** and relevant IAF Mandatory Documents while providing a modern, efficient user experience. The goal is to produce a specification that ensures compliance by design.

---

## 3. Expert Roundtable

### 3.1 Core Execution Agents

**Product Owner**:  
- **Expectation**: The module must support the full "Audit Lifecycle": *Planning → Preparation → Execution → Reporting → Technical Review → Certification Decision*.
- **Requirement**: Support for different audit types (Stage 1, Stage 2, Surveillance, Recertification, Special Audits) with distinct workflows.
- **Concern**: Complexity of "multi-site" audits and ensuring the UI remains intuitive for auditors in the field.

**Business Analyst**:  
- **Requirement**: The "Finding" (Non-conformity) lifecycle is critical. It must allow for: *Drafting → Issuance → Client Response (Root Cause/Correction) → Auditor Verification → Closure*.
- **Requirement**: Need a "Technical Review" gate before the Certification Decision, where a veto can be exercised.

**Architecture**:  
- **Design**: We will use the existing Event-Driven Architecture. `AuditCreated`, `FindingRaised`, `AuditSubmitted` events will drive the workflow.
- **Boundary**: The Audit Module should consume "Client" and "Site" data from the Core module but own the "Audit" and "Finding" data.
- **Constraint**: Must support offline capabilities in the future (PWA architecture recommended), though MVP can be online-only.

**Data Modeling**:  
- **Entities**: `Audit`, `AuditPlan`, `AuditTeamMember` (link to User + Role), `Finding` (NC Major/Minor, OFI), `EvidenceFile`, `AuditReport`, `CertificationDecision`.
- **Relationships**: Strong referential integrity required between `Finding` and `StandardClause`.

**Security**:  
- **Control**: Strict Role-Based Access Control (RBAC). Auditors must *only* see audits they are assigned to.
- **Risk**: Uploaded evidence files are high-risk. They must be scanned for malware and stored in encrypted buckets with time-limited signed URLs.
- **Requirement**: Immutable audit logs for *all* status changes and finding modifications.

**UI/UX**:  
- **Expectation**: "Distraction-free" mode for auditors during execution.
- **Requirement**: Clear visual indicators for audit progress and missing mandatory fields.

---

### 3.2 Standards Experts

**ISO 17021 Agent**:  
- **Mandatory**: Separation of duties is non-negotiable. The person who conducts the audit *cannot* make the certification decision (Clause 9.5). The system must technically prevent this.
- **Mandatory**: The audit report must cover specific elements defined in Clause 9.4.8 (scope, objectives, findings, conclusion).

**ISO 27001 Agent**:  
- **Context**: For ISMS audits, we need to capture "Statement of Applicability" (SoA) verification. The data model should support checking off controls.

**ISO 9001 Agent**:  
- **Context**: Need to ensure "Scope of Certification" is clearly defined and validated at every audit stage.

---

### 3.3 Accreditation & CB Experts

**IAF Expert**:  
- **Requirement (MD5)**: Audit duration calculations must be recorded and justified. If the actual duration deviates from the plan, a justification is mandatory.
- **Requirement (MD1)**: For multi-site audits, the sampling plan must be enforced. The system should track which sites were visited in previous years.

**CB Operations**:  
- **Workflow**: We need a "Draft" state for reports where the Lead Auditor can review team members' findings before releasing them to the client.
- **Requirement**: Automated generation of the "Audit Plan" document sent to clients before the audit.

**Lead Auditor Competence**:  
- **Constraint**: The system should warn if an auditor is assigned to a standard/sector code they are not qualified for (link to Competence Module).

---

### 3.4 Advisory Board

**CISO**:  
- **Risk**: Supply chain attacks. Ensure the module does not allow execution of arbitrary code via evidence uploads.
- **Requirement**: MFA mandatory for all external auditors and CB staff.

**GDPR/Privacy**:  
- **Risk**: Evidence files often contain PII (HR records, customer lists).
- **Requirement**: Data retention policies must be automated. Evidence should be purged or archived after the retention period (e.g., certification cycle + 1 year).
- **Requirement**: "Right to Erasure" workflows must handle audit evidence carefully (legal obligation to retain vs. GDPR).

**CRO (Risk)**:  
- **Risk**: "Soft" auditing. We need analytics to detect if an auditor *never* raises Major NCs (anomaly detection).

**Customer Council**:  
- **Expectation**: Clients want a dashboard to see their NCs and submit responses directly in the platform, rather than emailing Word documents.

---

## 4. Consolidated Requirements (By Orchestrator)

### MUST-HAVES (MVP)
1.  **Workflow Engine**: Enforce `Draft` → `Planned` → `Active` → `Review` → `Decision` → `Closed`.
2.  **RBAC**: Strict segregation of duties (Auditor vs. Decision Maker).
3.  **Finding Management**: Full lifecycle for NCs (Major/Minor) and OFIs, including client response portal.
4.  **Evidence Management**: Secure upload, storage, and association of evidence with specific findings or audit requirements.
5.  **Audit Reporting**: Generation of the final audit report based on structured data (not just a file upload).
6.  **Audit Trail**: Immutable logging of who changed what and when.
7.  **Competence Check**: Basic validation that assigned auditors hold the relevant standard qualification.

### SHOULD-HAVES (Post-MVP)
1.  **Automated MD5 Calculation**: Logic to calculate required days based on employee count and complexity.
2.  **Multi-site Sampling Logic**: Algorithm to suggest which sites to visit (IAF MD1).
3.  **Offline Mode**: PWA support for auditors in locations with poor internet.
4.  **SoA Digitalization**: Interactive Statement of Applicability for ISO 27001.

### NICE-TO-HAVES
1.  **Video Integration**: Embedded video conferencing for remote audits (IAF MD4).
2.  **AI Assistant**: Suggesting potential clauses based on finding description.
3.  **Sentiment Analysis**: On client feedback.

---

## 5. Actions Requiring Human Approval

1.  **Approve Data Model**: Confirm the entity relationship diagram for `Audit` <-> `Finding` <-> `Evidence`.
    - **Status**: **APPROVED** with conditions:
        - Must support future modules (risk, compliance, internal audit).
        - Must accommodate per-site findings.
        - Must track cross-audit recurring findings.
        - Must map findings to root causes (taxonomy-based).
        - Must classify audit evidence (document vs. interview vs. observation vs. record).
        - Must align with ISO 17021 and IAF MD1/MD22.

2.  **Approve Workflow States**: Confirm the specific status transitions and permission gates (specifically the "Technical Review" gate).
    - **Status**: **APPROVED** with revisions:
        - "Technical Review" is mandatory for ALL audits.
        - Explicit states: `Draft` → `In Review` → `Submitted to CB` → `Technical Review` → `Decision Pending` → `Closed`.
        - Add "Returned for Correction" sub-state before Technical Review.
        - Only CB personnel may access Technical Review and Decision stages.

3.  **Approve Retention Policy**: Decide on the default retention period for evidence files (Standard is usually 6 years or 2 cycles).
    - **Status**: **APPROVED** with conditions:
        - Default retention: **7 years**.
        - Minimum: Certification cycle + 1 year.
        - Allow CB override per standard/contract.

4.  **Approve "Veto" Authority**: Define exactly which roles have the power to overturn a Lead Auditor's recommendation.
    - **Status**: **APPROVED** with structure:
        - Lead Auditor: **Recommends**.
        - Technical Reviewer: **Requests Clarification**.
        - Certification Decision Maker: **Final Authority**.
        - No auditor can overrule a Decision Maker (ISO 17021 impartiality).

---

## 6. Proposed Next Steps

1.  **Architecture**: Create the `Audit` and `Finding` Django models in `audits/models.py`.
2.  **Business Analyst**: Map the detailed state transition diagram for the Audit Workflow.
3.  **UX/UI**: Design the "Auditor Dashboard" and "Finding Input Form".
4.  **Security**: Implement the `PermissionPredicate` logic for the new module.
5.  **Engineering**: Scaffold the `audits` app and views.

---

## 7. Closing Summary

The Board has defined a robust, compliance-first foundation for the External Audit Module. The key differentiator for Cedrus will be the "Compliance by Design" approach—preventing invalid states (like a decision maker auditing their own client) at the code level. We will proceed with the **MUST-HAVE** scope for the immediate sprint.

**Meeting Adjourned.**
