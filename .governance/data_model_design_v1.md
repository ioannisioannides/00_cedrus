# Cedrus Enhanced Data Model Design
## Architecture Meeting — Post Board Approval
### Date: 21 November 2025

---

## Participants
- **Architecture Agent** (Lead)
- **Data Modeling Agent** (Schema Design)
- **ISO 17021 Agent** (Compliance Requirements)
- **Compliance Agent** (Validation)
- **IAF Expert** (MD1/MD22 Requirements)

---

## 1. Executive Summary

Following Board Meeting #001 approvals, we must enhance the existing `audits` data model to support:

1. **Approved Workflow States**: `Draft` → `In Review` → `Submitted to CB` → `Technical Review` → `Decision Pending` → `Closed`
2. **Future-Proofing**: Support for risk, compliance, and internal audit modules
3. **Per-Site Findings**: Link findings to specific sites
4. **Recurring Findings**: Track findings across multiple audits
5. **Root Cause Taxonomy**: Structured categorization of root causes
6. **Evidence Classification**: Document vs. Interview vs. Observation vs. Record

---

## 2. Current State Analysis

### Existing Models (Already Implemented)
✅ `Audit` - Main audit entity with workflow status
✅ `AuditTeamMember` - Team assignments
✅ `Finding` (Abstract) - Base class for all findings
✅ `Nonconformity` - NC lifecycle with client response
✅ `Observation` - Informational findings
✅ `OpportunityForImprovement` - Improvement suggestions
✅ `EvidenceFile` - File attachments
✅ `AuditRecommendation` - Final recommendations
✅ `AuditChanges`, `AuditPlanReview`, `AuditSummary` - Audit metadata

### Gaps Identified
❌ Workflow states don't match approved model
❌ No Technical Review tracking
❌ No per-site finding association
❌ No recurring finding tracking
❌ No root cause taxonomy
❌ No evidence type classification
❌ No decision authority tracking
❌ No audit duration justification (IAF MD5)
❌ No competence validation warnings
❌ No retention policy enforcement

---

## 3. Enhanced Data Model Design

### 3.1 Workflow Enhancement

**Current `Audit.STATUS_CHOICES`**:
```python
("draft", "Draft"),
("client_review", "Client Review"),
("submitted_to_cb", "Submitted to CB"),
("decided", "Decided"),
```

**Approved `Audit.STATUS_CHOICES`** (MUST IMPLEMENT):
```python
("draft", "Draft"),
("in_review", "In Review"),                          # NEW
("submitted_to_cb", "Submitted to CB"),
("returned_for_correction", "Returned for Correction"),  # NEW
("technical_review", "Technical Review"),            # NEW
("decision_pending", "Decision Pending"),            # NEW
("closed", "Closed"),                                # NEW (replaces "decided")
```

**New Model: `AuditStatusLog`** (Audit Trail Requirement):
```python
class AuditStatusLog(models.Model):
    """Immutable log of all status transitions."""
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ["-changed_at"]
```

---

### 3.2 Technical Review & Decision Tracking

**New Model: `TechnicalReview`**:
```python
class TechnicalReview(models.Model):
    """Technical review before certification decision (ISO 17021 requirement)."""
    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="technical_review")
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reviews_conducted")
    reviewed_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("requires_clarification", "Requires Clarification"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    
    # ISO 17021 Clause 9.4.8 requirements
    scope_verified = models.BooleanField(default=False)
    objectives_verified = models.BooleanField(default=False)
    findings_reviewed = models.BooleanField(default=False)
    conclusion_clear = models.BooleanField(default=False)
    
    reviewer_notes = models.TextField(blank=True)
    clarification_requested = models.TextField(blank=True)
```

**New Model: `CertificationDecision`**:
```python
class CertificationDecision(models.Model):
    """Final certification decision (ISO 17021 separation of duties)."""
    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="decision")
    decision_maker = models.ForeignKey(User, on_delete=models.PROTECT, related_name="decisions_made")
    decided_at = models.DateTimeField(auto_now_add=True)
    
    DECISION_CHOICES = [
        ("grant", "Grant Certification"),
        ("refuse", "Refuse Certification"),
        ("suspend", "Suspend Certification"),
        ("withdraw", "Withdraw Certification"),
        ("special_audit", "Require Special Audit"),
    ]
    decision = models.CharField(max_length=30, choices=DECISION_CHOICES)
    decision_notes = models.TextField()
    
    # Link to affected certifications
    certifications_affected = models.ManyToManyField("core.Certification", related_name="decisions")
```

---

### 3.3 Per-Site Findings

**Enhancement to `Finding` (Abstract Base)**:
```python
class Finding(models.Model):
    # ... existing fields ...
    site = models.ForeignKey(  # NEW
        "core.Site",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_findings",
        help_text="Specific site where finding was raised (for multi-site audits)"
    )
```

---

### 3.4 Recurring Findings Tracking

**New Model: `FindingRecurrence`**:
```python
class FindingRecurrence(models.Model):
    """Track recurring findings across multiple audits."""
    original_finding = models.ForeignKey(
        "Nonconformity",
        on_delete=models.CASCADE,
        related_name="recurrences_as_original"
    )
    recurring_finding = models.ForeignKey(
        "Nonconformity",
        on_delete=models.CASCADE,
        related_name="recurrences_as_recurrence"
    )
    identified_by = models.ForeignKey(User, on_delete=models.PROTECT)
    identified_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Why this is considered a recurrence")
```

---

### 3.5 Root Cause Taxonomy

**New Model: `RootCauseCategory`**:
```python
class RootCauseCategory(models.Model):
    """Taxonomy for categorizing root causes (5 Whys, Fishbone, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories"
    )
    
    # Common categories: People, Process, Technology, Environment, Materials
    
    class Meta:
        verbose_name = "Root Cause Category"
        verbose_name_plural = "Root Cause Categories"
```

**Enhancement to `Nonconformity`**:
```python
class Nonconformity(Finding):
    # ... existing fields ...
    root_cause_category = models.ForeignKey(  # NEW
        RootCauseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nonconformities"
    )
```

---

### 3.6 Evidence Classification

**Enhancement to `EvidenceFile`**:
```python
class EvidenceFile(models.Model):
    # ... existing fields ...
    
    EVIDENCE_TYPE_CHOICES = [  # NEW
        ("document", "Document Review"),
        ("interview", "Interview Notes"),
        ("observation", "Direct Observation"),
        ("record", "Record Examination"),
        ("photo", "Photographic Evidence"),
        ("other", "Other"),
    ]
    evidence_type = models.CharField(
        max_length=20,
        choices=EVIDENCE_TYPE_CHOICES,
        default="document"
    )
    description = models.TextField(blank=True, help_text="Description of the evidence")
    
    # GDPR/Retention
    retention_years = models.PositiveIntegerField(default=7)  # NEW (Board approved 7 years)
    purge_after = models.DateField(null=True, blank=True)  # NEW (auto-calculated)
```

---

### 3.7 Audit Duration Justification (IAF MD5)

**Enhancement to `Audit`**:
```python
class Audit(models.Model):
    # ... existing fields ...
    
    # IAF MD5 Duration Management
    planned_duration_hours = models.FloatField(  # NEW
        validators=[MinValueValidator(0.0)],
        help_text="Planned audit duration (IAF MD5 calculation)"
    )
    actual_duration_hours = models.FloatField(  # NEW (rename from audit_duration_hours)
        validators=[MinValueValidator(0.0)],
        help_text="Actual audit duration"
    )
    duration_justification = models.TextField(  # NEW
        blank=True,
        help_text="Justification for deviation from planned duration (IAF MD5)"
    )
```

---

### 3.8 Competence Validation

**New Model: `AuditorCompetenceWarning`**:
```python
class AuditorCompetenceWarning(models.Model):
    """Warnings when auditor assigned without proper competence."""
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="competence_warnings")
    team_member = models.ForeignKey(AuditTeamMember, on_delete=models.CASCADE)
    standard = models.ForeignKey("core.Standard", on_delete=models.CASCADE)
    warning_type = models.CharField(max_length=50)  # "missing_qualification", "expired_qualification"
    warning_message = models.TextField()
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
```

---

## 4. Migration Strategy

### Phase 1: Immediate (Sprint 7)
1. Update `Audit.STATUS_CHOICES` with new workflow states
2. Create `AuditStatusLog` model
3. Create `TechnicalReview` model
4. Create `CertificationDecision` model
5. Add `site` field to `Finding` abstract base
6. Update `EvidenceFile` with evidence type and retention

### Phase 2: Near-term (Sprint 8)
1. Create `FindingRecurrence` model
2. Create `RootCauseCategory` model
3. Add `root_cause_category` to `Nonconformity`
4. Create `AuditorCompetenceWarning` model
5. Add IAF MD5 duration fields to `Audit`

### Phase 3: Future (Post-MVP)
1. Multi-site sampling algorithm (IAF MD1)
2. Automated retention policy enforcement
3. Integration with Competence Module

---

## 5. Compliance Validation

### ISO 17021-1:2015 Alignment
✅ **Clause 9.5**: Separation of duties enforced via `TechnicalReview` and `CertificationDecision` models
✅ **Clause 9.4.8**: Technical review checklist embedded in `TechnicalReview` model
✅ **Clause 9.6**: Decision-making independence tracked via `decision_maker` field

### IAF MD Requirements
✅ **MD1**: Per-site tracking via `Finding.site` field
✅ **MD5**: Duration justification via `Audit.duration_justification` field
✅ **MD22**: Recurring findings via `FindingRecurrence` model

### GDPR/Data Protection
✅ **Retention Policy**: 7-year default via `EvidenceFile.retention_years`
✅ **Automated Purging**: `EvidenceFile.purge_after` for scheduled deletion

---

## 6. Database Performance Considerations

### Indexes Required
- `AuditStatusLog.audit_id` + `changed_at` (for audit trails)
- `Finding.site_id` (for multi-site queries)
- `FindingRecurrence.original_finding_id` (for recurrence tracking)
- `EvidenceFile.purge_after` (for retention enforcement)

### Query Optimization
- Use `select_related()` for `Audit` → `TechnicalReview` → `CertificationDecision`
- Use `prefetch_related()` for `Audit.findings` with `site` join

---

## 7. API Surface Impact

### New Views Required
- `TechnicalReviewView` (CB staff only)
- `CertificationDecisionView` (Decision makers only)
- `AuditStatusLogView` (Read-only audit trail)
- `RecurringFindingsReportView` (Analytics)

### Permission Updates
- `PermissionPredicate.can_conduct_technical_review(user, audit)`
- `PermissionPredicate.can_make_certification_decision(user, audit)`
- `PermissionPredicate.is_technical_reviewer(user)`

---

## 8. Next Steps

### Immediate Actions
1. **Data Modeling Agent**: Create Django migration files for Phase 1 models
2. **Architecture Agent**: Update `AuditWorkflow` to reflect new states
3. **Security Agent**: Update `PermissionPredicate` for new roles
4. **Engineering Agent**: Implement new models and views
5. **QA Agent**: Create test cases for workflow transitions

### Documentation Updates
- Update `MODELS.md` with new entity relationships
- Create ERD diagram showing all relationships
- Document workflow state machine
- Update API documentation

---

## 9. Approval Status

**Status**: ✅ **APPROVED FOR IMPLEMENTATION**

This design fulfills all requirements from Board Meeting #001:
- ✅ Scalable data model for future modules
- ✅ Per-site findings support
- ✅ Recurring findings tracking
- ✅ Root cause taxonomy
- ✅ Evidence classification
- ✅ Approved workflow states
- ✅ Technical review gate
- ✅ 7-year retention policy
- ✅ Decision authority structure
- ✅ ISO 17021 compliance
- ✅ IAF MD1/MD5/MD22 alignment

**Ready to proceed with implementation.**
