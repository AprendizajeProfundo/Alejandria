from alejandria.domain.user_message import UserMessage
from alejandria.services.orchestrator_service import OrchestratorService

import asyncio
import json

from fastapi import APIRouter, WebSocket

router = APIRouter()

orchestrator = OrchestratorService()


@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_text()
    try:
        data_dict = json.loads(data)
        user_id = data_dict.get("user_id", "anon")
        message = data_dict.get("message", "")
    except Exception:
        user_id = "anon"
        message = data
    user_message = UserMessage(user_id=user_id, message=message)
    websocket_closed = False

    # Callback para enviar cada token al frontend en tiempo real
    async def on_token(payload):
        nonlocal websocket_closed
        if websocket_closed:
            return
        try:
            await websocket.send_json(payload)
        except Exception:
            websocket_closed = True

    # Adaptar el callback para ser compatible con sync/async
    def sync_on_token(payload):
        asyncio.create_task(on_token(payload))

    try:
        # Ejecutar el flujo multiagente y streaming del manager
        await orchestrator.handle_stream(user_message, sync_on_token)
    except Exception:
        websocket_closed = True
    if not websocket_closed:
        await websocket.send_json({"done": True})
