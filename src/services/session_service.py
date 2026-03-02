from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.work_session import WorkSession
from src.services.billing import calculate_hours, round_up_quarter


def now_local() -> datetime:
    """Get current datetime in configured timezone."""
    return datetime.now(ZoneInfo(settings.app_timezone))


async def get_active_session(db: AsyncSession) -> WorkSession | None:
    """Find a session with clock_in but no clock_out."""
    query = select(WorkSession).where(WorkSession.clock_out.is_(None))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def clock_in(db: AsyncSession) -> WorkSession:
    """Start a new work session."""
    active = await get_active_session(db)
    if active:
        raise ValueError("Already clocked in. Clock out first.")

    now = now_local()
    session = WorkSession(
        date=now.date(),
        clock_in=now.time(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def clock_out(db: AsyncSession) -> WorkSession:
    """End the active work session."""
    active = await get_active_session(db)
    if not active:
        raise ValueError("No active session. Clock in first.")

    now = now_local()
    clock_in_dt = datetime.combine(active.date, active.clock_in)
    clock_out_dt = datetime.combine(now.date(), now.time())

    raw = calculate_hours(clock_in_dt, clock_out_dt)
    adjusted = round_up_quarter(raw)

    active.clock_out = now.time()
    active.raw_hours = round(raw, 4)
    active.adjusted_hours = adjusted

    await db.commit()
    await db.refresh(active)
    return active


async def get_sessions_by_date_range(db, start, end):
    """Get all sessions within a date range."""
    query = (
        select(WorkSession)
        .where(WorkSession.date >= start, WorkSession.date <= end)
        .order_by(WorkSession.date, WorkSession.clock_in)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
