from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.config import settings
from src.core.database import async_session
from src.services.invoice_service import generate_invoice
from src.services.pdf_service import generate_invoice_pdf
from src.services.telegram_service import send_message, send_pdf


async def remind_expenses():
    """Send a reminder to add expenses before invoice generation."""
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    await send_message(
        f"🧾 InvoiceTrack Reminder\n\n"
        f"Week: {start} to {end}\n\n"
        f"If you have any expenses this week, add them before 10pm.\n"
        f"The invoice will be generated automatically at 10pm."
    )


async def generate_weekly_invoice():
    """Generate and send the weekly invoice."""
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    async with async_session() as db:
        try:
            result = await generate_invoice(db, start, end)

            pdf_path = generate_invoice_pdf(
                invoice_number=result["invoice"]["invoice_number"],
                lines=result["lines"],
                final_total=result["final_total"],
            )

            caption = (
                f"✅ Invoice #{result['invoice']['invoice_number']:03d}\n"
                f"Period: {start} to {end}\n"
                f"Hours: {result['invoice']['total_hours']}h\n"
                f"Total: ${result['final_total']:.2f} AUD"
            )
            await send_pdf(pdf_path, caption=caption)

        except ValueError as e:
            await send_message(
                f"⚠️ Could not generate invoice.\n"
                f"Reason: {e}\n\n"
                f"Make sure you have completed sessions this week."
            )
        except Exception as e:
            await send_message(f"❌ Error generating invoice: {e}")


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler with weekly jobs."""
    scheduler = AsyncIOScheduler(timezone=settings.app_timezone)

    scheduler.add_job(
        remind_expenses,
        "cron",
        day_of_week=settings.invoice_day,
        hour=settings.invoice_hour - 1,
        minute=settings.invoice_minute,
        id="remind_expenses",
    )

    scheduler.add_job(
        generate_weekly_invoice,
        "cron",
        day_of_week=settings.invoice_day,
        hour=settings.invoice_hour,
        minute=settings.invoice_minute,
        id="generate_invoice",
    )

    return scheduler
