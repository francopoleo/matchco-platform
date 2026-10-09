from gamification.models import GamificationSettings


class PermissionPolicy:
    model = GamificationSettings

    def user_has_permission(self, user, action):
        return user.is_superuser or user.has_perm(f'gamification.{action}_gamificationsettings')

    def user_has_any_permission(self, user, actions):
        return user.is_superuser or any(self.user_has_permission(user, action) for action in actions)


permission_policy = PermissionPolicy()
