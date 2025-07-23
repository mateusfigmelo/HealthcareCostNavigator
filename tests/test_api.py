"""API tests for Healthcare Cost Navigator."""

import asyncio
import os

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models import Hospital, Procedure, Rating

# Test database URL - Use SQLite for testing (no external database required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Don't drop tables - let the file cleanup handle it
    # Clean up test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
async def db_session(test_db):
    """Create a test database session."""
    async with TestingSessionLocal() as session:
        # Clear any existing data before each test
        await session.execute(text("DELETE FROM ratings"))
        await session.execute(text("DELETE FROM procedures"))
        await session.execute(text("DELETE FROM hospitals"))
        await session.commit()

        yield session
        await session.rollback()


@pytest.fixture
async def client_with_data(test_db):
    """Create test client with sample data."""
    # Create a session that will be shared
    session = TestingSessionLocal()

    # Clear any existing data
    await session.execute(text("DELETE FROM ratings"))
    await session.execute(text("DELETE FROM procedures"))
    await session.execute(text("DELETE FROM hospitals"))
    await session.commit()

    # Create test hospitals
    hospitals = [
        Hospital(
            provider_id="330123",
            provider_name="TEST HOSPITAL 1",
            provider_city="DOTHAN",
            provider_state="AL",
            provider_zip_code="36301",
        ),
        Hospital(
            provider_id="330124",
            provider_name="TEST HOSPITAL 2",
            provider_city="BIRMINGHAM",
            provider_state="AL",
            provider_zip_code="35201",
        ),
    ]

    for hospital in hospitals:
        session.add(hospital)

    # Create test procedures
    procedures = [
        Procedure(
            provider_id="330123",
            ms_drg_code="23",
            ms_drg_definition="CRANIOTOMY WITH MAJOR DEVICE IMPLANT OR ACUTE COMPLEX CNS PRINCIPAL DIAGNOSIS WITH MCC",
            total_discharges=100,
            average_covered_charges=158541.64,
            average_total_payments=37331.0,
            average_medicare_payments=35332.96,
        ),
        Procedure(
            provider_id="330124",
            ms_drg_code="24",
            ms_drg_definition="CRANIOTOMY WITH MAJOR DEVICE IMPLANT OR ACUTE COMPLEX CNS PRINCIPAL DIAGNOSIS WITHOUT MCC",
            total_discharges=80,
            average_covered_charges=107085.33,
            average_total_payments=25842.67,
            average_medicare_payments=23857.94,
        ),
    ]

    for procedure in procedures:
        session.add(procedure)

    # Create test ratings
    ratings = [
        Rating(provider_id="330123", rating=8.5),
        Rating(provider_id="330124", rating=9.0),
    ]

    for rating in ratings:
        session.add(rating)

    await session.commit()

    # Create a new session for the dependency override
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    # Verify data was inserted
    result = await session.execute(text("SELECT COUNT(*) FROM hospitals"))
    hospital_count = result.scalar()
    print(f"DEBUG: Inserted {hospital_count} hospitals")

    result = await session.execute(text("SELECT COUNT(*) FROM procedures"))
    procedure_count = result.scalar()
    print(f"DEBUG: Inserted {procedure_count} procedures")

    # Also verify the specific data we're looking for
    result = await session.execute(
        text("SELECT COUNT(*) FROM procedures WHERE ms_drg_code = '23'")
    )
    drg_023_count = result.scalar()
    print(f"DEBUG: Found {drg_023_count} procedures with DRG 23")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up dependency override and close session
    app.dependency_overrides.clear()
    await session.close()


@pytest.fixture
async def client():
    """Create test client for tests that don't need data."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestProvidersAPI:
    """Test providers API endpoints."""

    async def test_search_providers_with_drg(self, client_with_data):
        """Test searching providers by DRG code."""
        response = await client_with_data.get("/providers/?drg=023")
        assert response.status_code == 200

        data = response.json()
        print(f"DEBUG: API returned {len(data)} results")
        if data:
            print(f"DEBUG: First result: {data[0]}")
        assert len(data) == 1
        assert data[0]["ms_drg_code"] == "23"

    async def test_search_providers_with_zip(self, client_with_data):
        """Test searching providers by ZIP code."""
        response = await client_with_data.get("/providers/?zip_code=36301&radius_km=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert any(provider["provider_zip_code"] == "36301" for provider in data)

    async def test_search_providers_sort_by_cost(self, client_with_data):
        """Test sorting providers by cost."""
        response = await client_with_data.get("/providers/?drg=023&sort_by=cost")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1  # Only one hospital has DRG 023
        # Check that results are sorted by cost (ascending)
        costs = [provider["average_covered_charges"] for provider in data]
        assert costs == sorted(costs)

    async def test_search_providers_sort_by_rating(self, client_with_data):
        """Test sorting providers by rating."""
        response = await client_with_data.get("/providers/?drg=023&sort_by=rating")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1  # Only one hospital has DRG 023
        # Check that results are sorted by rating (descending)
        ratings = [
            provider["average_rating"]
            for provider in data
            if provider["average_rating"]
        ]
        assert ratings == sorted(ratings, reverse=True)

    async def test_search_providers_invalid_sort(self, client):
        """Test invalid sort parameter."""
        response = await client.get("/providers/?sort_by=invalid")
        assert response.status_code == 400

    async def test_search_providers_radius_without_zip(self, client):
        """Test radius parameter without ZIP code."""
        response = await client.get("/providers/?radius_km=10")
        assert response.status_code == 400

    async def test_search_by_text(self, client_with_data):
        """Test text-based search."""
        response = await client_with_data.get("/providers/search?q=craniotomy")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert any("CRANIOTOMY" in provider["ms_drg_definition"] for provider in data)


class TestAIAPI:
    """Test AI API endpoints."""

    async def test_ask_healthcare_question(self, client_with_data):
        """Test asking a healthcare-related question."""
        question = {"question": "Who is cheapest for DRG 023 near 36301?"}

        response = await client_with_data.post("/ask/", json=question)
        assert response.status_code == 200

        data = response.json()
        assert "answer" in data
        assert "results" in data
        assert data["out_of_scope"] is False

    async def test_ask_out_of_scope_question(self, client):
        """Test asking an out-of-scope question."""
        question = {"question": "What's the weather today?"}

        response = await client.post("/ask/", json=question)
        assert response.status_code == 200

        data = response.json()
        assert data["out_of_scope"] is True
        assert "weather" not in data["answer"].lower()

    async def test_ask_empty_question(self, client):
        """Test asking an empty question."""
        question = {"question": ""}

        response = await client.post("/ask/", json=question)
        assert response.status_code == 400

    async def test_ask_missing_question(self, client):
        """Test missing question field."""
        question = {}

        response = await client.post("/ask/", json=question)
        assert response.status_code == 422  # Validation error


class TestRootEndpoints:
    """Test root API endpoints."""

    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "providers" in data["endpoints"]
        assert "ai_assistant" in data["endpoints"]

    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "healthcare-cost-navigator"
