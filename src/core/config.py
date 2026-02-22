from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    app_timezone: str = "Australia/Brisbane"

    hourly_rate: float = 35.00
    currency: str = "AUD"
    service_description: str = "Laundry and Folding Services"

    telegram_bot_token: str = " "
    telegram_chat_id: str = " "

    invoice_day: str = "sun"
    invoice_hour: int = 22
    invoice_minute: int = 0

    database_url: str = "sqlite+aiosqlite:///data/invoicetrack.db"

    model_config = {"env_file": ".env"}


settings = Settings()
