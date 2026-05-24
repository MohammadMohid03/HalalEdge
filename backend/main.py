from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import database utilities and models to ensure they are registered on Base.metadata
from backend.database import Base, engine
from backend.models.user import User
from backend.models.portfolio import Holding
from backend.models.watchlist import Watchlist
from backend.models.prediction import Prediction
from backend.models.shariah import ShariahCache

# Import routers
from backend.routers import auth, stocks, portfolio, watchlist, predictions

# Programmatically create all tables if they don't exist
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
except Exception as e:
    print(f"Error initializing database tables: {e}")

app = FastAPI(
    title="NoorInvest API",
    description="Backend API for NoorInvest (HalalEdge) Stock Screener, Portfolio Tracker & AI Predictor",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Supports wildcard for easy local frontend testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under prefix /api
app.include_router(auth.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "NoorInvest API",
        "version": "1.0.0"
    }
