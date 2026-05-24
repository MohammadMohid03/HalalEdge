import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func, UUID
from backend.database import Base

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    shares = Column(Numeric(12, 4), nullable=False)
    avg_price = Column(Numeric(12, 2), nullable=False)
    added_at = Column(DateTime, server_default=func.now())
