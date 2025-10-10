from .models import RoleFeatureAccess, UserFeatureAccess

def has_feature_access(user, feature_code: str) -> bool:
    """
    Returns True if the user has access to the given feature.
    Priority:
      1. UserFeatureAccess (per-user overrides)
      2. RoleFeatureAccess (role-based access)
    """

    # Not logged in → no access
    if not user or not user.is_authenticated:
        return False

    # Superuser always allowed
    if user.is_superuser:
        return True

    #  Step 1: Check per-user feature access
    user_feature = UserFeatureAccess.objects.filter(
        user=user,
        feature__code=feature_code
    ).first()
    if user_feature is not None:
        return user_feature.is_allowed  # respect per-user override

    #  Step 2: Fallback to role-based access
    user_role = getattr(user, 'user_type', None)
    if not user_role:
        return False

    role_access = RoleFeatureAccess.objects.filter(
        role=user_role,
        feature__code=feature_code,
        is_allowed=True
    ).exists()

    return role_access

