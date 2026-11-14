from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("dashboard/learner/", views.learner_dashboard, name="learner_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
]
