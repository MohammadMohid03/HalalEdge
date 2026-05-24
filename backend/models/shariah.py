from sqlalchemy import Column, String, Integer, Numeric, DateTime, func
from backend.database import Base

class ShariahCache(Base):
    __tablename__ = "shariah_cache"

    symbol = Column(String(10), primary_key=True)
    status = Column(String(20), nullable=True)  # Halal / Doubtful / Haram
    score = Column(Integer, nullable=True)
    debt_ratio = Column(Numeric(5, 2), nullable=True)
    haram_revenue = Column(Numeric(5, 2), nullable=True)
    business_type = Column(String(100), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
