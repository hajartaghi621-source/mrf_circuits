# MRF Circuits — RF Engineering E-Commerce Platform

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd mrf_circuits
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and fill in your Railway PostgreSQL URL and Stripe keys
```

### 3. Initialize Database & Seed Data
```bash
python seed.py
```

### 4. Run the Server
```bash
uvicorn app.main:app --reload
```

Visit: http://localhost:8000

---

## 🔐 Default Credentials

| Role  | Email                  | Password        |
|-------|------------------------|-----------------|
| Admin | admin@mrflab.com       | MRFAdmin2024!   |
| User  | engineer@test.com      | test1234        |

---

## 📦 Project Structure

```
mrf_circuits/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment-based settings
│   ├── database.py          # SQLAlchemy engine & session
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── cart.py
│   │   ├── address.py
│   │   ├── payment.py
│   │   ├── history.py
│   │   ├── configurator.py
│   │   └── news.py
│   ├── routes/              # FastAPI routers
│   │   ├── pages.py         # Public pages (home, about, contact)
│   │   ├── auth.py          # Login, register, logout
│   │   ├── products.py      # Catalog, search, detail
│   │   ├── cart.py          # Cart & Stripe checkout
│   │   ├── dashboard.py     # User dashboard (favorites, orders, etc.)
│   │   ├── configurator.py  # 7-step RF configurator
│   │   └── admin.py         # Admin panel (full CRUD)
│   ├── services/
│   │   └── auth_service.py  # Password hashing, user creation, JWT
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Shared layout (nav + footer)
│   │   ├── home.html
│   │   ├── about.html
│   │   ├── contact.html
│   │   ├── cart.html
│   │   ├── auth/            # Login, Register
│   │   ├── products/        # Catalog, Product Detail
│   │   ├── dashboard/       # Favorites, Orders, Payments, Shipping, Settings
│   │   ├── configurator/    # 7-step wizard
│   │   └── admin/           # Full admin dashboard
│   └── static/
│       ├── css/styles.css   # Custom design system (dark cyberpunk theme)
│       ├── js/main.js       # Shared JS (cart, nav, toasts)
│       └── uploads/         # Product images (auto-created)
├── seed.py                  # Database seeder
├── requirements.txt
└── .env.example
```

---

## 🌐 Pages

| URL                      | Description                        |
|--------------------------|------------------------------------|
| `/`                      | Home — hero, products, news        |
| `/about`                 | About Us — team, mission           |
| `/contact`               | Contact form                       |
| `/products`              | RF component catalog with search   |
| `/products/{slug}`       | Product detail with add-to-cart    |
| `/cart`                  | Shopping cart + Stripe checkout    |
| `/configurator`          | 7-step RF product configurator     |
| `/auth/login`            | Login page                         |
| `/auth/register`         | Registration page                  |
| `/dashboard/favorites`   | Saved products                     |
| `/dashboard/orders`      | Order history with status tracker  |
| `/dashboard/payments`    | Saved payment methods              |
| `/dashboard/shipping`    | Shipping addresses                 |
| `/dashboard/settings`    | Account settings                   |
| `/admin`                 | Admin dashboard (admin only)       |
| `/admin/products`        | Product CRUD                       |
| `/admin/orders`          | Order management                   |
| `/admin/users`           | User management                    |
| `/admin/categories`      | Category management                |
| `/admin/quotes`          | Configurator quote management      |

---

## 🗄️ Database (Railway PostgreSQL)

1. Create a Railway project at https://railway.app
2. Add a PostgreSQL service
3. Copy the connection string to `.env` as `DATABASE_URL`
4. Run `python seed.py` to initialize tables and data

---

## 💳 Stripe Integration

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe dashboard
3. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```

---

## 🚂 Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set environment variables in the Railway dashboard matching your `.env` file.
