"""
URL configuration for identity app.
"""

from django.urls import path  # pylint: disable=no-name-in-module

from . import views

app_name = "identity"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/cb/", views.dashboard_cb, name="dashboard_cb"),
    path("dashboard/auditor/", views.dashboard_auditor, name="dashboard_auditor"),
    path("dashboard/client/", views.dashboard_client, name="dashboard_client"),
    # Auditor Qualifications
    path("qualifications/", views.AuditorQualificationListView.as_view(), name="qualification_list"),
    path("qualifications/add/", views.AuditorQualificationCreateView.as_view(), name="qualification_create"),
    path("qualifications/<int:pk>/edit/", views.AuditorQualificationUpdateView.as_view(), name="qualification_update"),
    # Auditor Training
    path("training/", views.AuditorTrainingListView.as_view(), name="training_list"),
    path("training/add/", views.AuditorTrainingCreateView.as_view(), name="training_create"),
    path("training/<int:pk>/edit/", views.AuditorTrainingUpdateView.as_view(), name="training_update"),
    # Competence Evaluations
    path("competence/", views.CompetenceEvaluationListView.as_view(), name="competence_list"),
    path("competence/add/", views.CompetenceEvaluationCreateView.as_view(), name="competence_create"),
    path("competence/<int:pk>/edit/", views.CompetenceEvaluationUpdateView.as_view(), name="competence_update"),
    # Conflicts of Interest
    path("coi/", views.ConflictOfInterestListView.as_view(), name="coi_list"),
    path("coi/add/", views.ConflictOfInterestCreateView.as_view(), name="coi_create"),
    path("coi/<int:pk>/edit/", views.ConflictOfInterestUpdateView.as_view(), name="coi_update"),
]
