import os

from src.services.pdf_service import generate_invoice_pdf


def test_generate_simple_pdf():
    lines = [
        {"description": "Laundry and Folding Services", "amount": 385.00},
    ]
    path = generate_invoice_pdf(
        invoice_number=1,
        lines=lines,
        final_total=385.00,
    )
    assert os.path.exists(path)
    assert path.endswith(".pdf")
    os.remove(path)


def test_generate_pdf_with_expenses_and_credit():
    lines = [
        {"description": "Laundry and Folding Services", "amount": 385.00},
        {"description": "Bunnings", "amount": 83.82},
        {"description": "Credit Balance", "amount": -71.00},
    ]
    path = generate_invoice_pdf(
        invoice_number=40,
        lines=lines,
        final_total=397.82,
    )
    assert os.path.exists(path)
    assert "INV040" in path
    os.remove(path)
