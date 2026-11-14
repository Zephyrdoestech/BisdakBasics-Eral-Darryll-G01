from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import RegistrationForm, UsernameOrEmailAuthenticationForm


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
