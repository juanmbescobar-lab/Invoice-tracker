from datetime import date, time

from src.models import Expense, Invoice, PettyCash, WorkSession


class TestWorkSession:
    def test_create_work_session(self):
        session = WorkSession(
            date=date(2026, 2, 24),
            clock_in=time(9, 0),
        )
        assert session.date == date(2026, 2, 24)
        assert session.clock_in == time(9, 0)
        assert session.clock_out is None
        assert session.raw_hours is None

    def test_complete_work_session(self):
        session = WorkSession(
            date=date(2026, 2, 24),
            clock_in=time(9, 0),
            clock_out=time(11, 40),
            raw_hours=2.6667,
            adjusted_hours=2.75,
        )
        assert session.adjusted_hours == 2.75


class TestInvoice:
    def test_create_invoice(self):
        inv = Invoice(
            invoice_number=1,
            date_from=date(2026, 2, 17),
            date_to=date(2026, 2, 23),
            total_hours=10.0,
            total_amount=350.00,
            expenses_total=25.50,
            final_total=375.50,
            status="draft",
        )
        assert inv.invoice_number == 1
        assert inv.final_total == 375.50
        assert inv.status == "draft"


class TestExpense:
    def test_personal_expense(self):
        exp = Expense(
            date=date(2026, 2, 20),
            description="Detergente",
            amount=15.50,
            paid_by="personal",
        )
        assert exp.paid_by == "personal"
        assert exp.invoice_id is None

    def test_petty_cash_expense(self):
        exp = Expense(
            date=date(2026, 2, 20),
            description="Bolsas",
            amount=8.00,
            paid_by="petty_cash",
        )
        assert exp.paid_by == "petty_cash"


class TestPettyCash:
    def test_topup(self):
        pc = PettyCash(
            movement_type="topup",
            amount=100.00,
            balance_after=100.00,
            description="Recarga inicial",
        )
        assert pc.movement_type == "topup"
        assert pc.balance_after == 100.00

    def test_expense_movement(self):
        pc = PettyCash(
            movement_type="expense",
            amount=20.00,
            balance_after=80.00,
            description="Detergente",
        )
        assert pc.balance_after == 80.00
