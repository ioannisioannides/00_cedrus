"""
REST API URL configuration for audit management.

Routes are registered with DRF DefaultRouter and included under /api/v1/audits/.
"""

from rest_framework.routers import DefaultRouter

from .viewsets import (
    AuditProgramViewSet,
    AuditTeamMemberViewSet,
    AuditViewSet,
    EvidenceFileViewSet,
    NonconformityViewSet,
    ObservationViewSet,
    OFIViewSet,
)

router = DefaultRouter()
router.register(r"programs", AuditProgramViewSet, basename="auditprogram")
router.register(r"audits", AuditViewSet, basename="audit")
router.register(r"nonconformities", NonconformityViewSet, basename="nonconformity")
router.register(r"observations", ObservationViewSet, basename="observation")
router.register(r"ofis", OFIViewSet, basename="ofi")
router.register(r"team-members", AuditTeamMemberViewSet, basename="auditteammember")
router.register(r"evidence", EvidenceFileViewSet, basename="evidencefile")

urlpatterns = router.urls
