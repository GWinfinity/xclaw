"""
xClaw Tesla Browser Backend Server

Serves the AI dashboard and exposes APIs for the Tesla browser extension
or any web browser. Combines Tesla Fleet API + user LLM API into a
Tesla-optimized AI assistant.

Start:
    python -m packages.tesla_client.browser_server

Environment variables:
    TESLA_CLIENT_ID
    TESLA_CLIENT_SECRET
    TESLA_REDIRECT_URI
    TESLA_REGION (default: cn)
    TESLA_ACCESS_TOKEN
    TESLA_REFRESH_TOKEN
    TESLA_VIN (optional)
    LLM_PROVIDER
    <provider-specific API keys>
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import contextlib

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from packages.llm_adapters import LLMFactory, create_llm_adapter
from packages.llm_adapters.base import BaseLLMAdapter

from .ai_copilot import TeslaAICopilot
from .client import TeslaFleetClient
from .vehicle import Vehicle


# Locate dashboard static files relative to this module
MODULE_DIR = Path(__file__).parent.resolve()
DASHBOARD_DIR = MODULE_DIR.parent.parent / "extensions" / "tesla_browser" / "dashboard"

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown handling."""
    # Startup
    try:
        _get_client()
        _get_llm_adapter()
    except Exception as exc:
        print(f"[xClaw] Startup validation warning: {exc}")

    background_task = asyncio.create_task(_vehicle_update_loop())

    yield

    # Shutdown
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass

    global _client
    if _client is not None:
        try:
            await _client.close()
        except TypeError:
            # _client may be a test mock without an async close()
            pass
        _client = None


app = FastAPI(title="xClaw Tesla AI Backend", lifespan=lifespan)

# Global state (simple single-tenant setup; can be replaced with sessions)
_client: Optional[TeslaFleetClient] = None
_vehicle: Optional[Vehicle] = None
_copilot: Optional[TeslaAICopilot] = None
_connections: List[WebSocket] = []


def _get_client() -> TeslaFleetClient:
    """Get or create Tesla Fleet API client from environment."""
    global _client

    if _client is None:
        _client = TeslaFleetClient(
            client_id=os.getenv("TESLA_CLIENT_ID"),
            client_secret=os.getenv("TESLA_CLIENT_SECRET"),
            redirect_uri=os.getenv("TESLA_REDIRECT_URI"),
            region=os.getenv("TESLA_REGION", "cn"),
            access_token=os.getenv("TESLA_ACCESS_TOKEN"),
            refresh_token=os.getenv("TESLA_REFRESH_TOKEN"),
        )
    return _client


def _get_llm_adapter() -> BaseLLMAdapter:
    """Create LLM adapter from environment."""
    try:
        return create_llm_adapter()
    except Exception as exc:
        raise RuntimeError(
            "Failed to create LLM adapter. Check LLM_PROVIDER and API key env vars."
        ) from exc


async def _get_vehicle() -> Vehicle:
    """Get target vehicle (cached or first available)."""
    global _vehicle

    if _vehicle is not None:
        return _vehicle

    client = _get_client()
    vehicles = await client.get_vehicles()
    if not vehicles:
        raise HTTPException(status_code=404, detail="No vehicles found")

    target_vin = os.getenv("TESLA_VIN")
    if target_vin:
        for v in vehicles:
            if v.vin == target_vin:
                _vehicle = v
                break
        if _vehicle is None:
            raise HTTPException(
                status_code=404,
                detail=f"Vehicle with VIN {target_vin} not found",
            )
    else:
        _vehicle = vehicles[0]

    return _vehicle


def _get_copilot(vehicle: Vehicle) -> TeslaAICopilot:
    """Get or create AI copilot for the vehicle."""
    global _copilot

    if _copilot is None:
        _copilot = TeslaAICopilot(
            vehicle=vehicle,
            llm_adapter=_get_llm_adapter(),
            auto_execute_tools=False,  # Browser commands require user approval
        )
    return _copilot




# ============== Static Dashboard ==============

if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")
else:
    print(f"[xClaw] Warning: dashboard directory not found at {DASHBOARD_DIR}")


@app.get("/")
async def root():
    """Redirect root to dashboard."""
    return FileResponse(str(DASHBOARD_DIR / "index.html"))


@app.get("/dashboard")
@app.get("/dashboard/")
async def dashboard():
    """Serve the AI dashboard."""
    index_path = DASHBOARD_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Dashboard not built")
    return FileResponse(str(index_path))


# ============== API Endpoints ==============


@app.get("/api/health")
async def health() -> Dict[str, str]:
    """Health check for browser extension."""
    return {"status": "ok", "service": "xclaw-tesla-ai"}


@app.get("/api/vehicle")
async def get_vehicle() -> Dict[str, Any]:
    """Get current vehicle snapshot (Fleet API + CAN if configured)."""
    try:
        vehicle = await _get_vehicle()
        copilot = _get_copilot(vehicle)
        snapshot = await copilot._get_vehicle_snapshot()
        return snapshot
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat")
async def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Chat with the AI copilot."""
    message = payload.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    try:
        vehicle = await _get_vehicle()
        copilot = _get_copilot(vehicle)
        response = await copilot.ask(message, enable_tools=True)

        return {
            "content": response.content,
            "tool_calls": response.tool_calls,
            "executed_commands": response.executed_commands,
            "vehicle_state": response.vehicle_state,
            "error": response.error,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/command")
async def execute_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single Fleet API command manually.

    Body: {"tool": "flash_lights", "arguments": {}}
    """
    tool = payload.get("tool", "").strip()
    arguments = payload.get("arguments", {})

    if not tool:
        raise HTTPException(status_code=400, detail="tool is required")

    try:
        vehicle = await _get_vehicle()
        copilot = _get_copilot(vehicle)
        result = await copilot.execute_tool(tool, arguments)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ============== WebSocket ==============


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time vehicle updates."""
    await websocket.accept()
    _connections.append(websocket)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("type") == "pong":
                    continue
            except json.JSONDecodeError:
                continue
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _connections:
            _connections.remove(websocket)


async def _broadcast(message: Dict[str, Any]) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    disconnected = []
    for conn in _connections:
        try:
            await conn.send_json(message)
        except Exception:
            disconnected.append(conn)

    for conn in disconnected:
        if conn in _connections:
            _connections.remove(conn)


async def _vehicle_update_loop() -> None:
    """Background loop: push vehicle state to browsers periodically."""
    while True:
        await asyncio.sleep(30)
        if _connections:
            try:
                vehicle = await _get_vehicle()
                copilot = _get_copilot(vehicle)
                snapshot = await copilot._get_vehicle_snapshot()
                await _broadcast({"type": "vehicle_update", "data": snapshot})
            except Exception:
                pass




# ============== Entry Point ==============

def main():
    import uvicorn

    host = os.getenv("XCLAW_HOST", "0.0.0.0")
    port = int(os.getenv("XCLAW_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
