import os

from celery import Celery


celery_app = Celery(
    "statusnest",
    broker=os.environ["CELERY_BROKER_URL"],
    include=["app.tasks"],
)

celery_app.conf.beat_schedule = {
    "check-active-monitors-every-5-minutes": {
        "task": "app.tasks.schedule_monitor_checks",
        "schedule": 300.0,
    },
}
