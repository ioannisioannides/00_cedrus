from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User

from core.models import CertificateHistory, Certification, Organization, Standard, SurveillanceSchedule


@pytest.mark.django_db
class TestCertificateHistory:
    def setup_method(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_create_history_entry(self):
        history = CertificateHistory.objects.create(
            certification=self.cert,
            action="issued",
            action_date=date.today(),
            action_by=self.user,
            action_reason="Initial Issue",
            internal_notes="Notes",
        )
        assert history.certification == self.cert
        assert history.action == "issued"
        assert history.action_by == self.user
        assert str(history) == f"{self.cert} issued ({date.today()})"

    def test_history_ordering(self):
        h1 = CertificateHistory.objects.create(
            certification=self.cert,
            action="issued",
            action_date=date.today() - timedelta(days=10),
        )
        h2 = CertificateHistory.objects.create(
            certification=self.cert,
            action="renewed",
            action_date=date.today(),
        )

        history = list(CertificateHistory.objects.filter(certification=self.cert))
        assert history[0] == h2
        assert history[1] == h1


@pytest.mark.django_db
class TestSurveillanceSchedule:
    def setup_method(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )

    def test_create_schedule(self):
        start = date.today()
        schedule = SurveillanceSchedule.objects.create(
            certification=self.cert,
            cycle_start=start,
            cycle_end=start + timedelta(days=1095),
            surveillance_1_due_date=start + timedelta(days=365),
            surveillance_2_due_date=start + timedelta(days=730),
            recertification_due_date=start + timedelta(days=1095),
        )
        assert schedule.certification == self.cert
        assert not schedule.surveillance_1_completed
        assert str(schedule) == f"Surveillance schedule for {self.cert}"

    def test_one_to_one_relationship(self):
        start = date.today()
        SurveillanceSchedule.objects.create(
            certification=self.cert,
            cycle_start=start,
            cycle_end=start + timedelta(days=1095),
            surveillance_1_due_date=start + timedelta(days=365),
            surveillance_2_due_date=start + timedelta(days=730),
            recertification_due_date=start + timedelta(days=1095),
        )

        # Try to create another schedule for the same cert
        from django.db.utils import IntegrityError

        with pytest.raises(IntegrityError):
            SurveillanceSchedule.objects.create(
                certification=self.cert,
                cycle_start=start,
                cycle_end=start + timedelta(days=1095),
                surveillance_1_due_date=start + timedelta(days=365),
                surveillance_2_due_date=start + timedelta(days=730),
                recertification_due_date=start + timedelta(days=1095),
            )
