from django.core.management.base import BaseCommand
from user_management.models import Feature, RoleFeatureAccess

class Command(BaseCommand):
    help = "Seed initial features and role-feature mappings"

    def handle(self, *args, **kwargs):
        features = [
            ("add_missing_person", "Add Missing Person"),
            ("edit_person_data", "Edit Person Data"),
            ("view_data", "View Data"),
            ("match_data", "Match Data"),
            ("confirm_matches", "Confirm Matches"),
            ("reject_matches", "Reject Matches"),
            ("add_unidentified_person", "Add Unidentified Person/Body"),
            ("edit_unidentified_data", "Edit Unidentified Data"),
        ]

        # create/update features
        for code, name in features:
            Feature.objects.update_or_create(code=code, defaults={"name": name})

        mapping = {
            "reporting_person": ["add_missing_person", "edit_person_data", "view_data"],
            "volunteer": ["add_missing_person", "view_data"],
            "family": ["add_missing_person", "edit_person_data", "view_data"],
            "police_station": [f[0] for f in features],
            "medical_staff": ["view_data", "match_data", "confirm_matches", "add_unidentified_person"],
            "anonymous": ["view_data"],
            "admin": [f[0] for f in features],
        }

        for role, allowed_features in mapping.items():
            for feature in Feature.objects.all():
                RoleFeatureAccess.objects.update_or_create(
                    role=role,
                    feature=feature,
                    defaults={"is_allowed": feature.code in allowed_features}
                )

        self.stdout.write(self.style.SUCCESS("✅ Roles & Features seeded successfully"))
