web: gunicorn disaster_notification.wsgi:application
worker: DJANGO_SETTINGS_MODULE=disaster_notification.settings celery -A disaster_notification worker -l info --concurrency=4
beat: DJANGO_SETTINGS_MODULE=disaster_notification.settings celery -A disaster_notification beat -l info