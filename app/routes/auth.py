"""Authentication routes: login, register, logout, Google OAuth."""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from authlib.integrations.starlette_client import OAuth

from app.config import settings
from app.services.auth_service import AuthService
from app.database import SessionLocal
from app.models.user import User

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/dashboard/favorites", status_code=302)
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "active_page": "login",
    })


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()
    try:
        user = AuthService.authenticate_user(db, email, password)
        if not user:
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "active_page": "login",
                "messages": [{"type": "error", "text": "Invalid email or password."}],
            })
        request.session["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
        }
        if user.role == "admin":
            return RedirectResponse("/admin", status_code=302)
        return RedirectResponse("/dashboard/favorites", status_code=302)
    finally:
        db.close()


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/dashboard/favorites", status_code=302)
    return templates.TemplateResponse("auth/register.html", {
        "request": request,
        "active_page": "register",
    })


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    company: str = Form(""),
    full_name: str = Form(""),
):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return templates.TemplateResponse("auth/register.html", {
                "request": request,
                "active_page": "register",
                "messages": [{"type": "error", "text": "Email already registered."}],
            })
        user = AuthService.create_user(db, username=username, email=email, password=password, company=company, full_name=full_name)
        request.session["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
        }
        return RedirectResponse("/dashboard/favorites", status_code=302)
    finally:
        db.close()


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@router.get("/google")
async def login_google(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "active_page": "login",
            "messages": [{"type": "error", "text": "Google OAuth is not configured on this server."}],
        })
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print(f"Google OAuth Exception: {str(e)}")
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "active_page": "login",
            "messages": [{"type": "error", "text": f"Google authentication failed: {str(e)}"}],
        })
        
    user_info = token.get('userinfo')
    if not user_info:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "active_page": "login",
            "messages": [{"type": "error", "text": "Failed to fetch user info from Google."}],
        })
        
    email = user_info.get("email")
    first_name = user_info.get("given_name", "")
    last_name = user_info.get("family_name", "")
    avatar_url = user_info.get("picture", "")
    oauth_id = user_info.get("sub", "")
    
    if not email:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "active_page": "login",
            "messages": [{"type": "error", "text": "Email not provided by Google."}],
        })
    
    db = SessionLocal()
    try:
        user = AuthService.get_user_by_email(db, email)
        if not user:
            user = AuthService.create_oauth_user(
                db, 
                email=email, 
                first_name=first_name, 
                last_name=last_name, 
                oauth_provider="google", 
                oauth_id=oauth_id, 
                avatar_url=avatar_url
            )
        request.session["user"] = AuthService.get_user_session_data(user)
        return RedirectResponse("/dashboard/favorites", status_code=302)
    finally:
        db.close()
