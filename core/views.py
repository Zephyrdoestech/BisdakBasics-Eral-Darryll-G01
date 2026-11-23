import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Case, Count, Exists, F, OuterRef, Q, Subquery, When
from django.db.models.deletion import ProtectedError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Profile, User
from .forms import (
    LessonForm,
    LessonPhraseFormSet,
    PhraseCategoryForm,
    PhraseForm,
    PhraseRequestForm,
    PhraseRequestReviewForm,
    PhraseSearchForm,
)
from .models import (
    Lesson,
    LessonAttempt,
    LessonCategory,
    LessonPhrase,
    LessonProgress,
    Phrase,
    PhraseCategory,
    PhrasePractice,
    PhraseRequest,
)


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard_redirect(request):
    if request.user.role == User.Role.ADMIN:
        return redirect("core:admin_dashboard")
    return redirect("core:learner_dashboard")


def _calculate_streak_days(activity_dates, today):
    if not activity_dates:
        return 0
    if today in activity_dates:
        cursor = today
    elif (today - timezone.timedelta(days=1)) in activity_dates:
        cursor = today - timezone.timedelta(days=1)
    else:
        return 0
    streak = 0
    while cursor in activity_dates:
        streak += 1
        cursor -= timezone.timedelta(days=1)
    return streak


_DAILY_GOAL_RE = re.compile(r"(\d+)\s*(?:min|minute)", re.IGNORECASE)


def _extract_daily_goal_minutes(user):
    if hasattr(user, "_state"):
        cached_profile = user._state.fields_cache.get("profile")
        if cached_profile is not None:
            learning_goal = cached_profile.learning_goal
        elif user.pk is not None:
            learning_goal = (
                Profile.objects.filter(user_id=user.pk)
                .values_list("learning_goal", flat=True)
                .first()
            )
        else:
            learning_goal = ""
    else:
        profile = getattr(user, "profile", None)
        learning_goal = profile.learning_goal if profile else ""

    if learning_goal:
        match = _DAILY_GOAL_RE.search(learning_goal)
        if match:
            minutes = int(match.group(1))
            if 1 <= minutes <= 180:
                return minutes
    return 10


def _delete_audio_files(storage, names):
    valid_names = [name for name in names if name]
    if not valid_names:
        return
    if hasattr(storage, "delete_many"):
        storage.delete_many(valid_names)
    else:
        for audio_name in valid_names:
            storage.delete(audio_name)


@login_required
def learner_dashboard(request):
    if request.user.role != User.Role.LEARNER:
        raise PermissionDenied

    today = timezone.localdate()
    published_lessons = list(
        Lesson.objects.filter(is_published=True)
        .annotate(phrase_count=Count("phrases"))
        .only(
            "id",
            "title",
            "slug",
            "situation",
            "summary",
            "estimated_minutes",
            "position",
        )
        .order_by("position", "id")
    )
    published_lesson_ids = [lesson.id for lesson in published_lessons]

    progress_records = (
        list(
            LessonProgress.objects.filter(
                user=request.user,
                lesson_id__in=published_lesson_ids,
                completed_at__isnull=False,
            ).values_list("lesson_id", "completed_at")
        )
        if published_lesson_ids
        else []
    )
    completed_lesson_ids = {lesson_id for lesson_id, _ in progress_records}
    completed_lesson_count = len(completed_lesson_ids)

    practice_records = list(
        PhrasePractice.objects.filter(user=request.user).values_list(
            "phrase__lesson_id", "last_practiced_at"
        )
    )

    attempts = list(
        LessonAttempt.objects.filter(user=request.user)
        .order_by("-attempted_at")
        .values_list("score", "is_correct", "attempted_at", "lesson__title")[:20]
    )
    latest_attempt = attempts[0] if attempts else None

    activity_dates = set()
    minutes_practiced_today = 0
    lesson_minutes_by_id = {
        lesson.id: lesson.estimated_minutes for lesson in published_lessons
    }
    completed_today_ids = set()
    for lesson_id, completed_at in progress_records:
        if completed_at:
            completed_date = timezone.localtime(completed_at).date()
            activity_dates.add(completed_date)
            if completed_date == today:
                completed_today_ids.add(lesson_id)
                minutes_practiced_today += lesson_minutes_by_id.get(lesson_id, 5)

    practiced_count_by_lesson = {}
    for lesson_id, practiced_at in practice_records:
        practiced_count_by_lesson[lesson_id] = (
            practiced_count_by_lesson.get(lesson_id, 0) + 1
        )
        if practiced_at:
            practiced_date = timezone.localtime(practiced_at).date()
            activity_dates.add(practiced_date)
            if practiced_date == today and lesson_id not in completed_today_ids:
                minutes_practiced_today += 2

    for _, _, attempted_at, _ in attempts:
        if attempted_at:
            activity_dates.add(timezone.localtime(attempted_at).date())

    daily_goal_target = _extract_daily_goal_minutes(request.user)
    daily_goal_percent = min(
        100, round(minutes_practiced_today / daily_goal_target * 100)
    )
    streak_days = _calculate_streak_days(activity_dates, today)
    xp_points = (completed_lesson_count * 20) + (len(practice_records) * 5)

    milestones = []
    if practice_records:
        milestones.append("First Phrase Practiced")
    if completed_lesson_count >= 1:
        milestones.append("First Lesson Complete")
    if any(is_correct for _, is_correct, _, _ in attempts):
        milestones.append("Checkpoint Passed")
    if minutes_practiced_today >= daily_goal_target:
        milestones.append("Daily Goal Reached")
    if published_lessons and completed_lesson_count >= len(published_lessons):
        milestones.append("Trail Finisher")
    achievements_count = len(milestones)
    latest_achievement = milestones[-1] if milestones else ""

    current_lesson = next(
        (lesson for lesson in published_lessons if lesson.id not in completed_lesson_ids),
        published_lessons[0] if published_lessons else None,
    )

    trail_steps = []
    current_found = False
    previous_title = ""
    for index, lesson in enumerate(published_lessons, start=1):
        is_completed = lesson.id in completed_lesson_ids
        phrase_total = lesson.phrase_count or 5
        practiced_in_lesson = practiced_count_by_lesson.get(lesson.id, 0)
        if is_completed:
            state = "completed"
            detail = f"Completed · {phrase_total} phrases · +20 XP"
        elif not current_found:
            current_found = True
            state = "current"
            if practiced_in_lesson:
                detail = f"In progress · {practiced_in_lesson}/{phrase_total} phrases practiced · +20 XP"
            else:
                prefix = "Next up" if completed_lesson_count else "Start here"
                detail = f"{prefix} · {phrase_total} phrases · +20 XP"
        else:
            state = "locked"
            if previous_title:
                detail = f"Complete {previous_title} to unlock · {phrase_total} phrases"
            else:
                detail = lesson.summary
        previous_title = lesson.title
        trail_steps.append(
            {
                "number": f"{index:02d}",
                "title": lesson.title,
                "situation": lesson.situation,
                "detail": detail,
                "state": state,
                "url": lesson.slug,
                "is_completed": is_completed,
            }
        )

    up_next_lesson = next(
        (
            lesson
            for lesson in published_lessons
            if lesson.id not in completed_lesson_ids
            and (not current_lesson or lesson.id != current_lesson.id)
        ),
        None,
    )
    if up_next_lesson:
        up_next_title = up_next_lesson.title
        up_next_description = (
            f"{up_next_lesson.summary} Unlock it after {current_lesson.title}."
            if current_lesson
            else up_next_lesson.summary
        )
        up_next_url = reverse("core:lesson_detail", kwargs={"slug": up_next_lesson.slug})
    elif current_lesson and current_lesson.id not in completed_lesson_ids:
        up_next_title = current_lesson.title
        up_next_description = current_lesson.summary
        up_next_url = reverse("core:lesson_detail", kwargs={"slug": current_lesson.slug})
    else:
        up_next_title = "Explore the Phrasebook"
        up_next_description = "You completed every lesson in the trail! Review phrases or request a new one."
        up_next_url = reverse("core:phrasebook")

    if minutes_practiced_today >= daily_goal_target:
        bito_heading = "You hit today’s goal!"
        bito_copy = "Maayo kaayo! Keep practicing at your own pace or review your favorite phrases."
    elif completed_lesson_count > 0 or practice_records:
        bito_heading = "Small steps add up fast."
        bito_copy = "You’re building real Cebuano confidence. Pick up your next phrase whenever you’re ready."
    else:
        bito_heading = "Every expert starts with hello."
        bito_copy = "I’m Bito, your friendly guide. Listen first, try it aloud, and don’t worry about getting it perfect."

    total_lesson_target = len(published_lessons)

    return render(
        request,
        "core/learner_dashboard.html",
        {
            "completed_lesson_count": completed_lesson_count,
            "total_lesson_target": total_lesson_target,
            "all_lessons_completed": bool(
                published_lessons and completed_lesson_count >= len(published_lessons)
            ),
            "streak_days": streak_days,
            "xp_points": xp_points,
            "minutes_practiced_today": minutes_practiced_today,
            "daily_goal_target": daily_goal_target,
            "daily_goal_percent": daily_goal_percent,
            "recent_quiz_score": latest_attempt[0] if latest_attempt else None,
            "recent_quiz_lesson": latest_attempt[3] if latest_attempt else "",
            "achievements_count": achievements_count,
            "latest_achievement": latest_achievement,
            "trail_steps": trail_steps,
            "current_lesson": current_lesson,
            "up_next_title": up_next_title,
            "up_next_description": up_next_description,
            "up_next_url": up_next_url,
            "bito_heading": bito_heading,
            "bito_copy": bito_copy,
            "show_welcome_banner": completed_lesson_count == 0 and not practice_records,
        },
    )


@login_required
def admin_dashboard(request):
    if request.user.role != User.Role.ADMIN:
        raise PermissionDenied
    learner_count = User.objects.filter(role=User.Role.LEARNER).count()
    lesson_completion_count = LessonProgress.objects.filter(
        completed_at__isnull=False
    ).count()
    avg_score = LessonAttempt.objects.aggregate(avg=Avg("score"))["avg"]
    pending_requests_count = PhraseRequest.objects.filter(
        status=PhraseRequest.Status.PENDING
    ).count()
    return render(
        request,
        "core/admin_dashboard.html",
        {
            "learner_count": learner_count,
            "lesson_completion_count": lesson_completion_count,
            "quiz_average_score": round(avg_score) if avg_score is not None else None,
            "pending_requests_count": pending_requests_count,
        },
    )


def _require_role(request, role):
    if request.user.role != role:
        raise PermissionDenied


@login_required
def lesson_list(request):
    _require_role(request, User.Role.LEARNER)
    category = None
    lessons = Lesson.objects.none()
    category_slug = request.GET.get("category", "")
    if category_slug:
        category = get_object_or_404(
            LessonCategory.objects.filter(
                Exists(
                    Lesson.objects.filter(category_id=OuterRef("pk"), is_published=True)
                )
            ),
            slug=category_slug,
        )
        lessons = (
            Lesson.objects.filter(is_published=True, category=category)
            .only("id", "title", "slug", "situation", "summary", "position")
            .order_by("position", "title")
        )
        categories = []
        published_lesson_count = 0
        completed_lesson_count = 0
        lesson_progress_percent = 0
    else:
        first_lesson_summary = Subquery(
            Lesson.objects.filter(is_published=True, category=OuterRef("pk"))
            .order_by("position", "title")
            .values("summary")[:1]
        )
        categories = list(
            LessonCategory.objects.annotate(
                published_count=Count("lessons", filter=Q(lessons__is_published=True)),
                display_description=Case(
                    When(description="", then=first_lesson_summary),
                    default="description",
                ),
            ).filter(published_count__gt=0)
        )
        published_lesson_count = sum(c.published_count for c in categories)
        completed_lesson_count = (
            LessonProgress.objects.filter(
                user=request.user,
                lesson__is_published=True,
                completed_at__isnull=False,
            ).count()
            if published_lesson_count
            else 0
        )
        lesson_progress_percent = (
            round(completed_lesson_count / published_lesson_count * 100)
            if published_lesson_count
            else 0
        )
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
    phrases = list(
        lesson.phrases.annotate(
            is_practiced=Exists(
                PhrasePractice.objects.filter(
                    user=request.user, phrase_id=OuterRef("pk")
                )
            )
        )
    )
    completed_count = 0
    for display_position, phrase in enumerate(phrases, start=1):
        phrase.display_position = display_position
        if phrase.is_practiced:
            completed_count += 1
    requested_phrase_id = request.GET.get("phrase")
    current_phrase = None
    if requested_phrase_id and requested_phrase_id.isdigit():
        target_id = int(requested_phrase_id)
        current_phrase = next((p for p in phrases if p.pk == target_id), None)
    if current_phrase is None:
        current_phrase = next(
            (phrase for phrase in phrases if not phrase.is_practiced),
            phrases[0] if phrases else None,
        )
    next_phrase = None
    if current_phrase and phrases:
        current_idx = next(
            (i for i, p in enumerate(phrases) if p.pk == current_phrase.pk), 0
        )
        next_phrase = next(
            (p for p in phrases[current_idx + 1 :] if not p.is_practiced),
            phrases[(current_idx + 1) % len(phrases)] if len(phrases) > 1 else None,
        )
    progress = (
        LessonProgress.objects.filter(user=request.user, lesson=lesson)
        .only("completed_at")
        .first()
    )
    next_lesson = (
        Lesson.objects.filter(is_published=True)
        .exclude(pk=lesson.pk)
        .filter(Q(position__gt=lesson.position) | Q(position=lesson.position, pk__gt=lesson.pk))
        .order_by("position", "pk")
        .only("title", "slug")
        .first()
        if progress and progress.completed_at
        else None
    )
    last_attempt = (
        LessonAttempt.objects.filter(user=request.user, lesson=lesson)
        .only("selected_answer", "score", "is_correct")
        .first()
        if lesson.checkpoint_question
        else None
    )
    phrase_count = len(phrases)
    practice_percent = round(completed_count / phrase_count * 100) if phrase_count else 0
    return render(
        request,
        "core/lesson_detail.html",
        {
            "lesson": lesson,
            "phrases": phrases,
            "current_phrase": current_phrase,
            "next_phrase": next_phrase,
            "next_lesson": next_lesson,
            "practiced_count": completed_count,
            "phrase_count": phrase_count,
            "practice_percent": practice_percent,
            "progress": progress,
            "last_attempt": last_attempt,
        },
    )


@login_required
@require_POST
def record_phrase_practice(request, slug, phrase_id):
    _require_role(request, User.Role.LEARNER)
    phrase = get_object_or_404(
        LessonPhrase.objects.only("id", "lesson_id"),
        pk=phrase_id,
        lesson__slug=slug,
        lesson__is_published=True,
    )
    now = timezone.now()
    updated = PhrasePractice.objects.filter(
        user=request.user, phrase=phrase
    ).update(
        practice_count=F("practice_count") + 1,
        last_practiced_at=now,
    )
    if not updated:
        try:
            PhrasePractice.objects.create(
                user=request.user, phrase=phrase, practice_count=1
            )
        except IntegrityError:
            PhrasePractice.objects.filter(
                user=request.user, phrase=phrase
            ).update(
                practice_count=F("practice_count") + 1,
                last_practiced_at=now,
            )
    counts = (
        LessonPhrase.objects.filter(lesson_id=phrase.lesson_id)
        .annotate(
            is_practiced=Exists(
                PhrasePractice.objects.filter(
                    user=request.user, phrase_id=OuterRef("pk")
                )
            )
        )
        .aggregate(
            phrase_count=Count("id"),
            practiced_count=Count("id", filter=Q(is_practiced=True)),
        )
    )
    practiced_count = counts["practiced_count"]
    phrase_count = counts["phrase_count"]
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
    lesson = get_object_or_404(
        Lesson.objects.only("id", "slug", "checkpoint_question", "checkpoint_correct_answer"),
        slug=slug,
        is_published=True,
    )
    selected_answer = request.POST.get("selected_answer", "")
    if selected_answer not in {"A", "B"} or not lesson.checkpoint_question:
        messages.error(request, "Choose an answer for this lesson checkpoint.")
        return redirect("core:lesson_detail", slug=lesson.slug)

    is_correct = selected_answer == lesson.checkpoint_correct_answer
    with transaction.atomic():
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
    if is_correct:
        messages.success(request, "Correct! This lesson is now complete.")
    else:
        messages.error(request, "Not quite. Review the phrases and try again.")
    return redirect("core:lesson_detail", slug=lesson.slug)


@login_required
@require_POST
def complete_lesson(request, slug):
    _require_role(request, User.Role.LEARNER)
    lesson = get_object_or_404(
        Lesson.objects.only("id", "slug", "checkpoint_question"),
        slug=slug,
        is_published=True,
    )
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
def phrasebook(request):
    _require_role(request, User.Role.LEARNER)
    search_form = PhraseSearchForm(request.GET or None)
    query = search_form.cleaned_data.get("q", "") if search_form.is_valid() else ""
    category_slug = request.GET.get("category", "")
    categories = list(
        PhraseCategory.objects.annotate(
            published_count=Count("phrases", filter=Q(phrases__is_published=True))
        )
        .filter(published_count__gt=0)
        .only("id", "name", "slug")
        .order_by("name")
    )
    phrases = (
        Phrase.objects.filter(is_published=True)
        .select_related("category")
        .only(
            "id",
            "cebuano_text",
            "english_translation",
            "situation",
            "pronunciation_note",
            "audio",
            "category__name",
        )
    )
    active_category = None
    if category_slug:
        active_category = next(
            (category for category in categories if category.slug == category_slug),
            None,
        )
        if active_category is None:
            raise Http404("No PhraseCategory matches the given query.")
        phrases = phrases.filter(category=active_category).order_by("cebuano_text")
    if query:
        phrases = phrases.filter(
            Q(cebuano_text__icontains=query)
            | Q(english_translation__icontains=query)
            | Q(situation__icontains=query)
            | Q(pronunciation_note__icontains=query)
            | Q(category__name__icontains=query)
        )
    page_obj = Paginator(phrases, 24).get_page(request.GET.get("page"))
    phrase_count = page_obj.paginator.count
    return render(
        request,
        "core/phrasebook.html",
        {
            "search_form": search_form,
            "query": query,
            "categories": categories,
            "active_category": active_category,
            "phrases": page_obj.object_list,
            "page_obj": page_obj,
            "phrase_count": phrase_count,
            "request_count": PhraseRequest.objects.filter(
                submitted_by=request.user, status=PhraseRequest.Status.PENDING
            ).count(),
        },
    )


@login_required
def phrase_request_create(request):
    _require_role(request, User.Role.LEARNER)
    form = PhraseRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        phrase_request = form.save(commit=False)
        phrase_request.submitted_by = request.user
        phrase_request.save()
        messages.success(request, "Your phrase request was sent to the administrator.")
        return redirect("core:phrase_requests")
    return render(request, "core/phrase_request_form.html", {"form": form})


@login_required
def phrase_requests(request):
    _require_role(request, User.Role.LEARNER)
    requests = (
        PhraseRequest.objects.filter(submitted_by=request.user)
        .select_related("created_phrase")
        .only(
            "id",
            "requested_phrase",
            "situation",
            "status",
            "admin_note",
            "created_at",
            "created_phrase__english_translation",
        )
    )
    return render(request, "core/phrase_requests.html", {"phrase_requests": requests})


@login_required
def admin_phrase_list(request):
    _require_role(request, User.Role.ADMIN)
    phrases = Phrase.objects.select_related("category").only(
        "id",
        "cebuano_text",
        "english_translation",
        "situation",
        "is_published",
        "category__name",
    )
    return render(request, "core/admin_phrase_list.html", {"phrases": phrases})


@login_required
def admin_phrase_create(request):
    _require_role(request, User.Role.ADMIN)
    form = PhraseForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        phrase = form.save(commit=False)
        phrase.created_by = request.user
        phrase.save()
        messages.success(request, "Phrase added to the phrasebook.")
        return redirect("core:admin_phrase_list")
    return render(request, "core/phrase_form.html", {"form": form, "heading": "Add phrase"})


@login_required
def admin_phrase_update(request, phrase_id):
    _require_role(request, User.Role.ADMIN)
    phrase = get_object_or_404(Phrase, pk=phrase_id)
    old_audio = phrase.audio.name
    form = PhraseForm(request.POST or None, request.FILES or None, instance=phrase)
    if request.method == "POST" and form.is_valid():
        updated = form.save()
        if old_audio and updated.audio.name != old_audio:
            _delete_audio_files(phrase.audio.storage, [old_audio])
        messages.success(request, "Phrase updated successfully.")
        return redirect("core:admin_phrase_list")
    return render(
        request,
        "core/phrase_form.html",
        {"form": form, "heading": "Edit phrase", "phrase": phrase},
    )


@login_required
@require_POST
def admin_phrase_delete(request, phrase_id):
    _require_role(request, User.Role.ADMIN)
    phrase = get_object_or_404(Phrase, pk=phrase_id)
    old_audio = phrase.audio.name
    storage = phrase.audio.storage
    phrase.delete()
    _delete_audio_files(storage, [old_audio])
    messages.success(request, "Phrase deleted successfully.")
    return redirect("core:admin_phrase_list")


@login_required
def admin_phrase_category_list(request):
    _require_role(request, User.Role.ADMIN)
    categories = PhraseCategory.objects.annotate(phrase_count=Count("phrases"))
    return render(
        request,
        "core/admin_phrase_categories.html",
        {"categories": categories},
    )


@login_required
def admin_phrase_category_create(request):
    _require_role(request, User.Role.ADMIN)
    form = PhraseCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Phrase category created successfully.")
        return redirect("core:admin_phrase_categories")
    return render(
        request,
        "core/phrase_category_form.html",
        {"form": form, "heading": "Add phrase category"},
    )


@login_required
def admin_phrase_category_update(request, category_id):
    _require_role(request, User.Role.ADMIN)
    category = get_object_or_404(PhraseCategory, pk=category_id)
    form = PhraseCategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Phrase category updated successfully.")
        return redirect("core:admin_phrase_categories")
    return render(
        request,
        "core/phrase_category_form.html",
        {"form": form, "heading": "Edit phrase category", "category": category},
    )


@login_required
@require_POST
def admin_phrase_category_delete(request, category_id):
    _require_role(request, User.Role.ADMIN)
    category = get_object_or_404(PhraseCategory, pk=category_id)
    try:
        category.delete()
    except ProtectedError:
        messages.error(request, "This category still has phrases. Move or delete them first.")
    else:
        messages.success(request, "Phrase category deleted successfully.")
    return redirect("core:admin_phrase_categories")


@login_required
def admin_phrase_requests(request):
    _require_role(request, User.Role.ADMIN)
    status = request.GET.get("status", PhraseRequest.Status.PENDING)
    if status not in PhraseRequest.Status.values:
        status = PhraseRequest.Status.PENDING
    requests = (
        PhraseRequest.objects.filter(status=status)
        .select_related("submitted_by")
        .only(
            "id",
            "requested_phrase",
            "english_translation",
            "situation",
            "created_at",
            "status",
            "submitted_by__username",
        )
    )
    return render(
        request,
        "core/admin_phrase_requests.html",
        {"phrase_requests": requests, "selected_status": status},
    )


@login_required
def admin_phrase_request_review(request, request_id):
    _require_role(request, User.Role.ADMIN)
    phrase_request = get_object_or_404(
        PhraseRequest.objects.select_related("submitted_by"), pk=request_id
    )
    if phrase_request.status != PhraseRequest.Status.PENDING:
        messages.info(request, "This phrase request has already been reviewed.")
        return redirect("core:admin_phrase_requests")
    form = PhraseRequestReviewForm(
        request.POST or None,
        initial={
            "category": phrase_request.requested_category_id,
            "english_translation": phrase_request.english_translation,
        },
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            decision = form.cleaned_data["decision"]
            if decision == PhraseRequest.Status.APPROVED:
                phrase = Phrase.objects.create(
                    category=form.cleaned_data["category"],
                    cebuano_text=phrase_request.requested_phrase,
                    english_translation=form.cleaned_data["english_translation"],
                    situation=phrase_request.situation,
                    created_by=request.user,
                )
                phrase_request.created_phrase = phrase
            phrase_request.status = decision
            phrase_request.admin_note = form.cleaned_data["admin_note"]
            phrase_request.reviewed_by = request.user
            phrase_request.reviewed_at = timezone.now()
            phrase_request.save()
        messages.success(request, "Phrase request reviewed successfully.")
        return redirect("core:admin_phrase_requests")
    return render(
        request,
        "core/admin_phrase_request_review.html",
        {"phrase_request": phrase_request, "form": form},
    )


@login_required
def admin_lesson_list(request):
    _require_role(request, User.Role.ADMIN)
    lessons = Lesson.objects.select_related("category").only(
        "id",
        "title",
        "slug",
        "situation",
        "is_published",
        "position",
        "category__name",
    )
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
        audio_to_delete = list(phrase_audio_to_delete)
        if old_audio and updated.audio.name != old_audio:
            audio_to_delete.append(old_audio)
        _delete_audio_files(lesson.audio.storage, audio_to_delete)
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
    audio_to_delete = list(
        lesson.phrases.exclude(audio="").values_list("audio", flat=True)
    )
    if lesson.audio:
        audio_to_delete.append(lesson.audio.name)
    storage = lesson.audio.storage
    lesson.delete()
    _delete_audio_files(storage, audio_to_delete)
    messages.success(request, "Lesson deleted successfully.")
    return redirect("core:admin_lesson_list")
