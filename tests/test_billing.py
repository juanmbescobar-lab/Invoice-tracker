from datetime import datetime

from src.services.billing import (
    calculate_hours,
    calculate_session_total,
    round_up_quarter,
)


class TestRoundUpQuarter:
    def test_exact_hour(self):
        assert round_up_quarter(2.0) == 2.0

    def test_exact_quarter(self):
        assert round_up_quarter(2.25) == 2.25

    def test_round_up_just_over(self):
        assert round_up_quarter(2.01) == 2.25

    def test_rounds_up_half(self):
        assert round_up_quarter(2.5) == 2.5

    def test_rounds_up_just_over_half(self):
        assert round_up_quarter(2.51) == 2.75

    def test_rounds_up_40_minutes(self):
        # 40 min = 0.667h -> should round to 0.75
        assert round_up_quarter(0.667) == 0.75

    def test_zero(self):
        assert round_up_quarter(0.0) == 0.0


class TestCalculateHours:
    def test_exact_two_hours(self):
        clock_in = datetime(2026, 1, 1, 9, 0)
        clock_out = datetime(2026, 1, 1, 11, 0)
        assert calculate_hours(clock_in, clock_out) == 2.0

    def test_two_hours_forty_minutes(self):
        clock_in = datetime(2026, 1, 1, 9, 0)
        clock_out = datetime(2026, 1, 1, 11, 40)
        result = calculate_hours(clock_in, clock_out)
        assert abs(result - 2.6667) < 0.001


class TestCalculateSessionTotal:
    def test_simple_session(self):
        clock_in = datetime(2026, 1, 1, 9, 0)
        clock_out = datetime(2026, 1, 1, 11, 0)
        result = calculate_session_total(clock_in, clock_out)

        assert result["raw_hours"] == 2.0
        assert result["adjusted_hours"] == 2.0
        assert result["rate"] == 35.00
        assert result["total"] == 70.00

    def test_session_with_rounding(self):
        clock_in = datetime(2026, 1, 1, 9, 0)
        clock_out = datetime(2026, 1, 1, 11, 40)
        result = calculate_session_total(clock_in, clock_out)

        assert result["adjusted_hours"] == 2.75
        assert result["total"] == 96.25
