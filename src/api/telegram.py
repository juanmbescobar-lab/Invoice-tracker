from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.services.invoice_service import generate_invoice
from src.services.pdf_service import generate_invoice_pdf
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
    """Generate invoice for a date range and optionally send via Telegram."""
    try:
        if not start:
            today = date.today()
            start = today - timedelta(days=today.weekday())
        if not end:
            end = start + timedelta(days=6)

        result = await generate_invoice(db, start, end)

        pdf_path = generate_invoice_pdf(
            invoice_number=result["invoice"]["invoice_number"],
            lines=result["lines"],
            final_total=result["final_total"],
        )

        if send:
            caption = (
                f"Invoice #{result['invoice']['invoice_number']:03d}\n"
                f"Period: {start} to {end}\n"
                f"Total: ${result['final_total']:.2f} AUD"
            )
            await send_pdf(pdf_path, caption=caption)

        return {
            "message": "Invoice generated" + (" and sent" if send else ""),
            "invoice": result["invoice"],
            "pdf_path": pdf_path,
            "lines": result["lines"],
            "final_total": result["final_total"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
