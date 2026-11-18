from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("dashboard/learner/", views.learner_dashboard, name="learner_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("lessons/", views.lesson_list, name="lesson_list"),
    path("lessons/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path("dashboard/admin/lessons/", views.admin_lesson_list, name="admin_lesson_list"),
    path("dashboard/admin/lessons/add/", views.admin_lesson_create, name="admin_lesson_create"),
    path("dashboard/admin/lessons/<slug:slug>/edit/", views.admin_lesson_update, name="admin_lesson_update"),
    path("dashboard/admin/lessons/<slug:slug>/delete/", views.admin_lesson_delete, name="admin_lesson_delete"),
]
