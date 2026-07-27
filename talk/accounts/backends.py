from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Allow users to log in with either username or email"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email first
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Fall back to username lookup
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        # Check password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
