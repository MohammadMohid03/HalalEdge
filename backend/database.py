from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings

SQLITE_FALLBACK = "sqlite:///./noorinvest.db"

def _build_engine(url, connect_args=None):
    if connect_args is None:
        connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)

# Try primary database; fallback to SQLite if unreachable
_active_url = settings.DATABASE_URL
try:
    if not _active_url.startswith("sqlite"):
        _test_engine = _build_engine(_active_url)
        with _test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _test_engine.dispose()
        print(f"[database] Connected to PostgreSQL successfully.")
    engine = _build_engine(_active_url)
except Exception as e:
    print(f"[database] PostgreSQL connection failed: {e}")
    print(f"[database] Falling back to local SQLite: {SQLITE_FALLBACK}")
    _active_url = SQLITE_FALLBACK
    engine = _build_engine(_active_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Lightweight startup migrations for columns added after initial deployment
# so existing Render Postgres tables stay compatible without manual ALTER TABLE.
def _run_startup_migrations():
    try:
        with engine.begin() as conn:
            if engine.url.drivername.startswith("postgresql"):
                conn.execute(text("""
                    ALTER TABLE predictions
                    ADD COLUMN IF NOT EXISTS target_bull DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS target_bear DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS details JSONB
                """))
            elif engine.url.drivername.startswith("sqlite"):
                conn.execute(text("""
                    ALTER TABLE predictions
                    ADD COLUMN IF NOT EXISTS target_bull REAL
                """))
                conn.execute(text("""
                    ALTER TABLE predictions
                    ADD COLUMN IF NOT EXISTS target_bear REAL
                """))
                conn.execute(text("""
                    ALTER TABLE predictions
                    ADD COLUMN IF NOT EXISTS details TEXT
                """))
    except Exception as e:
        print(f"[database] Startup migration skipped/already-applied: {e}")

_run_startup_migrations()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
