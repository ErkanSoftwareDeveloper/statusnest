import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.check_result import CheckResult
from app.models.incident import Incident
from app.models.monitor import Monitor
from app.models.user import User
from app.services.incidents import save_check_and_incident


@pytest.mark.asyncio
async def test_incident_opens_stays_open_and_resolves():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    SessionTest = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        async with SessionTest() as session:
            user = User(
                email="incident-test@example.com",
                password_hash="fake-password",
            )

            session.add(user)
            await session.flush()

            monitor = Monitor(
                name="Incident State Test",
                url="https://example.com",
                user_id=user.id,
                is_active=True,
            )

            session.add(monitor)
            await session.commit()

            monitor_id = monitor.id
            user_id = user.id

            # 1. DOWN -> incident açılmalı
            await save_check_and_incident(
                session,
                monitor_id,
                {
                    "status_code": None,
                    "response_time_ms": 25,
                    "is_up": False,
                },
                user_id=user_id,
            )

            result = await session.execute(
                select(Incident).where(
                    Incident.monitor_id == monitor_id
                )
            )

            incidents = result.scalars().all()

            assert len(incidents) == 1
            assert incidents[0].resolved_at is None

            # 2. Tekrar DOWN -> ikinci incident açılmamalı
            await save_check_and_incident(
                session,
                monitor_id,
                {
                    "status_code": None,
                    "response_time_ms": 30,
                    "is_up": False,
                },
                user_id=user_id,
            )

            result = await session.execute(
                select(Incident).where(
                    Incident.monitor_id == monitor_id
                )
            )

            incidents = result.scalars().all()

            assert len(incidents) == 1
            assert incidents[0].resolved_at is None

            # 3. UP -> açık incident kapanmalı
            await save_check_and_incident(
                session,
                monitor_id,
                {
                    "status_code": 200,
                    "response_time_ms": 40,
                    "is_up": True,
                },
                user_id=user_id,
            )

            result = await session.execute(
                select(Incident).where(
                    Incident.monitor_id == monitor_id
                )
            )

            incidents = result.scalars().all()

            assert len(incidents) == 1
            assert incidents[0].resolved_at is not None

            # Her kontrol ayrıca check_results'a yazılmış olmalı
            result = await session.execute(
                select(CheckResult).where(
                    CheckResult.monitor_id == monitor_id
                )
            )

            checks = result.scalars().all()

            assert len(checks) == 3

    finally:
        await engine.dispose()
