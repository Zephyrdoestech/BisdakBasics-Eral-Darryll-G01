from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    """Authenticate by case-insensitive username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if not username or password is None:
            return None

        user_model = get_user_model()
        identifier = username.strip()
        try:
            user = user_model._default_manager.get(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            )
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            # Do the same password hash work for unknown identifiers to reduce
            # timing differences between valid and invalid account names.
            user_model().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
