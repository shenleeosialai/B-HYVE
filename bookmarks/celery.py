import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")

app = Celery("your_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.timezone = 'Africa/Nairobi'

app.conf.beat_schedule = {
    'delete-expired-stories-every-hour': {
        'task': 'stories.tasks.delete_expired_stories',
        'schedule': crontab(minute=0, hour='*'),
    },
}
