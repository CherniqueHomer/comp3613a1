from datetime import date

from sqlmodel import Session, select

from app.models.booking import Booked
from app.models.property import Property


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, booking_id: int) -> Booked | None:
        return self.db.get(Booked, booking_id)

    def create(self, booking_record: Booked) -> Booked:
        self.db.add(booking_record)
        self.db.commit()
        self.db.refresh(booking_record)
        return booking_record

    def update_status(self, booking_record: Booked, status: str) -> Booked:
        booking_record.status = status
        self.save_statuses([(booking_record, status)])
        self.db.refresh(booking_record)
        return booking_record

    def save_statuses(self, status_changes: list[tuple[Booked, str]]) -> None:
        for booking_record, status in status_changes:
            booking_record.status = status
            self.db.add(booking_record)
        self.db.commit()

    def save_approval(
        self,
        status_changes: list[tuple[Booked, str]],
        property_record: Property,
        availability_start: date,
    ) -> None:
        for booking_record, status in status_changes:
            booking_record.status = status
            self.db.add(booking_record)
        property_record.availability_start = availability_start
        self.db.add(property_record)
        self.db.commit()

    def get_for_tenant(self, tenant_id: int) -> list[Booked]:
        statement = (
            select(Booked)
            .where(Booked.userID == tenant_id)
            .order_by(Booked.created_at.desc())
        )
        return list(self.db.exec(statement).all())

    def get_for_tenant_by_id(self, booking_id: int, tenant_id: int) -> Booked | None:
        statement = select(Booked).where(
            Booked.bookingID == booking_id,
            Booked.userID == tenant_id,
        )
        return self.db.exec(statement).one_or_none()

    def get_for_landlord(self, landlord_id: int) -> list[Booked]:
        statement = (
            select(Booked)
            .join(Property, Property.propertyID == Booked.propertyID)
            .where(Property.landlordID == landlord_id)
            .order_by(Booked.created_at.desc())
        )
        return list(self.db.exec(statement).all())

    def get_for_landlord_by_id(
        self,
        booking_id: int,
        landlord_id: int,
    ) -> Booked | None:
        statement = (
            select(Booked)
            .join(Property, Property.propertyID == Booked.propertyID)
            .where(
                Booked.bookingID == booking_id,
                Property.landlordID == landlord_id,
            )
        )
        return self.db.exec(statement).one_or_none()

    def get_pending_for_property(self, property_id: int) -> list[Booked]:
        statement = select(Booked).where(
            Booked.propertyID == property_id,
            Booked.status.ilike("pending"),
        )
        return list(self.db.exec(statement).all())