# 🛍 Qazaq Catering — Telegram Mini App

> Full-stack Telegram Mini App for a catering business.  
> **FastAPI + aiogram 3.x** backend · **Vanilla JS** frontend · **Docker + Nginx** deployment.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![Aiogram](https://img.shields.io/badge/Aiogram-3.7-blue?logo=telegram)
![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 Preview

| Home | Catalog | Product | Checkout |
|------|---------|---------|----------|
| Greeting + quick nav | Categories + paginated products | Detail + add modal | FSM form → WhatsApp |

---

## ✨ Features

### 📱 Mini App (Frontend)
- Opens as a **Telegram bottom sheet** — no browser redirect
- **Telegram theme-aware** — auto-applies user's dark/light theme colors
- **Catalog** with categories, pagination, product cards
- **Add to cart modal** — choose between штуки (manual) or по гостям (per-person)
- **Checkout form** — name, date, time, location with native date/time pickers
- **Order history** with repeat order feature
- **Haptic feedback** on all interactions
- Telegram **BackButton** and **MainButton** integration

### ⚙️ Backend (FastAPI + aiogram)
- **Single process** — bot webhook + REST API on the same port
- **18 REST endpoints** for the Mini App
- **HMAC-SHA256 initData validation** on every authenticated request
- **Dual calculation engine** — manual qty or per-person
- **Order validation** — 24h minimum lead time
- **WhatsApp link generation** with encoded order summary
- **Admin notifications** on new orders
- **APScheduler** — review requests 1 day after event

### 🔒 Security
- Every API call validated via Telegram's HMAC-SHA256 algorithm
- `X-Init-Data` header checked against bot token secret
- Data freshness check (max 24h old)
- Protection against timing attacks (`hmac.compare_digest`)

---

## 🏗 Architecture

```
qazaq_miniapp/
├── backend/
│   ├── main.py               # FastAPI app + aiogram webhook (single entry point)
│   ├── api/
│   │   └── routes.py         # 18 REST endpoints for Mini App
│   ├── bot/
│   │   └── handlers/         # aiogram handlers (reused from bot project)
│   ├── config/               # Settings, logging
│   ├── models/               # SQLAlchemy ORM (7 tables)
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic (cart, orders, AI, reports)
│   ├── middlewares/          # DB session, user registration, error handling
│   ├── scheduler/            # APScheduler review tasks
│   └── utils/
│       ├── security.py       # Telegram initData HMAC validation ⭐
│       ├── whatsapp.py       # WhatsApp link builder
│       └── formatters.py     # Text formatters
│
├── frontend/
│   ├── index.html            # Single HTML file (SPA)
│   ├── css/style.css         # Telegram theme-aware UI (582 lines)
│   └── js/
│       ├── telegram.js       # Telegram WebApp API wrapper
│       ├── api.js            # HTTP client (auto X-Init-Data header)
│       └── app.js            # App controller — all views and logic
│
├── nginx/
│   └── nginx.conf            # SSL + reverse proxy config
│
├── docker/
│   ├── Dockerfile            # Multi-stage Python build
│   └── docker-compose.yml    # backend + nginx services
│
└── DEPLOY.md                 # Full deployment guide
```

---

## 🔐 Security: initData Validation

```python
# Every authenticated API request goes through this:
secret_key = HMAC-SHA256("WebAppData", bot_token)
expected   = HMAC-SHA256(secret_key, data_check_string)

if not hmac.compare_digest(expected, received_hash):
    raise 401 Unauthorized  # Data may be forged
```

---

## 🌐 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | — | Health check |
| GET | `/api/v1/categories` | — | All active categories |
| GET | `/api/v1/categories/{id}/products` | — | Paginated products |
| GET | `/api/v1/products/{id}` | — | Product detail |
| GET | `/api/v1/me` | ✅ | Current user profile |
| GET | `/api/v1/cart` | ✅ | Cart with totals |
| POST | `/api/v1/cart` | ✅ | Add/update cart item |
| DELETE | `/api/v1/cart/{id}` | ✅ | Remove item |
| DELETE | `/api/v1/cart` | ✅ | Clear cart |
| POST | `/api/v1/orders/checkout` | ✅ | Full checkout |
| GET | `/api/v1/orders` | ✅ | Order history |
| POST | `/api/v1/orders/{id}/repeat` | ✅ | Repeat past order |

---

## 🚀 Deployment

### Prerequisites
- VPS with Ubuntu 22/24
- Domain name with A record pointing to VPS IP
- Docker + docker-compose installed

### 1. Clone & configure

```bash
git clone https://github.com/yourname/qazaq-miniapp.git
cd qazaq-miniapp
cp .env.example .env
nano .env
```

### 2. Get SSL certificate

```bash
apt install -y certbot
certbot certonly --standalone -d yourdomain.com
```

### 3. Configure domain

```bash
sed -i 's/yourdomain.com/YOUR_DOMAIN/g' nginx/nginx.conf frontend/index.html
```

### 4. Launch

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

### 5. Register Mini App in BotFather

1. `@BotFather` → your bot → **Bot Settings** → **Menu Button**
2. URL: `https://yourdomain.com`
3. Button text: `🛍 Открыть меню`

---

## 🔧 Environment Variables

```env
BOT_TOKEN=          # BotFather token
DATABASE_URL=       # postgresql+asyncpg://user:pass@host/db?ssl=require
GEMINI_KEY=         # Google AI Studio key
ADMIN_ID=           # Your Telegram user ID
ADMIN_WHATSAPP=     # WhatsApp number
WEBHOOK_HOST=       # https://yourdomain.com
WEBAPP_URL=         # https://yourdomain.com
SECRET_KEY=         # Random 32+ char string
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot framework | aiogram 3.7 |
| API framework | FastAPI 0.111 |
| Server | uvicorn |
| Database | PostgreSQL (Neon.tech) |
| ORM | SQLAlchemy 2.0 async |
| AI | Google Gemini 1.5 Flash |
| Scheduler | APScheduler |
| Frontend | Vanilla JS (ES6 modules) |
| Styling | CSS custom properties + Telegram theme |
| Reverse proxy | Nginx |
| Containerization | Docker + docker-compose |

---

## 📄 License

MIT — free to use and modify.
