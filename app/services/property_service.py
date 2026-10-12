from datetime import date

from app.models.property import Property
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.property import PropertyCreate


class PropertyService:
    def __init__(self, property_repository: PropertyRepository):
        self.property_repository = property_repository

    def publish_listing(self, landlord: User, details: PropertyCreate) -> Property:
        self._require_landlord(landlord)
        self.validate_listing(details)

        property_record = Property(
            landlordID=self._landlord_id(landlord),
            title=details.title,
            address=details.address,
            price=details.price,
            description=details.description,
            amenities=details.amenities,
            photo_url=details.photo_url,
            availability_start=details.availability_start,
            availability_end=details.availability_end,
            lease_duration_months=details.lease_duration_months,
            status="active",
        )

        return self.property_repository.create(property_record)

    def get_landlord_listings(self, landlord: User) -> list[Property]:
        self._require_landlord(landlord)
        return self.property_repository.get_for_landlord(self._landlord_id(landlord))

    def get_owned_listing(self, landlord: User, property_id: int) -> Property:
        self._require_landlord(landlord)
        listing = self.property_repository.get_owned(
            property_id,
            self._landlord_id(landlord),
        )
        if listing is None:
            raise LookupError("Listing not found.")
        return listing

    def browse_listings(
        self,
        *,
        min_price: float | None = None,
        max_price: float | None = None,
        amenities: list[str] | None = None,
        available_on: date | None = None,
    ) -> list[Property]:
        return self.property_repository.search_active(
            min_price=min_price,
            max_price=max_price,
            amenities=amenities,
            available_on=available_on,
        )

    def get_active_listing(self, property_id: int) -> Property:
        listing = self.property_repository.get(property_id)
        if listing is None or listing.status.lower() != "active":
            raise LookupError("Listing not found.")
        return listing

    @staticmethod
    def _require_landlord(landlord: User) -> None:
        if landlord.role != "landlord":
            raise PermissionError("Only landlords can manage listings.")

    @staticmethod
    def _landlord_id(landlord: User) -> int:
        if landlord.id is None:
            raise ValueError("Landlord account has no database ID.")
        return landlord.id

    @staticmethod
    def validate_listing(details: PropertyCreate) -> None:
        if not details.title.strip():
            raise ValueError("Enter a title for your listing.")
        if not details.address.strip():
            raise ValueError("Enter the property address.")
        if not details.description.strip():
            raise ValueError("Add a description for your listing.")
        if not details.photo_url.strip():
            raise ValueError("Add a photo URL for your listing.")
        if details.price <= 0:
            raise ValueError("Enter a price greater than zero.")
        if details.lease_duration_months <= 0:
            raise ValueError("Lease duration must be at least one month.")
        if details.availability_end < details.availability_start:
            raise ValueError("Availability end date must be on or after the start date.")