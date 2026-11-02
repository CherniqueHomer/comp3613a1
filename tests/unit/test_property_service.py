import pytest
from datetime import date, timedelta
from app.repositories.property import PropertyRepository
from app.services.property_service import PropertyService
from app.schemas.property import PropertyCreate


@pytest.fixture
def service(session):
    return PropertyService(PropertyRepository(session))


@pytest.fixture
def valid_details():
    return PropertyCreate(
        title="New Room",
        address="456 New St",
        price=1200.0,
        description="A great room",
        amenities="wifi",
        photo_url="https://example.com/new.jpg",
        availability_start=date.today(),
        availability_end=date.today() + timedelta(days=365),
        lease_duration_months=6,
    )


def test_U_PS_1_landlord_publishes(service, landlord, valid_details):
    prop = service.publish_listing(landlord, valid_details)
    assert prop.propertyID is not None
    assert prop.status == "active"
    assert prop.title == "New Room"


def test_U_PS_2_tenant_cannot_publish(service, tenant, valid_details):
    with pytest.raises(PermissionError):
        service.publish_listing(tenant, valid_details)


def test_U_PS_4_landlord_id_set(service, landlord, valid_details):
    prop = service.publish_listing(landlord, valid_details)
    assert prop.landlordID == landlord.id