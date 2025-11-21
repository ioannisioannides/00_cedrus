# Phase 2 Quick Reference Guide

**Version:** 1.0  
**Date:** November 21, 2025  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Root Cause Analysis](#root-cause-analysis)
2. [Finding Recurrence Tracking](#finding-recurrence-tracking)
3. [Auditor Competence Warnings](#auditor-competence-warnings)
4. [Multi-Site Sampling (IAF MD1)](#multi-site-sampling-iaf-md1)
5. [Duration Validation (IAF MD5)](#duration-validation-iaf-md5)
6. [Admin Interface Guide](#admin-interface-guide)

---

## 🔍 Root Cause Analysis

### Creating Root Cause Categories

**Admin Interface:**

1. Navigate to `/admin/audits/rootcausecategory/`
2. Click "Add Root Cause Category"
3. Enter:
   - **Code**: Unique identifier (e.g., RC-001)
   - **Name**: Category name (e.g., "Training Deficiency")
   - **Description**: Detailed explanation
   - **Parent**: Optional (for hierarchical structure)
   - **Is Active**: Check to enable

**Hierarchical Structure Example:**

```
RC-100: Resource Issues (Parent)
  ├─ RC-101: Training Deficiency (Child)
  ├─ RC-102: Equipment Inadequacy (Child)
  └─ RC-103: Personnel Shortage (Child)
```

### Assigning Categories to Findings

**In Nonconformity Edit Form:**

1. Navigate to nonconformity detail
2. Scroll to "Root Cause Categories" section
3. Select one or more categories
4. Save

**Programmatically:**

```python
nc.root_cause_categories.add(category1, category2)
nc.save()
```

### Querying by Root Cause

```python
# Find all NCs with specific root cause
from audits.models import RootCauseCategory, Nonconformity

training_cat = RootCauseCategory.objects.get(code="RC-101")
ncs = Nonconformity.objects.filter(root_cause_categories=training_cat)

# Find all NCs with any root cause in a hierarchy
parent_cat = RootCauseCategory.objects.get(code="RC-100")
child_cats = parent_cat.subcategories.all()
ncs = Nonconformity.objects.filter(
    root_cause_categories__in=[parent_cat] + list(child_cats)
)
```

---

## 🔁 Finding Recurrence Tracking

### Creating Recurrence Records

**Admin Interface:**

1. Navigate to `/admin/audits/findingrecurrence/`
2. Click "Add Finding Recurrence"
3. Enter:
   - **Finding**: Select the nonconformity
   - **Recurrence Count**: Number of occurrences
   - **First Occurrence**: Date of first finding
   - **Last Occurrence**: Date of most recent finding
   - **Previous Audits**: References (comma-separated)
   - **Corrective Actions Effective**: Yes/No
   - **Resolution Notes**: Detailed notes
   - **Escalation Required**: Flag for management attention

**Programmatically:**

```python
from audits.models import FindingRecurrence
from datetime import date

recurrence = FindingRecurrence.objects.create(
    finding=nc,
    recurrence_count=3,
    first_occurrence=date(2023, 1, 15),
    last_occurrence=date(2025, 11, 21),
    previous_audits="Audit-2023-001, Audit-2024-045",
    corrective_actions_effective=False,
    escalation_required=True,
    resolution_notes="Root cause not addressed - escalated to senior management"
)
```

### Querying Recurrence Data

```python
# Find all recurring findings
recurring = FindingRecurrence.objects.filter(recurrence_count__gte=2)

# Find findings requiring escalation
escalated = FindingRecurrence.objects.filter(escalation_required=True)

# Find findings with ineffective corrective actions
ineffective = FindingRecurrence.objects.filter(
    corrective_actions_effective=False
)

# Access recurrence data from finding
if hasattr(nc, 'recurrence_data'):
    print(f"This finding has occurred {nc.recurrence_data.recurrence_count} times")
```

### Best Practices

✅ **Do:**

- Track recurrence starting from the second occurrence
- Update recurrence count each time finding reappears
- Document why corrective actions were ineffective
- Flag escalation when recurrence count ≥ 3

❌ **Don't:**

- Create recurrence records for first-time findings
- Forget to update last_occurrence date
- Leave resolution_notes blank for escalated findings

---

## ⚠️ Auditor Competence Warnings

### Issuing Warnings

**Admin Interface:**

1. Navigate to `/admin/audits/auditorcompetencewarning/`
2. Click "Add Auditor Competence Warning"
3. Enter:
   - **Audit**: Related audit
   - **Auditor**: User receiving warning
   - **Warning Type**: Select from dropdown
   - **Severity**: Low/Medium/High/Critical
   - **Description**: Detailed explanation
   - **Issued By**: Auto-populated (current user)

**Warning Types:**

- **Scope Mismatch**: Auditor's competence doesn't match audit scope
- **Insufficient Experience**: Too few audits in this sector
- **Expired Qualification**: Certification/qualification expired
- **Language Barrier**: Language competence issue
- **Conflict of Interest**: Potential impartiality concern
- **Other**: Custom issue

**Severity Guidelines:**

- **Critical**: Blocks audit assignment (must be resolved)
- **High**: Requires approval from CB manager
- **Medium**: Monitor and document mitigation
- **Low**: Informational only

**Programmatically:**

```python
from audits.models import AuditorCompetenceWarning

warning = AuditorCompetenceWarning.objects.create(
    audit=audit,
    auditor=auditor_user,
    warning_type="expired_qualification",
    severity="critical",
    description="ISO 9001 Lead Auditor certification expired on 2025-10-15",
    issued_by=cb_admin_user
)
```

### Resolving Warnings

**Admin Interface:**

1. Open the warning in admin
2. Set **Resolved At**: Current datetime
3. Enter **Resolution Notes**: How issue was addressed
4. Check **Acknowledged by Auditor**: If auditor has seen it
5. Save

**Programmatically:**

```python
from django.utils import timezone

warning.resolved_at = timezone.now()
warning.resolution_notes = "Auditor renewed ISO 9001 LA certification (Cert #12345)"
warning.acknowledged_by_auditor = True
warning.save()
```

### Querying Warnings

```python
# Find all unresolved warnings
unresolved = AuditorCompetenceWarning.objects.filter(resolved_at__isnull=True)

# Find critical warnings for specific auditor
critical = AuditorCompetenceWarning.objects.filter(
    auditor=user,
    severity="critical",
    resolved_at__isnull=True
)

# Check if auditor has any active warnings
has_warnings = AuditorCompetenceWarning.objects.filter(
    auditor=user,
    resolved_at__isnull=True
).exists()
```

---

## 📐 Multi-Site Sampling (IAF MD1)

### Using the Sampling Algorithm

```python
from trunk.services.sampling import calculate_sample_size

# Basic usage - initial certification
result = calculate_sample_size(
    total_sites=25,
    is_initial_certification=True
)

print(f"Minimum sites: {result['minimum_sites']}")  # Output: 5
print(result['justification'])

# Advanced usage - with risk factors
result = calculate_sample_size(
    total_sites=100,
    high_risk_sites=10,
    previous_findings_count=5,
    is_initial_certification=False,
    scope_variation="high"
)

print(f"Base calculation: {result['base_calculation']}")  # √100 - 0.5 = 10
print(f"Risk adjustment: {result['risk_adjustment']}")    # Additional sites
print(f"Minimum sites: {result['minimum_sites']}")        # Total required
print(f"Coverage: {result['coverage_percentage']:.1f}%")

# Print detailed justification
print(result['justification'])

# Print risk factors
for factor in result['risk_factors']:
    print(f"  • {factor}")
```

### Validating Site Selection

```python
from trunk.services.sampling import validate_site_selection

validation = validate_site_selection(
    selected_sites=8,
    required_minimum=10,
    total_sites=25
)

if not validation['is_valid']:
    print(f"❌ {validation['message']}")
    print(f"Need {validation['shortfall']} more site(s)")
else:
    print(f"✅ {validation['message']}")
```

### IAF MD1 Quick Reference Table

| Total Sites | Initial Cert | Surveillance | Notes |
|-------------|-------------|--------------|-------|
| 1-4         | √x → 1-2    | 1            | Minimum 1 site |
| 5-16        | √x → 3-4    | √x - 0.5 → 2-3 | Round up |
| 17-36       | √x → 5-6    | √x - 0.5 → 4-5 | |
| 37-64       | √x → 7-8    | √x - 0.5 → 6-7 | |
| 65-100      | √x → 9-10   | √x - 0.5 → 9 | |
| 100+        | √x → 10+    | √x - 0.5 → 9+ | Add risk adjustments |

---

## ⏱️ Duration Validation (IAF MD5)

### Using the Duration Validator

```python
from trunk.services.duration_validator import validate_audit_duration

# Basic validation
result = validate_audit_duration(
    planned_hours=21.0,
    employee_count=100,
    is_initial_certification=True
)

print(f"Valid: {result['is_valid']}")                    # True/False
print(f"Required: {result['required_minimum']} hours")   # Minimum hours
print(f"Severity: {result['severity']}")                 # compliant/warning/critical
print(result['recommendation'])

# Advanced validation with complexity factors
result = validate_audit_duration(
    planned_hours=50.0,
    employee_count=500,
    is_initial_certification=True,
    number_of_sites=5,
    scope_variation="moderate",
    process_complexity="complex",
    regulatory_environment="high",
    has_outsourced_processes=True,
    previous_major_ncs=3
)

# Print formatted report
from trunk.services.duration_validator import format_duration_report
print(format_duration_report(result))
```

### IAF MD5 Base Duration Quick Reference

| Employees | Base Hours (ISO 9001) |
|-----------|-----------------------|
| 1-5       | 3.5                  |
| 6-10      | 6.0                  |
| 11-15     | 8.0                  |
| 16-25     | 10.0                 |
| 26-45     | 12.5                 |
| 46-65     | 16.0                 |
| 66-85     | 18.0                 |
| 86-125    | 21.0                 |
| 126-175   | 24.0                 |
| 176-275   | 29.0                 |
| 276-425   | 35.0                 |
| 426-625   | 42.0                 |
| 626-875   | 49.0                 |
| 876-1175  | 56.0                 |
| 1176-1550 | 63.0                 |
| 1551+     | See formula          |

**Formula for >10,500 employees:**

- Base (10,500) = 133 hours
- Add 14 hours per additional 2,000 employees

### Complexity Factor Guidelines

| Factor | Range | Impact |
|--------|-------|--------|
| Multi-site (per site) | +5% | Capped at +15% |
| Scope variation (high) | +10% | |
| Scope variation (moderate) | +5% | |
| Complex processes | +15% | |
| Simple processes | -10% | |
| High regulatory | +10% | |
| Low regulatory | -5% | |
| Outsourced processes | +8% | |
| Previous major NCs (>3) | +10% | |

**Total Factor Range:** 0.8x to 1.3x (±20% from base)

### Surveillance Audit Adjustments

**Rule:** Apply 67% (2/3) factor to the adjusted initial certification duration

**Example:**

- Initial cert: 100 employees = 21 hours base × 1.2 complexity = 25.2 hours
- Surveillance: 25.2 × 0.67 = 16.9 → 17 hours

---

## 🖥️ Admin Interface Guide

### Root Cause Category Admin

**Location:** `/admin/audits/rootcausecategory/`

**List View Columns:**

- Code
- Name
- Parent category
- Is Active
- Created At

**Filters:**

- Is Active (Yes/No)
- Parent category
- Created date range

**Search Fields:**

- Code
- Name
- Description

**Actions:**

- Bulk deactivate categories
- Export to CSV

### Finding Recurrence Admin

**Location:** `/admin/audits/findingrecurrence/`

**List View Columns:**

- Finding (with link)
- Recurrence Count
- First Occurrence
- Last Occurrence
- Corrective Actions Effective
- Escalation Required

**Filters:**

- Corrective Actions Effective
- Escalation Required
- Recurrence Count (≥2, ≥3, ≥5)
- Last Occurrence date range

**Search Fields:**

- Finding clause
- Finding statement
- Organization name
- Resolution notes

### Auditor Competence Warning Admin

**Location:** `/admin/audits/auditorcompetencewarning/`

**List View Columns:**

- Auditor
- Audit
- Warning Type
- Severity
- Issued At
- Resolved At
- Acknowledged

**Filters:**

- Warning Type
- Severity
- Issued date range
- Resolved (Yes/No)
- Acknowledged (Yes/No)

**Search Fields:**

- Auditor name
- Organization name
- Description
- Resolution notes

**Special Features:**

- Issued By auto-populated on create
- Color-coded severity in list view
- Quick actions for resolving

---

## 🎯 Common Use Cases

### Use Case 1: Planning a Multi-Site Audit

```python
from trunk.services.sampling import calculate_sample_size
from trunk.services.duration_validator import validate_audit_duration

# Step 1: Calculate site sample
sampling = calculate_sample_size(
    total_sites=org.sites.count(),
    high_risk_sites=5,  # Based on risk assessment
    is_initial_certification=True,
    scope_variation="moderate"
)

print(f"Sample {sampling['minimum_sites']} of {org.sites.count()} sites")

# Step 2: Calculate employee count for sampled sites
sampled_sites = org.sites.all()[:sampling['minimum_sites']]
total_employees = sum(site.site_employee_count for site in sampled_sites)

# Step 3: Validate duration
duration = validate_audit_duration(
    planned_hours=35.0,
    employee_count=total_employees,
    is_initial_certification=True,
    number_of_sites=sampling['minimum_sites'],
    scope_variation="moderate"
)

if not duration['is_valid']:
    print(f"⚠️ Increase duration to {duration['required_minimum']} hours")
```

### Use Case 2: Checking Auditor Competence

```python
from audits.models import AuditorCompetenceWarning

# Before assigning auditor to audit
warnings = AuditorCompetenceWarning.objects.filter(
    auditor=proposed_auditor,
    severity__in=["critical", "high"],
    resolved_at__isnull=True
)

if warnings.exists():
    print("⚠️ AUDITOR HAS ACTIVE WARNINGS:")
    for w in warnings:
        print(f"  - {w.get_severity_display()}: {w.get_warning_type_display()}")
        print(f"    {w.description}")
    # Block assignment or require CB manager approval
```

### Use Case 3: Analyzing Recurring Findings

```python
from audits.models import FindingRecurrence, RootCauseCategory

# Find all findings with 3+ recurrences
high_recurrence = FindingRecurrence.objects.filter(
    recurrence_count__gte=3,
    escalation_required=True
)

# Group by root cause
from django.db.models import Count

root_cause_stats = RootCauseCategory.objects.annotate(
    nc_count=Count('nonconformities'),
    recurring_count=Count(
        'nonconformities__recurrence_data',
        filter=Q(nonconformities__recurrence_data__recurrence_count__gte=2)
    )
).filter(nc_count__gt=0).order_by('-recurring_count')

print("Top Root Causes with Recurrence:")
for cat in root_cause_stats[:10]:
    print(f"{cat.code}: {cat.name} - {cat.recurring_count} recurring")
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue:** "No changes detected" when running makemigrations

- **Solution:** Migration already exists (0004). Run `migrate` to apply it.

**Issue:** Sampling calculation seems incorrect

- **Solution:** Review all risk factors. Algorithm adds adjustments conservatively.

**Issue:** Duration validation too strict

- **Solution:** Check complexity factors. Ensure all factors accurately reflect audit scope.

**Issue:** Can't delete root cause category

- **Solution:** Check if category has associated NCs. Deactivate instead of delete.

### Getting Help

- **Documentation:** `/docs/PHASE_2_COMPLETION_REPORT.md`
- **Code Reference:** `trunk/services/sampling.py`, `trunk/services/duration_validator.py`
- **Test Examples:** `audits/test_phase2.py`
- **Admin Interface:** Direct access via Django admin

---

## 📚 Additional Resources

- **IAF MD1:2018** - Multi-site certification requirements
- **IAF MD5:2019** - Duration calculation tables
- **ISO 17021-1:2015** - Conformity assessment requirements
- **Django Documentation** - Model relationships and queries

---

**Last Updated:** November 21, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅

---

*Need more help? Check the comprehensive Phase 2 Completion Report or review test cases for detailed examples.*
