from datetime import date

from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import LandlordDep, TenantDep
from app.dependencies.session import SessionDep
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService
from app.utilities.flash import flash
from . import router, templates


@router.post("/app/properties/{property_id}/book", name="request_booking")
async def request_booking(
    request: Request,
    property_id: int,
    tenant: TenantDep,
    db: SessionDep,
    move_in_date: date = Form(),
    lease_duration_months: int = Form(),
    applicant_name: str = Form(),
    applicant_contact: str = Form(),
    student_id: str = Form(),
    message: str = Form(default=""),
):
    details = BookingCreate(
        move_in_date=move_in_date,
        lease_duration_months=lease_duration_months,
        applicant_name=applicant_name,
        applicant_contact=applicant_contact,
        student_id=student_id,
        message=message,
    )

    booking_repository = BookingRepository(db)
    property_repository = PropertyRepository(db)
    service = BookingService(
        booking_repository,
        property_repository,
        ReviewRepository(db),
    )

    try:
        booking = service.request_booking(tenant, property_id, details)
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(
            url=request.url_for("booking_form_view", property_id=property_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    flash(request, "Booking request sent! Your landlord will respond shortly.")

    if booking.bookingID is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking was saved without an ID.")
    return RedirectResponse(
        url=request.url_for("booking_confirmation_view", booking_id=booking.bookingID),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/app/bookings", response_class=HTMLResponse, name="my_bookings_view")
async def my_bookings_view(
    request: Request,
    tenant: TenantDep,
    db: SessionDep,
):
    service = BookingService(
        BookingRepository(db),
        PropertyRepository(db),
        ReviewRepository(db),
    )
    booking_rows = service.get_tenant_booking_summaries(tenant)
    return templates.TemplateResponse(
        request=request,
        name="my-bookings.html",
        context={"user": tenant, "booking_rows": booking_rows},
    )


@router.get(
    "/app/landlord/bookings",
    response_class=HTMLResponse,
    name="landlord_bookings_view",
)
async def landlord_bookings_view(
    request: Request,
    landlord: LandlordDep,
    db: SessionDep,
):
    service = BookingService(
        BookingRepository(db),
        PropertyRepository(db),
        ReviewRepository(db),
    )
    booking_rows = service.get_landlord_booking_summaries(landlord)
    return templates.TemplateResponse(
        request=request,
        name="landlord-bookings.html",
        context={"user": landlord, "booking_rows": booking_rows},
    )


@router.post(
    "/app/landlord/bookings/{booking_id}/approve",
    name="approve_booking",
)
async def approve_booking(
    request: Request,
    booking_id: int,
    landlord: LandlordDep,
    db: SessionDep,
):
    service = BookingService(
        BookingRepository(db),
        PropertyRepository(db),
        ReviewRepository(db),
    )
    try:
        service.approve_booking(landlord, booking_id)
    except (LookupError, ValueError) as exc:
        flash(request, str(exc), "warning")
    else:
        flash(request, "Booking request approved. Other pending requests for this property were rejected.")
    return RedirectResponse(
        url=request.url_for("landlord_bookings_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/landlord/bookings/{booking_id}/reject",
    name="reject_booking",
)
async def reject_booking(
    request: Request,
    booking_id: int,
    landlord: LandlordDep,
    db: SessionDep,
):
    service = BookingService(
        BookingRepository(db),
        PropertyRepository(db),
        ReviewRepository(db),
    )
    try:
        service.reject_booking(landlord, booking_id)
    except (LookupError, ValueError) as exc:
        flash(request, str(exc), "warning")
    else:
        flash(request, "Booking request rejected.", "warning")
    return RedirectResponse(
        url=request.url_for("landlord_bookings_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/app/bookings/{booking_id}/confirmation",
    response_class=HTMLResponse,
    name="booking_confirmation_view",
)
async def booking_confirmation_view(
    request: Request,
    booking_id: int,
    tenant: TenantDep,
    db: SessionDep,
):
    service = BookingService(
        BookingRepository(db),
        PropertyRepository(db),
        ReviewRepository(db),
    )
    try:
        booking, listing = service.get_tenant_booking_details(tenant, booking_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="booking-confirmation.html",
        context={"user": tenant, "booking": booking, "listing": listing},
    )