import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func, UUID
from backend.database import Base

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    added_at = Column(DateTime, server_default=func.now())
