import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks test requiring real external APIs"
    )

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
async def client(mock_db):
    with patch("app.database.create_tables", new_callable=AsyncMock):
        app.dependency_overrides[get_db] = lambda: mock_db
        
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
            yield ac
        app.dependency_overrides.clear()
