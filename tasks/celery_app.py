from celery import Celery
from celery.schedules import crontab
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'ai_tutor',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'tasks.followup_tasks',
        'tasks.progress_tasks',
        'tasks.notification_tasks'
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    'check-upcoming-lessons': {
        'task': 'tasks.notification_tasks.send_lesson_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'generate-daily-progress': {
        'task': 'tasks.progress_tasks.generate_daily_progress_reports',
        'schedule': crontab(hour=20, minute=0),  # 8 PM daily
    },
    'send-weekly-summary': {
        'task': 'tasks.notification_tasks.send_weekly_summaries',
        'schedule': crontab(day_of_week=0, hour=10, minute=0),  # Sunday 10 AM
    },
    'check-inactive-students': {
        'task': 'tasks.followup_tasks.check_inactive_students',
        'schedule': crontab(hour=14, minute=0),  # 2 PM daily
    },
    'update-ai-news': {
        'task': 'tasks.followup_tasks.fetch_ai_news',
        'schedule': crontab(minute=0),  # Every hour
    },
}

if __name__ == '__main__':
    celery_app.start()