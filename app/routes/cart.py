"""Cart routes: add, update, remove, checkout."""
from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
import os

from app.database import SessionLocal
from app.models.cart import CartItem
from app.models.product import Product

router = APIRouter()


@router.get("/count", response_class=JSONResponse)
async def get_cart_count(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"count": 0})
    db = SessionLocal()
    try:
        from sqlalchemy import func
        count = db.query(func.sum(CartItem.quantity)).filter(CartItem.user_id == user["id"]).scalar() or 0
        return JSONResponse({"count": count})
    finally:
        db.close()


@router.post("/add", response_class=JSONResponse)
async def add_to_cart(request: Request, product_id: int = Form(...), quantity: int = Form(1)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    db = SessionLocal()
    try:
        existing = db.query(CartItem).filter(
            CartItem.user_id == user["id"],
            CartItem.product_id == product_id,
        ).first()
        if existing:
            existing.quantity += quantity
        else:
            item = CartItem(user_id=user["id"], product_id=product_id, quantity=quantity)
            db.add(item)
        db.commit()
        count = db.query(CartItem).filter(CartItem.user_id == user["id"]).count()
        return JSONResponse({"success": True, "cart_count": count})
    finally:
        db.close()


@router.post("/remove", response_class=JSONResponse)
async def remove_from_cart(request: Request, item_id: int = Form(...)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    db = SessionLocal()
    try:
        item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.user_id == user["id"],
        ).first()
        if item:
            db.delete(item)
            db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


@router.post("/update", response_class=JSONResponse)
async def update_cart(request: Request, item_id: int = Form(...), quantity: int = Form(...)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    db = SessionLocal()
    try:
        item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.user_id == user["id"],
        ).first()
        if item:
            if quantity <= 0:
                db.delete(item)
            else:
                item.quantity = quantity
            db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


@router.post("/checkout", response_class=JSONResponse)
async def create_checkout(request: Request):
    """Create a Stripe checkout session."""
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    db = SessionLocal()
    try:
        from app.config import settings
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        items = db.query(CartItem).filter(CartItem.user_id == user["id"]).all()
        if not items:
            return JSONResponse({"error": "Cart is empty"}, status_code=400)

        line_items = []
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": product.name, "description": product.sku},
                        "unit_amount": int(product.price * 100),
                    },
                    "quantity": item.quantity,
                })

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=str(request.base_url) + "cart/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=str(request.base_url) + "cart",
            customer_email=user["email"],
        )
        return JSONResponse({"checkout_url": session.url})
    finally:
        db.close()


@router.get("/success", response_class=JSONResponse)
async def checkout_success(request: Request, session_id: str = ""):
    """Handle Stripe success redirect — clear cart, create order."""
    user = request.session.get("user")
    if user and session_id:
        db = SessionLocal()
        try:
            from app.models.cart import CartItem
            from app.models.order import Order, OrderItem
            from app.models.product import Product
            import decimal
            items = db.query(CartItem).filter(CartItem.user_id == user["id"]).all()
            if items:
                total = sum(item.quantity * (db.query(Product).get(item.product_id).price or 0) for item in items)
                order = Order(
                    user_id=user["id"],
                    total_amount=total,
                    stripe_session_id=session_id,
                    status="paid",
                )
                db.add(order)
                db.flush()
                for item in items:
                    product = db.query(Product).get(item.product_id)
                    if product:
                        oi = OrderItem(
                            order_id=order.id,
                            product_id=item.product_id,
                            quantity=item.quantity,
                            unit_price=product.price,
                        )
                        db.add(oi)
                        db.delete(item)
                db.commit()
        finally:
            db.close()
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard/orders?paid=1", status_code=302)
