"""
REST API URL configuration for certification module.

Routes are registered with DRF DefaultRouter and included under /api/v1/certification/.
"""

from rest_framework.routers import DefaultRouter

from .viewsets import (
    AppealViewSet,
    CertificationDecisionViewSet,
    ComplaintViewSet,
    TechnicalReviewViewSet,
    TransferCertificationViewSet,
)

router = DefaultRouter()
router.register(r"complaints", ComplaintViewSet, basename="complaint")
router.register(r"appeals", AppealViewSet, basename="appeal")
router.register(r"decisions", CertificationDecisionViewSet, basename="certificationdecision")
router.register(r"technical-reviews", TechnicalReviewViewSet, basename="technicalreview")
router.register(r"transfers", TransferCertificationViewSet, basename="transfercertification")

urlpatterns = router.urls
