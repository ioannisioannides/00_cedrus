from datetime import date
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class AuditBaseDTO(BaseModel):
    """Base schema for Audit data."""

    audit_type: str
    total_audit_date_from: date
    total_audit_date_to: date
    planned_duration_hours: Optional[float] = None
    status: Optional[str] = "draft"

    @field_validator("total_audit_date_to")
    @classmethod
    def validate_dates(cls, v, info):
        if "total_audit_date_from" in info.data and v < info.data["total_audit_date_from"]:
            raise ValueError("Audit end date must be on or after start date.")
        return v


class AuditCreateDTO(AuditBaseDTO):
    """Schema for creating an Audit."""

    organization_id: int
    program_id: Optional[int] = None
    certification_ids: List[int] = Field(..., min_length=1)
    site_ids: List[int] = Field(..., min_length=1)
    lead_auditor_id: Optional[int] = None


class AuditUpdateDTO(BaseModel):
    """Schema for updating an Audit."""

    audit_type: Optional[str] = None
    total_audit_date_from: Optional[date] = None
    total_audit_date_to: Optional[date] = None
    planned_duration_hours: Optional[float] = None
    status: Optional[str] = None
    program_id: Optional[int] = None
    certification_ids: Optional[List[int]] = None
    site_ids: Optional[List[int]] = None
    lead_auditor_id: Optional[int] = None


class AuditResponseDTO(AuditBaseDTO):
    """Schema for Audit response."""

    id: int
    organization_id: int
    program_id: Optional[int] = None
    certification_ids: List[int]
    site_ids: List[int]
    lead_auditor_id: Optional[int]
    created_by_id: int
    created_at: date  # Simplified for now

    class Config:
        from_attributes = True


class AuditChangesDTO(BaseModel):
    """Schema for Audit Changes documentation."""

    change_of_name: bool = False
    change_of_scope: bool = False
    change_of_sites: bool = False
    change_of_ms_rep: bool = False
    change_of_signatory: bool = False
    change_of_employee_count: bool = False
    change_of_contact_info: bool = False
    other_has_change: bool = False
    other_description: str = ""


class AuditPlanReviewDTO(BaseModel):
    """Schema for Audit Plan Review documentation."""

    deviations_yes_no: bool = False
    deviations_details: str = ""
    issues_affecting_yes_no: bool = False
    issues_affecting_details: str = ""
    next_audit_date_from: Optional[date] = None
    next_audit_date_to: Optional[date] = None


class AuditSummaryDTO(BaseModel):
    """Schema for Audit Summary documentation."""

    objectives_met: bool = False
    objectives_comments: str = ""
    scope_appropriate: bool = False
    scope_comments: str = ""
    ms_meets_requirements: bool = False
    ms_comments: str = ""
    management_review_effective: bool = False
    management_review_comments: str = ""
    internal_audit_effective: bool = False
    internal_audit_comments: str = ""
    ms_effective: bool = False
    ms_effective_comments: str = ""
    correct_use_of_logos: bool = False
    logos_comments: str = ""
    promoted_to_committee: bool = False
    committee_comments: str = ""
    general_commentary: str = ""


class AuditRecommendationDTO(BaseModel):
    """Schema for Audit Recommendation documentation."""

    special_audit_required: bool = False
    special_audit_details: str = ""
    suspension_recommended: bool = False
    suspension_certificates: str = ""
    revocation_recommended: bool = False
    revocation_certificates: str = ""
    stage2_required: bool = False
    decision_notes: str = ""


class EvidenceUploadDTO(BaseModel):
    """Schema for uploading evidence."""

    file: Any  # Django UploadedFile
    evidence_type: str = "document"
    description: str = ""
    finding_id: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True
