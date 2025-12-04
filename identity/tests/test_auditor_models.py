from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Organization, Standard
from identity.adapters.models import (
    AuditorCompetenceEvaluation,
    AuditorQualification,
    AuditorTrainingRecord,
    ConflictOfInterest,
    ImpartialityDeclaration,
)


class AuditorModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", password="password")
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 Test St",
            customer_id="TEST001",
            total_employee_count=10,
        )
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")

    def test_auditor_qualification_creation(self):
        qual = AuditorQualification.objects.create(
            auditor=self.user,
            qualification_type="lead_auditor_cert",
            issuing_body="IRCA",
            certificate_number="12345",
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="active",
        )
        qual.standards.add(self.standard)
        self.assertEqual(str(qual), f"{self.user.username} - Lead Auditor Certificate")
        self.assertEqual(qual.standards.count(), 1)

    def test_auditor_training_record_creation(self):
        training = AuditorTrainingRecord.objects.create(
            auditor=self.user,
            course_title="ISO 9001 Update",
            training_provider="BSI",
            course_date=date.today(),
            duration_hours=8,
            cpd_points=8.0,
        )
        training.standards_covered.add(self.standard)
        self.assertEqual(str(training), f"Training: ISO 9001 Update ({self.user.username})")
        self.assertEqual(training.standards_covered.count(), 1)

    def test_auditor_competence_evaluation_creation(self):
        evaluator = User.objects.create_user(username="evaluator", password="password")
        evaluation = AuditorCompetenceEvaluation.objects.create(
            auditor=self.user,
            evaluation_date=date.today(),
            evaluator=evaluator,
            technical_knowledge_score=4,
            audit_skills_score=4,
            communication_skills_score=5,
            report_writing_score=4,
            overall_assessment="meets",
        )
        self.assertEqual(str(evaluation), f"Competence Eval {self.user.username} {date.today()}")

    def test_conflict_of_interest_creation(self):
        coi = ConflictOfInterest.objects.create(
            auditor=self.user,
            organization=self.org,
            relationship_type="former_employee",
            description="Worked there 5 years ago",
            impartiality_risk="low",
        )
        self.assertEqual(str(coi), f"COI {self.user.username} → {self.org.name} (Low)")

    def test_impartiality_declaration_creation(self):
        decl = ImpartialityDeclaration.objects.create(
            user=self.user, declaration_period_year=2023, no_conflicts_declared=True, declaration_accepted=True
        )
        self.assertEqual(str(decl), f"Impartiality {self.user.username} 2023")
