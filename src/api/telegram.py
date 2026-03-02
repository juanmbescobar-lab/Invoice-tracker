from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.services.invoice_service import generate_invoice
from src.services.pdf_service import generate_hours_pdf, generate_invoice_pdf
from src.services.telegram_service import send_message, send_pdf

router = APIRouter(prefix="/api", tags=["telegram"])

SessionDep = Depends(get_session)


@router.post("/telegram/test")
async def api_test_telegram():
    """Send a test message to verify Telegram is working."""
    try:
        await send_message("InvoiceTrack is connected! 🧾")
        return {"message": "Test message sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/invoice/generate")
async def api_generate_invoice(
    start: Optional[date] = None,
    end: Optional[date] = None,
    send: bool = True,
    db: AsyncSession = SessionDep,
):
    """Generate invoice and hours table, optionally send via Telegram."""
    try:
        if not start:
            today = date.today()
            start = today - timedelta(days=today.weekday())
        if not end:
            end = start + timedelta(days=6)

        result = await generate_invoice(db, start, end)
        inv_number = result["invoice"]["invoice_number"]
        total_hours = result["invoice"]["total_hours"]

        invoice_pdf = generate_invoice_pdf(
            invoice_number=inv_number,
            lines=result["lines"],
            final_total=result["final_total"],
        )

        hours_pdf = generate_hours_pdf(
            invoice_number=inv_number,
            sessions=result["sessions"],
            total_hours=total_hours,
            rate=settings.hourly_rate,
            total_amount=round(total_hours * settings.hourly_rate, 2),
            date_from=str(start),
            date_to=str(end),
        )

        if send:
            caption = (
                f"✅ Invoice #{inv_number:03d}\n"
                f"Period: {start} to {end}\n"
                f"Hours: {total_hours}h\n"
                f"Total: ${result['final_total']:.2f} AUD"
            )
            await send_pdf(invoice_pdf, caption=caption)
            await send_pdf(
                hours_pdf, caption=f"📊 Hours detail — Invoice #{inv_number:03d}"
            )

        return {
            "message": "Invoice generated" + (" and sent" if send else ""),
            "invoice": result["invoice"],
            "invoice_pdf": invoice_pdf,
            "hours_pdf": hours_pdf,
            "lines": result["lines"],
            "final_total": result["final_total"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
