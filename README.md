# InvoiceTrack

Personal time-tracking and invoice generation service for hourly-based work.

## What it does

- Clock-in / Clock-out tracking
- Automatic rounding to nearest quarter-hour (up)
- Weekly invoice PDF generation with consecutive numbering
- Expense/credit tracking
- Telegram notifications every Sunday at 10pm

## Tech Stack

- **Backend:** Python + FastAPI
- **Database:** SQLite
- **PDF Engine:** WeasyPrint
- **Notifications:** Telegram Bot API
- **Scheduler:** APScheduler
- **Container:** Docker
- **CI/CD:** GitHub Actions

## Quick Start

> Coming soon — project in development

## Branching Strategy

- `main` — Production-ready (protected, only via PR)
- `develop` — Integration branch
- `feature/*` — New features
- `fix/*` — Bug fixes
- `chore/*` — Maintenance and config