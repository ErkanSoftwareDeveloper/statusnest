
import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.services.checker import check_url
from app.worker import celery_app


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
