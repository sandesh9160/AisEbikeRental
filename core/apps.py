from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    
    def ready(self):
        # Import signal handlers to ensure they are registered
        # Avoid circular imports by importing within ready()
        import core.signals  # noqa: F401
