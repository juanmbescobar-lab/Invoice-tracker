from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, async_session, engine
from src.services.petty_cash_service import get_weekly_summary, spend, topup


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db():
    async with async_session() as session:
        yield session


async def test_weekly_summary_empty_week(db: AsyncSession):
    today = date.today()
    summary = await get_weekly_summary(db, today, today)
    assert summary["topups_total"] == 0.0
    assert summary["expenses_total"] == 0.0
    assert summary["net_change"] == 0.0
    assert summary["current_balance"] == 0.0
    assert summary["movements"] == []


async def test_weekly_summary_with_movements(db: AsyncSession):
    await topup(db, 100.00, "Recarga jefe")
    await spend(db, 50.00, "Bunnings")
    await spend(db, 25.00, "Bolsas")

    today = date.today()
    summary = await get_weekly_summary(db, today, today)

    assert summary["topups_total"] == 100.00
    assert summary["expenses_total"] == 75.00
    assert summary["net_change"] == 25.00
    assert summary["current_balance"] == 25.00
    assert len(summary["movements"]) == 3


async def test_weekly_summary_topups_vs_expenses(db: AsyncSession):
    """net_change = topups - expenses."""
    await topup(db, 200.00, "Carga grande")
    await spend(db, 80.00, "Ferreteria")

    today = date.today()
    summary = await get_weekly_summary(db, today, today)

    assert summary["topups_total"] == 200.00
    assert summary["expenses_total"] == 80.00
    assert summary["net_change"] == 120.00


async def test_weekly_summary_excludes_out_of_range_movements(db: AsyncSession):
    """Movements outside the date range are not included in totals or list."""
    await topup(db, 100.00, "Recarga")
    await spend(db, 40.00, "Compra")

    yesterday = date.today() - timedelta(days=1)
    summary = await get_weekly_summary(db, yesterday, yesterday)

    assert summary["topups_total"] == 0.0
    assert summary["expenses_total"] == 0.0
    assert summary["movements"] == []
    # current_balance still reflects all-time balance
    assert summary["current_balance"] == 60.00


async def test_weekly_summary_monday_to_sunday_range(db: AsyncSession):
    """get_weekly_summary uses an inclusive Monday–Sunday range."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday

    await topup(db, 100.00, "Recarga semana")
    await spend(db, 30.00, "Bunnings")

    summary = await get_weekly_summary(db, week_start, week_end)

    assert summary["topups_total"] == 100.00
    assert summary["expenses_total"] == 30.00
    assert summary["net_change"] == 70.00
    assert len(summary["movements"]) == 2


async def test_weekly_summary_movements_structure(db: AsyncSession):
    await topup(db, 50.00, "Recarga")
    await spend(db, 20.00, "Bolsas")

    today = date.today()
    summary = await get_weekly_summary(db, today, today)

    assert summary["movements"][0]["type"] == "topup"
    assert summary["movements"][0]["amount"] == 50.00
    assert summary["movements"][0]["description"] == "Recarga"
    assert summary["movements"][1]["type"] == "expense"
    assert summary["movements"][1]["amount"] == 20.00
    assert summary["movements"][1]["description"] == "Bolsas"
