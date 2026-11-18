from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("dashboard/learner/", views.learner_dashboard, name="learner_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("lessons/", views.lesson_list, name="lesson_list"),
    path("phrasebook/", views.phrasebook, name="phrasebook"),
    path("phrasebook/requests/", views.phrase_requests, name="phrase_requests"),
    path("phrasebook/requests/new/", views.phrase_request_create, name="phrase_request_create"),
    path("lessons/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<slug:slug>/phrases/<int:phrase_id>/practice/", views.record_phrase_practice, name="record_phrase_practice"),
    path("lessons/<slug:slug>/checkpoint/", views.submit_lesson_checkpoint, name="submit_lesson_checkpoint"),
    path("lessons/<slug:slug>/complete/", views.complete_lesson, name="complete_lesson"),
    path("dashboard/admin/lessons/", views.admin_lesson_list, name="admin_lesson_list"),
    path("dashboard/admin/lessons/add/", views.admin_lesson_create, name="admin_lesson_create"),
    path("dashboard/admin/lessons/<slug:slug>/edit/", views.admin_lesson_update, name="admin_lesson_update"),
    path("dashboard/admin/lessons/<slug:slug>/delete/", views.admin_lesson_delete, name="admin_lesson_delete"),
    path("dashboard/admin/phrases/", views.admin_phrase_list, name="admin_phrase_list"),
    path("dashboard/admin/phrases/add/", views.admin_phrase_create, name="admin_phrase_create"),
    path("dashboard/admin/phrases/<int:phrase_id>/edit/", views.admin_phrase_update, name="admin_phrase_update"),
    path("dashboard/admin/phrases/<int:phrase_id>/delete/", views.admin_phrase_delete, name="admin_phrase_delete"),
    path("dashboard/admin/phrase-categories/", views.admin_phrase_category_list, name="admin_phrase_categories"),
    path("dashboard/admin/phrase-categories/add/", views.admin_phrase_category_create, name="admin_phrase_category_create"),
    path("dashboard/admin/phrase-categories/<int:category_id>/edit/", views.admin_phrase_category_update, name="admin_phrase_category_update"),
    path("dashboard/admin/phrase-categories/<int:category_id>/delete/", views.admin_phrase_category_delete, name="admin_phrase_category_delete"),
    path("dashboard/admin/phrase-requests/", views.admin_phrase_requests, name="admin_phrase_requests"),
    path("dashboard/admin/phrase-requests/<int:request_id>/review/", views.admin_phrase_request_review, name="admin_phrase_request_review"),
]
