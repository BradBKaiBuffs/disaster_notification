from .celery import app as celery_app

# always start celery
__all__ = ('celery_app',)