import os

from src.services.pdf_service import generate_hours_pdf


def test_generate_hours_pdf():
    sessions = [
        {
            "date": "2026-03-02",
            "clock_in": "09:00",
            "clock_out": "11:40",
            "adjusted_hours": 2.75,
        },
        {
            "date": "2026-03-03",
            "clock_in": "09:00",
            "clock_out": "12:00",
            "adjusted_hours": 3.00,
        },
    ]
    path = generate_hours_pdf(
        invoice_number=1,
        sessions=sessions,
        total_hours=5.75,
        rate=35.00,
        total_amount=201.25,
        date_from="2026-03-02",
        date_to="2026-03-08",
    )
    assert os.path.exists(path)
    assert "Hours_CozyHomes" in path
    os.remove(path)


def test_hours_pdf_filename_format():
    sessions = [
        {
            "date": "2026-03-02",
            "clock_in": "09:00",
            "clock_out": "11:00",
            "adjusted_hours": 2.0,
        },
    ]
    path = generate_hours_pdf(
        invoice_number=41,
        sessions=sessions,
        total_hours=2.0,
        rate=35.00,
        total_amount=70.00,
        date_from="2026-03-02",
        date_to="2026-03-08",
    )
    assert "INV041" in path
    os.remove(path)
