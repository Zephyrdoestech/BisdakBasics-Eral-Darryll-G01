from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from .forms import LessonForm, LessonPhraseFormSet
from .models import (
    Lesson,
    LessonAttempt,
    LessonCategory,
    LessonPhrase,
    LessonProgress,
    PhrasePractice,
)


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
    published_lesson_count = Lesson.objects.filter(is_published=True).count()
    completed_lesson_count = LessonProgress.objects.filter(
        user=request.user,
        lesson__is_published=True,
        completed_at__isnull=False,
    ).count()
    lesson_progress_percent = (
        round(completed_lesson_count / published_lesson_count * 100)
        if published_lesson_count
        else 0
    )
    category = None
    category_slug = request.GET.get("category", "")
    if category_slug:
        category = get_object_or_404(categories, slug=category_slug)
        lessons = lessons.filter(category=category)
    return render(
        request,
        "core/lesson_list.html",
        {
            "categories": categories,
            "lessons": lessons,
            "category_filter": category,
            "completed_lesson_count": completed_lesson_count,
            "published_lesson_count": published_lesson_count,
            "lesson_progress_percent": lesson_progress_percent,
        },
    )


@login_required
def lesson_detail(request, slug):
    _require_role(request, User.Role.LEARNER)
    lesson = get_object_or_404(
        Lesson.objects.select_related("category"), slug=slug, is_published=True
    )
    phrases = list(lesson.phrases.all())
    practiced_ids = set(
        PhrasePractice.objects.filter(
            user=request.user, phrase__lesson=lesson
        ).values_list("phrase_id", flat=True)
    )
    for display_position, phrase in enumerate(phrases, start=1):
        phrase.display_position = display_position
        phrase.is_practiced = phrase.pk in practiced_ids
    current_phrase = next(
        (phrase for phrase in phrases if not phrase.is_practiced),
        phrases[0] if phrases else None,
    )
    progress = LessonProgress.objects.filter(user=request.user, lesson=lesson).first()
    completed_count = len(practiced_ids)
    phrase_count = len(phrases)
    practice_percent = round(completed_count / phrase_count * 100) if phrase_count else 0
    return render(
        request,
        "core/lesson_detail.html",
        {
            "lesson": lesson,
            "phrases": phrases,
            "current_phrase": current_phrase,
            "practiced_count": completed_count,
            "phrase_count": phrase_count,
            "practice_percent": practice_percent,
            "progress": progress,
            "last_attempt": LessonAttempt.objects.filter(
                user=request.user, lesson=lesson
            ).first(),
        },
    )


@login_required
@require_POST
def record_phrase_practice(request, slug, phrase_id):
    _require_role(request, User.Role.LEARNER)
    phrase = get_object_or_404(
        LessonPhrase.objects.select_related("lesson"),
        pk=phrase_id,
        lesson__slug=slug,
        lesson__is_published=True,
    )
    _, created = PhrasePractice.objects.get_or_create(
        user=request.user, phrase=phrase, defaults={"practice_count": 1}
    )
    if not created:
        PhrasePractice.objects.filter(user=request.user, phrase=phrase).update(
            practice_count=F("practice_count") + 1,
            last_practiced_at=timezone.now(),
        )
    practiced_count = PhrasePractice.objects.filter(
        user=request.user, phrase__lesson=phrase.lesson
    ).count()
    phrase_count = phrase.lesson.phrases.count()
    return JsonResponse(
        {
            "practiced_count": practiced_count,
            "phrase_count": phrase_count,
            "progress_percent": round(practiced_count / phrase_count * 100)
            if phrase_count
            else 0,
        }
    )


@login_required
@require_POST
def submit_lesson_checkpoint(request, slug):
    _require_role(request, User.Role.LEARNER)
    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)
    selected_answer = request.POST.get("selected_answer", "")
    if selected_answer not in {"A", "B"} or not lesson.checkpoint_question:
        messages.error(request, "Choose an answer for this lesson checkpoint.")
        return redirect("core:lesson_detail", slug=lesson.slug)

    is_correct = selected_answer == lesson.checkpoint_correct_answer
    LessonAttempt.objects.create(
        user=request.user,
        lesson=lesson,
        selected_answer=selected_answer,
        is_correct=is_correct,
        score=100 if is_correct else 0,
    )
    if is_correct:
        LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={"completed_at": timezone.now()},
        )
        messages.success(request, "Correct! This lesson is now complete.")
    else:
        messages.error(request, "Not quite. Review the phrases and try again.")
    return redirect("core:lesson_detail", slug=lesson.slug)


@login_required
@require_POST
def complete_lesson(request, slug):
    _require_role(request, User.Role.LEARNER)
    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)
    if lesson.checkpoint_question:
        messages.error(request, "Complete the lesson checkpoint to finish this lesson.")
    else:
        LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={"completed_at": timezone.now()},
        )
        messages.success(request, "Lesson completed. Nice work!")
    return redirect("core:lesson_detail", slug=lesson.slug)


@login_required
def admin_lesson_list(request):
    _require_role(request, User.Role.ADMIN)
    lessons = Lesson.objects.select_related("category", "created_by")
    return render(request, "core/admin_lesson_list.html", {"lessons": lessons})


@login_required
def admin_lesson_create(request):
    _require_role(request, User.Role.ADMIN)
    lesson = Lesson(created_by=request.user)
    form = LessonForm(request.POST or None, request.FILES or None, instance=lesson)
    phrase_formset = LessonPhraseFormSet(
        request.POST or None, request.FILES or None, instance=lesson, prefix="phrases"
    )
    if request.method == "POST" and form.is_valid() and phrase_formset.is_valid():
        with transaction.atomic():
            saved_lesson = form.save(commit=False)
            saved_lesson.created_by = request.user
            saved_lesson.save()
            phrase_formset.instance = saved_lesson
            phrase_formset.save()
        messages.success(request, "Lesson created successfully.")
        return redirect("core:admin_lesson_list")
    return render(
        request,
        "core/lesson_form.html",
        {"form": form, "phrase_formset": phrase_formset, "heading": "Add lesson"},
    )


@login_required
def admin_lesson_update(request, slug):
    _require_role(request, User.Role.ADMIN)
    lesson = get_object_or_404(Lesson, slug=slug)
    old_audio = lesson.audio.name
    form = LessonForm(request.POST or None, request.FILES or None, instance=lesson)
    phrase_formset = LessonPhraseFormSet(
        request.POST or None,
        request.FILES or None,
        instance=lesson,
        prefix="phrases",
    )
    if request.method == "POST" and form.is_valid() and phrase_formset.is_valid():
        phrase_audio_to_delete = []
        for phrase_form in phrase_formset.forms:
            if not phrase_form.instance.pk or not phrase_form.cleaned_data:
                continue
            old_name = phrase_form.instance.audio.name
            if old_name and (
                phrase_form.cleaned_data.get("DELETE")
                or "audio" in phrase_form.changed_data
            ):
                phrase_audio_to_delete.append(old_name)
        with transaction.atomic():
            updated = form.save()
            phrase_formset.save()
        if old_audio and updated.audio.name != old_audio:
            lesson.audio.storage.delete(old_audio)
        for audio_name in phrase_audio_to_delete:
            LessonPhrase._meta.get_field("audio").storage.delete(audio_name)
        messages.success(request, "Lesson updated successfully.")
        return redirect("core:admin_lesson_list")
    return render(
        request,
        "core/lesson_form.html",
        {
            "form": form,
            "phrase_formset": phrase_formset,
            "heading": "Edit lesson",
            "lesson": lesson,
        },
    )


@login_required
@require_POST
def admin_lesson_delete(request, slug):
    _require_role(request, User.Role.ADMIN)
    lesson = get_object_or_404(Lesson, slug=slug)
    if lesson.audio:
        lesson.audio.delete(save=False)
    for phrase in lesson.phrases.exclude(audio=""):
        phrase.audio.delete(save=False)
    lesson.delete()
    messages.success(request, "Lesson deleted successfully.")
    return redirect("core:admin_lesson_list")
