# ISO-Oriented Role & Access Model (AB–CB–Org–Public)

Version: 0.1  
Scope: Accreditation Body (AB), Certification Body (CB), Client Organizations, Public Registry, Platform Operator.

---

## 1. Role Catalogue (30 Roles)

### 1.1 Role Summary Table

| Role ID | Domain | Role Name | Description |
| --- | --- | --- | --- |
| PLAT_SUPER_ADMIN | Platform | Platform Super Admin | Manages tenants, global config, escalated support. No operational involvement in AB/CB decisions. |
| PLAT_SECURITY_OFFICER | Platform | Platform Security Officer | Manages security configuration, audit logs, data protection settings. |
| PLAT_SUPPORT_ENGINEER | Platform | Platform Support Engineer | Handles technical support and troubleshooting within scoped tenants. |
| AB_EXEC_ADMIN | Accreditation Body | AB Executive Admin | Manages AB tenant, users, schemes, and high-level accreditation configuration. |
| AB_ACCRED_PROG_MANAGER | Accreditation Body | AB Accreditation Program Manager | Owns accreditation programs (ISO 9001, 14001 etc.), manages assessment cycles. |
| AB_LEAD_ASSESSOR | Accreditation Body | AB Lead Assessor | Leads AB assessments of CBs, plans assessment teams, drafts conclusions. |
| AB_ASSESSOR | Accreditation Body | AB Assessor | Participates in accreditation assessments, records findings. |
| AB_TECH_EXPERT | Accreditation Body | AB Technical Expert | Provides technical evaluation on specific standards / sectors. |
| AB_SECRETARIAT_OFFICER | Accreditation Body | AB Secretariat Officer | Handles logistics, records, accreditation files, correspondence. |
| AB_FINANCE_OFFICER | Accreditation Body | AB Finance and Contracts Officer | Manages contracts, invoices, and financial records with CBs. |
| CB_EXEC_ADMIN | Certification Body | CB Executive Admin | Top-level admin of CB tenant, configures schemes, users, and business rules. |
| CB_SCHEME_MANAGER | Certification Body | CB Scheme Manager | Owns specific certification schemes, maintains rules and scopes. |
| CB_CERT_DECISION_MAKER | Certification Body | CB Certification Decision Maker | Records independent certification decisions, separate from audit team. |
| CB_IMPARTIALITY_MEMBER | Certification Body | CB Impartiality Committee Member | Reviews impartiality risks, accesses data for oversight only. |
| CB_QMS_COMPLIANCE_MANAGER | Certification Body | CB Quality and Compliance Manager | Manages CB’s internal QMS, procedures, competence records and alignment with ISO 17021. |
| CB_OPERATIONS_COORDINATOR | Certification Body | CB Operations Coordinator | Schedules audits, assigns audit teams, coordinates client communication. |
| CB_LEAD_AUDITOR_EMP | Certification Body | CB Lead Auditor (Employee) | Leads audit teams, finalizes audit reports and recommendations. |
| CB_AUDITOR_EMP | Certification Body | CB Auditor (Employee) | Conducts audits under a lead auditor, records findings and evidence. |
| CB_TRAINEE_AUDITOR | Certification Body | CB Trainee Auditor | Supports audits with restricted rights, used for competence development. |
| CB_EXTERNAL_AUDITOR | Certification Body | CB External Auditor | Outsourced auditor with access limited to assigned audits. |
| CB_TECH_REVIEWER | Certification Body | CB Technical Reviewer | Performs independent technical review of audit files before decision. |
| CB_FINANCE_OFFICER | Certification Body | CB Finance Officer | Manages CB-side billing, invoices to organizations, payment tracking. |
| CB_SALES_BD | Certification Body | CB Sales and Business Development | Manages leads, opportunities and has limited view of public and prospect data. |
| ORG_ACCOUNT_OWNER | Organization | Organization Account Owner | Primary admin for the client organization’s portal and users. |
| ORG_MANAGEMENT_REP | Organization | Management Representative (Quality/Compliance) | Main contact for audits, manages evidence, responds to NCs. |
| ORG_RISK_COMPLIANCE | Organization | Risk and Compliance Officer | Manages risk and compliance-related actions linked to findings. |
| ORG_PROCESS_OWNER | Organization | Process Owner / Department Manager | Provides local evidence, owns corrective actions for their process. |
| ORG_FINANCE | Organization | Organization Finance Officer | Manages financial interactions with CB (invoices, payments). |
| ORG_VIEWER | Organization | Organization Read-only Viewer | Read-only access to certificates, schedules and statuses. |
| PUBLIC_ANONYMOUS | Public | Anonymous Public User | Public registry user, can search and view limited certificate information. |

---

## 2. Permissions and RBAC

### 2.1 Permission Keys (Atomic Rights)

You can treat these as permission constants in code:

| Permission Key | Description |
| --- | --- |
| `SYS_TENANT_ADMIN` | Create and manage tenants, global tenant configuration. |
| `SYS_SECURITY_ADMIN` | Manage security settings, audit logs, retention, and incident flags. |
| `SYS_SUPPORT` | Read-only diagnostic access and scoped config changes for support. |
| `TENANT_USER_ADMIN` | Create, disable, and manage users inside the current tenant (AB or CB). |
| `ACCRED_ASSESSMENT_MANAGE` | Create, edit and progress accreditation assessments of CBs. |
| `ACCRED_ASSESSMENT_VIEW` | View accreditation-related information and assessment files. |
| `CB_SCHEME_MANAGE` | Create and maintain CB certification schemes, scopes, rules. |
| `AUDIT_PLAN_MANAGE` | Plan audits, create audit programs, assign teams, manage schedules. |
| `AUDIT_EXECUTE` | Access working papers, record findings, upload evidence for assigned audits. |
| `AUDIT_REVIEW` | Perform technical review of audits and access full audit files. |
| `CERT_DECIDE` | Record certification decisions at CB level, separate from audit team. |
| `FINANCE_MANAGE` | Manage invoices, fees, payment status for the current tenant. |
| `ORG_PORTAL_ADMIN` | Administer the client org portal, local users, and org master data. |
| `ORG_PORTAL_RESPOND` | Respond to findings, upload evidence, manage corrective actions. |
| `PUBLIC_REGISTRY_VIEW` | Search and view public registry (certificate, scope, issue/expiry). |

---

### 2.2 RBAC Matrix (Role vs Permission Keys)

`Y` indicates the role has that permission in its own tenant/context.

> You can parse this table directly if needed.

| Role ID | Domain | Role Name | SYS_TENANT_ADMIN | SYS_SECURITY_ADMIN | SYS_SUPPORT | TENANT_USER_ADMIN | ACCRED_ASSESSMENT_MANAGE | ACCRED_ASSESSMENT_VIEW | CB_SCHEME_MANAGE | AUDIT_PLAN_MANAGE | AUDIT_EXECUTE | AUDIT_REVIEW | CERT_DECIDE | FINANCE_MANAGE | ORG_PORTAL_ADMIN | ORG_PORTAL_RESPOND | PUBLIC_REGISTRY_VIEW |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PLAT_SUPER_ADMIN | Platform | Platform Super Admin | Y | Y | Y |  |  |  |  |  |  |  |  |  |  |  |  |
| PLAT_SECURITY_OFFICER | Platform | Platform Security Officer |  | Y | Y |  |  |  |  |  |  |  |  |  |  |  |  |
| PLAT_SUPPORT_ENGINEER | Platform | Platform Support Engineer |  |  | Y |  |  |  |  |  |  |  |  |  |  |  |  |
| AB_EXEC_ADMIN | Accreditation Body | AB Executive Admin |  |  |  | Y | Y | Y |  |  |  |  |  | Y |  |  |  |
| AB_ACCRED_PROG_MANAGER | Accreditation Body | AB Accreditation Program Manager |  |  |  |  | Y | Y |  |  |  |  |  |  |  |  |  |
| AB_LEAD_ASSESSOR | Accreditation Body | AB Lead Assessor |  |  |  |  | Y | Y |  |  |  |  |  |  |  |  |  |
| AB_ASSESSOR | Accreditation Body | AB Assessor |  |  |  |  |  | Y |  |  |  |  |  |  |  |  |  |
| AB_TECH_EXPERT | Accreditation Body | AB Technical Expert |  |  |  |  |  | Y |  |  |  |  |  |  |  |  |  |
| AB_SECRETARIAT_OFFICER | Accreditation Body | AB Secretariat Officer |  |  |  | Y |  | Y |  |  |  |  |  |  |  |  |  |
| AB_FINANCE_OFFICER | Accreditation Body | AB Finance and Contracts Officer |  |  |  |  |  | Y |  |  |  |  |  | Y |  |  |  |
| CB_EXEC_ADMIN | Certification Body | CB Executive Admin |  |  |  | Y |  |  | Y | Y |  |  |  | Y |  |  | Y |
| CB_SCHEME_MANAGER | Certification Body | CB Scheme Manager |  |  |  |  |  | Y | Y |  |  |  |  |  |  |  |  |
| CB_CERT_DECISION_MAKER | Certification Body | CB Certification Decision Maker |  |  |  |  |  | Y |  |  |  | Y | Y |  |  |  |  |
| CB_IMPARTIALITY_MEMBER | Certification Body | CB Impartiality Committee Member |  |  |  |  |  | Y |  |  |  | Y |  |  |  |  |  |
| CB_QMS_COMPLIANCE_MANAGER | Certification Body | CB Quality and Compliance Manager |  |  |  | Y |  | Y | Y |  |  | Y |  |  |  |  |  |
| CB_OPERATIONS_COORDINATOR | Certification Body | CB Operations Coordinator |  |  |  |  |  |  |  | Y | Y |  |  |  |  |  | Y |
| CB_LEAD_AUDITOR_EMP | Certification Body | CB Lead Auditor (Employee) |  |  |  |  |  |  |  |  | Y |  |  |  |  |  | Y |
| CB_AUDITOR_EMP | Certification Body | CB Auditor (Employee) |  |  |  |  |  |  |  |  | Y |  |  |  |  |  |  |
| CB_TRAINEE_AUDITOR | Certification Body | CB Trainee Auditor |  |  |  |  |  |  |  |  | Y |  |  |  |  |  |  |
| CB_EXTERNAL_AUDITOR | Certification Body | CB External Auditor |  |  |  |  |  |  |  |  | Y |  |  |  |  |  |  |
| CB_TECH_REVIEWER | Certification Body | CB Technical Reviewer |  |  |  |  |  |  |  |  |  | Y |  |  |  |  |  |
| CB_FINANCE_OFFICER | Certification Body | CB Finance Officer |  |  |  |  |  |  |  |  |  |  |  | Y |  |  |  |
| CB_SALES_BD | Certification Body | CB Sales and Business Development |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Y |
| ORG_ACCOUNT_OWNER | Organization | Organization Account Owner |  |  |  |  |  |  |  |  |  |  |  |  | Y | Y | Y |
| ORG_MANAGEMENT_REP | Organization | Management Representative (Quality/Compliance) |  |  |  |  |  |  |  |  |  |  |  |  | Y | Y | Y |
| ORG_RISK_COMPLIANCE | Organization | Risk and Compliance Officer |  |  |  |  |  |  |  |  |  |  |  |  |  | Y | Y |
| ORG_PROCESS_OWNER | Organization | Process Owner / Department Manager |  |  |  |  |  |  |  |  |  |  |  |  |  | Y |  |
| ORG_FINANCE | Organization | Organization Finance Officer |  |  |  |  |  |  |  |  |  |  |  | Y |  | Y |  |
| ORG_VIEWER | Organization | Organization Read-only Viewer |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Y |
| PUBLIC_ANONYMOUS | Public | Anonymous Public User |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Y |

---

### 2.3 Per-Role Permissions (Compact Form)

If you prefer a more compact mapping for code:

- `PLAT_SUPER_ADMIN` → `SYS_TENANT_ADMIN`, `SYS_SECURITY_ADMIN`, `SYS_SUPPORT`
- `PLAT_SECURITY_OFFICER` → `SYS_SECURITY_ADMIN`, `SYS_SUPPORT`
- `PLAT_SUPPORT_ENGINEER` → `SYS_SUPPORT`

- `AB_EXEC_ADMIN` → `TENANT_USER_ADMIN`, `ACCRED_ASSESSMENT_MANAGE`, `ACCRED_ASSESSMENT_VIEW`, `FINANCE_MANAGE`
- `AB_ACCRED_PROG_MANAGER` → `ACCRED_ASSESSMENT_MANAGE`, `ACCRED_ASSESSMENT_VIEW`
- `AB_LEAD_ASSESSOR` → `ACCRED_ASSESSMENT_MANAGE`, `ACCRED_ASSESSMENT_VIEW`
- `AB_ASSESSOR` → `ACCRED_ASSESSMENT_VIEW`
- `AB_TECH_EXPERT` → `ACCRED_ASSESSMENT_VIEW`
- `AB_SECRETARIAT_OFFICER` → `TENANT_USER_ADMIN`, `ACCRED_ASSESSMENT_VIEW`
- `AB_FINANCE_OFFICER` → `FINANCE_MANAGE`, `ACCRED_ASSESSMENT_VIEW`

- `CB_EXEC_ADMIN` → `TENANT_USER_ADMIN`, `CB_SCHEME_MANAGE`, `AUDIT_PLAN_MANAGE`, `FINANCE_MANAGE`, `PUBLIC_REGISTRY_VIEW`
- `CB_SCHEME_MANAGER` → `CB_SCHEME_MANAGE`, `ACCRED_ASSESSMENT_VIEW`
- `CB_CERT_DECISION_MAKER` → `CERT_DECIDE`, `AUDIT_REVIEW`, `ACCRED_ASSESSMENT_VIEW`
- `CB_IMPARTIALITY_MEMBER` → `ACCRED_ASSESSMENT_VIEW`, `AUDIT_REVIEW`
- `CB_QMS_COMPLIANCE_MANAGER` → `TENANT_USER_ADMIN`, `CB_SCHEME_MANAGE`, `ACCRED_ASSESSMENT_VIEW`, `AUDIT_REVIEW`
- `CB_OPERATIONS_COORDINATOR` → `AUDIT_PLAN_MANAGE`, `AUDIT_EXECUTE`, `PUBLIC_REGISTRY_VIEW`
- `CB_LEAD_AUDITOR_EMP` → `AUDIT_EXECUTE`, `PUBLIC_REGISTRY_VIEW`
- `CB_AUDITOR_EMP` → `AUDIT_EXECUTE`
- `CB_TRAINEE_AUDITOR` → `AUDIT_EXECUTE`
- `CB_EXTERNAL_AUDITOR` → `AUDIT_EXECUTE`
- `CB_TECH_REVIEWER` → `AUDIT_REVIEW`
- `CB_FINANCE_OFFICER` → `FINANCE_MANAGE`
- `CB_SALES_BD` → `PUBLIC_REGISTRY_VIEW`

- `ORG_ACCOUNT_OWNER` → `ORG_PORTAL_ADMIN`, `ORG_PORTAL_RESPOND`, `PUBLIC_REGISTRY_VIEW`
- `ORG_MANAGEMENT_REP` → `ORG_PORTAL_ADMIN`, `ORG_PORTAL_RESPOND`, `PUBLIC_REGISTRY_VIEW`
- `ORG_RISK_COMPLIANCE` → `ORG_PORTAL_RESPOND`, `PUBLIC_REGISTRY_VIEW`
- `ORG_PROCESS_OWNER` → `ORG_PORTAL_RESPOND`
- `ORG_FINANCE` → `FINANCE_MANAGE`, `ORG_PORTAL_RESPOND`
- `ORG_VIEWER` → `PUBLIC_REGISTRY_VIEW`
- `PUBLIC_ANONYMOUS` → `PUBLIC_REGISTRY_VIEW`

---

## 3. PBAC Layer (Policy-Based Access Control)

RBAC gives *who* can generally do *what*. PBAC adds rules on *when* and *on which objects* based on attributes.

### 3.1 Attribute Model (Examples)

You can implement object/user attributes such as:

- `user.tenant_type` ∈ { PLATFORM, AB, CB, ORG }
- `user.roles` ∋ Role IDs
- `user.is_on_audit_team(audit_id)`  
- `audit.cb_id`, `audit.org_id`, `audit.status`
- `certificate.cb_id`, `certificate.org_id`, `certificate.status`
- `cb.accreditation_body_id`
- `assessment.ab_id`, `assessment.cb_id`
- `user.conflict_of_interest_flags`

### 3.2 PBAC Policy Matrix (Examples)

| Policy ID | Description | Condition (pseudo) | Effect | Used By |
| --- | --- | --- | --- | --- |
| P1_AB_Scope | AB users can only access CB data they accredit. | `user.tenant_type == AB` AND `cb.accreditation_body_id == user.tenant_id` | Allow `ACCRED_ASSESSMENT_VIEW/MANAGE` on that CB. | All AB roles with accreditation perms. |
| P2_CB_AuditTeamScope | CB auditors can only access audits where they are on the team. | `user.tenant_type == CB` AND `user.is_on_audit_team(audit.id)` | Allow `AUDIT_EXECUTE` on that audit. | CB auditors (internal and external). |
| P3_ExternalAuditorMinScope | External auditors cannot see CB-wide client lists or finances. | `role == CB_EXTERNAL_AUDITOR` | Deny access to CB-level finance, client master data; allow only assigned audits. | CB_EXTERNAL_AUDITOR. |
| P4_OrgScope | Org users only access audits and certificates of their own org. | `user.tenant_type == ORG` AND `audit.org_id == user.org_id` | Allow `ORG_PORTAL_RESPOND` on those audits. | ORG_* roles. |
| P5_IndependenceOfDecision | Decision makers cannot be on the same audit team. | `role == CB_CERT_DECISION_MAKER` AND `user.is_on_audit_team(audit.id)` | Deny `CERT_DECIDE` for that audit; require another decision maker. | CB_CERT_DECISION_MAKER. |
| P6_ImpartialityReadOnly | Impartiality committee has read-only access. | `role == CB_IMPARTIALITY_MEMBER` | Allow `ACCRED_ASSESSMENT_VIEW` and `AUDIT_REVIEW` as read-only; deny `AUDIT_EXECUTE`, `CERT_DECIDE`. | CB_IMPARTIALITY_MEMBER. |
| P7_PublicRegistryScope | Public can only see limited certificate data. | `user.tenant_type == PUBLIC` | Allow `PUBLIC_REGISTRY_VIEW` but only on approved fields; mask internal data. | PUBLIC_ANONYMOUS. |
| P8_PlatformNoOperationalInterference | Platform users never manipulate accreditation or certification state. | `user.tenant_type == PLATFORM` | Deny `ACCRED_ASSESSMENT_MANAGE`, `CB_SCHEME_MANAGE`, `CERT_DECIDE` globally. | PLAT_* roles. |

You can implement these as policy rules in code or in an authorization engine (e.g. OPA / Casbin).

---

## 4. Best Practice Architecture Diagram

Mermaid diagram showing main actors and tenants:

```mermaid
flowchart LR
    subgraph PLATFORM["Platform Operator"]
        PS[PLAT_* Roles]
    end

    subgraph AB["Accreditation Body Tenant"]
        ABUsers[AB_* Roles\n(Admin, Assessors, Finance)]
    end

    subgraph CB["Certification Body Tenant"]
        CBUsers[CB_* Roles\n(Admin, Auditors, Decision, Finance)]
    end

    subgraph ORG["Client Organization Tenants"]
        OrgUsers[ORG_* Roles\n(Admin, Mgmt Rep, Risk, Finance, Viewer]
    end

    Public[PUBLIC_ANONYMOUS\nPublic Registry User]

    PS --> AB
    PS --> CB

    ABUsers --> CBUsers:::assess
    CBUsers --> OrgUsers:::audit
    OrgUsers --> CBUsers

    Public --> CB:::registry
    Public --> ORG:::registry

    classDef assess stroke-width:2px,stroke-dasharray: 4 2;
    classDef audit stroke-width:2px,stroke-dasharray: 2 2;
    classDef registry stroke-width:1px,stroke:#888;
