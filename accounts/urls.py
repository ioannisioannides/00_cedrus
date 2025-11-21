"""
URL configuration for accounts app.
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/cb/", views.dashboard_cb, name="dashboard_cb"),
    path("dashboard/auditor/", views.dashboard_auditor, name="dashboard_auditor"),
    path("dashboard/client/", views.dashboard_client, name="dashboard_client"),
]
