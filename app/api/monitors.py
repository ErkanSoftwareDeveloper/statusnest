from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
