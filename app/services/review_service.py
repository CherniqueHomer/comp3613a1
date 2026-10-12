from app.models.review import Review
from app.models.booking import Booked
from app.models.user import User
from app.repositories.booking import BookingRepository
from app.repositories.review import ReviewRepository


class ReviewService:
    def __init__(
        self,
        review_repository: ReviewRepository,
        booking_repository: BookingRepository | None = None,
    ):
        self.review_repository = review_repository
        self.booking_repository = booking_repository

    def create_review(
        self,
        tenant: User,
        booking_id: int,
        rating: int,
        comment: str,
    ) -> Review:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        booking = self.get_reviewable_booking(tenant, booking_id)
        review_record = Review(
            bookingID=booking_id,
            propertyID=booking.propertyID,
            userID=tenant.id,
            rating=rating,
            comment=comment.strip() or None,
        )
        return self.review_repository.create(review_record)

    def get_reviewable_booking(self, tenant: User, booking_id: int) -> Booked:
        if tenant.role not in {"tenant", "regular_user"} or tenant.id is None:
            raise PermissionError("Only tenants can review their own bookings.")

        booking = self._booking_repository().get(booking_id)
        if booking is None or booking.userID != tenant.id:
            raise LookupError("Booking not found.")
        if booking.status.lower() != "completed":
            raise ValueError("You can only review a completed stay.")
        if self.review_repository.get_for_booking(booking_id) is not None:
            raise ValueError("This booking has already been reviewed.")
        return booking

    def get_submitted_review(self, tenant: User, booking_id: int) -> Review:
        if tenant.id is None:
            raise PermissionError("Tenant account has no database ID.")
        booking = self._booking_repository().get(booking_id)
        if booking is None or booking.userID != tenant.id:
            raise LookupError("Booking not found.")
        review = self.review_repository.get_for_booking(booking_id)
        if review is None:
            raise LookupError("Review not found.")
        return review

    def get_property_reviews(self, property_id: int) -> list[Review]:
        return self.review_repository.get_for_property(property_id)

    def _booking_repository(self) -> BookingRepository:
        if self.booking_repository is None:
            raise RuntimeError(
                "BookingRepository is required for booking review operations."
            )
        return self.booking_repository