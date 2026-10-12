from datetime import date

from fastapi import HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse

from app.dependencies.auth import TenantDep
from app.dependencies.session import SessionDep
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService
from . import router, templates


def _property_service(db: SessionDep) -> PropertyService:
    return PropertyService(PropertyRepository(db))


def _optional_price(value: str | None, label: str) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{label} must be a valid number.",
        ) from exc


@router.get("/app/browse", response_class=HTMLResponse, name="property_catalogue_view")
async def property_catalogue_view(
    request: Request,
    tenant: TenantDep,
    db: SessionDep,
    min_price: str | None = None,
    max_price: str | None = None,
    amenities: list[str] | None = Query(default=None),
    available_on: str | None = None,
):
    min_price_value = _optional_price(min_price, "Minimum price")
    max_price_value = _optional_price(max_price, "Maximum price")
    if min_price_value is not None and min_price_value < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Minimum price cannot be negative.")
    if max_price_value is not None and max_price_value < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Maximum price cannot be negative.")
    if (
        min_price_value is not None
        and max_price_value is not None
        and min_price_value > max_price_value
    ):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Minimum price must not exceed maximum price.")

    if available_on is None or not available_on.strip():
        available_on_value = None
    else:
        try:
            available_on_value = date.fromisoformat(available_on)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Move-in date must be a valid date.",
            ) from exc

    listings = _property_service(db).browse_listings(
        min_price=min_price_value,
        max_price=max_price_value,
        amenities=amenities,
        available_on=available_on_value,
    )
    return templates.TemplateResponse(
        request=request,
        name="property-catalogue.html",
        context={
            "user": tenant,
            "listings": listings,
            "min_price": min_price_value,
            "max_price": max_price_value,
            "selected_amenities": amenities or [],
            "available_on": available_on_value,
        },
    )


@router.get(
    "/app/properties/{property_id}",
    response_class=HTMLResponse,
    name="property_detail_view",
)
async def property_detail_view(
    request: Request,
    property_id: int,
    tenant: TenantDep,
    db: SessionDep,
):
    try:
        listing = _property_service(db).get_active_listing(property_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    reviews = ReviewService(ReviewRepository(db)).get_property_reviews(property_id)
    return templates.TemplateResponse(
        request=request,
        name="property-detail.html",
        context={"user": tenant, "listing": listing, "reviews": reviews},
    )


@router.get(
    "/app/properties/{property_id}/booking",
    response_class=HTMLResponse,
    name="booking_form_view",
)
async def booking_form_view(
    request: Request,
    property_id: int,
    tenant: TenantDep,
    db: SessionDep,
):
    try:
        listing = _property_service(db).get_active_listing(property_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="booking-form.html",
        context={"user": tenant, "listing": listing},
    )
