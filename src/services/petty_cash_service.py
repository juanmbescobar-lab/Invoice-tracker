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


async def spend(db: AsyncSession, amount: float, description: str) -> PettyCash:
    """Spend from petty cash. Balance may go negative if funds are insufficient."""
    if amount <= 0:
        raise ValueError("Spend amount must be positive.")

    current = await get_current_balance(db)
    movement = PettyCash(
        movement_type="expense",
        amount=amount,
        balance_after=round(current - amount, 2),
        description=description,
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement


async def get_movements(db: AsyncSession) -> list[PettyCash]:
    """Get all petty cash movements."""
    query = select(PettyCash).order_by(PettyCash.id)
    result = await db.execute(query)
    return list(result.scalars().all())
