"""Product catalog routes."""
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, func
import os

from app.database import SessionLocal
from app.models.product import Product, Category

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("", response_class=HTMLResponse)
async def catalog(
    request: Request,
    q: str = Query(""),
    category: str = Query(""),
    sort: str = Query("newest"),
    page: int = Query(1),
):
    db = SessionLocal()
    try:
        query = db.query(Product).filter(Product.is_active == True)
        if q:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{q}%"),
                    Product.description.ilike(f"%{q}%"),
                    Product.sku.ilike(f"%{q}%"),
                )
            )
        if category:
            cat = db.query(Category).filter(Category.slug == category).first()
            if cat:
                query = query.filter(Product.category_id == cat.id)
        if sort == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort == "name":
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.created_at.desc())
        per_page = 12
        total = query.count()
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        categories = db.query(Category).all()
        total_pages = (total + per_page - 1) // per_page
    finally:
        db.close()
    return templates.TemplateResponse("products/catalog.html", {
        "request": request,
        "active_page": "products",
        "products": products,
        "categories": categories,
        "q": q,
        "selected_category": category,
        "sort": sort,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@router.get("/search", response_class=JSONResponse)
async def search_api(q: str = Query("")):
    """Quick search API for the live search bar."""
    if not q or len(q) < 2:
        return []
    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.sku.ilike(f"%{q}%"),
            )
        ).limit(8).all()
        return [
            {"id": p.id, "name": p.name, "sku": p.sku, "price": float(p.price), "slug": p.slug}
            for p in products
        ]
    finally:
        db.close()


@router.get("/{slug}", response_class=HTMLResponse)
async def product_detail(request: Request, slug: str):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.slug == slug, Product.is_active == True).first()
        if not product:
            return HTMLResponse("Product not found", status_code=404)
        # Track browsing history
        user = request.session.get("user")
        if user:
            from app.models.history import BrowsingHistory
            existing = db.query(BrowsingHistory).filter(
                BrowsingHistory.user_id == user["id"],
                BrowsingHistory.product_id == product.id,
            ).first()
            if existing:
                from datetime import datetime
                existing.viewed_at = datetime.utcnow()
            else:
                h = BrowsingHistory(user_id=user["id"], product_id=product.id)
                db.add(h)
            db.commit()
        related = db.query(Product).filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active == True,
        ).limit(4).all()
    finally:
        db.close()
    return templates.TemplateResponse("products/product_detail.html", {
        "request": request,
        "active_page": "products",
        "product": product,
        "related": related,
    })
