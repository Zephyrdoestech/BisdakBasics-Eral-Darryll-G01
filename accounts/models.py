from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.db.models.functions import Lower


class AccountUserManager(DjangoUserManager):
    """Create Django superusers with the matching application role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields["role"] = User.Role.ADMIN
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        LEARNER = "LEARNER", "Learner"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.LEARNER,
        db_index=True,
    )

    objects = AccountUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("username"),
                name="accounts_user_username_case_insensitive_unique",
            ),
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_case_insensitive_unique",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Profile(models.Model):
    """Additional editable details associated with one account."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    contact_number = models.CharField(max_length=32, blank=True)
    location = models.CharField(max_length=150, blank=True)
    learning_goal = models.CharField(max_length=160, blank=True)
    bio = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
