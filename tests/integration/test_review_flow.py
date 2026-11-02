from app.repositories.review import ReviewRepository
from app.repositories.booking import BookingRepository
from app.services.review_service import ReviewService


def test_I_2_review_fk_links(session, tenant, completed_booking):
    repo = ReviewRepository(session)
    service = ReviewService(repo, BookingRepository(session))
    review = service.create_review(
        tenant=tenant,
        booking_id=completed_booking.bookingID,
        rating=5,
        comment="Excellent"
    )
    fetched = repo.get_for_booking(completed_booking.bookingID)
    assert fetched is not None
    assert fetched.bookingID == completed_booking.bookingID
    assert fetched.propertyID == completed_booking.propertyID
    assert fetched.userID == tenant.id