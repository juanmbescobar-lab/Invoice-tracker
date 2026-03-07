from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.config import settings
from src.core.database import async_session
from src.services.invoice_service import generate_invoice
from src.services.pdf_service import generate_hours_pdf, generate_invoice_pdf
from src.services.petty_cash_service import get_current_balance, get_movements
from src.services.telegram_service import send_message, send_pdf


async def petty_cash_weekly_report():
    """Send a weekly petty cash movements report via Telegram.

    Runs every Sunday before the invoice job. Alerts if balance is negative,
    indicating the shortfall will be compensated in the next invoice.
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    async with async_session() as db:
        try:
            balance = await get_current_balance(db)
            all_movements = await get_movements(db)

            # Filter to movements that occurred this week
            week_movements = [
                m for m in all_movements
                if week_start <= m.date.astimezone(None).date() <= week_end
            ]

            lines = [
                "💰 *Petty Cash — Weekly Report*",
                f"Period: {week_start} → {week_end}",
                "",
            ]

            if week_movements:
                lines.append("*Movements this week:*")
                for m in week_movements:
                    icon = "⬆️" if m.movement_type == "topup" else "⬇️"
                    sign = "+" if m.movement_type == "topup" else "-"
                    desc = f" — {m.description}" if m.description else ""
                    lines.append(
                        f"{icon} {m.movement_type.title()}: "
                        f"{sign}${m.amount:.2f} AUD{desc}"
                    )
                    lines.append(f"   Balance after: ${m.balance_after:.2f} AUD")
            else:
                lines.append("No movements recorded this week.")

            lines.append("")
            balance_line = f"*Closing Balance: ${balance:.2f} AUD*"
            if balance < 0:
                balance_line = f"*Closing Balance: ${balance:.2f} AUD* 🔴"
            lines.append(balance_line)

            if balance < 0:
                lines.append("")
                lines.append("⚠️ *NEGATIVE BALANCE ALERT*")
                lines.append(
                    f"The petty cash fund is short by *${abs(balance):.2f} AUD*."
                )
                lines.append(
                    "This amount will be added to and compensated in the next invoice."
                )

            await send_message("\n".join(lines))

        except Exception as e:
            await send_message(f"❌ Error generating petty cash report: {e}")


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
    """Generate and send the weekly invoice and hours table."""
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    async with async_session() as db:
        try:
            result = await generate_invoice(db, start, end)
            inv_number = result["invoice"]["invoice_number"]
            total_hours = result["invoice"]["total_hours"]

            # Generate invoice PDF
            invoice_pdf = generate_invoice_pdf(
                invoice_number=inv_number,
                lines=result["lines"],
                final_total=result["final_total"],
            )

            # Generate hours table PDF
            hours_pdf = generate_hours_pdf(
                invoice_number=inv_number,
                sessions=result["sessions"],
                total_hours=total_hours,
                rate=settings.hourly_rate,
                total_amount=round(total_hours * settings.hourly_rate, 2),
                date_from=str(start),
                date_to=str(end),
            )

            # Send invoice
            caption = (
                f"✅ Invoice #{inv_number:03d}\n"
                f"Period: {start} to {end}\n"
                f"Hours: {total_hours}h\n"
                f"Total: ${result['final_total']:.2f} AUD"
            )
            await send_pdf(invoice_pdf, caption=caption)

            # Send hours table
            await send_pdf(
                hours_pdf, caption=f"📊 Hours detail — Invoice #{inv_number:03d}"
            )

        except ValueError as e:
            await send_message(
                f"⚠️ Could not generate invoice.\n"
                f"Reason: {e}\n\n"
                f"Make sure you have completed sessions this week."
            )
        except Exception as e:
            await send_message(f"❌ Error generating invoice: {e}")


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler with weekly jobs.

    Sunday timeline (default, configurable via env):
      21:00 — Petty cash weekly report (with negative balance alert)
      21:30 — Expense reminder
      22:00 — Invoice generation + PDF delivery
    """
    scheduler = AsyncIOScheduler(timezone=settings.app_timezone)

    # Petty cash report: 1 hour before the invoice, on the same day
    scheduler.add_job(
        petty_cash_weekly_report,
        "cron",
        day_of_week=settings.invoice_day,
        hour=settings.invoice_hour - 1,
        minute=settings.invoice_minute,
        id="petty_cash_report",
    )

    # Expense reminder: 30 min before the invoice
    scheduler.add_job(
        remind_expenses,
        "cron",
        day_of_week=settings.invoice_day,
        hour=settings.invoice_hour - 1,
        minute=30,
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
