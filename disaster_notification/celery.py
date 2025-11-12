import os
from celery import Celery
from django.conf import settings

# Celery configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster_notification.settings')

# set app
app = Celery('disaster_notification')

app.conf.broker_url = os.getenv('REDIS_URL')

app.conf.result_backend = os.getenv('REDIS_URL')

app.config_from_object('django.conf:settings', namespace='CELERY')

# load task modules
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')