from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import TenantDep
from app.dependencies.session import SessionDep
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.services.booking_service import BookingService
from app.services.review_service import ReviewService
from app.utilities.flash import flash
from . import router, templates


@router.get(
    "/app/bookings/{booking_id}/review",
    response_class=HTMLResponse,
    name="review_form_view",
)
async def review_form_view(
    request: Request,
    booking_id: int,
    tenant: TenantDep,
    db: SessionDep,
):
    service = ReviewService(ReviewRepository(db), BookingRepository(db))
    try:
        booking = service.get_reviewable_booking(tenant, booking_id)
    except (LookupError, ValueError, PermissionError) as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(
            url=request.url_for("my_bookings_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    listing = PropertyRepository(db).get(booking.propertyID)
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )
    return templates.TemplateResponse(
        request=request,
        name="review-form.html",
        context={"user": tenant, "booking": booking, "listing": listing},
    )


@router.post("/app/bookings/{booking_id}/review", name="submit_review")
async def submit_review(
    request: Request,
    booking_id: int,
    tenant: TenantDep,
    db: SessionDep,
    rating: int = Form(),
    comment: str = Form(default=""),
):
    booking_repository = BookingRepository(db)
    review_repository = ReviewRepository(db)
    service = ReviewService(review_repository, booking_repository)

    try:
        service.create_review(
            tenant=tenant,
            booking_id=booking_id,
            rating=rating,
            comment=comment,
        )
    except (LookupError, ValueError, PermissionError) as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(
            url=request.url_for("my_bookings_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=request.url_for("review_submitted_view", booking_id=booking_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/app/bookings/{booking_id}/review/submitted",
    response_class=HTMLResponse,
    name="review_submitted_view",
)
async def review_submitted_view(
    request: Request,
    booking_id: int,
    tenant: TenantDep,
    db: SessionDep,
):
    review_service = ReviewService(ReviewRepository(db), BookingRepository(db))
    try:
        review_service.get_submitted_review(tenant, booking_id)
    except (LookupError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    booking_service = BookingService(
        BookingRepository(db),
        PropertyRepository(db),
        ReviewRepository(db),
    )
    try:
        booking, listing = booking_service.get_tenant_booking_details(
            tenant,
            booking_id,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return templates.TemplateResponse(
        request=request,
        name="review-submitted.html",
        context={"user": tenant, "booking": booking, "listing": listing},
    )
