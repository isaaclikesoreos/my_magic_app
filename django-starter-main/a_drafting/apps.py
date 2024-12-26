from django.apps import AppConfig


class DraftingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_drafting'


    def ready(self):
        import a_drafting.signals
