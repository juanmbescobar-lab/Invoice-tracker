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


async def test_clock_in_success(client):
    response = await client.post("/api/clock-in")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Clocked in successfully"
    assert "session" in data


async def test_clock_in_twice_fails(client):
    await client.post("/api/clock-in")
    response = await client.post("/api/clock-in")
    assert response.status_code == 400
    assert "Already clocked in" in response.json()["detail"]


async def test_clock_out_without_clock_in_fails(client):
    response = await client.post("/api/clock-out")
    assert response.status_code == 400
    assert "No active session" in response.json()["detail"]


async def test_clock_in_then_out(client):
    await client.post("/api/clock-in")
    response = await client.post("/api/clock-out")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Clocked out successfully"
    assert data["session"]["adjusted_hours"] is not None


async def test_no_active_session(client):
    response = await client.get("/api/sessions/active")
    assert response.status_code == 200
    assert response.json()["active"] is False


async def test_has_active_session(client):
    await client.post("/api/clock-in")
    response = await client.get("/api/sessions/active")
    assert response.status_code == 200
    assert response.json()["active"] is True


async def test_empty_sessions(client):
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_sessions_after_clock_in_out(client):
    await client.post("/api/clock-in")
    await client.post("/api/clock-out")
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert response.json()["count"] == 1
