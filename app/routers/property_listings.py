from datetime import date

from fastapi import Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import LandlordDep
from app.dependencies.session import SessionDep
from app.schemas.property import PropertyCreate
from app.repositories.property import PropertyRepository
from app.services.property_service import PropertyService
from app.utilities.flash import flash
from . import router, templates


def _property_service(db: SessionDep) -> PropertyService:
    return PropertyService(PropertyRepository(db))


@router.get("/app/properties/mine", response_class=HTMLResponse, name="property_listings_view")
async def property_listings_view(
    request: Request,
    landlord: LandlordDep,
    db: SessionDep,
):
    service = _property_service(db)
    listings = service.get_landlord_listings(landlord)
    return templates.TemplateResponse(
        request=request,
        name="property-listings.html",
        context={"user": landlord, "listings": listings},
    )


@router.post("/app/properties/edit", response_class=HTMLResponse, name="edit_property_preview")
async def edit_property_preview(
    request: Request,
    landlord: LandlordDep,
    title: str = Form(),
    address: str = Form(),
    price: float = Form(),
    description: str = Form(),
    amenities: str = Form(),
    photo_url: str = Form(),
    availability_start: date = Form(),
    availability_end: date = Form(),
    lease_duration_months: int = Form(),
):
    details = PropertyCreate(
        title=title,
        address=address,
        price=price,
        description=description,
        amenities=amenities,
        photo_url=photo_url,
        availability_start=availability_start,
        availability_end=availability_end,
        lease_duration_months=lease_duration_months,
    )
    return templates.TemplateResponse(
        request=request,
        name="property-form.html",
        context={"user": landlord, "details": details},
    )


@router.get("/app/properties/new", response_class=HTMLResponse, name="property_form_view")
async def property_form_view(request: Request, landlord: LandlordDep):
    return templates.TemplateResponse(
        request=request,
        name="property-form.html",
        context={"user": landlord},
    )


@router.post("/app/properties/preview", response_class=HTMLResponse, name="preview_property")
async def preview_property(
    request: Request,
    landlord: LandlordDep,
    title: str = Form(),
    address: str = Form(),
    price: float = Form(),
    description: str = Form(),
    amenities: list[str] = Form(default=[]),
    photo_url: str = Form(),
    availability_start: date = Form(),
    availability_end: date = Form(),
    lease_duration_months: int = Form(),
):
    details = PropertyCreate(
        title=title.strip(),
        address=address.strip(),
        price=price,
        description=description.strip(),
        amenities=", ".join(amenities),
        photo_url=photo_url.strip(),
        availability_start=availability_start,
        availability_end=availability_end,
        lease_duration_months=lease_duration_months,
    )
    try:
        PropertyService.validate_listing(details)
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(
            url=request.url_for("property_form_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=request,
        name="property-preview.html",
        context={"user": landlord, "details": details},
    )


@router.post("/app/properties/publish", name="publish_property")
async def publish_property(
    request: Request,
    landlord: LandlordDep,
    db: SessionDep,
    title: str = Form(),
    address: str = Form(),
    price: float = Form(),
    description: str = Form(),
    amenities: str = Form(),
    photo_url: str = Form(),
    availability_start: date = Form(),
    availability_end: date = Form(),
    lease_duration_months: int = Form(),
):
    details = PropertyCreate(
        title=title,
        address=address,
        price=price,
        description=description,
        amenities=amenities,
        photo_url=photo_url,
        availability_start=availability_start,
        availability_end=availability_end,
        lease_duration_months=lease_duration_months,
    )

    service = _property_service(db)
    try:
        property_record = service.publish_listing(landlord, details)
    except ValueError as exc:
        flash(request, str(exc), "warning")
        return RedirectResponse(
            url=request.url_for("property_form_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=request.url_for(
            "property_published_view",
            property_id=property_record.propertyID,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/app/properties/published/{property_id}",
    response_class=HTMLResponse,
    name="property_published_view",
)
async def property_published_view(
    request: Request,
    property_id: int,
    landlord: LandlordDep,
    db: SessionDep,
):
    service = _property_service(db)
    try:
        listing = service.get_owned_listing(landlord, property_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
    return templates.TemplateResponse(
        request=request,
        name="property-published.html",
        context={"user": landlord, "listing": listing},
    )