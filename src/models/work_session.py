from datetime import date, time

from sqlalchemy import Date, Float, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class WorkSession(Base):
    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    clock_in: Mapped[time] = mapped_column(Time, nullable=False)
    clock_out: Mapped[time | None] = mapped_column(Time, nullable=True)
    raw_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    adjusted_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
