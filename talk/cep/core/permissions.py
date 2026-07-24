from publishing.models import Tag
class TagPermissionPolicy:
    """Small Django-compatible policy used by legacy callers."""

    model = Tag

    def user_has_any_permission(self, user, actions):
        return user.is_superuser or user.has_perm('publishing.change_tag')


tag_permission_policy = TagPermissionPolicy()
category_permission_policy = tag_permission_policy
