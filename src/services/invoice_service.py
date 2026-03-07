from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.expense import Expense
from src.models.invoice import Invoice
from src.models.work_session import WorkSession


async def get_next_invoice_number(db: AsyncSession) -> int:
    """Get the next invoice number based on existing invoices or start number."""
    query = select(func.max(Invoice.invoice_number))
    result = await db.execute(query)
    last = result.scalar_one_or_none()
    if last is None:
        return settings.invoice_start_number
    return last + 1


async def generate_invoice(db: AsyncSession, start: date, end: date) -> dict:
    """Generate an invoice for a date range."""
    # Get sessions
    sessions_query = (
        select(WorkSession)
        .where(
            WorkSession.date >= start,
            WorkSession.date <= end,
            WorkSession.clock_out.is_not(None),
        )
        .order_by(WorkSession.date, WorkSession.clock_in)
    )
    sessions_result = await db.execute(sessions_query)
    sessions = list(sessions_result.scalars().all())

    if not sessions:
        raise ValueError("No completed sessions found for this period.")

    # Calculate hours
    total_hours = sum(s.adjusted_hours for s in sessions)
    hours_amount = round(total_hours * settings.hourly_rate, 2)

    # Get expenses
    expenses_query = (
        select(Expense)
        .where(Expense.date >= start, Expense.date <= end)
        .order_by(Expense.date)
    )
    expenses_result = await db.execute(expenses_query)
    expenses = list(expenses_result.scalars().all())

    # Calculate expense totals
    personal_expenses = [e for e in expenses if e.paid_by == "personal"]
    petty_cash_expenses = [e for e in expenses if e.paid_by == "petty_cash"]

    personal_total = sum(e.amount for e in personal_expenses)
    petty_cash_total = sum(e.amount for e in petty_cash_expenses)

    # Build invoice lines
    lines = []
    lines.append(
        {
            "description": settings.service_description,
            "amount": hours_amount,
        }
    )

    # Add personal expenses as individual lines
    for exp in personal_expenses:
        lines.append(
            {
                "description": exp.description,
                "amount": exp.amount,
            }
        )

    # Credit balance logic
    credit_balance = 0.0
    if (
        petty_cash_total > 0
        and personal_total > 0
        and petty_cash_total < personal_total
    ):
        credit_balance = -petty_cash_total
        lines.append(
            {
                "description": "Credit Balance",
                "amount": credit_balance,
            }
        )
    # Final total
    final_total = round(hours_amount + personal_total + credit_balance, 2)

    # Get next invoice number
    invoice_number = await get_next_invoice_number(db)

    # Save invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        date_from=start,
        date_to=end,
        total_hours=total_hours,
        total_amount=hours_amount,
        expenses_total=round(personal_total + credit_balance, 2),
        final_total=final_total,
        status="draft",
    )
    db.add(invoice)

    # Link expenses to invoice
    for exp in expenses:
        exp.invoice_id = invoice.id

    await db.commit()
    await db.refresh(invoice)

    return {
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice_number,
            "date_from": str(start),
            "date_to": str(end),
            "total_hours": total_hours,
            "rate": settings.hourly_rate,
            "status": invoice.status,
        },
        "lines": lines,
        "final_total": final_total,
        "sessions": [
            {
                "date": str(s.date),
                "clock_in": str(s.clock_in),
                "clock_out": str(s.clock_out),
                "adjusted_hours": s.adjusted_hours,
            }
            for s in sessions
        ],
    }
