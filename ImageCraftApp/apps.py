from django.apps import AppConfig


class ImagecraftappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ImageCraftApp"

    def ready(self):
        import ImageCraftApp.signals
