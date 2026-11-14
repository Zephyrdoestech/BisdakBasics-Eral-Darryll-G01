from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import User


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    email = forms.EmailField(label="Email address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Choose a username",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "you@example.com",
            "password1": "Create a password",
            "password2": "Enter your password again",
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["placeholder"] = placeholders.get(name, "")
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).exists():
            raise ValidationError("That username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = User.Role.LEARNER
        if commit:
            user.save()
            self.save_m2m()
        return user


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Invalid username or email, or password. Please try again.",
        "inactive": "This account is inactive.",
    }
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "class": "form-control",
                "placeholder": "Your username or email",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "form-control",
                "placeholder": "Your password",
            }
        ),
    )
