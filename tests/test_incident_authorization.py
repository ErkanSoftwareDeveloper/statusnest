from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.api.monitors import get_current_user, get_db
from app.db.base import Base
from app.main import app
from app.models.incident import Incident
from app.models.monitor import Monitor
from app.models.user import User


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_incidents():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    SessionTest = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with SessionTest() as session:
        owner = User(
            email="owner@example.com",
            password_hash="fake-password",
        )

        other_user = User(
            email="other@example.com",
            password_hash="fake-password",
        )

        session.add_all([owner, other_user])
        await session.flush()

        monitor = Monitor(
            name="Private Monitor",
            url="https://example.com",
            user_id=owner.id,
            is_active=True,
        )

        session.add(monitor)
        await session.flush()

        incident = Incident(
            monitor_id=monitor.id,
            started_at=datetime(2026, 1, 1, 12, 0, 0),
        )

        session.add(incident)
        await session.commit()

        monitor_id = monitor.id
        other_user_id = other_user.id

    class FakeCurrentUser:
        id = other_user_id

    async def override_get_current_user():
        return FakeCurrentUser()

    async def override_get_db():
        async with SessionTest() as session:
            yield session

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/monitors/{monitor_id}/incidents"
            )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Monitor not found"
        }

    finally:
        app.dependency_overrides = {}
        await engine.dispose()
