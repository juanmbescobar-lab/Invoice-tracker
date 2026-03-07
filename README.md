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
- **Frontend:** Vanilla HTML5 / CSS3 / JavaScript (served by FastAPI)
- **Database:** SQLite
- **PDF Engine:** WeasyPrint
- **Notifications:** Telegram Bot API
- **Scheduler:** APScheduler
- **Container:** Docker
- **CI/CD:** GitHub Actions

## Quick Start

### Prerequisites

- Docker & Docker Compose, **or** Python 3.11+ with `uv` / `pip`
- (Optional) A Telegram Bot token + chat ID for invoice delivery

### With Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/juanmbescobar-lab/Invoice-tracker.git
cd Invoice-tracker

# 2. Copy and fill in your environment variables
cp .env.example .env   # edit TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HOURLY_RATE, etc.

# 3. Start the service
docker compose up -d

# 4. Open the dashboard
open http://localhost:8000
```

### Without Docker

```bash
# 1. Install dependencies (requires Python 3.11+)
pip install -e ".[dev]"

# 2. Set up environment variables
cp .env.example .env   # edit as needed

# 3. Run the app
uvicorn src.main:app --reload --port 8000

# 4. Open the dashboard
open http://localhost:8000
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HOURLY_RATE` | `35.00` | Your hourly billing rate (AUD) |
| `CURRENCY` | `AUD` | Currency code |
| `SERVICE_DESCRIPTION` | `Laundry and Folding Services` | Line item label on invoices |
| `INVOICE_START_NUMBER` | `1` | First invoice number |
| `TELEGRAM_BOT_TOKEN` | — | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | — | Target chat ID |
| `INVOICE_DAY` | `sun` | Day of week for scheduled invoice |
| `INVOICE_HOUR` | `22` | Hour for scheduled invoice (24h) |
| `APP_TIMEZONE` | `Australia/Brisbane` | Timezone for all timestamps |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/invoicetrack.db` | SQLite database path |

## Project Structure

```
Invoice-tracker/
├── src/
│   ├── api/            # FastAPI routers (sessions, expenses, telegram/invoice)
│   ├── core/           # Config, database engine
│   ├── models/         # SQLAlchemy ORM models
│   ├── services/       # Business logic (billing, PDF, scheduler, Telegram)
│   ├── static/         # Frontend (HTML, CSS, JS)
│   │   ├── index.html
│   │   ├── css/style.css
│   │   └── js/app.js
│   ├── templates/      # Jinja2 templates for PDF generation
│   └── main.py         # FastAPI application entry point
├── tests/
├── docs/
├── docker-compose.yml
└── pyproject.toml
```

## API Reference

The full interactive API docs are available at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/clock-in` | Start a work session |
| `POST` | `/api/clock-out` | End the active session (rounds to 15 min) |
| `GET` | `/api/sessions/active` | Check if a session is in progress |
| `GET` | `/api/sessions?start=&end=` | List sessions for a date range |
| `POST` | `/api/expenses` | Register an expense |
| `GET` | `/api/expenses?start=&end=` | List expenses for a date range |
| `POST` | `/api/petty-cash/topup` | Add funds to petty cash |
| `GET` | `/api/petty-cash/balance` | Get current petty cash balance |
| `GET` | `/api/petty-cash/movements` | List all petty cash movements |
| `POST` | `/api/invoice/generate?start=&end=&send=true` | Generate PDF invoice (optionally send via Telegram) |

## Branching Strategy

- `main` — Production-ready (protected, only via PR)
- `develop` — Integration branch
- `feature/*` — New features
- `fix/*` — Bug fixes
- `chore/*` — Maintenance and config