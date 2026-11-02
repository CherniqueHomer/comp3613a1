import pytest
from datetime import date, timedelta
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate


def test_I_1_booking_persists_to_db(session, tenant, sample_property):
    repo = BookingRepository(session)
    service = BookingService(
        repo,
        PropertyRepository(session),
        ReviewRepository(session)
    )
    
    details = BookingCreate(
        move_in_date=date.today() + timedelta(days=5),
        lease_duration_months=6,
        applicant_name="Integration Test",
        applicant_contact="int@test.com",
        student_id="999",
        message="Test",
    )
    booking = service.request_booking(tenant, sample_property.propertyID, details)
    fetched = repo.get(booking.bookingID)
    assert fetched is not None
    assert fetched.applicant_name == "Integration Test"
    assert fetched.status.lower() == "pending"


def test_I_3_property_retrieval(session, landlord, sample_property):
    repo = PropertyRepository(session)
    fetched = repo.get(sample_property.propertyID)
    assert fetched is not None
    assert fetched.title == "Test Room"
    assert fetched.landlordID == landlord.id
    assert fetched.price == 1500.0