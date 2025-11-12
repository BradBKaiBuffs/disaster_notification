web: gunicorn disaster_notification.wsgi
worker: celery -A disaster_notification worker -l info --concurrency=3
beat: celery -A disaster_notification beat -l info