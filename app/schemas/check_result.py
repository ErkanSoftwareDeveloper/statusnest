from datetime import datetime

from pydantic import BaseModel


class CheckResultResponse(BaseModel):
    id: int
    status_code: int | None
    response_time_ms: int
    is_up: bool
    checked_at: datetime
