from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.services.expense_service import add_expense, get_expenses_by_date_range
from src.services.petty_cash_service import get_current_balance, get_movements, topup

router = APIRouter(prefix="/api", tags=["expenses"])

SessionDep = Depends(get_session)


class ExpenseRequest(BaseModel):
    description: str
    amount: float
    paid_by: str = "personal"
    date: Optional[date] = None


class TopupRequest(BaseModel):
    amount: float
    description: str = ""


@router.post("/expenses")
async def api_add_expense(req: ExpenseRequest, db: AsyncSession = SessionDep):
    try:
        expense = await add_expense(
            db,
            description=req.description,
            amount=req.amount,
            paid_by=req.paid_by,
            expense_date=req.date,
        )
        return {
            "message": "Expense registered",
            "expense": {
                "id": expense.id,
                "date": str(expense.date),
                "description": expense.description,
                "amount": expense.amount,
                "paid_by": expense.paid_by,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/expenses")
async def api_get_expenses(
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: AsyncSession = SessionDep,
):
    if not start:
        today = date.today()
        start = today - timedelta(days=today.weekday())
    if not end:
        end = start + timedelta(days=6)

    expenses = await get_expenses_by_date_range(db, start, end)
    return {
        "start": str(start),
        "end": str(end),
        "count": len(expenses),
        "expenses": [
            {
                "id": e.id,
                "date": str(e.date),
                "description": e.description,
                "amount": e.amount,
                "paid_by": e.paid_by,
            }
            for e in expenses
        ],
    }


@router.post("/petty-cash/topup")
async def api_topup(req: TopupRequest, db: AsyncSession = SessionDep):
    try:
        movement = await topup(db, req.amount, req.description)
        return {
            "message": "Petty cash topped up",
            "balance": movement.balance_after,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/petty-cash/balance")
async def api_petty_cash_balance(db: AsyncSession = SessionDep):
    balance = await get_current_balance(db)
    return {"balance": balance}


@router.get("/petty-cash/movements")
async def api_petty_cash_movements(db: AsyncSession = SessionDep):
    movements = await get_movements(db)
    return {
        "count": len(movements),
        "movements": [
            {
                "id": m.id,
                "date": str(m.date),
                "type": m.movement_type,
                "amount": m.amount,
                "balance_after": m.balance_after,
                "description": m.description,
            }
            for m in movements
        ],
    }
