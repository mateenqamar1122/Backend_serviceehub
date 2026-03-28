"""
Review service business logic using Supabase.

Handles:
- Creating reviews for completed bookings
- Rating validation
- Provider rating aggregation
- Review moderation
"""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from supabase import Client

from app.models import Review, ReviewStatus


class ReviewService:
    """Service for review operations."""

    @staticmethod
    async def verify_booking_completed(
        supabase: Client,
        booking_id: UUID,
    ) -> bool:
        """
        Verify booking is completed.

        Args:
            supabase: Supabase client
            booking_id: Booking ID

        Returns:
            True if booking status is 'completed'
        """
        try:
            response = supabase.table("bookings").select("status").eq(
                "id", str(booking_id)
            ).execute()

            if not response.data:
                return False

            booking = response.data[0]
            return booking.get("status") == "completed"
        except Exception as e:
            print(f"Error verifying booking: {str(e)}")
            return False

    @staticmethod
    async def verify_booking_participants(
        supabase: Client,
        booking_id: UUID,
        reviewer_id: UUID,
    ) -> Tuple[bool, Optional[UUID]]:
        """
        Verify reviewer is booking participant and get reviewee ID.

        Args:
            supabase: Supabase client
            booking_id: Booking ID
            reviewer_id: Reviewer user ID

        Returns:
            Tuple of (is_valid, reviewee_id)
        """
        try:
            response = supabase.table("bookings").select(
                "customer_id, provider_id"
            ).eq("id", str(booking_id)).execute()

            if not response.data:
                return False, None

            booking = response.data[0]
            customer_id = booking.get("customer_id")
            provider_id = booking.get("provider_id")

            reviewer_id_str = str(reviewer_id)

            # Reviewer must be customer or provider
            if reviewer_id_str == customer_id:
                # Customer reviewing provider
                return True, UUID(provider_id)
            elif reviewer_id_str == provider_id:
                # Provider reviewing customer
                return True, UUID(customer_id)
            else:
                return False, None
        except Exception as e:
            print(f"Error verifying participants: {str(e)}")
            return False, None

    @staticmethod
    async def check_review_exists(
        supabase: Client,
        booking_id: UUID,
    ) -> bool:
        """
        Check if review already exists for booking.

        Args:
            supabase: Supabase client
            booking_id: Booking ID

        Returns:
            True if review exists
        """
        try:
            response = supabase.table("reviews").select("id").eq(
                "booking_id", str(booking_id)
            ).limit(1).execute()

            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking review: {str(e)}")
            return False

    @staticmethod
    async def create_review(
        supabase: Client,
        booking_id: UUID,
        service_id: UUID,
        reviewer_id: UUID,
        reviewee_id: UUID,
        rating: int,
        title: str,
        comment: str,
        quality_rating: Optional[int] = None,
        professionalism_rating: Optional[int] = None,
        communication_rating: Optional[int] = None,
        punctuality_rating: Optional[int] = None,
    ) -> Optional[Review]:
        """
        Create a new review.

        Args:
            supabase: Supabase client
            booking_id: Booking ID
            service_id: Service ID
            reviewer_id: Reviewer user ID
            reviewee_id: Reviewee user ID
            rating: Overall rating (1-5)
            title: Review title
            comment: Review comment
            quality_rating: Optional quality rating (1-5)
            professionalism_rating: Optional professionalism rating (1-5)
            communication_rating: Optional communication rating (1-5)
            punctuality_rating: Optional punctuality rating (1-5)

        Returns:
            Review object or None if failed
        """
        try:
            review_data = {
                "booking_id": str(booking_id),
                "service_id": str(service_id),
                "reviewer_id": str(reviewer_id),
                "reviewee_id": str(reviewee_id),
                "rating": rating,
                "title": title,
                "comment": comment,
                "status": ReviewStatus.PUBLISHED,
                "is_verified_purchase": True,
            }

            # Add aspect ratings if provided
            if quality_rating:
                review_data["quality_rating"] = quality_rating
            if professionalism_rating:
                review_data["professionalism_rating"] = professionalism_rating
            if communication_rating:
                review_data["communication_rating"] = communication_rating
            if punctuality_rating:
                review_data["punctuality_rating"] = punctuality_rating

            response = supabase.table("reviews").insert(review_data).execute()

            if response.data and len(response.data) > 0:
                return Review(**response.data[0])

            return None
        except Exception as e:
            print(f"Error creating review: {str(e)}")
            return None

    @staticmethod
    async def update_provider_rating(
        supabase: Client,
        provider_id: UUID,
    ) -> bool:
        """
        Update provider's average rating based on reviews.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID

        Returns:
            True if successful
        """
        try:
            # Get all reviews for provider
            reviews_response = supabase.table("reviews").select(
                "rating"
            ).eq("reviewee_id", str(provider_id)).eq("status", ReviewStatus.PUBLISHED).execute()

            if not reviews_response.data:
                # No reviews, set rating to 0
                supabase.table("users").update({
                    "average_rating": 0,
                    "total_reviews": 0,
                }).eq("id", str(provider_id)).execute()
                return True

            reviews = reviews_response.data
            average_rating = sum(r["rating"] for r in reviews) / len(reviews)
            total_reviews = len(reviews)

            # Update user's average rating
            supabase.table("users").update({
                "average_rating": round(average_rating, 2),
                "total_reviews": total_reviews,
            }).eq("id", str(provider_id)).execute()

            return True
        except Exception as e:
            print(f"Error updating provider rating: {str(e)}")
            return False

    @staticmethod
    async def get_provider_reviews(
        supabase: Client,
        provider_id: UUID,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Review], int]:
        """
        Get all reviews for a provider.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            skip: Pagination offset
            limit: Results per page

        Returns:
            Tuple of (reviews list, total count)
        """
        try:
            # Get total count
            count_response = supabase.table("reviews").select(
                "id", count="exact"
            ).eq("reviewee_id", str(provider_id)).eq("status", ReviewStatus.PUBLISHED).execute()

            total = count_response.count or 0

            # Get paginated reviews
            response = supabase.table("reviews").select("*").eq(
                "reviewee_id", str(provider_id)
            ).eq("status", ReviewStatus.PUBLISHED).order(
                "created_at", desc=True
            ).range(skip, skip + limit - 1).execute()

            reviews = [Review(**r) for r in response.data or []]
            return reviews, total
        except Exception as e:
            print(f"Error getting provider reviews: {str(e)}")
            return [], 0

    @staticmethod
    async def get_service_reviews(
        supabase: Client,
        service_id: UUID,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Review], int]:
        """
        Get all reviews for a service.

        Args:
            supabase: Supabase client
            service_id: Service ID
            skip: Pagination offset
            limit: Results per page

        Returns:
            Tuple of (reviews list, total count)
        """
        try:
            # Get total count
            count_response = supabase.table("reviews").select(
                "id", count="exact"
            ).eq("service_id", str(service_id)).eq("status", ReviewStatus.PUBLISHED).execute()

            total = count_response.count or 0

            # Get paginated reviews
            response = supabase.table("reviews").select("*").eq(
                "service_id", str(service_id)
            ).eq("status", ReviewStatus.PUBLISHED).order(
                "created_at", desc=True
            ).range(skip, skip + limit - 1).execute()

            reviews = [Review(**r) for r in response.data or []]
            return reviews, total
        except Exception as e:
            print(f"Error getting service reviews: {str(e)}")
            return [], 0

    @staticmethod
    async def get_booking_review(
        supabase: Client,
        booking_id: UUID,
    ) -> Optional[Review]:
        """
        Get review for a specific booking.

        Args:
            supabase: Supabase client
            booking_id: Booking ID

        Returns:
            Review object or None
        """
        try:
            response = supabase.table("reviews").select("*").eq(
                "booking_id", str(booking_id)
            ).execute()

            if response.data:
                return Review(**response.data[0])

            return None
        except Exception as e:
            print(f"Error getting booking review: {str(e)}")
            return None

    @staticmethod
    async def add_provider_response(
        supabase: Client,
        review_id: UUID,
        response_text: str,
    ) -> Optional[Review]:
        """
        Add provider response to review.

        Args:
            supabase: Supabase client
            review_id: Review ID
            response_text: Response text

        Returns:
            Updated Review object or None
        """
        try:
            response = supabase.table("reviews").update({
                "response": response_text,
                "response_date": datetime.utcnow().isoformat(),
            }).eq("id", str(review_id)).execute()

            if response.data:
                return Review(**response.data[0])

            return None
        except Exception as e:
            print(f"Error adding provider response: {str(e)}")
            return None

    @staticmethod
    async def mark_review_helpful(
        supabase: Client,
        review_id: UUID,
    ) -> bool:
        """
        Increment helpful count for review.

        Args:
            supabase: Supabase client
            review_id: Review ID

        Returns:
            True if successful
        """
        try:
            # Get current count
            response = supabase.table("reviews").select("helpful_count").eq(
                "id", str(review_id)
            ).execute()

            if not response.data:
                return False

            current_count = response.data[0].get("helpful_count", 0)

            # Increment
            supabase.table("reviews").update({
                "helpful_count": current_count + 1,
            }).eq("id", str(review_id)).execute()

            return True
        except Exception as e:
            print(f"Error marking review helpful: {str(e)}")
            return False

    @staticmethod
    async def get_provider_rating_stats(
        supabase: Client,
        provider_id: UUID,
    ) -> dict:
        """
        Get rating statistics for provider.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID

        Returns:
            Dict with rating stats
        """
        try:
            reviews_response = supabase.table("reviews").select(
                "rating, quality_rating, professionalism_rating, "
                "communication_rating, punctuality_rating"
            ).eq("reviewee_id", str(provider_id)).eq(
                "status", ReviewStatus.PUBLISHED
            ).execute()

            if not reviews_response.data:
                return {
                    "average_rating": 0,
                    "total_reviews": 0,
                    "rating_distribution": {},
                    "aspect_ratings": {},
                }

            reviews = reviews_response.data

            # Calculate average rating
            ratings = [r["rating"] for r in reviews]
            average_rating = sum(ratings) / len(ratings)

            # Rating distribution
            rating_distribution = {}
            for i in range(1, 6):
                rating_distribution[i] = len([r for r in ratings if r == i])

            # Aspect ratings
            aspect_ratings = {}
            for aspect in ["quality_rating", "professionalism_rating", "communication_rating", "punctuality_rating"]:
                values = [r[aspect] for r in reviews if r.get(aspect)]
                if values:
                    aspect_ratings[aspect.replace("_rating", "")] = round(sum(values) / len(values), 2)

            return {
                "average_rating": round(average_rating, 2),
                "total_reviews": len(reviews),
                "rating_distribution": rating_distribution,
                "aspect_ratings": aspect_ratings,
            }
        except Exception as e:
            print(f"Error getting rating stats: {str(e)}")
            return {
                "average_rating": 0,
                "total_reviews": 0,
                "rating_distribution": {},
                "aspect_ratings": {},
            }

