import pytest
from app.repositories.review import ReviewRepository
from app.repositories.booking import BookingRepository
from app.services.review_service import ReviewService
from app.models.booking import Booked
from app.models.user import User
from datetime import date


@pytest.fixture
def service(session):
    return ReviewService(ReviewRepository(session), BookingRepository(session))


def test_U_RS_1_tenant_reviews_completed(service, tenant, completed_booking):
    review = service.create_review(
        tenant=tenant,
        booking_id=completed_booking.bookingID,
        rating=5,
        comment="Great stay!"
    )
    assert review.reviewID is not None
    assert review.rating == 5
    assert review.bookingID == completed_booking.bookingID


def test_U_RS_2_pending_booking_cannot_be_reviewed(service, tenant, session, sample_property):
    pending_booking = Booked(
        propertyID=sample_property.propertyID,
        userID=tenant.id,
        move_in_date=date.today(),
        lease_duration_months=6,
        applicant_name="T",
        applicant_contact="t@t.com",
        student_id="123",
        message="hi",
        status="pending",
    )
    session.add(pending_booking)
    session.commit()
    session.refresh(pending_booking)

    with pytest.raises(ValueError):
        service.create_review(
            tenant=tenant,
            booking_id=pending_booking.bookingID,
            rating=4,
            comment="Too early"
        )


def test_U_RS_3_duplicate_review(service, tenant, completed_booking):
    service.create_review(
        tenant=tenant,
        booking_id=completed_booking.bookingID,
        rating=4,
        comment="First"
    )
    with pytest.raises(ValueError):
        service.create_review(
            tenant=tenant,
            booking_id=completed_booking.bookingID,
            rating=5,
            comment="Second"
        )


def test_U_RS_4_wrong_tenant(service, session, completed_booking):
    wrong_tenant = User(
        username="wrong", email="wrong@test.com", password="pw", role="tenant"
    )
    session.add(wrong_tenant)
    session.commit()
    session.refresh(wrong_tenant)

    with pytest.raises(LookupError):
        service.create_review(
            tenant=wrong_tenant,
            booking_id=completed_booking.bookingID,
            rating=5,
            comment="Not mine"
        )