from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Story


@shared_task
def delete_expired_stories():
    expired = Story.objects.filter(created__lt=timezone.now() - timedelta(hours=24))
    count = expired.count()
    expired.delete()
    return f"{count} expired stories deleted."
