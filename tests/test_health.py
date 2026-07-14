import pytest


@pytest.mark.anyio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
