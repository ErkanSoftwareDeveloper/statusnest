from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.auth import router as auth_router

from app.api.deps import get_current_user
from app.models.user import User


app = FastAPI(title="StatusNest")

app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
async def database_health(
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("SELECT 1"))
    return {"database": "ok"}


@app.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }
