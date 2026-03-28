"""
Booking service business logic using Supabase.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from supabase import Client

from app.models import Booking, Service
from app.schemas import BookingCreate, BookingUpdate, BookingReview


class BookingService:
    """Booking service for Supabase database operations."""

    @staticmethod
    async def create_booking(
        supabase: Client,
        booking_data: BookingCreate,
        customer_id: UUID
    ) -> Optional[Booking]:
        """Create a new booking."""
        # Get service to calculate total price and get provider_id
        service_response = supabase.table("services").select("*").eq(
            "id", str(booking_data.service_id)
        ).execute()

        if not service_response.data or len(service_response.data) == 0:
            return None

        service = Service(**service_response.data[0])
        total_price = service.price_per_hour * booking_data.duration_hours

        response = supabase.table("bookings").insert({
            "service_id": str(booking_data.service_id),
            "customer_id": str(customer_id),
            "provider_id": str(service.provider_id),
            "scheduled_date": booking_data.scheduled_date.isoformat(),
            "duration_hours": booking_data.duration_hours,
            "total_price": total_price,
            "notes": booking_data.notes,
            "status": "pending",
        }).execute()

        if response.data:
            return Booking(**response.data[0])
        raise ValueError("Failed to create booking")

    @staticmethod
    async def get_booking_by_id(
        supabase: Client,
        booking_id: UUID
    ) -> Optional[Booking]:
        """Get booking by ID."""
        response = supabase.table("bookings").select("*").eq("id", str(booking_id)).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def get_bookings_by_customer(
        supabase: Client,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> List[Booking]:
        """Get all bookings for a customer."""
        response = supabase.table("bookings").select("*").eq(
            "customer_id", str(customer_id)
        ).range(skip, skip + limit - 1).execute()

        return [Booking(**booking) for booking in response.data]

    @staticmethod
    async def get_bookings_by_provider(
        supabase: Client,
        provider_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> List[Booking]:
        """Get all bookings for a provider."""
        response = supabase.table("bookings").select("*").eq(
            "provider_id", str(provider_id)
        ).range(skip, skip + limit - 1).execute()

        return [Booking(**booking) for booking in response.data]

    @staticmethod
    async def get_all_bookings(
        supabase: Client,
        skip: int = 0,
        limit: int = 10
    ) -> List[Booking]:
        """Get all bookings."""
        response = supabase.table("bookings").select("*").range(
            skip, skip + limit - 1
        ).execute()

        return [Booking(**booking) for booking in response.data]

    @staticmethod
    async def update_booking(
        supabase: Client,
        booking_id: UUID,
        booking_data: BookingUpdate
    ) -> Optional[Booking]:
        """Update booking information."""
        update_data = booking_data.dict(exclude_unset=True)

        response = supabase.table("bookings").update(update_data).eq(
            "id", str(booking_id)
        ).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def add_review(
        supabase: Client,
        booking_id: UUID,
        review_data: BookingReview
    ) -> Optional[Booking]:
        """Add review to a completed booking."""
        response = supabase.table("bookings").update({
            "rating": review_data.rating,
            "review": review_data.review,
        }).eq("id", str(booking_id)).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def cancel_booking(
        supabase: Client,
        booking_id: UUID
    ) -> Optional[Booking]:
        """Cancel a booking."""
        response = supabase.table("bookings").update(
            {"status": "cancelled"}
        ).eq("id", str(booking_id)).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def get_booking_count(supabase: Client) -> int:
        """Get total count of bookings."""
        response = supabase.table("bookings").select("id", count="exact").execute()
        return response.count or 0

    @staticmethod
    async def get_bookings_by_status(
        supabase: Client,
        status: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Booking]:
        """Get bookings by status."""
        response = supabase.table("bookings").select("*").eq(
            "status", status
        ).range(skip, skip + limit - 1).execute()

        return [Booking(**booking) for booking in response.data]

    @staticmethod
    async def accept_booking(
        supabase: Client,
        booking_id: UUID,
        provider_id: UUID
    ) -> Optional[Booking]:
        """
        Accept pending booking request (provider only).

        Status transition: pending → confirmed
        """
        # Verify booking exists and belongs to provider
        booking_response = supabase.table("bookings").select("*").eq(
            "id", str(booking_id)
        ).execute()

        if not booking_response.data or len(booking_response.data) == 0:
            return None

        booking = Booking(**booking_response.data[0])

        # Verify provider owns this booking
        if booking.provider_id != provider_id:
            raise ValueError("Not authorized to accept this booking")

        # Verify booking is in pending status
        if booking.status != "pending":
            raise ValueError(f"Can only accept pending bookings. Current status: {booking.status}")

        # Update status to confirmed
        response = supabase.table("bookings").update({
            "status": "confirmed"
        }).eq("id", str(booking_id)).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def reject_booking(
        supabase: Client,
        booking_id: UUID,
        provider_id: UUID,
        rejection_reason: str = None
    ) -> Optional[Booking]:
        """
        Reject pending booking request (provider only).

        Status transition: pending → declined
        """
        # Verify booking exists and belongs to provider
        booking_response = supabase.table("bookings").select("*").eq(
            "id", str(booking_id)
        ).execute()

        if not booking_response.data or len(booking_response.data) == 0:
            return None

        booking = Booking(**booking_response.data[0])

        # Verify provider owns this booking
        if booking.provider_id != provider_id:
            raise ValueError("Not authorized to reject this booking")

        # Verify booking is in pending status
        if booking.status != "pending":
            raise ValueError(f"Can only reject pending bookings. Current status: {booking.status}")

        # Update status to declined
        update_data = {"status": "declined"}
        if rejection_reason:
            update_data["provider_notes"] = rejection_reason

        response = supabase.table("bookings").update(update_data).eq(
            "id", str(booking_id)
        ).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def start_booking(
        supabase: Client,
        booking_id: UUID,
        provider_id: UUID
    ) -> Optional[Booking]:
        """
        Start service on confirmed booking (provider only).

        Status transition: confirmed → in_progress
        """
        # Verify booking exists and belongs to provider
        booking_response = supabase.table("bookings").select("*").eq(
            "id", str(booking_id)
        ).execute()

        if not booking_response.data or len(booking_response.data) == 0:
            return None

        booking = Booking(**booking_response.data[0])

        # Verify provider owns this booking
        if booking.provider_id != provider_id:
            raise ValueError("Not authorized to start this booking")

        # Verify booking is in confirmed status
        if booking.status != "confirmed":
            raise ValueError(f"Can only start confirmed bookings. Current status: {booking.status}")

        # Update status to in_progress
        response = supabase.table("bookings").update({
            "status": "in_progress"
        }).eq("id", str(booking_id)).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def complete_booking(
        supabase: Client,
        booking_id: UUID,
        provider_id: UUID,
        actual_duration_hours: float = None,
        provider_notes: str = None
    ) -> Optional[Booking]:
        """
        Complete in-progress booking (provider only).

        Status transition: in_progress → completed
        """
        # Verify booking exists and belongs to provider
        booking_response = supabase.table("bookings").select("*").eq(
            "id", str(booking_id)
        ).execute()

        if not booking_response.data or len(booking_response.data) == 0:
            return None

        booking = Booking(**booking_response.data[0])

        # Verify provider owns this booking
        if booking.provider_id != provider_id:
            raise ValueError("Not authorized to complete this booking")

        # Verify booking is in in_progress status
        if booking.status != "in_progress":
            raise ValueError(f"Can only complete in_progress bookings. Current status: {booking.status}")

        # Update status to completed
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }

        if actual_duration_hours is not None:
            update_data["actual_duration_hours"] = actual_duration_hours

        if provider_notes is not None:
            update_data["provider_notes"] = provider_notes

        response = supabase.table("bookings").update(update_data).eq(
            "id", str(booking_id)
        ).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None

    @staticmethod
    async def cancel_booking_with_reason(
        supabase: Client,
        booking_id: UUID,
        customer_id: UUID,
        cancellation_reason: str = None
    ) -> Optional[Booking]:
        """
        Cancel booking by customer.

        Can cancel: pending → cancelled, confirmed → cancelled
        Cannot cancel: in_progress, completed, already cancelled/declined
        """
        # Verify booking exists and belongs to customer
        booking_response = supabase.table("bookings").select("*").eq(
            "id", str(booking_id)
        ).execute()

        if not booking_response.data or len(booking_response.data) == 0:
            return None

        booking = Booking(**booking_response.data[0])

        # Verify customer owns this booking
        if booking.customer_id != customer_id:
            raise ValueError("Not authorized to cancel this booking")

        # Verify booking can be cancelled
        if booking.status not in ["pending", "confirmed"]:
            raise ValueError(
                f"Can only cancel pending or confirmed bookings. Current status: {booking.status}"
            )

        # Update status to cancelled
        update_data = {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_by": str(customer_id)
        }

        if cancellation_reason:
            update_data["cancellation_reason"] = cancellation_reason

        response = supabase.table("bookings").update(update_data).eq(
            "id", str(booking_id)
        ).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])
        return None
