"""Shared pytest fixtures for unit and integration tests."""
import pytest
from datetime import date, timedelta
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models.user import User
from app.models.property import Property
from app.models.booking import Booked
from app.models.review import Review


@pytest.fixture(name="session")
def session_fixture():
    """In-memory SQLite session, isolated per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def landlord(session):
    user = User(
        username="test_landlord",
        email="landlord@test.com",
        password="hashedpassword",
        role="landlord",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def tenant(session):
    user = User(
        username="test_tenant",
        email="tenant@test.com",
        password="hashedpassword",
        role="tenant",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def sample_property(session, landlord):
    prop = Property(
        landlordID=landlord.id,
        title="Test Room",
        address="123 Test St",
        price=1500.0,
        description="Cozy test room",
        amenities="wifi,furnished",
        photo_url="https://example.com/photo.jpg",
        availability_start=date.today(),
        availability_end=date.today() + timedelta(days=365),
        lease_duration_months=6,
        status="active",
    )
    session.add(prop)
    session.commit()
    session.refresh(prop)
    return prop


@pytest.fixture
def completed_booking(session, tenant, sample_property):
    booking = Booked(
        propertyID=sample_property.propertyID,
        userID=tenant.id,
        move_in_date=date.today() - timedelta(days=200),
        lease_duration_months=6,
        applicant_name="Test Tenant",
        applicant_contact="test@mail.com",
        student_id="816000000",
        message="Test message",
        status="completed",
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking