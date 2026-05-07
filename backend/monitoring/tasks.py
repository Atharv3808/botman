from celery import shared_task
from .models import SystemLog

@shared_task
def log_system_event_async(level, category, message, metadata):
    """
    Logs a system event to the database asynchronously.
    """
    try:
        SystemLog.objects.create(
            level=level,
            category=category,
            message=message,
            metadata=metadata
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to write to SystemLog in task: {e}")
