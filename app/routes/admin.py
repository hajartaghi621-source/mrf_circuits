"""Admin dashboard routes — full CRUD for products, orders, users, categories."""
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import joinedload
import os, shutil, uuid

from app.database import SessionLocal
from app.models.product import Product, Category
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.configurator import ConfiguratorQuote
from app.models.news import NewsArticle

def parse_float(value):
    """Convert form string to float, treating empty string as None."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(request: Request):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return None
    return user


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        total_products = db.query(Product).count()
        total_orders = db.query(Order).count()
        total_users = db.query(User).count()
        total_revenue = db.query(func.sum(Order.total_amount)).filter(Order.status == "paid").scalar() or 0
        recent_orders = db.query(Order).order_by(Order.order_date.desc()).limit(5).all()
        # Eagerly load user for recent orders
        recent_orders_data = [
            {
                "id": o.id,
                "order_ref": o.order_ref,
                "status": o.status,
                "total_amount": float(o.total_amount or 0),
                "order_date": o.order_date,
                "user_email": db.query(User).filter(User.id == o.user_id).first().email if o.user_id else "",
            }
            for o in recent_orders
        ]
        low_stock = db.query(Product).filter(Product.stock_quantity <= 5, Product.is_active == True).all()
        low_stock_data = [
            {"id": p.id, "name": p.name, "sku": p.sku, "stock_quantity": p.stock_quantity}
            for p in low_stock
        ]
        pending_quotes = db.query(ConfiguratorQuote).filter(ConfiguratorQuote.status == "pending").count()
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "admin": user,
            "active_admin": "dashboard",
            "total_products": total_products,
            "total_orders": total_orders,
            "total_users": total_users,
            "total_revenue": float(total_revenue),
            "recent_orders": recent_orders_data,
            "low_stock": low_stock_data,
            "pending_quotes": pending_quotes,
        })
    finally:
        db.close()


# ---- PRODUCTS ----
@router.get("/products", response_class=HTMLResponse)
async def admin_products(request: Request, q: str = "", page: int = 1):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        query = db.query(Product)
        if q:
            query = query.filter(Product.name.ilike(f"%{q}%") | Product.sku.ilike(f"%{q}%"))
        per_page = 20
        total = query.count()
        products = query.order_by(Product.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
        products_data = [
            {
                "id": p.id, "name": p.name, "sku": p.sku, "price": float(p.price or 0),
                "stock_quantity": p.stock_quantity, "is_active": p.is_active,
                "image_url": p.image_url, "stock_status": p.stock_status,
                "category_id": p.category_id,
            }
            for p in products
        ]
        categories = db.query(Category).all()
        categories_data = [{"id": c.id, "name": c.name} for c in categories]
        total_pages = (total + per_page - 1) // per_page
        return templates.TemplateResponse("admin/products.html", {
            "request": request,
            "admin": user,
            "active_admin": "products",
            "products": products_data,
            "categories": categories_data,
            "q": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        })
    finally:
        db.close()


@router.get("/products/new", response_class=HTMLResponse)
async def admin_product_new(request: Request):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        categories = db.query(Category).all()
        categories_data = [{"id": c.id, "name": c.name} for c in categories]
        return templates.TemplateResponse("admin/product_form.html", {
            "request": request,
            "admin": user,
            "active_admin": "products",
            "product": None,
            "categories": categories_data,
        })
    finally:
        db.close()


@router.post("/products/new", response_class=HTMLResponse)
async def admin_product_create(
    request: Request,
    name: str = Form(...),
    sku: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock_quantity: int = Form(0),
    category_id: int = Form(None),
    frequency_min: str = Form(None),
    frequency_max: str = Form(None),
    power_output: str = Form(None),
    gain: str = Form(None),
    noise_figure: str = Form(None),
    is_active: bool = Form(True),
    image: UploadFile = File(None),
    datasheet: UploadFile = File(None),
    data_file: UploadFile = File(None),
    pcb_layout: UploadFile = File(None),
):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        frequency_min = parse_float(frequency_min)
        frequency_max = parse_float(frequency_max)
        power_output = parse_float(power_output)
        gain = parse_float(gain)
        noise_figure = parse_float(noise_figure)
        image_url = None
        if image and image.filename:
            ext = image.filename.rsplit(".", 1)[-1]
            fname = f"{uuid.uuid4().hex}.{ext}"
            fpath = os.path.join(UPLOAD_DIR, fname)
            with open(fpath, "wb") as f:
                shutil.copyfileobj(image.file, f)
            image_url = f"/static/uploads/{fname}"

        datasheet_url = None
        if datasheet and datasheet.filename:
            ext = datasheet.filename.rsplit(".", 1)[-1]
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = os.path.join(UPLOAD_DIR, "datasheets")
            os.makedirs(folder, exist_ok=True)
            fpath = os.path.join(folder, fname)
            with open(fpath, "wb") as f:
                shutil.copyfileobj(datasheet.file, f)
            datasheet_url = f"/static/uploads/datasheets/{fname}"

        data_file_url = None
        if data_file and data_file.filename:
            ext = data_file.filename.rsplit(".", 1)[-1]
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = os.path.join(UPLOAD_DIR, "data")
            os.makedirs(folder, exist_ok=True)
            fpath = os.path.join(folder, fname)
            with open(fpath, "wb") as f:
                shutil.copyfileobj(data_file.file, f)
            data_file_url = f"/static/uploads/data/{fname}"

        pcb_layout_url = None
        if pcb_layout and pcb_layout.filename:
            ext = pcb_layout.filename.rsplit(".", 1)[-1]
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = os.path.join(UPLOAD_DIR, "pcb")
            os.makedirs(folder, exist_ok=True)
            fpath = os.path.join(folder, fname)
            with open(fpath, "wb") as f:
                shutil.copyfileobj(pcb_layout.file, f)
            pcb_layout_url = f"/static/uploads/pcb/{fname}"

        product = Product(
            name=name, sku=sku, slug=slug, description=description,
            price=price, stock_quantity=stock_quantity, category_id=category_id,
            frequency_min=frequency_min, frequency_max=frequency_max,
            power_output=power_output, gain=gain, noise_figure=noise_figure,
            is_active=is_active, image_url=image_url,
            datasheet_url=datasheet_url, data_file_url=data_file_url,
            pcb_layout_url=pcb_layout_url,
        )
        db.add(product)
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/products", status_code=302)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def admin_product_edit(request: Request, product_id: int):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        categories = db.query(Category).all()
        if not product:
            return RedirectResponse("/admin/products", status_code=302)
        product_data = {
            "id": product.id, "name": product.name, "sku": product.sku,
            "slug": product.slug, "description": product.description,
            "price": float(product.price or 0), "stock_quantity": product.stock_quantity,
            "category_id": product.category_id, "frequency_min": product.frequency_min,
            "frequency_max": product.frequency_max, "power_output": product.power_output,
            "gain": product.gain, "noise_figure": product.noise_figure,
            "is_active": product.is_active, "image_url": product.image_url,
            "datasheet_url": product.datasheet_url,
            "data_file_url": product.data_file_url,
            "pcb_layout_url": product.pcb_layout_url,
        }
        categories_data = [{"id": c.id, "name": c.name} for c in categories]
        return templates.TemplateResponse("admin/product_form.html", {
            "request": request,
            "admin": user,
            "active_admin": "products",
            "product": product_data,
            "categories": categories_data,
        })
    finally:
        db.close()


@router.post("/products/{product_id}/edit", response_class=HTMLResponse)
async def admin_product_update(
    request: Request, product_id: int,
    name: str = Form(...),
    sku: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock_quantity: int = Form(0),
    category_id: int = Form(None),
    frequency_min: str = Form(None),
    frequency_max: str = Form(None),
    power_output: str = Form(None),
    gain: str = Form(None),
    noise_figure: str = Form(None),
    is_active: bool = Form(True),
    image: UploadFile = File(None),
    datasheet: UploadFile = File(None),
    data_file: UploadFile = File(None),
    pcb_layout: UploadFile = File(None),
):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        frequency_min = parse_float(frequency_min)
        frequency_max = parse_float(frequency_max)
        power_output = parse_float(power_output)
        gain = parse_float(gain)
        noise_figure = parse_float(noise_figure)
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.name = name; product.sku = sku; product.slug = slug
            product.description = description; product.price = price
            product.stock_quantity = stock_quantity; product.category_id = category_id
            product.frequency_min = frequency_min; product.frequency_max = frequency_max
            product.power_output = power_output; product.gain = gain
            product.noise_figure = noise_figure; product.is_active = is_active
            if image and image.filename:
                ext = image.filename.rsplit(".", 1)[-1]
                fname = f"{uuid.uuid4().hex}.{ext}"
                fpath = os.path.join(UPLOAD_DIR, fname)
                with open(fpath, "wb") as f:
                    shutil.copyfileobj(image.file, f)
                product.image_url = f"/static/uploads/{fname}"

            if datasheet and datasheet.filename:
                ext = datasheet.filename.rsplit(".", 1)[-1]
                fname = f"{uuid.uuid4().hex}.{ext}"
                folder = os.path.join(UPLOAD_DIR, "datasheets")
                os.makedirs(folder, exist_ok=True)
                fpath = os.path.join(folder, fname)
                with open(fpath, "wb") as f:
                    shutil.copyfileobj(datasheet.file, f)
                product.datasheet_url = f"/static/uploads/datasheets/{fname}"

            if data_file and data_file.filename:
                ext = data_file.filename.rsplit(".", 1)[-1]
                fname = f"{uuid.uuid4().hex}.{ext}"
                folder = os.path.join(UPLOAD_DIR, "data")
                os.makedirs(folder, exist_ok=True)
                fpath = os.path.join(folder, fname)
                with open(fpath, "wb") as f:
                    shutil.copyfileobj(data_file.file, f)
                product.data_file_url = f"/static/uploads/data/{fname}"

            if pcb_layout and pcb_layout.filename:
                ext = pcb_layout.filename.rsplit(".", 1)[-1]
                fname = f"{uuid.uuid4().hex}.{ext}"
                folder = os.path.join(UPLOAD_DIR, "pcb")
                os.makedirs(folder, exist_ok=True)
                fpath = os.path.join(folder, fname)
                with open(fpath, "wb") as f:
                    shutil.copyfileobj(pcb_layout.file, f)
                product.pcb_layout_url = f"/static/uploads/pcb/{fname}"



            db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/products", status_code=302)


@router.post("/products/{product_id}/delete", response_class=HTMLResponse)
async def admin_product_delete(request: Request, product_id: int):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.is_active = False
            db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/products", status_code=302)


# ---- ORDERS ----
@router.get("/orders", response_class=HTMLResponse)
async def admin_orders(request: Request, status: str = "", page: int = 1):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        per_page = 20
        total = query.count()
        orders = query.order_by(Order.order_date.desc()).offset((page-1)*per_page).limit(per_page).all()
        total_pages = (total + per_page - 1) // per_page
        orders_data = []
        for o in orders:
            u = db.query(User).filter(User.id == o.user_id).first()
            orders_data.append({
                "id": o.id,
                "order_ref": o.order_ref or f"#{o.id}",
                "status": o.status,
                "total_amount": float(o.total_amount or 0),
                "order_date": o.order_date,
                "user_email": u.email if u else "—",
                "user_name": u.full_name or u.username if u else "—",
            })
        return templates.TemplateResponse("admin/orders.html", {
            "request": request,
            "admin": user,
            "active_admin": "orders",
            "orders": orders_data,
            "status_filter": status,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        })
    finally:
        db.close()


@router.post("/orders/{order_id}/status", response_class=JSONResponse)
async def update_order_status(request: Request, order_id: int, status: str = Form(...)):
    user = require_admin(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


# ---- USERS ----
@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, q: str = "", page: int = 1):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        query = db.query(User)
        if q:
            query = query.filter(User.email.ilike(f"%{q}%") | User.username.ilike(f"%{q}%"))
        per_page = 20
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
        total_pages = (total + per_page - 1) // per_page
        users_data = [
            {
                "id": u.id, "email": u.email, "username": u.username,
                "full_name": u.full_name, "role": u.role,
                "is_active": u.is_active, "created_at": u.created_at,
            }
            for u in users
        ]
        return templates.TemplateResponse("admin/users.html", {
            "request": request,
            "admin": user,
            "active_admin": "users",
            "users": users_data,
            "q": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        })
    finally:
        db.close()


# ---- CATEGORIES ----
@router.get("/categories", response_class=HTMLResponse)
async def admin_categories(request: Request):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        categories = db.query(Category).all()
        categories_data = [
            {"id": c.id, "name": c.name, "slug": c.slug, "description": c.description,
             "is_active": c.is_active, "sort_order": c.sort_order}
            for c in categories
        ]
        return templates.TemplateResponse("admin/categories.html", {
            "request": request,
            "admin": user,
            "active_admin": "categories",
            "categories": categories_data,
        })
    finally:
        db.close()


@router.post("/categories/add", response_class=HTMLResponse)
async def admin_category_add(request: Request, name: str = Form(...), slug: str = Form(...), description: str = Form("")):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        cat = Category(name=name, slug=slug, description=description)
        db.add(cat)
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/categories", status_code=302)


# ---- CONFIGURATOR QUOTES ----
@router.get("/quotes", response_class=HTMLResponse)
async def admin_quotes(request: Request, status: str = ""):
    user = require_admin(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    db = SessionLocal()
    try:
        query = db.query(ConfiguratorQuote)
        if status:
            query = query.filter(ConfiguratorQuote.status == status)
        quotes = query.order_by(ConfiguratorQuote.created_at.desc()).all()
        quotes_data = []
        for q in quotes:
            u = db.query(User).filter(User.id == q.user_id).first() if q.user_id else None
            quotes_data.append({
                "id": q.id,
                "quote_ref": q.quote_ref,
                "status": q.status,
                "created_at": q.created_at,
                "admin_notes": q.admin_notes or "",
                "notes": q.notes,
                "config_data": q.config_data if hasattr(q, 'config_data') else None,
                "parameters": q.parameters,
                "product_type": q.product_type,
                "technology": q.technology,
                "frequency_band": q.frequency_band,
                "frequency_min": float(q.frequency_min) if q.frequency_min else None,
                "frequency_max": float(q.frequency_max) if q.frequency_max else None,
                "substrate": q.substrate,
                "enclosure_type": q.enclosure_type,
                "estimated_cost": float(q.estimated_cost) if q.estimated_cost else None,
                "quantity": q.quantity or 1,
                "contact_email": q.contact_email or "",
                "user_email": u.email if u else (q.contact_email or "Guest"),
                "user_name": (u.full_name or u.username) if u else "Guest",
            })
        return templates.TemplateResponse("admin/quotes.html", {
            "request": request,
            "admin": user,
            "active_admin": "quotes",
            "quotes": quotes_data,
            "status_filter": status,
        })
    finally:
        db.close()


@router.post("/quotes/{quote_id}/status", response_class=JSONResponse)
async def update_quote_status(request: Request, quote_id: int, status: str = Form(...), admin_notes: str = Form("")):
    user = require_admin(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    db = SessionLocal()
    try:
        quote = db.query(ConfiguratorQuote).filter(ConfiguratorQuote.id == quote_id).first()
        if quote:
            quote.status = status
            quote.admin_notes = admin_notes
            db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()
