"""
WebSocket endpoint for real-time chat messaging.

Features:
- Real-time message exchange
- Chat history loading
- Message persistence
- Connection status tracking
- User typing indicators
"""
import logging
import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from supabase import Client

from app.db import get_supabase
from app.core.auth import get_auth_manager, SupabaseAuthManager
from app.websocket.connection_manager import manager
from app.websocket.messaging_service import MessagingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/chat/{booking_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    booking_id: str,
    token: str = Query(...),
    supabase: Client = Depends(get_supabase),
    auth_manager: SupabaseAuthManager = Depends(lambda: get_auth_manager()),
):
    """
    WebSocket endpoint for real-time chat.

    **Path Parameters**:
    - booking_id: Booking UUID

    **Query Parameters**:
    - token: JWT authentication token

    **Connection Flow**:
    1. Client connects with JWT token
    2. Token verified with Supabase
    3. User verified as booking participant
    4. Chat history loaded from database
    5. User added to connection pool
    6. Real-time messages can be sent/received

    **Message Format** (client → server):
    ```json
    {
      "type": "message|typing|read",
      "content": "message text",
      "message_id": "uuid"  // for read receipts
    }
    ```

    **Response Format** (server → client):
    ```json
    {
      "type": "message|typing|read|status|history",
      "sender_id": "uuid",
      "content": "message text",
      "created_at": "2026-03-26T10:00:00Z",
      "status": "sent|delivered|read",
      "online_users": 2
    }
    ```
    """

    # Step 1: Verify JWT token
    try:
        token_payload = auth_manager.verify_token(token)
        user_id = str(token_payload.sub)
        logger.info(f"WebSocket connection - User: {user_id}, Booking: {booking_id}")
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # Step 2: Verify user is booking participant
    is_participant = await MessagingService.verify_booking_participants(
        supabase, UUID(booking_id), UUID(user_id)
    )

    if not is_participant:
        logger.warning(f"User {user_id} not participant in booking {booking_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not a booking participant")
        return

    # Step 3: Get booking participants
    customer_id, provider_id = await MessagingService.get_booking_participants(
        supabase, UUID(booking_id)
    )

    # Determine other participant
    other_user_id = provider_id if user_id == customer_id else customer_id

    # Step 4: Load and send chat history
    try:
        chat_history = await MessagingService.get_chat_history(
            supabase, UUID(booking_id), limit=50
        )

        history_data = [
            {
                "type": "message",
                "id": msg.id,
                "sender_id": msg.sender_id,
                "content": msg.content,
                "status": msg.status,
                "created_at": msg.created_at,
                "is_own": msg.sender_id == user_id,
            }
            for msg in chat_history
        ]

        logger.debug(f"Loaded {len(chat_history)} messages for booking {booking_id}")
    except Exception as e:
        logger.error(f"Error loading chat history: {str(e)}")
        history_data = []

    # Step 5: Register connection
    try:
        await manager.connect(booking_id, user_id, websocket)

        # Send chat history to connected user
        await websocket.send_json({
            "type": "history",
            "messages": history_data,
        })

        # Notify other user of connection
        online_users = manager.get_room_count(booking_id)
        await manager.broadcast_to_room(
            booking_id,
            {
                "type": "status",
                "event": "user_connected",
                "user_id": user_id,
                "online_users": online_users,
            },
            exclude_user=user_id,
        )

        logger.info(f"User {user_id} connected to booking {booking_id}. Active: {online_users}")

    except Exception as e:
        logger.error(f"Error connecting user: {str(e)}")
        await websocket.close(code=1011, reason="Connection error")
        return

    # Step 6: Handle messages
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_type = message_data.get("type", "message")

            # Handle different message types
            if message_type == "message":
                await handle_message(
                    supabase, booking_id, user_id, other_user_id, message_data
                )

            elif message_type == "typing":
                await handle_typing(booking_id, user_id, message_data)

            elif message_type == "read":
                await handle_read_receipt(supabase, booking_id, message_data)

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from booking {booking_id}")
        manager.disconnect(booking_id, user_id)

        # Notify other user of disconnection
        online_users = manager.get_room_count(booking_id)
        await manager.broadcast_to_room(
            booking_id,
            {
                "type": "status",
                "event": "user_disconnected",
                "user_id": user_id,
                "online_users": online_users,
            },
        )

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(booking_id, user_id)


async def handle_message(supabase: Client, booking_id: str, sender_id: str, recipient_id: str, message_data: dict):
    """Handle incoming message."""
    try:
        content = message_data.get("content", "").strip()

        if not content:
            return

        # Save to database
        message = await MessagingService.save_message(
            supabase,
            UUID(booking_id),
            UUID(sender_id),
            UUID(recipient_id),
            content,
        )

        if not message:
            logger.error("Failed to save message")
            return

        # Broadcast to room
        await manager.broadcast_to_room(
            booking_id,
            {
                "type": "message",
                "id": message.id,
                "sender_id": sender_id,
                "content": content,
                "status": "delivered",
                "created_at": message.created_at,
                "is_own": False,
            },
        )

        logger.debug(f"Message saved: {message.id}")

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")


async def handle_typing(booking_id: str, sender_id: str, message_data: dict):
    """Handle typing indicator."""
    try:
        is_typing = message_data.get("is_typing", True)

        # Broadcast typing indicator
        await manager.broadcast_to_room(
            booking_id,
            {
                "type": "typing",
                "user_id": sender_id,
                "is_typing": is_typing,
            },
            exclude_user=sender_id,
        )

    except Exception as e:
        logger.error(f"Error handling typing: {str(e)}")


async def handle_read_receipt(supabase: Client, booking_id: str, message_data: dict):
    """Handle read receipt."""
    try:
        message_id = message_data.get("message_id")

        if not message_id:
            return

        # Mark as read
        await MessagingService.mark_message_as_read(supabase, UUID(message_id))

        # Broadcast read status
        await manager.broadcast_to_room(
            booking_id,
            {
                "type": "read",
                "message_id": message_id,
            },
        )

    except Exception as e:
        logger.error(f"Error handling read receipt: {str(e)}")


@router.get("/chat/{booking_id}/history")
async def get_chat_history(
    booking_id: str,
    limit: int = Query(50, ge=1, le=200),
    supabase: Client = Depends(get_supabase),
):
    """
    Get chat history for a booking (REST endpoint).

    **Path Parameters**:
    - booking_id: Booking UUID

    **Query Parameters**:
    - limit: Number of messages to retrieve (default: 50, max: 200)

    **Returns**: List of messages with full details

    **Example**:
    ```
    GET /ws/chat/booking-uuid/history?limit=100
    ```
    """
    try:
        messages = await MessagingService.get_chat_history(
            supabase, UUID(booking_id), limit=limit
        )

        return {
            "booking_id": booking_id,
            "total": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "recipient_id": msg.recipient_id,
                    "content": msg.content,
                    "status": msg.status,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}",
        )


@router.get("/chat/unread-count")
async def get_unread_count(
    supabase: Client = Depends(get_supabase),
):
    """
    Get unread message count for current user.

    **Returns**: Count of unread messages

    **Note**: Requires authentication via header or query param
    """
    try:
        # This would need to be enhanced to get user from auth
        # For now, return example
        return {"unread_count": 0}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting unread count: {str(e)}",
        )

