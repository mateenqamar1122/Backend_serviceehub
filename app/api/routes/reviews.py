"""
Review endpoints for service ratings and feedback.

Features:
- Create reviews for completed bookings
- Get provider reviews
- Get service reviews
- Provider responses to reviews
- Rating statistics and distribution
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.api.dependencies import get_current_active_user
from app.db import get_supabase
from app.models import User, ReviewStatus
from app.schemas import (
    ReviewCreate, ReviewResponse, ReviewListResponse,
    ProviderResponseSchema, RatingStatsResponse
)
from app.services import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> ReviewResponse:
    """
    Create a review for a completed booking.

    **Authorization**: Authenticated customer or provider

    **Validation**:
    - Booking must be completed
    - User must be booking participant
    - Only one review per booking
    - Rating must be 1-5
    - Title: 5-200 characters
    - Comment: 10-5000 characters

    **Returns**: 201 Created review

    **Errors**:
    - 400: Booking not completed or invalid data
    - 404: Booking not found
    - 409: Review already exists for booking

    **Example**:
    ```json
    {
      "booking_id": "uuid",
      "service_id": "uuid",
      "title": "Excellent service!",
      "comment": "The provider was very professional and completed the work on time.",
      "rating": 5,
      "quality_rating": 5,
      "professionalism_rating": 5,
      "communication_rating": 4,
      "punctuality_rating": 5
    }
    ```
    """
    try:
        # Verify booking is completed
        is_completed = await ReviewService.verify_booking_completed(
            supabase, review_data.booking_id
        )

        if not is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking must be completed to leave a review",
            )

        # Verify user is booking participant and get reviewee
        is_valid, reviewee_id = await ReviewService.verify_booking_participants(
            supabase, review_data.booking_id, current_user.id
        )

        if not is_valid or not reviewee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this booking",
            )

        # Check if review already exists
        review_exists = await ReviewService.check_review_exists(
            supabase, review_data.booking_id
        )

        if review_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A review already exists for this booking",
            )

        # Create review
        review = await ReviewService.create_review(
            supabase,
            review_data.booking_id,
            review_data.service_id,
            current_user.id,
            reviewee_id,
            review_data.rating,
            review_data.title,
            review_data.comment,
            review_data.quality_rating,
            review_data.professionalism_rating,
            review_data.communication_rating,
            review_data.punctuality_rating,
        )

        if not review:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create review",
            )

        # Update provider's average rating
        await ReviewService.update_provider_rating(supabase, reviewee_id)

        return ReviewResponse(
            id=review.id,
            booking_id=review.booking_id,
            service_id=review.service_id,
            reviewer_id=review.reviewer_id,
            reviewee_id=review.reviewee_id,
            title=review.title,
            comment=review.comment,
            rating=review.rating,
            quality_rating=review.quality_rating,
            professionalism_rating=review.professionalism_rating,
            communication_rating=review.communication_rating,
            punctuality_rating=review.punctuality_rating,
            status=review.status,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count,
            unhelpful_count=review.unhelpful_count,
            response=review.response,
            response_date=review.response_date,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating review: {str(e)}",
        )


@router.get("/providers/{provider_id}", response_model=ReviewListResponse)
async def get_provider_reviews(
    provider_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> ReviewListResponse:
    """
    Get all reviews for a provider.

    **Path Parameters**:
    - provider_id: Provider UUID

    **Query Parameters**:
    - skip: Pagination offset (default: 0)
    - limit: Results per page (default: 10, max: 100)

    **Returns**: Paginated reviews with rating statistics

    **Example**:
    ```
    GET /api/v1/reviews/providers/uuid?skip=0&limit=20
    ```
    """
    try:
        reviews, total = await ReviewService.get_provider_reviews(
            supabase, provider_id, skip=skip, limit=limit
        )

        # Get rating stats
        stats = await ReviewService.get_provider_rating_stats(supabase, provider_id)

        # Convert reviews to response format
        review_responses = [
            ReviewResponse(
                id=r.id,
                booking_id=r.booking_id,
                service_id=r.service_id,
                reviewer_id=r.reviewer_id,
                reviewee_id=r.reviewee_id,
                title=r.title,
                comment=r.comment,
                rating=r.rating,
                quality_rating=r.quality_rating,
                professionalism_rating=r.professionalism_rating,
                communication_rating=r.communication_rating,
                punctuality_rating=r.punctuality_rating,
                status=r.status,
                is_verified_purchase=r.is_verified_purchase,
                helpful_count=r.helpful_count,
                unhelpful_count=r.unhelpful_count,
                response=r.response,
                response_date=r.response_date,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in reviews
        ]

        return ReviewListResponse(
            total=total,
            page=(skip // limit) + 1 if limit > 0 else 1,
            page_size=limit,
            average_rating=stats.get("average_rating", 0),
            rating_distribution=stats.get("rating_distribution", {}),
            items=review_responses,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving provider reviews: {str(e)}",
        )


@router.get("/services/{service_id}", response_model=ReviewListResponse)
async def get_service_reviews(
    service_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> ReviewListResponse:
    """
    Get all reviews for a service.

    **Path Parameters**:
    - service_id: Service UUID

    **Query Parameters**:
    - skip: Pagination offset (default: 0)
    - limit: Results per page (default: 10, max: 100)

    **Returns**: Paginated service reviews

    **Example**:
    ```
    GET /api/v1/reviews/services/uuid?limit=20
    ```
    """
    try:
        reviews, total = await ReviewService.get_service_reviews(
            supabase, service_id, skip=skip, limit=limit
        )

        # Calculate average for this service
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
        else:
            avg_rating = 0

        # Rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[i] = len([r for r in reviews if r.rating == i])

        # Convert reviews to response format
        review_responses = [
            ReviewResponse(
                id=r.id,
                booking_id=r.booking_id,
                service_id=r.service_id,
                reviewer_id=r.reviewer_id,
                reviewee_id=r.reviewee_id,
                title=r.title,
                comment=r.comment,
                rating=r.rating,
                quality_rating=r.quality_rating,
                professionalism_rating=r.professionalism_rating,
                communication_rating=r.communication_rating,
                punctuality_rating=r.punctuality_rating,
                status=r.status,
                is_verified_purchase=r.is_verified_purchase,
                helpful_count=r.helpful_count,
                unhelpful_count=r.unhelpful_count,
                response=r.response,
                response_date=r.response_date,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in reviews
        ]

        return ReviewListResponse(
            total=total,
            page=(skip // limit) + 1 if limit > 0 else 1,
            page_size=limit,
            average_rating=round(avg_rating, 2),
            rating_distribution=rating_dist,
            items=review_responses,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving service reviews: {str(e)}",
        )


@router.get("/stats/provider/{provider_id}", response_model=RatingStatsResponse)
async def get_provider_rating_stats(
    provider_id: UUID,
    supabase: Client = Depends(get_supabase),
) -> RatingStatsResponse:
    """
    Get rating statistics for a provider.

    **Path Parameters**:
    - provider_id: Provider UUID

    **Returns**:
    - Average rating
    - Total number of reviews
    - Distribution of ratings (1-5)
    - Aspect ratings (quality, professionalism, communication, punctuality)

    **Example**:
    ```
    GET /api/v1/reviews/stats/provider/uuid
    ```
    """
    try:
        stats = await ReviewService.get_provider_rating_stats(supabase, provider_id)

        return RatingStatsResponse(
            average_rating=stats.get("average_rating", 0),
            total_reviews=stats.get("total_reviews", 0),
            rating_distribution=stats.get("rating_distribution", {}),
            aspect_ratings=stats.get("aspect_ratings", {}),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving rating stats: {str(e)}",
        )


@router.post("/{review_id}/response", response_model=dict)
async def add_provider_response(
    review_id: UUID,
    response_data: ProviderResponseSchema,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Add provider response to a review.

    **Authorization**: Provider only (must be reviewee)

    **Path Parameters**:
    - review_id: Review UUID

    **Body**:
    - response: Response text (10-2000 characters)

    **Returns**: 200 Response added

    **Errors**:
    - 403: Not the provider being reviewed
    - 404: Review not found

    **Example**:
    ```json
    {
      "response": "Thank you for the positive review! We appreciate your feedback."
    }
    ```
    """
    try:
        # Get review
        review = await ReviewService.get_booking_review(
            supabase, UUID("00000000-0000-0000-0000-000000000000")  # placeholder
        )

        # Check if current user is the reviewee (provider)
        review_response = supabase.table("reviews").select("reviewee_id").eq(
            "id", str(review_id)
        ).execute()

        if not review_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        reviewee_id = review_response.data[0].get("reviewee_id")

        if str(current_user.id) != reviewee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the provider being reviewed can respond",
            )

        # Add response
        updated_review = await ReviewService.add_provider_response(
            supabase, review_id, response_data.response
        )

        if not updated_review:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add response",
            )

        return {
            "id": str(review_id),
            "message": "Response added successfully",
            "response": response_data.response,
            "response_date": updated_review.response_date,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding response: {str(e)}",
        )


@router.post("/{review_id}/helpful", response_model=dict)
async def mark_review_helpful(
    review_id: UUID,
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Mark a review as helpful.

    **Path Parameters**:
    - review_id: Review UUID

    **Returns**: 200 Review marked as helpful

    **Example**:
    ```
    POST /api/v1/reviews/uuid/helpful
    ```
    """
    try:
        success = await ReviewService.mark_review_helpful(supabase, review_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        return {
            "id": str(review_id),
            "message": "Review marked as helpful",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking review helpful: {str(e)}",
        )

