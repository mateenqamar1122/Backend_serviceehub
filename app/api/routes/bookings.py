"""
Booking endpoints using Supabase.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.api.dependencies import get_current_active_user
from app.db import get_supabase
from app.models import User, Booking
from app.schemas import BookingCreate, BookingUpdate, BookingReview, BookingResponse, BookingListResponse
from app.services import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> BookingResponse:
    """Create a new booking."""
    booking = await BookingService.create_booking(
        supabase, booking_data, current_user.id
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return booking


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> BookingResponse:
    """Get booking details by ID."""
    booking = await BookingService.get_booking_by_id(supabase, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check authorization
    if booking.customer_id != current_user.id and booking.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking",
        )

    return booking


@router.get("/", response_model=BookingListResponse)
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: str = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> BookingListResponse:
    """
    List bookings for current user (customer or provider).

    Query parameters:
    - skip: Number of bookings to skip (default: 0)
    - limit: Number of bookings to return (default: 10, max: 100)
    - status: Filter by booking status (optional)
    """
    if status_filter:
        bookings = await BookingService.get_bookings_by_status(
            supabase, status_filter, skip=skip, limit=limit
        )
    else:
        # Get bookings where user is customer or provider
        customer_bookings = await BookingService.get_bookings_by_customer(
            supabase, current_user.id, skip=skip, limit=limit
        )
        provider_bookings = await BookingService.get_bookings_by_provider(
            supabase, current_user.id, skip=skip, limit=limit
        )
        bookings = customer_bookings + provider_bookings

    total = await BookingService.get_booking_count(supabase)

    return BookingListResponse(
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        items=bookings,
    )


@router.get("/customer/{customer_id}", response_model=BookingListResponse)
async def list_customer_bookings(
    customer_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> BookingListResponse:
    """Get all bookings for a customer."""
    bookings = await BookingService.get_bookings_by_customer(
        supabase, customer_id, skip=skip, limit=limit
    )
    total = len(bookings)

    return BookingListResponse(
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        items=bookings,
    )


@router.get("/provider/{provider_id}", response_model=BookingListResponse)
async def list_provider_bookings(
    provider_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> BookingListResponse:
    """Get all bookings for a provider."""
    bookings = await BookingService.get_bookings_by_provider(
        supabase, provider_id, skip=skip, limit=limit
    )
    total = len(bookings)

    return BookingListResponse(
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        items=bookings,
    )


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    booking_data: BookingUpdate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> BookingResponse:
    """Update booking status (provider only)."""
    booking = await BookingService.get_booking_by_id(supabase, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this booking",
        )

    updated_booking = await BookingService.update_booking(
        supabase, booking_id, booking_data
    )
    return updated_booking


@router.post("/{booking_id}/review", response_model=BookingResponse)
async def add_booking_review(
    booking_id: UUID,
    review_data: BookingReview,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> BookingResponse:
    """Add review to a completed booking (customer only)."""
    booking = await BookingService.get_booking_by_id(supabase, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer can review",
        )

    if booking.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed bookings",
        )

    reviewed_booking = await BookingService.add_review(
        supabase, booking_id, review_data
    )
    return reviewed_booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking_post(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> BookingResponse:
    """Cancel a booking (customer only) - deprecated, use PATCH instead."""
    booking = await BookingService.get_booking_by_id(supabase, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer can cancel",
        )

    if booking.status not in ["pending", "confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed or already cancelled bookings",
        )

    cancelled_booking = await BookingService.cancel_booking(supabase, booking_id)
    return cancelled_booking


@router.patch("/{booking_id}/accept", response_model=dict, status_code=status.HTTP_200_OK)
async def accept_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Accept pending booking request (provider only).

    Status transition: pending → confirmed

    **Authorization**: Provider who owns the booking

    **Returns**:
    - 200: Booking accepted successfully
    - 403: Not authorized (not the provider)
    - 404: Booking not found
    - 409: Cannot accept - invalid status
    """
    try:
        booking = await BookingService.accept_booking(
            supabase, booking_id, current_user.id
        )

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        return {
            "id": str(booking.id),
            "status": "confirmed",
            "message": "Booking accepted successfully"
        }
    except ValueError as e:
        if "Not authorized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.patch("/{booking_id}/reject", response_model=dict, status_code=status.HTTP_200_OK)
async def reject_booking(
    booking_id: UUID,
    rejection_reason: str = None,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Reject pending booking request (provider only).

    Status transition: pending → declined

    **Authorization**: Provider who owns the booking

    **Parameters**:
    - rejection_reason (optional): Reason for rejection

    **Returns**:
    - 200: Booking rejected successfully
    - 403: Not authorized (not the provider)
    - 404: Booking not found
    - 409: Cannot reject - invalid status
    """
    try:
        booking = await BookingService.reject_booking(
            supabase, booking_id, current_user.id, rejection_reason
        )

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        return {
            "id": str(booking.id),
            "status": "declined",
            "message": "Booking rejected successfully"
        }
    except ValueError as e:
        if "Not authorized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.patch("/{booking_id}/start", response_model=dict, status_code=status.HTTP_200_OK)
async def start_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Start service on confirmed booking (provider only).

    Status transition: confirmed → in_progress

    **Authorization**: Provider who owns the booking

    **Returns**:
    - 200: Service started successfully
    - 403: Not authorized (not the provider)
    - 404: Booking not found
    - 409: Cannot start - booking not confirmed
    """
    try:
        booking = await BookingService.start_booking(
            supabase, booking_id, current_user.id
        )

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        return {
            "id": str(booking.id),
            "status": "in_progress",
            "message": "Service started successfully"
        }
    except ValueError as e:
        if "Not authorized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.patch("/{booking_id}/complete", response_model=dict, status_code=status.HTTP_200_OK)
async def complete_booking(
    booking_id: UUID,
    actual_duration_hours: float = None,
    provider_notes: str = None,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Complete in-progress booking (provider only).

    Status transition: in_progress → completed

    **Authorization**: Provider who owns the booking

    **Parameters**:
    - actual_duration_hours (optional): Actual hours worked
    - provider_notes (optional): Notes about the service

    **Returns**:
    - 200: Service completed successfully
    - 403: Not authorized (not the provider)
    - 404: Booking not found
    - 409: Cannot complete - booking not in_progress
    """
    try:
        booking = await BookingService.complete_booking(
            supabase, booking_id, current_user.id,
            actual_duration_hours, provider_notes
        )

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        return {
            "id": str(booking.id),
            "status": "completed",
            "message": "Service completed successfully"
        }
    except ValueError as e:
        if "Not authorized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.patch("/{booking_id}/cancel", response_model=dict, status_code=status.HTTP_200_OK)
async def cancel_booking_patch(
    booking_id: UUID,
    cancellation_reason: str = None,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Cancel booking by customer.

    Status transition: pending/confirmed → cancelled

    **Authorization**: Customer who created the booking

    **Parameters**:
    - cancellation_reason (optional): Reason for cancellation

    **Returns**:
    - 200: Booking cancelled successfully
    - 403: Not authorized (not the customer)
    - 404: Booking not found
    - 409: Cannot cancel - booking already started or completed
    """
    try:
        booking = await BookingService.cancel_booking_with_reason(
            supabase, booking_id, current_user.id, cancellation_reason
        )

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        return {
            "id": str(booking.id),
            "status": "cancelled",
            "message": "Booking cancelled successfully"
        }
    except ValueError as e:
        if "Not authorized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
