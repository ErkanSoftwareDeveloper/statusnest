import os

from celery import Celery


celery_app = Celery(
    "statusnest",
    broker=os.getenv(
        "CELERY_BROKER_URL",
        "redis://redis:6379/0",
    ),
)

celery_app.autodiscover_tasks(["app"])
