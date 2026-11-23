from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import Q
from django.db.models.functions import Lower

from .models import User


class ProfileForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Full name")
    email = forms.EmailField(label="Email address")
    contact_number = forms.CharField(max_length=32, required=False, label="Contact number")
    location = forms.CharField(max_length=150, required=False, label="Location")
    learning_goal = forms.CharField(max_length=160, required=False, label="Learning goal")

    def __init__(self, *args, user, profile, **kwargs):
        self.user = user
        self.profile = profile
        kwargs.setdefault("initial", {
            "full_name": user.get_full_name(),
            "email": user.email,
            "contact_number": profile.contact_number,
            "location": profile.location,
            "learning_goal": profile.learning_goal,
        })
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control profile-control"
            field.widget.attrs["autocomplete"] = {
                "full_name": "name",
                "email": "email",
                "contact_number": "tel",
                "location": "address-level2",
            }.get(name, "off")

    def clean_full_name(self):
        name = " ".join(self.cleaned_data["full_name"].split())
        if not name:
            raise ValidationError("Enter your full name.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if email == (self.user.email or "").strip().lower():
            return email
        if (
            User.objects.exclude(pk=self.user.pk)
            .alias(email_lower=Lower("email"), username_lower=Lower("username"))
            .filter(Q(email_lower=email) | Q(username_lower=email))
            .exists()
        ):
            raise ValidationError("This email address is already in use.")
        return email

    def save(self):
        first_name, *remaining_names = self.cleaned_data["full_name"].split(maxsplit=1)
        last_name = remaining_names[0] if remaining_names else ""
        email = self.cleaned_data["email"]
        if (
            self.user.first_name != first_name
            or self.user.last_name != last_name
            or self.user.email != email
        ):
            self.user.first_name = first_name
            self.user.last_name = last_name
            self.user.email = email
            self.user.save(update_fields=("first_name", "last_name", "email"))

        contact_number = self.cleaned_data["contact_number"].strip()
        location = self.cleaned_data["location"].strip()
        learning_goal = self.cleaned_data["learning_goal"].strip()
        if (
            self.profile.contact_number != contact_number
            or self.profile.location != location
            or self.profile.learning_goal != learning_goal
        ):
            self.profile.contact_number = contact_number
            self.profile.location = location
            self.profile.learning_goal = learning_goal
            self.profile.save(
                update_fields=("contact_number", "location", "learning_goal", "updated_at")
            )
        return self.user


class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Username",
        min_length=3,
        max_length=24,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9.]+$",
                message="Use only letters, numbers, and periods.",
            )
        ],
    )
    full_name = forms.CharField(max_length=150, label="Full name")
    email = forms.EmailField(label="Email address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "maria.santos",
            "full_name": "Maria Santos",
            "email": "you@example.com",
            "password1": "At least 8 characters",
            "password2": "Enter your password again",
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["placeholder"] = placeholders.get(name, "")
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["full_name"].widget.attrs["autocomplete"] = "name"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["username"].help_text = "3–24 characters. Letters, numbers and periods."
        self.fields["password1"].help_text = "Use at least 8 characters, including a number."

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        username_lower = username.lower()
        if (
            User.objects.alias(
                username_lower=Lower("username"),
                email_lower=Lower("email"),
            )
            .filter(Q(username_lower=username_lower) | Q(email_lower=username_lower))
            .exists()
        ):
            raise ValidationError("That username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.alias(
                email_lower=Lower("email"),
                username_lower=Lower("username"),
            )
            .filter(Q(email_lower=email) | Q(username_lower=email))
            .exists()
        ):
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_full_name(self):
        full_name = " ".join(self.cleaned_data["full_name"].split())
        if not full_name:
            raise ValidationError("Enter your full name.")
        return full_name

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password and not any(character.isdigit() for character in password):
            raise ValidationError("Include at least one number.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        name_parts = self.cleaned_data["full_name"].split(maxsplit=1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""
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
    remember_me = forms.BooleanField(
        required=False,
        label="Keep me signed in on this browser",
        widget=forms.CheckboxInput(attrs={"class": "login-remember__input"}),
    )


class AdministratorAuthenticationForm(UsernameOrEmailAuthenticationForm):
    """Allow only administrator-role accounts through the admin sign-in link."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role != User.Role.ADMIN:
            raise ValidationError(
                "This sign-in is for administrator accounts.",
                code="invalid_login",
            )
