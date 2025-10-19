from django.db import models
from django.conf import settings
from Mainapp.models.user import User
class Feature(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class RoleFeatureAccess(models.Model):
    role = models.CharField(max_length=50)  # maps to User.user_type
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    is_allowed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'feature')

    def __str__(self):
        return f"{self.role} -> {self.feature.code} ({'✔' if self.is_allowed else '❌'})"

class UserFeatureAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    is_allowed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'feature')

    def __str__(self):
        return f"{self.user.email_id} -> {self.feature.code} ({'✔' if self.is_allowed else '❌'})"


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('RESTORE', 'Restore'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('REAPPROVE', 'Reapprove'),
        ('SUSPEND', 'Suspend'),
        ('HOLD', 'Hold'),
        ('CHANGE_FROM_APPROVED', 'Change From Approved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    user_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Add this
    user_role = models.CharField(max_length=100, null=True, blank=True)
    person = models.ForeignKey('Mainapp.Person', on_delete=models.SET_NULL, null=True, blank=True)
    case_id = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'user_activity_logs'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action} - {self.created_at}"