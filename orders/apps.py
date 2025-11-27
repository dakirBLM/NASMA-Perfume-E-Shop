from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    def ready(self):
<<<<<<< HEAD
        import orders.signals
=======
        import orders.signals
>>>>>>> 262ce5adbee25db4f7d2a12bc1b12711e3671eb8
