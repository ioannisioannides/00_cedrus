# Audit Workflow Diagrams

**Version:** 1.0  
**Last Updated:** 20 November 2025  
**Purpose:** Visual representation of Cedrus audit workflows

---

## Table of Contents

1. [Audit Status Lifecycle](#audit-status-lifecycle)
2. [Permission Matrix](#permission-matrix)
3. [Status Transition Flow](#status-transition-flow)
4. [Documentation Requirements Flow](#documentation-requirements-flow)
5. [Nonconformity Response Flow](#nonconformity-response-flow)
6. [Evidence File Management Flow](#evidence-file-management-flow)
7. [Recommendation and Decision Flow](#recommendation-and-decision-flow)
8. [Complete Audit Process](#complete-audit-process)

---

## Audit Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft: Audit Created
    draft --> client_review: Lead Auditor Submits
    client_review --> draft: CB Admin Override
    client_review --> submitted_to_cb: Lead Auditor/CB Admin Submits
    submitted_to_cb --> decided: CB Admin Makes Decision
    decided --> [*]: Final Status
    
    note right of draft
        Initial audit creation
        Documentation in progress
        Team assignments
    end note
    
    note right of client_review
        Client reviews findings
        Responds to major NCs
        Verification period
    end note
    
    note right of submitted_to_cb
        CB reviews audit
        Lead Auditor creates recommendation
        Awaiting decision
    end note
    
    note right of decided
        Final certification decision
        Certificate issued (if approved)
        Status cannot be changed
    end note
```

---

## Permission Matrix

```mermaid
graph TB
    subgraph "Roles and Permissions"
        CB[CB Administrator]
        LA[Lead Auditor]
        AU[Auditor]
        CL[Client User]
    end
    
    subgraph "Actions"
        CREATE[Create Audit]
        STATUS[Change Status]
        UPLOAD[Upload Files]
        REC[Create Recommendation]
        DEC[Make Decision]
        RESPOND[Respond to NC]
    end
    
    CB -->|Full Access| CREATE
    CB -->|All Transitions| STATUS
    CB -->|Yes| UPLOAD
    CB -->|Can Override| REC
    CB -->|Only Role| DEC
    
    LA -->|No| CREATE
    LA -->|Limited| STATUS
    LA -->|Yes| UPLOAD
    LA -->|Yes| REC
    LA -->|No| DEC
    
    AU -->|No| CREATE
    AU -->|No| STATUS
    AU -->|Yes| UPLOAD
    AU -->|No| REC
    AU -->|No| DEC
    
    CL -->|No| CREATE
    CL -->|No| STATUS
    CL -->|No| UPLOAD
    CL -->|No| REC
    CL -->|No| DEC
    CL -->|Yes| RESPOND
```

---

## Status Transition Flow

```mermaid
flowchart TD
    Start([User Initiates Status Change])
    Start --> CheckAuth{User Authenticated?}
    
    CheckAuth -->|No| AuthError[Error: Login Required]
    CheckAuth -->|Yes| CheckValid{Valid Transition?}
    
    CheckValid -->|No| InvalidError[Error: Invalid Transition]
    CheckValid -->|Yes| CheckPerm{User Has Permission?}
    
    CheckPerm -->|No| PermError[Error: Permission Denied]
    CheckPerm -->|Yes| CheckRules{Business Rules Pass?}
    
    CheckRules -->|No| RuleError[Error: Validation Failed]
    CheckRules -->|Yes| UpdateStatus[Update Audit Status]
    
    UpdateStatus --> LogChange[Log Status Change]
    LogChange --> Notify[Send Notifications]
    Notify --> Success([Status Changed Successfully])
    
    AuthError --> End([Redirect to Login])
    InvalidError --> End
    PermError --> End
    RuleError --> End
    Success --> End
    
    style Success fill:#90EE90
    style AuthError fill:#FFB6C1
    style InvalidError fill:#FFB6C1
    style PermError fill:#FFB6C1
    style RuleError fill:#FFB6C1
```

---

## Documentation Requirements Flow

```mermaid
flowchart TD
    Draft[Audit in Draft Status]
    Draft --> OrgChanges{Organization Changes Documented?}
    
    OrgChanges -->|No| AddOrg[Lead Auditor: Edit Organization Changes]
    OrgChanges -->|Yes| PlanReview{Audit Plan Review Complete?}
    
    AddOrg --> PlanReview
    
    PlanReview -->|No| AddPlan[Lead Auditor: Edit Audit Plan Review]
    PlanReview -->|Yes| Evidence{Evidence Files Uploaded?}
    
    AddPlan --> Evidence
    
    Evidence -->|No| UploadFiles[Auditor: Upload Evidence Files]
    Evidence -->|Yes| NCs{Nonconformities Documented?}
    
    UploadFiles --> NCs
    
    NCs -->|No| CreateNCs[Auditor: Create Nonconformities]
    NCs -->|Yes| ReadySubmit{Ready for Client Review?}
    
    CreateNCs --> ReadySubmit
    
    ReadySubmit -->|No| MoreDoc[Complete Additional Documentation]
    ReadySubmit -->|Yes| SubmitClient[Submit to Client Review]
    
    MoreDoc --> Draft
    SubmitClient --> ClientReview[Status: client_review]
    
    style Draft fill:#FFE4B5
    style ClientReview fill:#90EE90
```

---

## Nonconformity Response Flow

```mermaid
sequenceDiagram
    participant LA as Lead Auditor
    participant SYS as System
    participant CL as Client
    participant CB as CB Admin
    
    LA->>SYS: Create Major NC
    LA->>SYS: Link Evidence Files
    LA->>SYS: Submit to Client Review
    SYS->>SYS: Validate Documentation
    SYS->>CL: Notify Client (future)
    
    CL->>SYS: View Major NC
    CL->>SYS: Submit NC Response
    Note over CL,SYS: Root Cause<br/>Correction<br/>Corrective Action<br/>Evidence
    
    SYS->>SYS: Validate Response Complete
    SYS->>LA: Notify Lead Auditor (future)
    
    LA->>SYS: Review Client Response
    LA->>SYS: Check All Major NCs Responded
    
    alt All Major NCs Responded
        LA->>SYS: Submit to CB
        SYS->>CB: Audit Ready for Decision
    else Major NCs Not Responded
        SYS->>LA: Error: Cannot Submit
        LA->>CL: Request Response
    end
```

---

## Evidence File Management Flow

```mermaid
flowchart TD
    Start([Auditor Initiates Upload])
    Start --> CheckAuth{Authenticated<br/>as Auditor?}
    
    CheckAuth -->|No| AuthError[Error: Auditors Only]
    CheckAuth -->|Yes| SelectFile[Select File]
    
    SelectFile --> ValidateSize{File Size<br/>≤ 10MB?}
    
    ValidateSize -->|No| SizeError[Error: File Too Large]
    ValidateSize -->|Yes| ValidateType{File Type<br/>Allowed?}
    
    ValidateType -->|No| TypeError[Error: Invalid File Type]
    ValidateType -->|Yes| AddDesc[Add Description]
    
    AddDesc --> LinkNC{Link to NC?}
    
    LinkNC -->|Yes| SelectNC[Select Nonconformity]
    LinkNC -->|No| Upload
    
    SelectNC --> Upload[Upload File]
    
    Upload --> SaveFile[Save to Media Storage]
    SaveFile --> CreateRecord[Create EvidenceFile Record]
    CreateRecord --> Success([File Uploaded Successfully])
    
    Success --> CanDownload{User Can Download?}
    CanDownload -->|Auditor/CB Admin| Download[Download Available]
    CanDownload -->|Client/Other| NoDownload[Download Restricted]
    
    Success --> CanDelete{User is Uploader<br/>or CB Admin?}
    CanDelete -->|Yes| Delete[Delete Available]
    CanDelete -->|No| NoDelete[Delete Restricted]
    
    style Success fill:#90EE90
    style AuthError fill:#FFB6C1
    style SizeError fill:#FFB6C1
    style TypeError fill:#FFB6C1
```

---

## Recommendation and Decision Flow

```mermaid
flowchart TD
    Submitted[Audit in submitted_to_cb Status]
    Submitted --> LACheck{Lead Auditor<br/>Assigned?}
    
    LACheck -->|No| Error1[Error: No Lead Auditor]
    LACheck -->|Yes| CreateRec[Lead Auditor: Create Recommendation]
    
    CreateRec --> RecType{Recommendation<br/>Type}
    
    RecType -->|Certify| RecCert[Recommend Certification]
    RecType -->|Certify w/ Conditions| RecCond[Recommend with Conditions]
    RecType -->|Deny| RecDeny[Do Not Recommend]
    
    RecCert --> RecJust[Add Justification]
    RecCond --> RecJust
    RecDeny --> RecJust
    
    RecJust --> SaveRec[Save Recommendation]
    SaveRec --> NotifyCB[Notify CB Admin]
    
    NotifyCB --> CBReview{CB Admin<br/>Reviews Audit}
    
    CBReview --> MakeDecision[CB Admin: Make Decision]
    
    MakeDecision --> DecType{Decision<br/>Type}
    
    DecType -->|Certify| IssueCert[Issue Certificate]
    DecType -->|Certify w/ Conditions| IssueCondCert[Issue Conditional Certificate]
    DecType -->|Deny| DenyApp[Deny Application]
    
    IssueCert --> GenCert[Generate Certificate Number]
    IssueCondCert --> GenCert
    
    GenCert --> SetValid[Set Validity Period]
    SetValid --> UpdateStatus[Status → decided]
    
    DenyApp --> DocReason[Document Denial Reason]
    DocReason --> UpdateStatus
    
    UpdateStatus --> Final([Final Decision - Permanent])
    
    style Final fill:#90EE90
    style Error1 fill:#FFB6C1
```

---

## Complete Audit Process

```mermaid
graph TB
    subgraph "Phase 1: Audit Creation"
        A1[CB Admin Creates Audit]
        A2[Assign Lead Auditor]
        A3[Assign Team Members]
        A4[Set Audit Schedule]
    end
    
    subgraph "Phase 2: Audit Execution"
        B1[Lead Auditor: Plan Review]
        B2[Team: Conduct Audit]
        B3[Team: Upload Evidence]
        B4[Team: Create Nonconformities]
        B5[Lead Auditor: Review Findings]
    end
    
    subgraph "Phase 3: Client Review"
        C1[Lead Auditor: Submit to Client]
        C2[Client: Review Findings]
        C3[Client: Respond to Major NCs]
        C4[Lead Auditor: Verify Responses]
    end
    
    subgraph "Phase 4: CB Review"
        D1[Lead Auditor: Complete Summary]
        D2[Lead Auditor: Submit to CB]
        D3[Lead Auditor: Create Recommendation]
        D4[CB Admin: Review Package]
    end
    
    subgraph "Phase 5: Decision"
        E1[CB Admin: Make Decision]
        E2[System: Update Status to Decided]
        E3[System: Generate Certificate if Approved]
        E4[Notify Client]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B1
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> B5
    B5 --> C1
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> D1
    
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> E1
    
    E1 --> E2
    E2 --> E3
    E3 --> E4
    
    style E4 fill:#90EE90
```

---

## Status Transition Validation Rules

```mermaid
flowchart LR
    subgraph "draft → client_review"
        D1[Lead Auditor Only]
        D2[Documentation Complete]
    end
    
    subgraph "client_review → submitted_to_cb"
        C1[Lead Auditor OR CB Admin]
        C2[All Major NCs Responded]
        C3[Audit Summary Complete]
    end
    
    subgraph "submitted_to_cb → decided"
        S1[CB Admin Only]
        S2[Recommendation Exists]
    end
    
    D1 --> D2
    C1 --> C2
    C2 --> C3
    S1 --> S2
```

---

## Role-Based Access Control

```mermaid
graph TD
    User[User Login]
    User --> RoleCheck{Check User Role}
    
    RoleCheck -->|CB Admin| CBPerms[Full Permissions]
    RoleCheck -->|Lead Auditor| LAPerms[Audit Management]
    RoleCheck -->|Auditor| AUPerms[Limited Access]
    RoleCheck -->|Client| CLPerms[Read Only]
    
    CBPerms --> Actions1[Create/Edit Audits<br/>Change Any Status<br/>Make Decisions<br/>Upload/Delete Files<br/>Override Permissions]
    
    LAPerms --> Actions2[Edit Own Audits<br/>Submit to Client<br/>Submit to CB<br/>Create Recommendations<br/>Upload Files]
    
    AUPerms --> Actions3[View Assigned Audits<br/>Upload Files<br/>Create NCs<br/>No Status Changes]
    
    CLPerms --> Actions4[View Own Audits<br/>Download Files<br/>Respond to NCs<br/>No Uploads/Changes]
```

---

## Error Handling Flow

```mermaid
flowchart TD
    Action[User Action]
    Action --> Try{Try Action}
    
    Try -->|Success| Success[Action Completed]
    Try -->|Error| ErrorType{Error Type}
    
    ErrorType -->|Authentication| Auth[Redirect to Login]
    ErrorType -->|Permission| Perm[Show Permission Error]
    ErrorType -->|Validation| Valid[Show Validation Error]
    ErrorType -->|Not Found| NotFound[Show 404 Page]
    ErrorType -->|Server Error| Server[Show Error Page]
    
    Auth --> Log[Log Error]
    Perm --> Log
    Valid --> Log
    NotFound --> Log
    Server --> Log
    
    Log --> Notify{Critical?}
    
    Notify -->|Yes| Alert[Alert Admins]
    Notify -->|No| Continue
    
    Success --> Continue[Continue]
    Alert --> Continue
    
    style Success fill:#90EE90
    style Auth fill:#FFB6C1
    style Perm fill:#FFB6C1
    style Valid fill:#FFD700
    style NotFound fill:#FFB6C1
    style Server fill:#FF6347
```

---

## Usage Notes

### Viewing These Diagrams

These diagrams use Mermaid syntax and can be viewed in:

- **GitHub:** Automatically renders Mermaid
- **VS Code:** Install "Markdown Preview Mermaid Support" extension
- **GitLab:** Native Mermaid support
- **Documentation Sites:** Most modern docs platforms support Mermaid
- **Online:** Copy to <https://mermaid.live> for interactive viewing

### Diagram Legends

| Color | Meaning |
|-------|---------|
| 🟢 Green | Success state or final outcome |
| 🔴 Red/Pink | Error state or denied action |
| 🟡 Yellow | Warning or conditional state |
| 🔵 Blue | Process step or intermediate state |

### Customization

These diagrams can be customized by:

1. Editing the Mermaid code blocks
2. Changing colors with `style` directives
3. Adding notes with `note` or `Note over` syntax
4. Adjusting layout with subgraph organization

---

## Related Documentation

- **User Guide:** See `AUDIT_WORKFLOW_GUIDE.md` for detailed step-by-step instructions
- **Architecture:** See `../ARCHITECTURE.md` for technical implementation
- **Models:** See `../MODELS.md` for database schema
- **API Reference:** See `../API_REFERENCE.md` for developer documentation

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-20 | Documentation Agent | Initial creation with all Priority 2 workflow diagrams |

---

*These diagrams represent the Priority 2 implementation as of November 2025. Future enhancements may add additional flows and transitions.*
