from django.contrib import messages
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.models import LessonAttempt, LessonProgress, PhrasePractice
from .forms import (
    AdministratorAuthenticationForm,
    ProfileForm,
    RegistrationForm,
    UsernameOrEmailAuthenticationForm,
)
from .models import Profile


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard_redirect")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(None, "That username or email is already registered. Please try another.")
            return render(request, "accounts/register.html", {"form": form})
        messages.success(request, "Your account was created. Please log in to continue.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


class RememberMeLoginMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            self.request.session.set_expiry(0)
        return response


class AccountLoginView(RememberMeLoginMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = UsernameOrEmailAuthenticationForm
    redirect_authenticated_user = True


class AdministratorLoginView(RememberMeLoginMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = AdministratorAuthenticationForm
    redirect_authenticated_user = True
    extra_context = {"is_admin_login": True}


@require_POST
def account_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("core:home")


@login_required
def profile(request):
    profile_record, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, user=request.user, profile=profile_record)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("email", "This email address is already in use.")
        else:
            messages.success(request, "Your profile was saved successfully.")
            return redirect("accounts:profile")

    completed_lessons = list(
        LessonProgress.objects.filter(
            user=request.user,
            lesson__is_published=True,
            completed_at__isnull=False,
        )
        .select_related("lesson")
        .order_by("-completed_at")[:5]
    )
    completed_lesson_count = LessonProgress.objects.filter(
        user=request.user,
        lesson__is_published=True,
        completed_at__isnull=False,
    ).count()
    practiced_phrase_count = PhrasePractice.objects.filter(user=request.user).count()
    latest_attempt = (
        LessonAttempt.objects.filter(user=request.user)
        .select_related("lesson")
        .order_by("-attempted_at")
        .first()
    )
    xp_points = (completed_lesson_count * 20) + (practiced_phrase_count * 5)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "profile": profile_record,
            "completed_lessons": completed_lessons,
            "completed_lesson_count": completed_lesson_count,
            "practiced_phrase_count": practiced_phrase_count,
            "latest_attempt": latest_attempt,
            "xp_points": xp_points,
        },
    )
