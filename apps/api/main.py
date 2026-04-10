"""FastAPI entrypoint for Phase 0 infrastructure."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.config import settings
from apps.api.routers.documents import router as documents_router
from apps.api.routers.telegram import router as telegram_router

try:
    import structlog

    logger = structlog.get_logger()
except ImportError:  # pragma: no cover - fallback for minimal environments
    import logging

    logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Startup and shutdown hooks."""
    logger.info("app_starting", env=settings.app_env)
    yield
    logger.info("app_shutting_down")


app = FastAPI(
    title="AI Collaboration Coach API",
    description="Phase 0 infrastructure and health endpoints",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telegram_router)
app.include_router(documents_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }


@app.get("/health/db")
async def health_check_db() -> dict[str, str]:
    """PostgreSQL connectivity probe."""
    from sqlalchemy import text

    from packages.db.session import get_engine

    engine = get_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:  # pragma: no cover - runtime integration check
        return {"status": "error", "database": str(exc)}


@app.get("/health/redis")
async def health_check_redis() -> dict[str, str]:
    """Redis connectivity probe."""
    import redis.asyncio as aioredis

    try:
        redis_client = aioredis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.aclose()
        return {"status": "ok", "redis": "connected"}
    except Exception as exc:  # pragma: no cover - runtime integration check
        return {"status": "error", "redis": str(exc)}
