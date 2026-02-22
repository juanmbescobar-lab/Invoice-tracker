# ADR-001: Initial Architecture Decisions

**Date:** 2026-02-22
**Status:** Accepted

## Context

We need a personal time-tracking and invoice generation service
for hourly-based work billed at 35 AUD/hour with quarter-hour
rounding.

## Decisions

### Backend: FastAPI
**Chosen over:** Django, Flask
**Why:** Async-native, auto-generates API docs, lightweight.
Django is overkill for a personal tool. Flask lacks native async.

### Database: SQLite
**Chosen over:** PostgreSQL, MySQL
**Why:** Zero configuration, file-based, perfect for single-user.
No need to run a separate database server.
**Trade-off:** Not suitable for multi-user concurrent access,
but this is a personal tool.

### Notifications: Telegram Bot
**Chosen over:** Email (SMTP), SMS, WhatsApp
**Why:** Instant delivery, bidirectional (can reply to prompts),
free, no spam folder issues. Works on mobile natively.

### PDF Generation: WeasyPrint
**Chosen over:** ReportLab, fpdf2
**Why:** Uses HTML/CSS to generate PDFs. We can design invoices
with familiar web tech instead of programmatic coordinates.

### Scheduler: APScheduler
**Chosen over:** system cron, celery
**Why:** Runs inside the app process. No external dependencies.
Works cleanly in Docker where system cron is problematic.

## Consequences

- SQLite DB file needs persistent storage (Docker volume)
- Telegram requires one-time bot setup via @BotFather
- WeasyPrint needs system libraries (cairo, pango) in Docker