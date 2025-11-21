import os
from celery import Celery
from django.conf import settings

# load module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster_notification.settings')

# celery
app = Celery('disaster_notification')

# redis url
app.conf.broker_url = os.getenv('REDIS_URL')

# redis backend
app.conf.result_backend = os.getenv('REDIS_URL')

#celery settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# auto finds tasks
app.autodiscover_tasks()
