import os
from celery import Celery

# Celery configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'disaster_notification.settings')

# set app
app = Celery('disaster_notification')
app.config_from_object('django.conf:settings', namespace='CELERY')

# load task modules
app.autodiscover_tasks

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')