from datetime import date, timedelta
from datetime import time as time_type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.services.session_service import (
    clock_in,
    clock_out,
    create_session,
    delete_session,
    get_active_session,
    get_sessions_by_date_range,
    update_session,
)

router = APIRouter(prefix="/api", tags=["sessions"])

SessionDep = Depends(get_session)


class SessionCreate(BaseModel):
    date: date
    clock_in: time_type
    clock_out: time_type | None = None


class SessionUpdate(BaseModel):
    date: date
    clock_in: time_type
    clock_out: time_type | None = None


@router.post("/clock-in")
async def api_clock_in(db: AsyncSession = SessionDep):
    try:
        session = await clock_in(db)
        return {
            "message": "Clocked in successfully",
            "session": {
                "id": session.id,
                "date": str(session.date),
                "clock_in": str(session.clock_in),
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/clock-out")
async def api_clock_out(db: AsyncSession = SessionDep):
    try:
        session = await clock_out(db)
        return {
            "message": "Clocked out successfully",
            "session": {
                "id": session.id,
                "date": str(session.date),
                "clock_in": str(session.clock_in),
                "clock_out": str(session.clock_out),
                "raw_hours": session.raw_hours,
                "adjusted_hours": session.adjusted_hours,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/sessions/active")
async def api_active_session(db: AsyncSession = SessionDep):
    session = await get_active_session(db)
    if not session:
        return {"active": False}
    return {
        "active": True,
        "session": {
            "id": session.id,
            "date": str(session.date),
            "clock_in": str(session.clock_in),
        },
    }


@router.get("/sessions")
async def api_get_sessions(
    start: date | None = None,
    end: date | None = None,
    db: AsyncSession = SessionDep,
):
    if not start:
        today = date.today()
        start = today - timedelta(days=today.weekday())
    if not end:
        end = start + timedelta(days=6)

    sessions = await get_sessions_by_date_range(db, start, end)
    return {
        "start": str(start),
        "end": str(end),
        "count": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "date": str(s.date),
                "clock_in": str(s.clock_in),
                "clock_out": str(s.clock_out) if s.clock_out else None,
                "raw_hours": s.raw_hours,
                "adjusted_hours": s.adjusted_hours,
            }
            for s in sessions
        ],
    }


@router.post("/sessions")
async def api_create_session(body: SessionCreate, db: AsyncSession = SessionDep):
    try:
        session = await create_session(db, body.date, body.clock_in, body.clock_out)
        return {
            "message": "Session created successfully",
            "session": {
                "id": session.id,
                "date": str(session.date),
                "clock_in": str(session.clock_in),
                "clock_out": str(session.clock_out) if session.clock_out else None,
                "raw_hours": session.raw_hours,
                "adjusted_hours": session.adjusted_hours,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/sessions/{session_id}")
async def api_update_session(
    session_id: int, body: SessionUpdate, db: AsyncSession = SessionDep
):
    try:
        session = await update_session(
            db, session_id, body.date, body.clock_in, body.clock_out
        )
        return {
            "message": "Session updated successfully",
            "session": {
                "id": session.id,
                "date": str(session.date),
                "clock_in": str(session.clock_in),
                "clock_out": str(session.clock_out) if session.clock_out else None,
                "raw_hours": session.raw_hours,
                "adjusted_hours": session.adjusted_hours,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: int, db: AsyncSession = SessionDep):
    try:
        await delete_session(db, session_id)
        return {"message": f"Session {session_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
