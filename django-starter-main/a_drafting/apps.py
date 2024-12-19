from django.apps import AppConfig


class DraftingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'drafting'


    def ready(self):
        import drafting.signals
