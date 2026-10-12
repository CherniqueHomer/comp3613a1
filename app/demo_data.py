from datetime import date, timedelta

from sqlmodel import Session

from app.database import engine
from app.models.property import Property
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.repositories.user import UserRepository
from app.utilities.security import encrypt_password

DEMO_LANDLORD_USERNAME = "demo-landlord"
DEMO_LANDLORD_PASSWORD = "landlordpass"


def seed_demo_properties() -> int:
    """Create the marker landlord and sample listings, without duplicating them."""
    today = date.today()
    availability_end = today + timedelta(days=365)
    property_specs: list[tuple[str, str, float, str, str, str]] = [
        (
            "Historic Lincolnville Room",
            "Lincolnville, St. Augustine, FL",
            850,
            "A furnished room in a shared home near the historic district.",
            "Furnished, Wi-Fi, Air conditioning",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        ),
        (
            "Uptown Student Apartment",
            "Uptown, St. Augustine, FL",
            1150,
            "A bright apartment with convenient access to downtown and campus.",
            "Kitchen, Laundry, Wi-Fi, Parking",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
        ),
        (
            "Vilano Beach Shared Suite",
            "Vilano Beach, St. Augustine, FL",
            975,
            "A private bedroom in a shared coastal home.",
            "Furnished, Wi-Fi, Air conditioning, Shared kitchen",
            "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
        ),
        (
            "St. Augustine South Cottage",
            "St. Augustine South, FL",
            1050,
            "A quiet furnished cottage with a short drive to central St. Augustine.",
            "Furnished, Kitchen, Laundry, Parking",
            "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde",
        ),
        (
            "Beachside Student Room",
            "St. Augustine Beach, FL",
            900,
            "A comfortable room in a shared home near the beach.",
            "Furnished, Wi-Fi, Shared kitchen, Bike storage",
            "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d",
        ),
        (
            "Palencia One-Bedroom",
            "Palencia, St. Augustine, FL",
            1250,
            "A one-bedroom rental in a residential community north of town.",
            "Kitchen, Laundry, Air conditioning, Parking",
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
        ),
    ]

    with Session(engine) as session:
        user_repository = UserRepository(session)
        landlord = user_repository.get_by_username(DEMO_LANDLORD_USERNAME)
        if landlord is None:
            landlord = User(
                username=DEMO_LANDLORD_USERNAME,
                email="demo-landlord@example.com",
                password=encrypt_password(DEMO_LANDLORD_PASSWORD),
                role="landlord",
            )
            session.add(landlord)
            session.commit()
            session.refresh(landlord)
        elif landlord.role != "landlord":
            raise ValueError(
                f"Cannot seed demo listings: {DEMO_LANDLORD_USERNAME} "
                "already exists without the landlord role."
            )

        if landlord.id is None:
            raise ValueError("Cannot seed demo listings: landlord has no database ID.")

        property_repository = PropertyRepository(session)
        existing = {
            (item.title, item.address)
            for item in property_repository.get_for_landlord(landlord.id)
        }
        created = 0
        for title, address, price, description, amenities, photo_url in property_specs:
            if (title, address) in existing:
                continue
            property_record = Property(
                landlordID=landlord.id,
                title=title,
                address=address,
                price=price,
                description=description,
                amenities=amenities,
                photo_url=photo_url,
                availability_start=today,
                availability_end=availability_end,
                lease_duration_months=12,
                status="active",
            )
            property_repository.create(property_record)
            created += 1

    return created
