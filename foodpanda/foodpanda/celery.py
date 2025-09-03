import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodpanda.settings")

app = Celery("foodpanda")

# Load settings from Django, using CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks.py in apps
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    "daily-order-summary": {
        "task": "api.tasks.daily_orders_received",
        "schedule": crontab(hour=23, minute=59),  
    },
}