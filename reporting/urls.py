from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("audit/<int:audit_id>/report/", views.generate_audit_report_pdf, name="audit_report_pdf"),
    path("audit/<int:audit_id>/certificate/", views.generate_certificate_pdf, name="certificate_pdf"),
]
