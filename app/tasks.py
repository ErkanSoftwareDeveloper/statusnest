import asyncio
import os
from datetime import datetime, timezone

from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.models.check_result import CheckResult
from app.models.incident import Incident
from app.models.monitor import Monitor
from app.services.checker import check_url
from app.worker import celery_app


logger = get_task_logger(__name__)


@celery_app.task
def schedule_monitor_checks():
    database_url = os.environ["DATABASE_SYNC_URL"]

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT id
                    FROM monitors
                    WHERE is_active = TRUE
                    """
                )
            )

            monitor_ids = result.scalars().all()

        for monitor_id in monitor_ids:
            check_monitor_task.delay(monitor_id)

        logger.info(
            "Scheduled %s monitor checks",
            len(monitor_ids),
        )

        return len(monitor_ids)

    finally:
        engine.dispose()


@celery_app.task
def check_monitor_task(monitor_id: int):
    _check_monitor(monitor_id)


def _check_monitor(monitor_id: int):
    engine = create_engine(
        os.environ["DATABASE_SYNC_URL"],
        pool_pre_ping=True,
    )

    WorkerSession = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    try:
        # Monitor
        with WorkerSession() as db:
            monitor = db.execute(
                select(Monitor).where(
                    Monitor.id == monitor_id,
                    Monitor.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if monitor is None:
                return

            url = monitor.url

        # HTTP
        check_data = asyncio.run(check_url(url))

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Check
        with WorkerSession.begin() as db:
            monitor = db.execute(
                select(Monitor)
                .where(
                    Monitor.id == monitor_id,
                    Monitor.is_active.is_(True),
                )
                .with_for_update()
            ).scalar_one_or_none()

            if monitor is None:
                return

            check_result = CheckResult(
                monitor_id=monitor.id,
                status_code=check_data["status_code"],
                response_time_ms=check_data["response_time_ms"],
                is_up=check_data["is_up"],
                checked_at=now,
            )

            db.add(check_result)

            open_incident = db.execute(
                select(Incident).where(
                    Incident.monitor_id == monitor.id,
                    Incident.resolved_at.is_(None),
                )
            ).scalar_one_or_none()

            # DOWN
            if not check_data["is_up"] and open_incident is None:
                db.add(
                    Incident(
                        monitor_id=monitor.id,
                        started_at=now,
                    )
                )

            # UP
            elif check_data["is_up"] and open_incident is not None:
                open_incident.resolved_at = now

    finally:
        engine.dispose()
