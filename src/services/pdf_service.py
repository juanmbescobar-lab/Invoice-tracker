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
