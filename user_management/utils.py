from .models import RoleFeatureAccess

def has_feature_access(user, feature_code: str) -> bool:
    """
    Returns True if the user has access to the given feature.
    """
    if not user.is_authenticated:
        return False

    user_role = getattr(user, 'user_type', None)
    if not user_role:
        return False

    return RoleFeatureAccess.objects.filter(
        role=user_role,
        feature__code=feature_code,
        is_allowed=True
    ).exists()
