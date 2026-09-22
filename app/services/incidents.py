from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check_result import CheckResult
from app.models.incident import Incident
from app.models.monitor import Monitor


async def save_check_and_incident(
    db: AsyncSession,
    monitor_id: int,
    check_data: dict,
    *,
    user_id: int | None = None,
    require_active: bool = False,
) -> CheckResult | None:

    statement = (
        select(Monitor)
        .where(Monitor.id == monitor_id)
        .with_for_update()
    )

    if user_id is not None:
        statement = statement.where(
            Monitor.user_id == user_id
        )

    if require_active:
        statement = statement.where(
            Monitor.is_active.is_(True)
        )

    result = await db.execute(statement)
    monitor = result.scalar_one_or_none()

    if monitor is None:
        return None

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    check_result = CheckResult(
        monitor_id=monitor.id,
        status_code=check_data["status_code"],
        response_time_ms=check_data["response_time_ms"],
        is_up=check_data["is_up"],
        checked_at=now,
    )

    db.add(check_result)

    result = await db.execute(
        select(Incident).where(
            Incident.monitor_id == monitor.id,
            Incident.resolved_at.is_(None),
        )
    )

    open_incident = result.scalar_one_or_none()

    if not check_result.is_up and open_incident is None:
        incident = Incident(
            monitor_id=monitor.id,
            started_at=now,
        )

        db.add(incident)

    elif check_result.is_up and open_incident is not None:
        open_incident.resolved_at = now

    await db.commit()
    await db.refresh(check_result)

    return check_result
