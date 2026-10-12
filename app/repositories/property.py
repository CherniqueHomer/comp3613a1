from datetime import date

from sqlmodel import Session, func, select

from app.models.property import Property


class PropertyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, property_record: Property) -> Property:
        self.db.add(property_record)
        self.db.commit()
        self.db.refresh(property_record)
        return property_record

    def get(self, property_id: int) -> Property | None:
        return self.db.get(Property, property_id)

    def get_active(self) -> list[Property]:
        statement = select(Property).where(func.lower(Property.status) == "active")
        return list(self.db.exec(statement).all())

    def search_active(
        self,
        *,
        min_price: float | None = None,
        max_price: float | None = None,
        amenities: list[str] | None = None,
        available_on: date | None = None,
    ) -> list[Property]:
        statement = select(Property).where(func.lower(Property.status) == "active")
        if min_price is not None:
            statement = statement.where(Property.price >= min_price)
        if max_price is not None:
            statement = statement.where(Property.price <= max_price)
        if available_on is not None:
            statement = statement.where(
                Property.availability_start <= available_on,
                Property.availability_end >= available_on,
            )
        for amenity in amenities or []:
            statement = statement.where(Property.amenities.ilike(f"%{amenity}%"))
        return list(self.db.exec(statement.order_by(Property.price)).all())

    def get_for_landlord(self, landlord_id: int) -> list[Property]:
        statement = select(Property).where(Property.landlordID == landlord_id)
        return list(self.db.exec(statement).all())

    def get_owned(self, property_id: int, landlord_id: int) -> Property | None:
        statement = select(Property).where(
            Property.propertyID == property_id,
            Property.landlordID == landlord_id,
        )
        return self.db.exec(statement).one_or_none()
