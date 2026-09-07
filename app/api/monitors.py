from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.monitor import MonitorCreate, MonitorResponse


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
