from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=(settings.environment == "development"),
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def wait_for_db(max_attempts=30, delay=1):
    """Wait for database to be available (useful for Docker startup)."""
    import asyncio
    from sqlalchemy import text

    for attempt in range(max_attempts):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✓ Database connection established")
            return True
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"✗ Failed to connect to database after {max_attempts} attempts")
                raise
            print(f"⏳ Database not ready (attempt {attempt + 1}/{max_attempts}), retrying in {delay}s...")
            await asyncio.sleep(delay)
    return False
