"""
Celery configuration
"""

import os
from celery import Celery

# 1. Point to the Level 2 settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

app = Celery('AgriGenie')

# 2. Load config from settings.py (looks for CELERY_ variables)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 3. Auto-discover tasks in all apps (and the local tasks.py)
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')