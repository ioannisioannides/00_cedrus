from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User

from trunk.events import EventType
from trunk.events.handlers import (
    on_appeal_received,
    on_audit_status_changed,
    on_certificate_history_created,
    on_complaint_received,
    on_nc_verified,
    register_event_handlers,
)


@pytest.mark.django_db
class TestEventHandlers:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="test_user", password="password")

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_audit_status_changed_client_review(self, mock_get_model, mock_dispatcher, user):
        # Setup
        mock_audit_model = MagicMock()
        mock_audit = MagicMock()
        mock_audit.id = 1
        mock_audit_model.objects.get.return_value = mock_audit

        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = user

        def get_model_side_effect(app_label, model_name):
            if model_name == "Audit":
                return mock_audit_model
            if model_name == "User":
                return mock_user_model
            return MagicMock()

        mock_get_model.side_effect = get_model_side_effect

        payload = {"audit_id": 1, "new_status": "client_review", "changed_by_id": user.id}

        # Execute
        on_audit_status_changed(payload)

        # Verify
        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_SUBMITTED_TO_CLIENT,
            {"audit_id": 1, "changed_by_id": user.id},
        )

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_audit_status_changed_submitted(self, mock_get_model, mock_dispatcher, user):
        # Setup
        mock_audit_model = MagicMock()
        mock_audit = MagicMock()
        mock_audit.id = 1
        mock_audit_model.objects.get.return_value = mock_audit

        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = user

        def get_model_side_effect(app_label, model_name):
            if model_name == "Audit":
                return mock_audit_model
            if model_name == "User":
                return mock_user_model
            return MagicMock()

        mock_get_model.side_effect = get_model_side_effect

        payload = {"audit_id": 1, "new_status": "submitted", "changed_by_id": user.id}

        # Execute
        on_audit_status_changed(payload)

        # Verify
        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_SUBMITTED_TO_CB,
            {"audit_id": 1, "changed_by_id": user.id},
        )

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_audit_status_changed_decided(self, mock_get_model, mock_dispatcher, user):
        # Setup
        mock_audit_model = MagicMock()
        mock_audit = MagicMock()
        mock_audit.id = 1
        mock_audit_model.objects.get.return_value = mock_audit

        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = user

        def get_model_side_effect(app_label, model_name):
            if model_name == "Audit":
                return mock_audit_model
            if model_name == "User":
                return mock_user_model
            return MagicMock()

        mock_get_model.side_effect = get_model_side_effect

        payload = {"audit_id": 1, "new_status": "decided", "changed_by_id": user.id}

        # Execute
        on_audit_status_changed(payload)

        # Verify
        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_DECIDED,
            {"audit_id": 1, "changed_by_id": user.id},
        )

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_nc_verified_accepted(self, mock_get_model, mock_dispatcher):
        # Setup
        mock_nc_model = MagicMock()
        mock_nc = MagicMock()
        mock_nc.id = 10
        mock_nc.clause = "7.1"
        mock_nc_model.objects.get.return_value = mock_nc

        mock_get_model.return_value = mock_nc_model

        payload = {"nc_id": 10, "verification_status": "accepted"}

        # Execute
        on_nc_verified(payload)

        # Verify
        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_VERIFIED_ACCEPTED,
            {"nc_id": 10},
        )

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_nc_verified_rejected(self, mock_get_model, mock_dispatcher):
        # Setup
        mock_nc_model = MagicMock()
        mock_nc = MagicMock()
        mock_nc.id = 10
        mock_nc.clause = "7.1"
        mock_nc_model.objects.get.return_value = mock_nc

        mock_get_model.return_value = mock_nc_model

        payload = {"nc_id": 10, "verification_status": "rejected"}

        # Execute
        on_nc_verified(payload)

        # Verify
        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_VERIFIED_REJECTED,
            {"nc_id": 10},
        )

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_nc_verified_closed(self, mock_get_model, mock_dispatcher):
        # Setup
        mock_nc_model = MagicMock()
        mock_nc = MagicMock()
        mock_nc.id = 10
        mock_nc.clause = "7.1"
        mock_nc_model.objects.get.return_value = mock_nc

        mock_get_model.return_value = mock_nc_model

        payload = {"nc_id": 10, "verification_status": "closed"}

        # Execute
        on_nc_verified(payload)

        # Verify
        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_CLOSED,
            {"nc_id": 10},
        )

    @patch("trunk.events.handlers.NotificationService")
    @patch("trunk.events.handlers.apps.get_model")
    def test_on_complaint_received(self, mock_get_model, mock_notification):
        # Setup
        mock_complaint_model = MagicMock()
        mock_complaint = MagicMock()
        mock_complaint.complaint_number = "COMP-001"
        mock_complaint.complainant_name = "John Doe"
        mock_complaint_model.objects.get.return_value = mock_complaint

        mock_get_model.return_value = mock_complaint_model

        payload = {"complaint_id": 100}

        # Execute
        on_complaint_received(payload)

        # Verify
        mock_complaint_model.objects.get.assert_called_once_with(id=100)
        mock_notification.notify_complaint_received.assert_called_once_with(payload)

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_appeal_received(self, mock_get_model):
        # Setup
        mock_appeal_model = MagicMock()
        mock_appeal = MagicMock()
        mock_appeal.appeal_number = "APP-001"
        mock_appeal.appellant_name = "Jane Doe"
        mock_appeal_model.objects.get.return_value = mock_appeal

        mock_get_model.return_value = mock_appeal_model

        payload = {"appeal_id": 200}

        # Execute
        on_appeal_received(payload)

        # Verify
        mock_appeal_model.objects.get.assert_called_once_with(id=200)

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_certificate_history_created(self, mock_get_model):
        # Setup
        mock_history_model = MagicMock()
        mock_history = MagicMock()
        mock_history.action = "issued"
        mock_history.certification.certificate_id = "CERT-001"
        mock_history_model.objects.get.return_value = mock_history

        mock_get_model.return_value = mock_history_model

        payload = {"history_id": 300}

        # Execute
        on_certificate_history_created(payload)

        # Verify
        mock_history_model.objects.get.assert_called_once_with(id=300)

    @patch("trunk.events.handlers.event_dispatcher")
    def test_register_event_handlers(self, mock_dispatcher):
        # Execute
        register_event_handlers()

        # Verify
        assert mock_dispatcher.register.call_count == 9
