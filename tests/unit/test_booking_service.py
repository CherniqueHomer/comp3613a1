import pytest
from datetime import date, timedelta
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate


@pytest.fixture
def service(session):
    return BookingService(
        BookingRepository(session),
        PropertyRepository(session),
        ReviewRepository(session)
    )


@pytest.fixture
def valid_booking_details():
    return BookingCreate(
        move_in_date=date.today() + timedelta(days=10),
        lease_duration_months=6,
        applicant_name="Bob",
        applicant_contact="bob@test.com",
        student_id="816000000",
        message="Looking forward",
    )


def test_U_BS_1_tenant_books(service, tenant, sample_property, valid_booking_details):
    booking = service.request_booking(
        tenant, sample_property.propertyID, valid_booking_details
    )
    assert booking.bookingID is not None
    assert booking.status.lower() == "pending"
    assert booking.userID == tenant.id


def test_U_BS_2_landlord_cannot_book(service, landlord, sample_property, valid_booking_details):
    with pytest.raises(PermissionError):
        service.request_booking(
            landlord, sample_property.propertyID, valid_booking_details
        )


def test_U_BS_3_date_outside_availability(service, tenant, sample_property):
    bad_details = BookingCreate(
        move_in_date=date.today() - timedelta(days=10),
        lease_duration_months=6,
        applicant_name="Bob",
        applicant_contact="bob@test.com",
        student_id="816000000",
        message="Bad date",
    )
    with pytest.raises(ValueError):
        service.request_booking(tenant, sample_property.propertyID, bad_details)


def test_U_BS_4_nonexistent_property(service, tenant, valid_booking_details):
    with pytest.raises(ValueError):
        service.request_booking(tenant, 99999, valid_booking_details)