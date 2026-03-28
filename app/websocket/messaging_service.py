"""
Messaging service for real-time chat operations.

Handles:
- Storing messages in PostgreSQL
- Retrieving chat history
- Message validation
- User verification
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from supabase import Client

from app.models import User


class Message:
    """Message model."""
    def __init__(
        self,
        id: str,
        booking_id: str,
        sender_id: str,
        recipient_id: str,
        content: str,
        status: str = "sent",
        created_at: str = None,
        **kwargs
    ):
        self.id = id
        self.booking_id = booking_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.status = status
        self.created_at = created_at


class MessagingService:
    """Service for messaging operations."""

    @staticmethod
    async def save_message(
        supabase: Client,
        booking_id: UUID,
        sender_id: UUID,
        recipient_id: UUID,
        content: str,
    ) -> Optional[Message]:
        """
        Save message to database.

        Args:
            supabase: Supabase client
            booking_id: Booking ID
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            content: Message content

        Returns:
            Message object or None if failed
        """
        try:
            response = supabase.table("messages").insert({
                "booking_id": str(booking_id),
                "sender_id": str(sender_id),
                "recipient_id": str(recipient_id),
                "content": content,
                "status": "sent",
            }).execute()

            if response.data and len(response.data) > 0:
                msg_data = response.data[0]
                return Message(**msg_data)

            return None
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @staticmethod
    async def get_chat_history(
        supabase: Client,
        booking_id: UUID,
        limit: int = 50,
    ) -> List[Message]:
        """
        Retrieve chat history for a booking.

        Args:
            supabase: Supabase client
            booking_id: Booking ID
            limit: Number of messages to retrieve

        Returns:
            List of messages
        """
        try:
            response = supabase.table("messages").select("*").eq(
                "booking_id", str(booking_id)
            ).order("created_at", desc=False).limit(limit).execute()

            messages = [Message(**msg) for msg in response.data or []]
            return messages
        except Exception as e:
            print(f"Error retrieving chat history: {str(e)}")
            return []

    @staticmethod
    async def mark_message_as_read(
        supabase: Client,
        message_id: UUID,
    ) -> bool:
        """
        Mark message as read.

        Args:
            supabase: Supabase client
            message_id: Message ID

        Returns:
            True if successful
        """
        try:
            supabase.table("messages").update({
                "status": "read",
                "read_at": datetime.utcnow().isoformat()
            }).eq("id", str(message_id)).execute()
            return True
        except Exception as e:
            print(f"Error marking message as read: {str(e)}")
            return False

    @staticmethod
    async def mark_messages_as_delivered(
        supabase: Client,
        booking_id: UUID,
    ) -> bool:
        """
        Mark all messages in booking as delivered.

        Args:
            supabase: Supabase client
            booking_id: Booking ID

        Returns:
            True if successful
        """
        try:
            supabase.table("messages").update({
                "status": "delivered"
            }).eq("booking_id", str(booking_id)).eq(
                "status", "sent"
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking messages as delivered: {str(e)}")
            return False

    @staticmethod
    async def get_unread_count(
        supabase: Client,
        recipient_id: UUID,
    ) -> int:
        """
        Get count of unread messages for user.

        Args:
            supabase: Supabase client
            recipient_id: Recipient user ID

        Returns:
            Count of unread messages
        """
        try:
            response = supabase.table("messages").select(
                "id", count="exact"
            ).eq("recipient_id", str(recipient_id)).neq("status", "read").execute()
            return response.count or 0
        except Exception as e:
            print(f"Error getting unread count: {str(e)}")
            return 0

    @staticmethod
    async def verify_booking_participants(
        supabase: Client,
        booking_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Verify user is participant in booking.

        Args:
            supabase: Supabase client
            booking_id: Booking ID
            user_id: User ID to verify

        Returns:
            True if user is customer or provider
        """
        try:
            response = supabase.table("bookings").select(
                "id, customer_id, provider_id"
            ).eq("id", str(booking_id)).execute()

            if not response.data:
                return False

            booking = response.data[0]
            user_id_str = str(user_id)

            # Check if user is customer or provider
            is_participant = (
                booking.get("customer_id") == user_id_str or
                booking.get("provider_id") == user_id_str
            )

            return is_participant
        except Exception as e:
            print(f"Error verifying participants: {str(e)}")
            return False

    @staticmethod
    async def get_booking_participants(
        supabase: Client,
        booking_id: UUID,
    ) -> tuple:
        """
        Get customer and provider IDs for booking.

        Args:
            supabase: Supabase client
            booking_id: Booking ID

        Returns:
            Tuple of (customer_id, provider_id) or (None, None)
        """
        try:
            response = supabase.table("bookings").select(
                "customer_id, provider_id"
            ).eq("id", str(booking_id)).execute()

            if not response.data:
                return None, None

            booking = response.data[0]
            return booking.get("customer_id"), booking.get("provider_id")
        except Exception as e:
            print(f"Error getting booking participants: {str(e)}")
            return None, None

    @staticmethod
    async def delete_message(
        supabase: Client,
        message_id: UUID,
        sender_id: UUID,
    ) -> bool:
        """
        Delete message (sender only).

        Args:
            supabase: Supabase client
            message_id: Message ID
            sender_id: Sender user ID

        Returns:
            True if successful
        """
        try:
            # Verify sender owns message
            response = supabase.table("messages").select("id").eq(
                "id", str(message_id)
            ).eq("sender_id", str(sender_id)).execute()

            if not response.data:
                return False

            # Delete message
            supabase.table("messages").delete().eq(
                "id", str(message_id)
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting message: {str(e)}")
            return False

