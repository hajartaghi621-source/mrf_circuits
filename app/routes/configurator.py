"""RF Product Configurator — 7-step wizard."""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os, json

from app.database import SessionLocal
from app.models.configurator import ConfiguratorQuote

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("", response_class=HTMLResponse)
async def configurator(request: Request):
    return templates.TemplateResponse("configurator/index.html", {
        "request": request,
        "active_page": "configurator",
    })


@router.post("/quote", response_class=JSONResponse)
async def submit_quote(request: Request):
    data = await request.json()
    user = request.session.get("user")
    db = SessionLocal()
    try:
        quote = ConfiguratorQuote(
            user_id=user["id"] if user else None,
            product_type=data.get("product_type", ""),
            technology=data.get("technology", ""),
            frequency_min=data.get("frequency_min"),
            frequency_max=data.get("frequency_max"),
            parameters=data.get("parameters", {}),
            substrate=data.get("substrate", ""),
            estimated_cost=data.get("estimated_cost"),
            quantity=data.get("quantity", 1),
            contact_email=data.get("contact_email", user["email"] if user else ""),
            notes=data.get("notes", ""),
            status="pending",
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return JSONResponse({"success": True, "quote_id": quote.id})
    finally:
        db.close()
