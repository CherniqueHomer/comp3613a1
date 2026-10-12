from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import AuthDep
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(request: Request, user: AuthDep):
    if user.role == "landlord":
        return RedirectResponse(url=request.url_for("property_listings_view"), status_code=303)
    return RedirectResponse(url=request.url_for("property_catalogue_view"), status_code=303)