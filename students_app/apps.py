from django.apps import AppConfig


class StudentsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'students_app'
    
    def ready(self):
        """Import signals when app is ready"""
        import students_app.signals  # noqa