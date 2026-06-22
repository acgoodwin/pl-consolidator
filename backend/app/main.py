import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, wait_for_db

# Import routes
from app.api import documents, balances

# Create tables on startup
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    try:
        await wait_for_db()
        print("✓ Application startup complete")
    except Exception as e:
        print(f"✗ Startup error: {e}")
        raise

    yield

    # Shutdown
    print("✓ Application shutdown")


app = FastAPI(
    title="P&L Consolidator API",
    version="0.1.0",
    description="Extract and consolidate German financial statements (HGB)",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(balances.router)


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": "0.1.0"
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": "P&L Consolidator API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.environment == "development")
    )
