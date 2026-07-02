"""User dashboard routes."""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os

from app.database import SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


def require_login(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user


@router.get("/favorites", response_class=HTMLResponse)
async def favorites(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.history import Favorite
        from app.models.product import Product
        favs = db.query(Favorite).filter(Favorite.user_id == user["id"]).order_by(Favorite.added_at.desc()).all()
        fav_products = []
        for f in favs:
            p = db.query(Product).filter(Product.id == f.product_id).first()
            if p:
                fav_products.append({
                    "favorite": {"id": f.id, "added_at": f.added_at},
                    "product": {
                        "id": p.id, "name": p.name, "sku": p.sku,
                        "price": float(p.price or 0), "image_url": p.image_url,
                        "slug": p.slug,
                    },
                })
        return templates.TemplateResponse("dashboard/favorites.html", {
            "request": request,
            "active_dash": "favorites",
            "user": user,
            "fav_products": fav_products,
        })
    finally:
        db.close()


@router.post("/favorites/toggle", response_class=HTMLResponse)
async def toggle_favorite(request: Request, product_id: int = Form(...)):
    user = require_login(request)
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    db = SessionLocal()
    try:
        from app.models.history import Favorite
        existing = db.query(Favorite).filter(
            Favorite.user_id == user["id"],
            Favorite.product_id == product_id,
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            return JSONResponse({"action": "removed"})
        else:
            fav = Favorite(user_id=user["id"], product_id=product_id)
            db.add(fav)
            db.commit()
            return JSONResponse({"action": "added"})
    finally:
        db.close()


@router.get("/history", response_class=HTMLResponse)
async def browsing_history(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.history import BrowsingHistory
        from app.models.product import Product
        history = db.query(BrowsingHistory).filter(
            BrowsingHistory.user_id == user["id"]
        ).order_by(BrowsingHistory.viewed_at.desc()).limit(50).all()
        history_products = []
        for h in history:
            p = db.query(Product).filter(Product.id == h.product_id).first()
            if p:
                history_products.append({
                    "history": {"id": h.id, "viewed_at": h.viewed_at},
                    "product": {
                        "id": p.id, "name": p.name, "sku": p.sku,
                        "price": float(p.price or 0), "image_url": p.image_url,
                        "slug": p.slug,
                    },
                })
        return templates.TemplateResponse("dashboard/history.html", {
            "request": request,
            "active_dash": "history",
            "user": user,
            "history_products": history_products,
        })
    finally:
        db.close()


@router.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.order import Order, OrderItem
        from app.models.product import Product
        user_orders = db.query(Order).filter(Order.user_id == user["id"]).order_by(Order.order_date.desc()).all()
        orders_with_items = []
        for order in user_orders:
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            items_with_products = []
            for oi in items:
                p = db.query(Product).filter(Product.id == oi.product_id).first()
                items_with_products.append({
                    "order_item": {
                        "id": oi.id,
                        "quantity": oi.quantity,
                        "unit_price": float(oi.unit_price or 0),
                    },
                    "product": {
                        "id": p.id, "name": p.name, "sku": p.sku, "image_url": p.image_url,
                    } if p else None,
                })
            orders_with_items.append({
                "order": {
                    "id": order.id,
                    "order_ref": order.order_ref or f"#{order.id}",
                    "status": order.status,
                    "total_amount": float(order.total_amount or 0),
                    "order_date": order.order_date,
                },
                "items": items_with_products,
            })
        return templates.TemplateResponse("dashboard/orders.html", {
            "request": request,
            "active_dash": "orders",
            "user": user,
            "orders": orders_with_items,
            "paid": request.query_params.get("paid", ""),
        })
    finally:
        db.close()


@router.get("/payments", response_class=HTMLResponse)
async def payments(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.payment import PaymentMethod
        methods = db.query(PaymentMethod).filter(PaymentMethod.user_id == user["id"]).all()
        methods_data = [
            {
                "id": m.id, "card_last4": getattr(m, "card_last4", ""),
                "card_brand": getattr(m, "card_brand", ""),
                "is_default": getattr(m, "is_default", False),
            }
            for m in methods
        ]
        return templates.TemplateResponse("dashboard/payments.html", {
            "request": request,
            "active_dash": "payments",
            "user": user,
            "payment_methods": methods_data,
        })
    finally:
        db.close()

@router.post("/payments/add", response_class=JSONResponse)
async def add_payment(request: Request):
    user = require_login(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    db = SessionLocal()
    try:
        from app.models.payment import PaymentMethod
        import random
        pm = PaymentMethod(
            user_id=user["id"],
            stripe_payment_method_id=f"pm_mock_{random.randint(1000, 9999)}",
            card_brand=random.choice(["Visa", "Mastercard", "Amex"]),
            card_last4=str(random.randint(1000, 9999)),
            expiry_month=random.randint(1, 12),
            expiry_year=random.randint(2025, 2030),
            cardholder_name=user.get("full_name") or user.get("username"),
            is_default=False
        )
        db.add(pm)
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()

@router.post("/payments/{payment_id}/delete", response_class=JSONResponse)
async def delete_payment(request: Request, payment_id: int):
    user = require_login(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    db = SessionLocal()
    try:
        from app.models.payment import PaymentMethod
        pm = db.query(PaymentMethod).filter(PaymentMethod.id == payment_id, PaymentMethod.user_id == user["id"]).first()
        if pm:
            db.delete(pm)
            db.commit()
            return JSONResponse({"success": True})
        return JSONResponse({"error": "Payment method not found"}, status_code=404)
    finally:
        db.close()


@router.get("/shipping", response_class=HTMLResponse)
async def shipping(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.address import ShippingAddress
        addresses = db.query(ShippingAddress).filter(ShippingAddress.user_id == user["id"]).all()
        addresses_data = [
            {
                "id": a.id, "full_name": a.full_name, "address_line1": a.address_line1,
                "address_line2": getattr(a, "address_line2", ""),
                "city": a.city, "state": getattr(a, "state", ""),
                "postal_code": a.postal_code, "country": a.country,
            }
            for a in addresses
        ]
        return templates.TemplateResponse("dashboard/shipping.html", {
            "request": request,
            "active_dash": "shipping",
            "user": user,
            "addresses": addresses_data,
        })
    finally:
        db.close()


@router.post("/shipping/add", response_class=HTMLResponse)
async def add_shipping(
    request: Request,
    full_name: str = Form(...),
    address_line1: str = Form(...),
    address_line2: str = Form(""),
    city: str = Form(...),
    state: str = Form(""),
    postal_code: str = Form(...),
    country: str = Form(...),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.address import ShippingAddress
        addr = ShippingAddress(
            user_id=user["id"],
            full_name=full_name,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )
        db.add(addr)
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/dashboard/shipping", status_code=302)


@router.get("/settings", response_class=HTMLResponse)
async def account_settings(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.user import User
        db_user = db.query(User).filter(User.id == user["id"]).first()
        db_user_data = {
            "id": db_user.id, "email": db_user.email, "username": db_user.username,
            "full_name": db_user.full_name, "company": getattr(db_user, "company", ""),
            "phone": getattr(db_user, "phone", ""),
        } if db_user else None
        return templates.TemplateResponse("dashboard/settings.html", {
            "request": request,
            "active_dash": "settings",
            "user": user,
            "db_user": db_user_data,
        })
    finally:
        db.close()


@router.post("/settings", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    full_name: str = Form(""),
    company: str = Form(""),
    phone: str = Form(""),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        from app.models.user import User
        db_user = db.query(User).filter(User.id == user["id"]).first()
        if db_user:
            db_user.full_name = full_name
            db_user.company = company
            db_user.phone = phone
            db.commit()
            request.session["user"]["full_name"] = full_name
    finally:
        db.close()
    return RedirectResponse("/dashboard/settings", status_code=302)
