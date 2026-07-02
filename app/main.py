"""MRF Circuits — FastAPI Application Entry Point."""
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import init_db

# Create FastAPI app
app = FastAPI(
    title="MRF Circuits",
    description="Engineering Precision for RF Systems",
    version="2.4.0",
)

# Import all models to ensure they are registered with the SQLAlchemy registry
from app.models.user import User
from app.models.product import Product, Category
from app.models.address import ShippingAddress
from app.models.cart import CartItem
from app.models.configurator import ConfiguratorQuote
from app.models.history import Favorite, BrowsingHistory
from app.models.news import NewsArticle
from app.models.order import Order, OrderItem
from app.models.payment import PaymentMethod



# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Ensure upload directory exists
uploads_dir = os.path.join(static_dir, "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# Jinja2 templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


def get_current_user(request: Request):
    """Extract current user from session. Returns None if not logged in."""
    return request.session.get("user", None)


# --- Register route modules ---
from app.routes.pages import router as pages_router
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.cart import router as cart_router
from app.routes.dashboard import router as dashboard_router
from app.routes.configurator import router as configurator_router
from app.routes.admin import router as admin_router

app.include_router(pages_router)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(cart_router, prefix="/cart", tags=["Cart"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(configurator_router, prefix="/configurator", tags=["Configurator"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.on_event("startup")
def on_startup():
    """Initialize database tables on startup."""
    init_db()


# --- Template context processor ---
@app.middleware("http")
async def add_global_context(request: Request, call_next):
    """Add global template variables to every request."""
    request.state.user = get_current_user(request)
    request.state.stripe_publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    response = await call_next(request)
    return response


# Session middleware for auth cookies (must be added after custom HTTP middleware to run first)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
