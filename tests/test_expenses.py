import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import Base, engine
from src.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_add_personal_expense(client):
    response = await client.post(
        "/api/expenses",
        json={"description": "Detergente", "amount": 15.50, "paid_by": "personal"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["description"] == "Detergente"
    assert data["expenses"][0]["amount"] == 15.50
    assert data["expenses"][0]["paid_by"] == "personal"


async def test_add_petty_cash_expense_full_coverage(client):
    """When balance >= expense amount, a single petty_cash expense is created."""
    await client.post(
        "/api/petty-cash/topup", json={"amount": 100, "description": "Recarga"}
    )
    response = await client.post(
        "/api/expenses",
        json={"description": "Bolsas", "amount": 20.00, "paid_by": "petty_cash"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["paid_by"] == "petty_cash"
    assert data["expenses"][0]["amount"] == 20.00


async def test_petty_cash_expense_partial_coverage(client):
    """When balance < expense amount, the expense is split into petty_cash + personal."""
    await client.post("/api/petty-cash/topup", json={"amount": 50})
    response = await client.post(
        "/api/expenses",
        json={"description": "Bunnings", "amount": 100.00, "paid_by": "petty_cash"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 2
    assert data["expenses"][0]["paid_by"] == "petty_cash"
    assert data["expenses"][0]["amount"] == 50.00
    assert data["expenses"][1]["paid_by"] == "personal"
    assert data["expenses"][1]["amount"] == 50.00

    balance = await client.get("/api/petty-cash/balance")
    assert balance.json()["balance"] == 0.0


async def test_petty_cash_expense_zero_balance_becomes_personal(client):
    """When petty cash balance is 0, expense becomes fully personal."""
    response = await client.post(
        "/api/expenses",
        json={"description": "Bolsas", "amount": 20.00, "paid_by": "petty_cash"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["paid_by"] == "personal"
    assert data["expenses"][0]["amount"] == 20.00

    balance = await client.get("/api/petty-cash/balance")
    assert balance.json()["balance"] == 0.0


async def test_invalid_paid_by_fails(client):
    response = await client.post(
        "/api/expenses",
        json={"description": "Test", "amount": 10.00, "paid_by": "invalid"},
    )
    assert response.status_code == 400


async def test_get_expenses_empty(client):
    response = await client.get("/api/expenses")
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_get_expenses_after_adding(client):
    await client.post(
        "/api/expenses",
        json={"description": "Detergente", "amount": 15.50},
    )
    response = await client.get("/api/expenses")
    assert response.status_code == 200
    assert response.json()["count"] == 1
