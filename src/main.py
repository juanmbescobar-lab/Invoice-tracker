from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.expenses import router as expenses_router
from src.api.sessions import router as sessions_router
from src.api.telegram import router as telegram_router
from src.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


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
