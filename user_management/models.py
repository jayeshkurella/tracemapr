from django.db import models

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
