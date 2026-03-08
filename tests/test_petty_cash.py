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


async def test_initial_balance_is_zero(client):
    response = await client.get("/api/petty-cash/balance")
    assert response.status_code == 200
    assert response.json()["balance"] == 0.0


async def test_topup(client):
    response = await client.post(
        "/api/petty-cash/topup",
        json={"amount": 100, "description": "Recarga inicial"},
    )
    assert response.status_code == 200
    assert response.json()["balance"] == 100.0


async def test_topup_negative_fails(client):
    response = await client.post("/api/petty-cash/topup", json={"amount": -50})
    assert response.status_code == 400


async def test_balance_after_topup_and_expense(client):
    await client.post("/api/petty-cash/topup", json={"amount": 100})
    await client.post(
        "/api/expenses",
        json={"description": "Bolsas", "amount": 30, "paid_by": "petty_cash"},
    )
    response = await client.get("/api/petty-cash/balance")
    assert response.json()["balance"] == 70.0


async def test_movements_history(client):
    await client.post(
        "/api/petty-cash/topup",
        json={"amount": 100, "description": "Recarga"},
    )
    await client.post(
        "/api/expenses",
        json={"description": "Detergente", "amount": 25, "paid_by": "petty_cash"},
    )
    response = await client.get("/api/petty-cash/movements")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["movements"][0]["type"] == "topup"
    assert data["movements"][1]["type"] == "expense"
    assert data["movements"][1]["balance_after"] == 75.0


async def test_balance_goes_to_zero_on_partial_spend(client):
    """When expense > petty cash balance, balance reaches 0 (not negative)."""
    await client.post("/api/petty-cash/topup", json={"amount": 50})
    await client.post(
        "/api/expenses",
        json={"description": "Bunnings", "amount": 100.00, "paid_by": "petty_cash"},
    )
    balance = await client.get("/api/petty-cash/balance")
    assert balance.json()["balance"] == 0.0

    # Only $50 was deducted, so one expense movement of $50
    movements = await client.get("/api/petty-cash/movements")
    data = movements.json()
    assert data["count"] == 2  # 1 topup + 1 expense movement
    assert data["movements"][1]["amount"] == 50.0


async def test_empty_movements(client):
    response = await client.get("/api/petty-cash/movements")
    assert response.status_code == 200
    assert response.json()["count"] == 0
