from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from .forms import LessonForm
from .models import Lesson, LessonCategory


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard_redirect(request):
    if request.user.role == User.Role.ADMIN:
        return redirect("core:admin_dashboard")
    return redirect("core:learner_dashboard")


@login_required
def learner_dashboard(request):
    if request.user.role != User.Role.LEARNER:
        raise PermissionDenied
    return render(request, "core/learner_dashboard.html")


@login_required
def admin_dashboard(request):
    if request.user.role != User.Role.ADMIN:
        raise PermissionDenied
    learner_count = User.objects.filter(role=User.Role.LEARNER).count()
    return render(
        request,
        "core/admin_dashboard.html",
        {"learner_count": learner_count},
    )


def _require_role(request, role):
    if request.user.role != role:
        raise PermissionDenied


@login_required
def lesson_list(request):
    _require_role(request, User.Role.LEARNER)
    categories = (
        LessonCategory.objects.annotate(
            published_count=Count("lessons", filter=Q(lessons__is_published=True))
        )
        .filter(published_count__gt=0)
        .prefetch_related(
            Prefetch(
                "lessons",
                queryset=Lesson.objects.filter(is_published=True).order_by("position", "title"),
                to_attr="published_lessons",
            )
        )
    )
    lessons = Lesson.objects.filter(is_published=True).select_related("category")
    category = None
    category_slug = request.GET.get("category", "")
    if category_slug:
        category = get_object_or_404(categories, slug=category_slug)
        lessons = lessons.filter(category=category)
    return render(
        request,
        "core/lesson_list.html",
        {"categories": categories, "lessons": lessons, "category_filter": category},
    )


@login_required
def lesson_detail(request, slug):
    _require_role(request, User.Role.LEARNER)
    lesson = get_object_or_404(
        Lesson.objects.select_related("category"), slug=slug, is_published=True
    )
    return render(request, "core/lesson_detail.html", {"lesson": lesson})


@login_required
def admin_lesson_list(request):
    _require_role(request, User.Role.ADMIN)
    lessons = Lesson.objects.select_related("category", "created_by")
    return render(request, "core/admin_lesson_list.html", {"lessons": lessons})


@login_required
def admin_lesson_create(request):
    _require_role(request, User.Role.ADMIN)
    form = LessonForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        lesson = form.save(commit=False)
        lesson.created_by = request.user
        lesson.save()
        messages.success(request, "Lesson created successfully.")
        return redirect("core:admin_lesson_list")
    return render(request, "core/lesson_form.html", {"form": form, "heading": "Add lesson"})


@login_required
def admin_lesson_update(request, slug):
    _require_role(request, User.Role.ADMIN)
    lesson = get_object_or_404(Lesson, slug=slug)
    old_audio = lesson.audio.name
    form = LessonForm(request.POST or None, request.FILES or None, instance=lesson)
    if request.method == "POST" and form.is_valid():
        updated = form.save()
        if old_audio and updated.audio.name != old_audio:
            lesson.audio.storage.delete(old_audio)
        messages.success(request, "Lesson updated successfully.")
        return redirect("core:admin_lesson_list")
    return render(
        request,
        "core/lesson_form.html",
        {"form": form, "heading": "Edit lesson", "lesson": lesson},
    )


@login_required
@require_POST
def admin_lesson_delete(request, slug):
    _require_role(request, User.Role.ADMIN)
    lesson = get_object_or_404(Lesson, slug=slug)
    if lesson.audio:
        lesson.audio.delete(save=False)
    lesson.delete()
    messages.success(request, "Lesson deleted successfully.")
    return redirect("core:admin_lesson_list")
