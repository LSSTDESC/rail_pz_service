import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_index_routes(
    client: AsyncClient,
) -> None:
    """Test `/` API endpoint."""

    response = await client.get("/")
    assert response.status_code == 200

    assert response.json()["name"] == "rail-pz-service"
