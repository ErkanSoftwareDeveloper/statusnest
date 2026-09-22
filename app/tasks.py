import os
import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.services.checker import check_url
from app.services.incidents import save_check_and_incident
from app.worker import celery_app
from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, text

logger = get_task_logger(__name__)


@celery_app.task
def schedule_monitor_checks():
    database_url = os.environ["DATABASE_SYNC_URL"]

    engine = create_engine(database_url, pool_pre_ping=True)

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
    asyncio.run(_check_monitor(monitor_id))


async def _check_monitor(monitor_id: int):
    async with SessionLocal() as db:
        result = await db.execute(
            select(Monitor).where(
                Monitor.id == monitor_id,
                Monitor.is_active.is_(True),
            )
        )

        url = result.scalar_one_or_none()
    if url is None:
        return

    check_data = await check_url(url.url)

    async with SessionLocal() as db:
        await save_check_and_incident(db, monitor_id, check_data, require_active=True,)

        monitor = result.scalar_one_or_none()

        if monitor is None:
            return

        check_data = await check_url(monitor.url)

        check_result = CheckResult(
            monitor_id=monitor.id,
            status_code=check_data["status_code"],
            response_time_ms=check_data["response_time_ms"],
            is_up=check_data["is_up"],
        )

        db.add(check_result)
        await db.commit()
