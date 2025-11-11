web: gunicorn disaster_notification.wsgi:application
worker: disaster_notification.settings celery -A disaster_notification worker -l info --concurrency=4
beat: disaster_notification.settings celery -A disaster_notification beat -l info