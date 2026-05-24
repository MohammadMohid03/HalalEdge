import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, UUID
from backend.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), nullable=False)
    verdict = Column(String(10), nullable=True)  # BUY / HOLD / AVOID
    confidence = Column(Integer, nullable=True)
    lstm_score = Column(Integer, nullable=True)
    sentiment = Column(Integer, nullable=True)
    shariah_score = Column(Integer, nullable=True)
    ensemble = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
