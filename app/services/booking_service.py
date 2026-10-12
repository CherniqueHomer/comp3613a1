import calendar
from datetime import date, timedelta

from app.models.booking import Booked
from app.models.property import Property
from app.models.user import User
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.schemas.booking import BookingCreate


class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        property_repository: PropertyRepository,
        review_repository: ReviewRepository,
    ):
        self.booking_repository = booking_repository
        self.property_repository = property_repository
        self.review_repository = review_repository

    def request_booking(
        self,
        tenant: User,
        property_id: int,
        details: BookingCreate,
    ) -> Booked:
        
        if tenant.role not in {"tenant", "regular_user"}:
            raise PermissionError("Only tenants can request bookings.")

        property_record = self.property_repository.get(property_id)
        if not property_record:
            raise ValueError("Listing not found.")
        if property_record.status.lower() != "active":
            raise ValueError("This listing is not currently available.")
        if tenant.id is None:
            raise ValueError("Tenant account has no database ID.")
        if details.lease_duration_months <= 0:
            raise ValueError("Lease duration must be at least one month.")

        lease_end = self._lease_end_date_from(
            details.move_in_date,
            details.lease_duration_months,
        )
        if (
            details.move_in_date < property_record.availability_start
            or lease_end > property_record.availability_end
        ):
            raise ValueError(
                "The move-in date and full lease must fit within the listing's availability period."
            )

        booking_record = Booked(
            propertyID=property_id,
            userID=tenant.id,
            move_in_date=details.move_in_date,
            lease_duration_months=details.lease_duration_months,
            applicant_name=details.applicant_name,
            applicant_contact=details.applicant_contact,
            student_id=details.student_id,
            message=details.message,
            status="Pending",
        )

        return self.booking_repository.create(booking_record)

    def get_tenant_bookings(self, tenant: User) -> list[Booked]:
        return self.booking_repository.get_for_tenant(self._tenant_id(tenant))

    def get_tenant_booking_summaries(
        self,
        tenant: User,
    ) -> list[tuple[Booked, Property | None, bool]]:
        bookings = self.get_tenant_bookings(tenant)
        today = date.today()
        for booking in bookings:
            if (
                booking.status.lower() == "confirmed"
                and today >= self._lease_end_date(booking)
            ):
                property_record = self.property_repository.get(booking.propertyID)
                if property_record is None:
                    self.booking_repository.update_status(booking, "Completed")
                    continue

                availability_start = max(
                    property_record.availability_start,
                    self._lease_end_date(booking) + timedelta(days=1),
                    today,
                )
                next_term_end = self._lease_end_date_from(
                    availability_start,
                    property_record.lease_duration_months,
                )
                availability_end = max(
                    property_record.availability_end,
                    next_term_end,
                )
                self.booking_repository.complete_booking_and_reopen_property(
                    booking,
                    property_record,
                    availability_start,
                    availability_end,
                )

        return [
            (
                booking,
                self.property_repository.get(booking.propertyID),
                booking.bookingID is not None
                and self.review_repository.get_for_booking(booking.bookingID)
                is not None,
            )
            for booking in bookings
        ]

    def get_landlord_booking_summaries(
        self,
        landlord: User,
    ) -> list[tuple[Booked, Property | None]]:
        landlord_id = self._landlord_id(landlord)
        bookings = self.booking_repository.get_for_landlord(landlord_id)
        return [
            (booking, self.property_repository.get(booking.propertyID))
            for booking in bookings
        ]

    def approve_booking(self, landlord: User, booking_id: int) -> Booked:
        booking = self._get_landlord_booking(landlord, booking_id)
        if booking.status.lower() != "pending":
            raise ValueError("Only pending requests can be approved.")

        property_record = self.property_repository.get(booking.propertyID)
        if property_record is None:
            raise LookupError("Listing not found.")
        if property_record.status.lower() != "active":
            raise ValueError("This listing is no longer available.")

        lease_end = self._lease_end_date(booking)
        if (
            booking.move_in_date < property_record.availability_start
            or lease_end > property_record.availability_end
        ):
            raise ValueError(
                "This request no longer fits within the listing's availability period."
            )

        pending_requests = self.booking_repository.get_pending_for_property(
            booking.propertyID,
        )
        status_changes = [(booking, "Confirmed")]
        status_changes.extend(
            (pending, "Rejected")
            for pending in pending_requests
            if pending.bookingID != booking.bookingID
        )
        availability_start = lease_end + timedelta(days=1)
        self.booking_repository.save_approval(
            status_changes,
            property_record,
            availability_start,
        )
        return booking

    def reject_booking(self, landlord: User, booking_id: int) -> Booked:
        booking = self._get_landlord_booking(landlord, booking_id)
        if booking.status.lower() != "pending":
            raise ValueError("Only pending requests can be rejected.")
        self.booking_repository.update_status(booking, "Rejected")
        return booking

    def get_tenant_booking(self, tenant: User, booking_id: int) -> Booked:
        booking = self.booking_repository.get_for_tenant_by_id(
            booking_id,
            self._tenant_id(tenant),
        )
        if booking is None:
            raise LookupError("Booking not found.")
        return booking

    def get_tenant_booking_details(
        self,
        tenant: User,
        booking_id: int,
    ) -> tuple[Booked, Property]:
        booking = self.get_tenant_booking(tenant, booking_id)
        listing = self.property_repository.get(booking.propertyID)
        if listing is None:
            raise LookupError("Listing not found.")
        return booking, listing

    @staticmethod
    def _tenant_id(tenant: User) -> int:
        if tenant.role not in {"tenant", "regular_user"}:
            raise PermissionError("Only tenants can access bookings.")
        if tenant.id is None:
            raise ValueError("Tenant account has no database ID.")
        return tenant.id

    @staticmethod
    def _landlord_id(landlord: User) -> int:
        if landlord.role != "landlord":
            raise PermissionError("Only landlords can manage booking requests.")
        if landlord.id is None:
            raise ValueError("Landlord account has no database ID.")
        return landlord.id

    def _get_landlord_booking(self, landlord: User, booking_id: int) -> Booked:
        booking = self.booking_repository.get_for_landlord_by_id(
            booking_id,
            self._landlord_id(landlord),
        )
        if booking is None:
            raise LookupError("Booking request not found.")
        return booking

    @staticmethod
    def _lease_end_date(booking: Booked) -> date:
        return BookingService._lease_end_date_from(
            booking.move_in_date,
            booking.lease_duration_months,
        )

    @staticmethod
    def _lease_end_date_from(move_in_date: date, lease_duration_months: int) -> date:
        month_index = move_in_date.year * 12 + move_in_date.month - 1
        month_index += lease_duration_months
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        day = min(move_in_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
