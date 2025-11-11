web: gunicorn disaster_notification.wsgi:application
DJANGO_SETTINGS_MODULE=disaster_notification.settings
worker: DJANGO_SETTINGS_MODULE=disaster_notification.settings celery -A disaster_notification worker --concurrency=4 -l info
beat: DJANGO_SETTINGS_MODULE=disaster_notification.settings celery -A disaster_notification beat -l info