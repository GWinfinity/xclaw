"""
Tests for Tesla browser backend server.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from . import browser_server as server


@pytest.fixture
def client():
    """Create a FastAPI test client with mocked dependencies."""
    original_client = server._client
    original_vehicle = server._vehicle
    original_copilot = server._copilot

    server._client = None
    server._vehicle = None
    server._copilot = None
    server._connections.clear()

    with TestClient(server.app) as test_client:
        yield test_client

    server._client = original_client
    server._vehicle = original_vehicle
    server._copilot = original_copilot
    server._connections.clear()


class TestHealthEndpoint:
    """Test basic health endpoint."""

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestVehicleEndpoint:
    """Test /api/vehicle with mocked Tesla client."""

    @pytest.mark.asyncio
    async def test_get_vehicle_success(self, client):
        mock_vehicle = MagicMock()
        mock_vehicle.vin = "5YJ3E1EA8JF000000"
        mock_vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}
        mock_vehicle.get_vehicle_data = AsyncMock(
            side_effect=Exception("offline for test")
        )

        mock_fleet_client = MagicMock()
        mock_fleet_client.get_vehicles = AsyncMock(return_value=[mock_vehicle])

        mock_llm = MagicMock()

        server._client = mock_fleet_client
        server._vehicle = mock_vehicle
        server._copilot = None

        with patch.object(server, "_get_client", return_value=mock_fleet_client):
            with patch.object(server, "_get_llm_adapter", return_value=mock_llm):
                response = client.get("/api/vehicle")

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == ["fleet_api"]
        assert data["platform"]["model_type"] == "model3"


class TestChatEndpoint:
    """Test /api/chat endpoint."""

    def test_chat_missing_message(self, client):
        response = client.post("/api/chat", json={})
        # Endpoint returns 400 because it checks for missing message manually
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_chat_with_message(self, client):
        mock_vehicle = MagicMock()
        mock_vehicle.vin = "5YJ3E1EA8JF000000"
        mock_vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}
        mock_vehicle.get_vehicle_data = AsyncMock(
            side_effect=Exception("offline for test")
        )

        mock_llm = MagicMock()
        mock_llm.chat_completion = AsyncMock(
            return_value=MagicMock(
                content="电量充足，无需充电。",
                tool_calls=[],
                has_tool_calls=False,
            )
        )
        mock_llm.handle_error = lambda e: str(e)

        server._vehicle = mock_vehicle
        server._copilot = None

        with patch.object(server, "_get_llm_adapter", return_value=mock_llm):
            response = client.post("/api/chat", json={"message": "我应该现在充电吗？"})

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "电量充足，无需充电。"
        assert data["error"] is None


class TestCommandEndpoint:
    """Test /api/command endpoint."""

    @pytest.mark.asyncio
    async def test_execute_flash_lights(self, client):
        mock_vehicle = MagicMock()
        mock_vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}

        mock_copilot = MagicMock()
        mock_copilot.execute_tool = AsyncMock(return_value={"tool": "flash_lights", "result": True})

        server._vehicle = mock_vehicle
        server._copilot = mock_copilot

        response = client.post(
            "/api/command",
            json={"tool": "flash_lights", "arguments": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        mock_copilot.execute_tool.assert_awaited_once_with("flash_lights", {})

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, client):
        mock_vehicle = MagicMock()
        mock_vehicle.platform_info.to_dict.return_value = {"model_type": "model3"}

        mock_copilot = MagicMock()
        mock_copilot.execute_tool = AsyncMock(
            return_value={"tool": "unknown_tool", "error": "Unknown tool: unknown_tool"}
        )

        server._vehicle = mock_vehicle
        server._copilot = mock_copilot

        response = client.post(
            "/api/command",
            json={"tool": "unknown_tool", "arguments": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert "Unknown tool" in data["error"]


class TestDashboardServing:
    """Test static dashboard serving."""

    def test_dashboard_served(self, client):
        response = client.get("/dashboard/")
        if server.DASHBOARD_DIR.exists():
            assert response.status_code == 200
            assert "xClaw Tesla AI Dashboard" in response.text
        else:
            assert response.status_code == 500
