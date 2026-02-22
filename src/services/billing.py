import math
from datetime import datetime

from src.core.config import settings


def round_up_quarter(hours: float) -> float:
    """Round hours up to nearest quarter (0.25)"""
    return math.ceil(hours * 4) / 4


def calculate_hours(clock_in: datetime, clock_out: datetime) -> float:
    """Calculate raw hours between two timestamps"""

    delta = clock_out - clock_in
    return delta.total_seconds() / 3600


def calculate_session_total(clock_in: datetime, clock_out: datetime) -> dict:
    """Calculate billing for a single work session"""
    raw_hours = calculate_hours(clock_in, clock_out)
    adjusted_hours = round_up_quarter(raw_hours)
    total = adjusted_hours * settings.hourly_rate

    return {
        "clock_in": clock_in,
        "clock_out": clock_out,
        "raw_hours": round(raw_hours, 4),
        "adjusted_hours": adjusted_hours,
        "rate": settings.hourly_rate,
        "total": round(total, 2),
    }
