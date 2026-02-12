"""
REST API URL routing for core app.

Registers DRF router with all core viewsets.
"""

from rest_framework.routers import DefaultRouter

from .viewsets import CertificationViewSet, OrganizationViewSet, SiteViewSet, StandardViewSet

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"sites", SiteViewSet, basename="site")
router.register(r"standards", StandardViewSet, basename="standard")
router.register(r"certifications", CertificationViewSet, basename="certification")

urlpatterns = router.urls
