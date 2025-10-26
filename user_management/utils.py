# utils.py
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

    # ✅ Step 1: Check per-user feature access
    user_feature = UserFeatureAccess.objects.filter(
        user=user,
        feature__code=feature_code
    ).first()
    if user_feature is not None:
        return user_feature.is_allowed  # respect per-user override

    # ✅ Step 2: Fallback to role-based access
    user_role = getattr(user, 'user_type', None)
    if not user_role:
        return False

    role_access = RoleFeatureAccess.objects.filter(
        role=user_role,
        feature__code=feature_code,
        is_allowed=True
    ).exists()

    return role_access


from django.contrib.contenttypes.models import ContentType
from user_management.models import UserActivityLog
from django.contrib.auth import get_user_model

User = get_user_model()

def log_user_activity(user, action, description=None, person=None, case_id=None):
    """
    Logs user activity for any action
    """
    try:
        user_name = f"{user.first_name} {user.last_name}".strip() or user.name or user.email_id
        user_role = getattr(user, 'user_type', 'Unknown')

        activity_data = {
            'user': user,
            'user_name': user_name,
            'user_role': user_role,
            'action': action,
            'description': description
        }

        if person:
            activity_data['person'] = person
            activity_data['case_id'] = getattr(person, 'case_id', None)
        elif case_id:
            activity_data['case_id'] = case_id

        UserActivityLog.objects.create(**activity_data)

        return True
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        return False



def get_recent_activities(limit=50, user_id=None):
    """
    Get recent activities with optional user filter
    """
    queryset = UserActivityLog.objects.select_related('user', 'person').order_by('-created_at')

    if user_id:
        queryset = queryset.filter(user_id=user_id)

    return queryset[:limit]


def log_search_activity(user, search_type, filters, results_count=0):
    """
    Logs user search activity with applied filters
    """
    try:
        user_name = f"{user.first_name} {user.last_name}".strip() or user.name or user.email_id
        user_role = getattr(user, 'user_type', 'Unknown')

        # Format filters for display
        filter_display = []
        for key, value in filters.items():
            if value and value != "null" and value != "":
                filter_display.append(f"{key}: {value}")

        filter_text = ", ".join(filter_display) if filter_display else "No filters"

        description = f"Searched {search_type} with filters: {filter_text} | Results: {results_count}"

        UserActivityLog.objects.create(
            user=user,
            user_name=user_name,
            user_role=user_role,
            action='VIEW',  # or 'SEARCH' if you add it to choices
            description=description
        )

        return True
    except Exception as e:
        print(f"Error logging search activity: {str(e)}")
        return False
