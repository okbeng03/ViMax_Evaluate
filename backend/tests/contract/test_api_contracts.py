"""API contract tests for REST endpoints.

Reference: specs/001-agent-image-evaluation/contracts/api-contracts.md
"""

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """GET /health should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestTaskEndpoints:
    """Tests for task management endpoints."""

    @pytest.mark.asyncio
    async def test_create_task_requires_prompt(self, client: AsyncClient):
        """POST /api/v1/tasks should require prompt field."""
        response = await client.post(
            "/api/v1/tasks",
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_requires_image(self, client: AsyncClient):
        """POST /api/v1/tasks should require at least one image source."""
        response = await client.post(
            "/api/v1/tasks",
            json={"prompt": "A cat sitting on a windowsill"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "image" in data["detail"][0]["loc"][-1].lower() or "at least" in str(data).lower()

    @pytest.mark.asyncio
    async def test_create_task_with_image_url(self, client: AsyncClient):
        """POST /api/v1/tasks with image_url should succeed."""
        response = await client.post(
            "/api/v1/tasks",
            json={
                "prompt": "A cat sitting on a windowsill",
                "image_url": "https://example.com/cat.jpg",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_task_with_base64(self, client: AsyncClient):
        """POST /api/v1/tasks with image_base64 should succeed."""
        response = await client.post(
            "/api/v1/tasks",
            json={
                "prompt": "A cat sitting on a windowsill",
                "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client: AsyncClient):
        """GET /api/v1/tasks/{task_id} should return 404 for nonexistent task."""
        response = await client.get("/api/v1/tasks/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "TASK_NOT_FOUND"


class TestProjectEndpoints:
    """Tests for project management endpoints."""

    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient):
        """POST /api/v1/projects should create a project."""
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "description": "A test project",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_project_requires_name(self, client: AsyncClient):
        """POST /api/v1/projects should require name field."""
        response = await client.post(
            "/api/v1/projects",
            json={"description": "No name provided"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_nonexistent_project(self, client: AsyncClient):
        """GET /api/v1/projects/{project_id} should return 404."""
        response = await client.get("/api/v1/projects/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "PROJECT_NOT_FOUND"


class TestErrorResponseFormat:
    """Tests for consistent error response format."""

    @pytest.mark.asyncio
    async def test_error_response_structure(self, client: AsyncClient):
        """Error responses should follow consistent format."""
        response = await client.get("/api/v1/tasks/nonexistent-id")
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
