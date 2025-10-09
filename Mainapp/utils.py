from Mainapp.models import ChangeLog

# Mainapp/utils.py

def get_current_version():
    try:
        from django.apps import apps
        if apps.ready:  # Only if Django finished loading apps
            ChangeLog = apps.get_model("Mainapp", "ChangeLog")
            last_log = ChangeLog.objects.last()
            return last_log.version if last_log else "v1.0.0"
    except Exception:
        return "v1.0.0"  # Fallback if DB not ready
    return "v1.0.0"
