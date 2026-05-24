from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class WatchlistBase(BaseModel):
    symbol: str

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistOut(WatchlistBase):
    id: UUID
    user_id: UUID
    added_at: datetime

    class Config:
        from_attributes = True
