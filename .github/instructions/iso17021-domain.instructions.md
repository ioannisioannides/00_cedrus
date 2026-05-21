---
applyTo: "frontend/**/*.ts,frontend/**/*.tsx"
---

# ISO 17021 Audit Domain Knowledge — Cedrus

## Audit Lifecycle (ISO 17021-1:2015)

The standard audit lifecycle for a Certification Body conducting third-party audits:

```
Draft → Client Review → Submitted to CB → Technical Review → Decision Pending → Closed
```

| Status | Who transitions | What happens |
|--------|----------------|--------------|
| Draft | Lead Auditor | Audit created, team being assembled |
| Client Review | Lead Auditor | Findings sent to client for NC responses |
| Submitted to CB | Client Admin | Client has responded to all NCs |
| Technical Review | CB Admin | Technical reviewer checks audit quality |
| Decision Pending | Technical Reviewer | Ready for certification decision |
| Closed | CB Admin | Certification decision made |

## Finding Types

| Type | Code | Definition |
|------|------|-----------|
| Major Nonconformity | NC-major | Systematic failure; certification at risk |
| Minor Nonconformity | NC-minor | Isolated lapse; requires corrective action |
| Observation | OFI | Opportunity for improvement (no mandatory response) |

## Role Permissions

| Role | Can Create Audit | Can Add Findings | Can Respond to NC | Can Make Decision |
|------|:-:|:-:|:-:|:-:|
| CB Admin | ✅ | ✅ | ❌ | ✅ |
| Lead Auditor | ❌ | ✅ | ❌ | ❌ |
| Auditor | ❌ | ✅ | ❌ | ❌ |
| Client Admin | ❌ | ❌ | ✅ | ❌ |
| Client User | ❌ | ❌ | ✅ | ❌ |

## Certification Decision Types

- **Grant** — Issue/renew certification
- **Refuse** — Do not issue certification  
- **Suspend** — Temporarily suspend existing certification
- **Withdraw** — Permanently withdraw certification

## Key Business Rules

1. An audit **must have a lead auditor** before transitioning from Draft.
2. A certification can only be granted if **all major NCs have verified corrective actions**.
3. Client users can only see audits for **their own organization**.
4. Evidence files belong to a specific audit **and** optional finding.
5. The same auditor cannot audit a client where they have a **conflict of interest** (to be implemented).
6. Audit dates: `total_audit_date_to >= total_audit_date_from`.
7. Certifications and sites must belong to **the same organization as the audit**.

## Domain Models (Key Fields)

```python
# Audit: the central entity
class Audit:
    organization       # The company being audited
    certification      # Scope of certification
    lead_auditor       # Responsible auditor (User)
    team_members       # Additional auditors
    status             # Current lifecycle state
    audit_type         # Initial/Surveillance/Recertification/Special
    total_audit_date_from/to  # Date range

# Finding: a specific audit observation
class Finding:
    audit              # Parent audit
    finding_type       # NC-major / NC-minor / OFI
    description        # What was found
    clause_reference   # ISO clause (e.g., "4.1", "6.2")
    status             # open / client_responded / verified / closed
    client_response    # Client's corrective action description
    evidence_files     # Supporting documentation

# EvidenceFile: document attached to audit or finding
class EvidenceFile:
    audit              # Parent audit
    finding            # Optional: finding this evidence supports
    file               # The uploaded file
    uploaded_by        # User who uploaded
```
