# events_api_app/apps.py
from django.apps import AppConfig

class EventsApiAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events_api_app'

    def ready(self):
        # Import signals here to avoid AppRegistryNotReady errors
        import events_api_app.signals  # noqa: F401,E402
