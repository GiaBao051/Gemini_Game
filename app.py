import asyncio
import json
import logging
import uuid
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

from game import RoomManager

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("maze-game")

app = FastAPI(title="2P Maze Game Server", version="0.1.0")
rooms = RoomManager()

# Dev-friendly CORS (nếu client web). Production nên giới hạn origin cụ thể.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def client():
    """Serve the web client UI."""
    here = Path(__file__).resolve().parent
    return FileResponse(here / "web_client_v2.html")

def _safe_json_loads(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    player_id = f"p-{uuid.uuid4().hex[:10]}"
    room = None

    try:
        # 1) Require JOIN first (with timeout)
        try:
            raw = await asyncio.wait_for(ws.receive_text(), timeout=10)
        except asyncio.TimeoutError:
            await ws.send_text(json.dumps({"type": "error", "message": "JOIN timeout"}))
            await ws.close(code=1000)
            return

        msg = _safe_json_loads(raw)
        if msg.get("type") != "join":
            await ws.send_text(json.dumps({"type": "error", "message": "First message must be {type:'join'}"}))
            await ws.close(code=1003)
            return

        name = str(msg.get("name") or "Player")

        # 2) Matchmake / join room
        room = await rooms.join_or_create(ws=ws, player_id=player_id, name=name)
        await room.send_start(player_id)
        log.info("Player %s joined room %s as %s", player_id, room.room_id, name)

        # 3) Main loop: forward client messages to room
        while True:
            raw = await ws.receive_text()
            msg = _safe_json_loads(raw)
            if not msg:
                await ws.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            await room.handle_client_msg(player_id, msg)

    except WebSocketDisconnect:
        log.info("Player %s disconnected", player_id)
        await rooms.disconnect(player_id)

    except Exception as e:
        log.exception("Server error for player %s: %s", player_id, e)
        try:
            await ws.send_text(json.dumps({"type": "error", "message": f"Server error: {type(e).__name__}"}))
        except Exception:
            pass
        await rooms.disconnect(player_id)
        try:
            await ws.close(code=1011)
        except Exception:
            pass
