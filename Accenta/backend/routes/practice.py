"""
WebSocket Practice Route
Real-time practice streaming endpoint
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/practice/{session_id}")
async def practice_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time practice feedback
    
    Client sends audio chunks, server responds with:
    - Partial feedback (phoneme deviations)
    - Real-time analysis updates
    - Encouragement messages
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    logger.info(f"WebSocket connected for session: {session_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "audio_chunk":
                # Process audio chunk (in production, would analyze here)
                # For now, send acknowledgment
                response = {
                    "type": "acknowledgment",
                    "message": "Audio chunk received",
                    "timestamp": message.get("timestamp"),
                }
                await websocket.send_text(json.dumps(response))

            elif message.get("type") == "ping":
                # Keep-alive ping
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        if session_id in active_connections:
            del active_connections[session_id]


async def send_feedback_to_client(session_id: str, feedback: dict):
    """Send feedback to a specific client"""
    if session_id in active_connections:
        try:
            await active_connections[session_id].send_text(json.dumps(feedback))
        except Exception as e:
            logger.error(f"Error sending feedback to {session_id}: {e}")

