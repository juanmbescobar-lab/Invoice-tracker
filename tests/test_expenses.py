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
    assert data["expense"]["description"] == "Detergente"
    assert data["expense"]["amount"] == 15.50
    assert data["expense"]["paid_by"] == "personal"


async def test_add_petty_cash_expense(client):
    await client.post(
        "/api/petty-cash/topup", json={"amount": 100, "description": "Recarga"}
    )
    response = await client.post(
        "/api/expenses",
        json={"description": "Bolsas", "amount": 20.00, "paid_by": "petty_cash"},
    )
    assert response.status_code == 200
    assert response.json()["expense"]["paid_by"] == "petty_cash"


async def test_petty_cash_expense_without_balance_goes_negative(client):
    # Petty cash expenses are allowed even with no balance — balance goes negative.
    response = await client.post(
        "/api/expenses",
        json={"description": "Bolsas", "amount": 20.00, "paid_by": "petty_cash"},
    )
    assert response.status_code == 200
    assert response.json()["expense"]["paid_by"] == "petty_cash"

    balance = await client.get("/api/petty-cash/balance")
    assert balance.json()["balance"] == -20.00


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
