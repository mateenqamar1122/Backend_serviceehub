"""
WebSocket connection manager for real-time messaging.

Handles:
- Active WebSocket connections per chat room (booking)
- Broadcasting messages to participants
- Connection/disconnection logic
- Message routing
"""
import logging
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""

    def __init__(self):
        """Initialize connection manager."""
        # Format: {booking_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, booking_id: str, user_id: str, websocket: WebSocket):
        """
        Register new WebSocket connection.

        Args:
            booking_id: Booking/chat room ID
            user_id: User ID connecting
            websocket: WebSocket connection object
        """
        await websocket.accept()

        # Initialize chat room if doesn't exist
        if booking_id not in self.active_connections:
            self.active_connections[booking_id] = {}

        # Add connection to room
        self.active_connections[booking_id][user_id] = websocket

        logger.info(f"User {user_id} connected to booking {booking_id}")

    def disconnect(self, booking_id: str, user_id: str):
        """
        Remove WebSocket connection.

        Args:
            booking_id: Booking/chat room ID
            user_id: User ID disconnecting
        """
        if booking_id in self.active_connections:
            if user_id in self.active_connections[booking_id]:
                del self.active_connections[booking_id][user_id]

            # Clean up empty rooms
            if not self.active_connections[booking_id]:
                del self.active_connections[booking_id]

        logger.info(f"User {user_id} disconnected from booking {booking_id}")

    async def broadcast_to_room(
        self,
        booking_id: str,
        message: dict,
        exclude_user: str = None,
    ):
        """
        Send message to all users in a chat room.

        Args:
            booking_id: Booking/chat room ID
            message: Message dict to broadcast
            exclude_user: User ID to exclude (optional)
        """
        if booking_id not in self.active_connections:
            return

        # Send to all connected users in room
        for user_id, connection in self.active_connections[booking_id].items():
            # Optionally exclude sender
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {str(e)}")

    async def send_personal_message(
        self,
        booking_id: str,
        user_id: str,
        message: dict,
    ):
        """
        Send message to specific user.

        Args:
            booking_id: Booking/chat room ID
            user_id: Target user ID
            message: Message dict
        """
        if booking_id not in self.active_connections:
            return

        if user_id not in self.active_connections[booking_id]:
            return

        connection = self.active_connections[booking_id][user_id]

        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message to {user_id}: {str(e)}")

    def get_room_users(self, booking_id: str) -> Set[str]:
        """
        Get all connected users in a room.

        Args:
            booking_id: Booking/chat room ID

        Returns:
            Set of user IDs connected to room
        """
        if booking_id not in self.active_connections:
            return set()

        return set(self.active_connections[booking_id].keys())

    def get_room_count(self, booking_id: str) -> int:
        """
        Get number of connected users in room.

        Args:
            booking_id: Booking/chat room ID

        Returns:
            Number of connected users
        """
        if booking_id not in self.active_connections:
            return 0

        return len(self.active_connections[booking_id])

    def get_active_rooms(self) -> Dict[str, int]:
        """
        Get all active chat rooms with user count.

        Returns:
            Dict of {booking_id: user_count}
        """
        return {
            booking_id: len(users)
            for booking_id, users in self.active_connections.items()
            if users
        }


# Global connection manager instance
manager = ConnectionManager()

