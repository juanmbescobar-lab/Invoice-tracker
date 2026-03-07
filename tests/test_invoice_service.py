from datetime import date, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, async_session, engine
from src.models.expense import Expense
from src.models.work_session import WorkSession
from src.services.invoice_service import generate_invoice, get_next_invoice_number


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


async def add_session(db: AsyncSession, d: date, cin: time, cout: time, adj: float):
    ws = WorkSession(
        date=d, clock_in=cin, clock_out=cout, raw_hours=adj, adjusted_hours=adj
    )
    db.add(ws)
    await db.commit()


async def add_expense(
    db: AsyncSession, desc: str, amount: float, paid_by: str, d: date
):
    exp = Expense(date=d, description=desc, amount=amount, paid_by=paid_by)
    db.add(exp)
    await db.commit()


async def test_next_invoice_number_starts_from_config(db):
    number = await get_next_invoice_number(db)
    assert number == 1


async def test_generate_simple_invoice(db):
    await add_session(db, date(2026, 3, 2), time(9, 0), time(11, 0), 2.0)
    await add_session(db, date(2026, 3, 3), time(9, 0), time(12, 0), 3.0)

    result = await generate_invoice(db, date(2026, 3, 2), date(2026, 3, 8))

    assert result["invoice"]["invoice_number"] == 1
    assert result["invoice"]["total_hours"] == 5.0
    assert result["final_total"] == 175.00
    assert len(result["lines"]) == 1
    assert result["lines"][0]["description"] == "Laundry and Folding Services"


async def test_invoice_with_personal_expenses(db):
    await add_session(db, date(2026, 3, 2), time(9, 0), time(11, 0), 2.0)
    await add_expense(db, "Bunnings", 83.82, "personal", date(2026, 3, 3))

    result = await generate_invoice(db, date(2026, 3, 2), date(2026, 3, 8))

    assert result["final_total"] == 153.82
    assert len(result["lines"]) == 2
    assert result["lines"][1]["description"] == "Bunnings"


async def test_invoice_with_petty_cash_covers_all(db):
    await add_session(db, date(2026, 3, 2), time(9, 0), time(11, 0), 2.0)
    await add_expense(db, "Bolsas", 20.00, "petty_cash", date(2026, 3, 3))

    result = await generate_invoice(db, date(2026, 3, 2), date(2026, 3, 8))

    # All expenses appear on the invoice regardless of paid_by.
    # 2h * 35 = 70 + 20 (petty cash) = 90
    assert result["final_total"] == 90.00
    assert len(result["lines"]) == 2
    assert result["lines"][1]["description"] == "Bolsas (Petty Cash)"
    assert result["lines"][1]["amount"] == 20.00


async def test_invoice_with_partial_petty_cash(db):
    await add_session(db, date(2026, 3, 2), time(9, 0), time(20, 0), 11.0)
    await add_expense(db, "Bunnings", 83.82, "personal", date(2026, 3, 3))
    await add_expense(db, "Bolsas", 71.00, "petty_cash", date(2026, 3, 3))

    result = await generate_invoice(db, date(2026, 3, 2), date(2026, 3, 8))

    # All expenses are line items. No credit balance deduction.
    # 11h * 35 = 385 + 83.82 + 71.00 = 539.82
    assert result["final_total"] == 539.82
    assert len(result["lines"]) == 3
    assert result["lines"][1]["description"] == "Bunnings"
    assert result["lines"][2]["description"] == "Bolsas (Petty Cash)"
    assert result["lines"][2]["amount"] == 71.00


async def test_no_sessions_raises_error(db):
    with pytest.raises(ValueError, match="No completed sessions"):
        await generate_invoice(db, date(2026, 3, 2), date(2026, 3, 8))


async def test_consecutive_invoice_numbers(db):
    await add_session(db, date(2026, 3, 2), time(9, 0), time(11, 0), 2.0)
    await generate_invoice(db, date(2026, 3, 2), date(2026, 3, 8))

    await add_session(db, date(2026, 3, 9), time(9, 0), time(11, 0), 2.0)
    result = await generate_invoice(db, date(2026, 3, 9), date(2026, 3, 15))

    assert result["invoice"]["invoice_number"] == 2
