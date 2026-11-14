from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from accounts.models import User


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
