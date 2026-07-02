"""Static / public page routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import httpx
from pydantic import BaseModel
from fastapi import HTTPException
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from app.database import SessionLocal
    from app.models.product import Product
    from app.models.news import NewsArticle
    db = SessionLocal()
    try:
        latest_products = db.query(Product).filter(Product.is_active == True).order_by(Product.created_at.desc()).limit(4).all()
        news = db.query(NewsArticle).filter(NewsArticle.is_published == True).order_by(NewsArticle.published_date.desc()).limit(3).all()
    finally:
        db.close()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "active_page": "home",
        "latest_products": latest_products,
        "news": news,
    })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {
        "request": request,
        "active_page": "about",
    })


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "active_page": "contact",
    })


@router.post("/contact", response_class=HTMLResponse)
async def contact_submit(request: Request):
    form = await request.form()
    # In production, send email via SMTP / SendGrid
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "active_page": "contact",
        "messages": [{"type": "success", "text": "Message sent! We'll get back to you within 24 hours."}],
    })


@router.get("/cart", response_class=HTMLResponse)
async def cart(request: Request):
    user = request.session.get("user")
    cart_items = []
    if user:
        from app.database import SessionLocal
        from app.models.cart import CartItem
        from app.models.product import Product
        db = SessionLocal()
        try:
            items = db.query(CartItem).filter(CartItem.user_id == user["id"]).all()
            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    cart_items.append({"item": item, "product": product})
        finally:
            db.close()
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "active_page": "cart",
        "cart_items": cart_items,
    })

class ChatMessage(BaseModel):
    message: str

@router.post("/api/chat")
async def api_chat(chat_msg: ChatMessage):
    if not settings.MISTRAL_API_KEY:
        raise HTTPException(status_code=500, detail="Mistral API key not configured. Please add it to your .env file.")
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system", 
                "content": (
                    "You are MRF Assistant, the official AI representative for MRF Circuits, a premier RF (Radio Frequency) Engineering company based in Tétouan, 93030, Morocco.\n"
                    "Your goal is to provide exceptional, professional, and concise support to our clients.\n\n"
                    "Here is the core information you need to answer client questions:\n\n"
                    "1. HOW TO ORDER / PURCHASING:\n"
                    "- To purchase standard RF components, amplifiers, antennas, and filters, direct users to the 'Products' page (/products). They can add items to their cart and checkout securely.\n"
                    "- For custom PCB design, specific RF testing setups, or custom fabrication, direct them to our 'Configurator' (/configurator) to submit their custom requirements for a quote.\n\n"
                    "2. SUPPORT & CONTACT INFO:\n"
                    "- Technical Support Email: tech-support@mrflab.com (Response time: within 4 hours).\n"
                    "- Phone: +212 539 65 78 34.\n"
                    "- Quote Requests: Processed within 24 hours.\n"
                    "- Address: Tétouan, 93030, Morocco.\n\n"
                    "3. SERVICES WE OFFER:\n"
                    "- Standard RF & Microwave component manufacturing.\n"
                    "- Custom PCB Layout and Prototyping.\n"
                    "- Advanced RF Testing, Measurement, and Validation.\n\n"
                    "4. TONE & BEHAVIOR:\n"
                    "- Always be polite, highly professional, and helpful. Use a clean, tech-savvy tone.\n"
                    "- If a user asks a question outside of RF engineering or our company's scope, politely decline and steer the conversation back to MRF Circuits.\n"
                    "- Keep your answers concise, readable, and well-formatted. Do not overwhelm the user with long paragraphs.\n"
                    "- Never invent or hallucinate prices or timelines that are not explicitly stated above. If you are unsure, politely tell them to email tech-support@mrflab.com.\n"
                    "- CRITICAL: Do NOT use Markdown formatting (such as **asterisks** for bolding or italics). Respond strictly in plain text.\n"
                )
            },
            {"role": "user", "content": chat_msg.message}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            return {"reply": reply}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to communicate with Mistral API")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

