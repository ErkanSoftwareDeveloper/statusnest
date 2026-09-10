from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.check_result import CheckResult
from app.schemas.check_result import CheckResultResponse

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.monitor import MonitorCreate, MonitorResponse
from fastapi import HTTPException
from app.schemas.monitor import (
    MonitorCreate,
    MonitorResponse,
    MonitorUpdate,
)
from app.models.check_result import CheckResult
from app.services.checker import check_url

router = APIRouter(
    prefix="/monitors",
    tags=["monitors"],
)


@router.post(
    "",
    response_model=MonitorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_monitor(
    data: MonitorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    monitor = Monitor(
        user_id=current_user.id,
        name=data.name,
        url=str(data.url),
    )

    db.add(monitor)
    await db.commit()
    await db.refresh(monitor)

    return monitor


@router.get(
    "",
    response_model=list[MonitorResponse],
)
async def get_monitors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.user_id == current_user.id
        )
    )

    return result.scalars().all()


@router.get(
    "/{monitor_id}",
    response_model=MonitorResponse,
)
async def get_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id,
        )
    )

    monitor = result.scalar_one_or_none()

    if monitor is None:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found",
        )

    return monitor


@router.patch(
    "/{monitor_id}",
    response_model=MonitorResponse,
)
async def update_monitor(
    monitor_id: int,
    data: MonitorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id,
        )
    )

    monitor = result.scalar_one_or_none()

    if monitor is None:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found",
        )

    if data.name is not None:
        monitor.name = data.name

    if data.url is not None:
        monitor.url = str(data.url)

    if data.is_active is not None:
        monitor.is_active = data.is_active

    await db.commit()
    await db.refresh(monitor)

    return monitor


@router.delete(
    "/{monitor_id}",
    status_code=204,
)
async def delete_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id,
        )
    )

    monitor = result.scalar_one_or_none()

    if monitor is None:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found",
        )

    await db.delete(monitor)
    await db.commit()


@router.post("/{monitor_id}/check")
async def check_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id,
        )
    )

    monitor = result.scalar_one_or_none()

    if monitor is None:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found",
        )

    check_data = await check_url(monitor.url)

    check_result = CheckResult(
        monitor_id=monitor.id,
        status_code=check_data["status_code"],
        response_time_ms=check_data["response_time_ms"],
        is_up=check_data["is_up"],
    )

    db.add(check_result)
    await db.commit()
    await db.refresh(check_result)

    return {
        "monitor_id": monitor.id,
        "status_code": check_result.status_code,
        "response_time_ms": check_result.response_time_ms,
        "is_up": check_result.is_up,
        "checked_at": check_result.checked_at,
    }


@router.get(
    "/{monitor_id}/checks",
    response_model=list[CheckResultResponse],
)
async def get_monitor_checks(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id,
        )
    )

    monitor = result.scalar_one_or_none()

    if monitor is None:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found",
        )

    result = await db.execute(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor.id)
        .order_by(CheckResult.checked_at.desc())
    )

    return result.scalars().all()


@router.get("/{monitor_id}/stats")
async def get_monitor_stats(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == current_user.id,
        )
    )

    monitor = result.scalar_one_or_none()

    if monitor is None:
        raise HTTPException(
            status_code=404,
            detail="Monitor not found",
        )

    result = await db.execute(
        select(
            func.count(CheckResult.id),
            func.sum(CheckResult.is_up),
            func.avg(CheckResult.response_time_ms),
        ).where(
            CheckResult.monitor_id == monitor.id
        )
    )

    total_checks, successful_checks, average_response_time = result.one()

    successful_checks = successful_checks or 0

    uptime = (
        (successful_checks / total_checks) * 100
        if total_checks > 0
        else 0
    )

    return {
        "monitor_id": monitor.id,
        "total_checks": total_checks,
        "uptime": round(uptime, 2),
        "average_response_time_ms": (
            round(float(average_response_time), 2)
            if average_response_time is not None
            else 0
        ),
    }
