from datetime import datetime

from pydantic import BaseModel, HttpUrl


class MonitorCreate(BaseModel):
    name: str
    url: HttpUrl


class MonitorResponse(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    created_at: datetime


class MonitorUpdate(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None
    is_active: bool | None = None
