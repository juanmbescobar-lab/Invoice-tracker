from src.core.config import Settings


def test_default_settings():
    s = Settings()
    assert s.hourly_rate == 35.00
    assert s.currency == "AUD"
    assert s.app_timezone == "Australia/Brisbane"
    assert s.invoice_hour == 22


def test_custom_settings_from_env(monkeypatch):
    monkeypatch.setenv("HOURLY_RATE", "40.00")
    monkeypatch.setenv("CURRENCY", "USD")

    s = Settings()
    assert s.hourly_rate == 40.00
    assert s.currency == "USD"
