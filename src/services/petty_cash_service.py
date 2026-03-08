from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.petty_cash import PettyCash


async def get_current_balance(db: AsyncSession) -> float:
    """Get the latest petty cash balance."""
    query = select(PettyCash).order_by(desc(PettyCash.id)).limit(1)
    result = await db.execute(query)
    last = result.scalar_one_or_none()
    return last.balance_after if last else 0.0


async def topup(db: AsyncSession, amount: float, description: str = "") -> PettyCash:
    """Add funds to petty cash."""
    if amount <= 0:
        raise ValueError("Topup amount must be positive.")

    current = await get_current_balance(db)
    movement = PettyCash(
        movement_type="topup",
        amount=amount,
        balance_after=current + amount,
        description=description,
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement


async def spend(
    db: AsyncSession, amount: float, description: str
) -> tuple[float, float]:
    """Spend from petty cash. Returns (petty_cash_spent, remainder).

    Only spends what is available (up to the current balance). The remainder
    is the portion not covered by petty cash and should be treated as a
    personal expense. Balance never goes below zero.
    """
    if amount <= 0:
        raise ValueError("Spend amount must be positive.")

    current = await get_current_balance(db)
    petty_cash_spent = round(min(amount, max(current, 0.0)), 2)
    remainder = round(amount - petty_cash_spent, 2)

    if petty_cash_spent > 0:
        movement = PettyCash(
            movement_type="expense",
            amount=petty_cash_spent,
            balance_after=round(current - petty_cash_spent, 2),
            description=description,
        )
        db.add(movement)
        await db.commit()
        await db.refresh(movement)

    return petty_cash_spent, remainder


async def get_movements(db: AsyncSession) -> list[PettyCash]:
    """Get all petty cash movements."""
    query = select(PettyCash).order_by(PettyCash.id)
    result = await db.execute(query)
    return list(result.scalars().all())
