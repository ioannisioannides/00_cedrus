"""Auditor competence related service functions.

Provides validation helpers used during audit team assignment and
auditor selection to enforce ISO 17021-1 Clause 7 competency rules.
"""

from datetime import date
from typing import List

from django.core.exceptions import ValidationError

from accounts.models import AuditorCompetenceEvaluation, AuditorQualification
from audits.models import Audit


class CompetenceService:
    """Service layer for auditor competence validation."""

    @staticmethod
    def get_active_qualifications(user) -> List[AuditorQualification]:
        return list(
            AuditorQualification.objects.filter(auditor=user, status="active").order_by("-issue_date")
        )

    @staticmethod
    def ensure_auditor_has_active_qualification(user, audit: Audit):
        """Validate that auditor has at least one active qualification covering audit standards."""
        if not hasattr(audit, "certifications"):
            return  # Safeguard
        audit_standards = {c.standard_id for c in audit.certifications.all()}
        quals = CompetenceService.get_active_qualifications(user)
        if not quals:
            raise ValidationError(
                f"Auditor {user.username} lacks active qualifications (ISO 17021-1 Clause 7.1)."
            )
        # Check coverage: at least one qualification referencing any of the audit standards
        covered = False
        for q in quals:
            q_standard_ids = set(q.standards.values_list("id", "id"))
            if audit_standards & q_standard_ids:
                covered = True
                break
        if not covered and audit_standards:
            raise ValidationError(
                f"Auditor {user.username} qualifications do not cover audit standards (Clause 7.1)."
            )

    @staticmethod
    def check_recent_competence_evaluation(user):
        """Warn if auditor lacks a competence evaluation in last 12 months (Clause 7.2.6)."""
        evaluation = (
            AuditorCompetenceEvaluation.objects.filter(auditor=user).order_by("-evaluation_date").first()
        )
        if not evaluation:
            raise ValidationError(
                f"Auditor {user.username} has no competence evaluation record (Clause 7.2.6)."
            )
        if (date.today() - evaluation.evaluation_date).days > 365:
            raise ValidationError(
                f"Auditor {user.username} competence evaluation is older than 12 months (Clause 7.2.6)."
            )
