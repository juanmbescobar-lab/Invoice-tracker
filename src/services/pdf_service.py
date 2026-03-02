import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def generate_invoice_pdf(invoice_number: int, lines: list, final_total: float) -> str:
    """Generate a PDF invoice and return the file path."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("invoice.html")

    html_content = template.render(
        invoice_number=f"{invoice_number:03d}",
        lines=lines,
        final_total=final_total,
    )

    os.makedirs("data/invoices", exist_ok=True)
    pdf_path = f"data/invoices/Invoice_CozyHomes_INV{invoice_number:03d}.pdf"

    HTML(string=html_content).write_pdf(pdf_path)

    return pdf_path


def generate_hours_pdf(
    invoice_number: int,
    sessions: list,
    total_hours: float,
    rate: float,
    total_amount: float,
    date_from: str,
    date_to: str,
) -> str:
    """Generate a PDF with the hours detail table."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("hours_table.html")

    html_content = template.render(
        invoice_number=f"{invoice_number:03d}",
        sessions=sessions,
        total_hours=total_hours,
        rate=rate,
        total_amount=total_amount,
        date_from=date_from,
        date_to=date_to,
    )

    os.makedirs("data/invoices", exist_ok=True)
    pdf_path = f"data/invoices/Hours_CozyHomes_INV{invoice_number:03d}.pdf"

    HTML(string=html_content).write_pdf(pdf_path)

    return pdf_path
