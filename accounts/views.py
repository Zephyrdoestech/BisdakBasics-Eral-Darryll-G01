from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileForm, RegistrationForm, UsernameOrEmailAuthenticationForm
from .models import Profile


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard_redirect")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error(None, "That username or email is already registered. Please try another.")
            return render(request, "accounts/register.html", {"form": form})
        login(request, user, backend="accounts.backends.UsernameOrEmailBackend")
        messages.success(request, "Your account is ready. Welcome to Bisdak Basics!")
        return redirect("core:dashboard_redirect")

    return render(request, "accounts/register.html", {"form": form})


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = UsernameOrEmailAuthenticationForm
    redirect_authenticated_user = True


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

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "profile": profile_record},
    )
