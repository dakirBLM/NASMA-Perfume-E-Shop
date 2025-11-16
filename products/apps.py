from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    def ready(self):
        # Ensure modeltranslation registers translation options before admin loads
        try:
            import products.translation  # noqa: F401
        except Exception:
            # Avoid breaking startup if migrations not applied yet
            pass
