from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.expenses import router as expenses_router
from src.api.sessions import router as sessions_router
from src.api.telegram import router as telegram_router
from src.core.database import Base, engine
from src.services.scheduler_service import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scheduler = create_scheduler()
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(
    title="InvoiceTrack",
    description="Personal time-tracking and invoice generation service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(sessions_router)
app.include_router(expenses_router)
app.include_router(telegram_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    from src.core.config import settings

    return {
        "app": "InvoiceTrack",
        "version": "0.1.0",
        "environment": settings.app_env,
        "timezone": settings.app_timezone,
        "rate": f"${settings.hourly_rate:.2f} {settings.currency}/hour",
        "telegram_configured": bool(settings.telegram_bot_token),
        "scheduler_day": settings.invoice_day,
        "scheduler_time": f"{settings.invoice_hour}:{settings.invoice_minute:02d}",
    }
