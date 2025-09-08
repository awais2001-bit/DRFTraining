from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import ActiveConnection

@shared_task
def close_inactive_connections():
    cutoff = timezone.now() - timedelta(minutes=10)
    inactive_connections = ActiveConnection.objects.filter(last_active__lt=cutoff)
    count = inactive_connections.count()

    # Delete inactive connections
    inactive_connections.delete()
    return f"Closed {count} inactive connections"
