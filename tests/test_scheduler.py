from src.services.scheduler_service import create_scheduler


def test_scheduler_creates_three_jobs():
    scheduler = create_scheduler()
    jobs = scheduler.get_jobs()
    assert len(jobs) == 3

    job_ids = [j.id for j in jobs]
    assert "petty_cash_report" in job_ids
    assert "remind_expenses" in job_ids
    assert "generate_invoice" in job_ids


def test_scheduler_uses_correct_timezone():
    scheduler = create_scheduler()
    assert str(scheduler.timezone) == "Australia/Brisbane"
