# Lafzverse

A poetry/shayari platform built with Django, DRF, PostgreSQL, and TailwindCSS. Users can browse, like, save, share, and submit shayaris. Admins can moderate submissions. A translation API supports Hindi ↔ English ↔ Urdu with pluggable providers.

## Tech Notes
- This project targets **Django 6.x** as requested.
- Database migrations are standard Django migrations (work with PostgreSQL). If you truly need MongoDB, you will need a different backend (e.g., Djongo) and a separate migration strategy.

## Features
- Home page with latest shayaris and categories
- Browse/search/filter by category, popularity, or author
- Shayari detail with likes, save, share, copy
- User submission flow with moderation queue
- Admin moderation panel and Django admin
- REST API for shayari CRUD and translation
- JWT auth for API + session auth for web
- Email/password registration and login without OTP verification

## Local Setup

### 1) Create virtualenv and install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
```bash
cp .env.example .env
```
Update values as needed.

### 3) Run migrations
```bash
python manage.py migrate
```

### 4) Seed sample data (optional)
```bash
python manage.py seed_data
```
Demo user: `demo / demo1234`

### 5) Create admin
```bash
python manage.py createsuperuser
```

### 6) Start server
```bash
python manage.py runserver
```
Open: http://127.0.0.1:8000/

## Docker
```bash
docker compose up --build
```
Then open http://localhost/

## Deploy on Render (Web Service + Render PostgreSQL)

This repo now includes [`render.yaml`](./render.yaml), so you can deploy from Render Blueprint.

If you prefer manual setup, use these Render settings:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `./scripts/entrypoint.sh`
- **Health Check Path**: `/healthz/`

Set environment variables in Render:

- `DEBUG=0`
- `SECRET_KEY=<long-random-secret>`
- `DATABASE_URL=<Render PostgreSQL Internal Database URL>`
- `ALLOWED_HOSTS=<your-render-domain>` (required only when using a custom domain)
- `CSRF_TRUSTED_ORIGINS=https://<your-render-domain>` (required only when using a custom domain)
- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` (for password-reset email links)
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
- `EMAIL_TIMEOUT=15`
- `WEB_CONCURRENCY=1`
- `GUNICORN_TIMEOUT=120`

Recommended security vars:

- `SESSION_COOKIE_SECURE=1`
- `CSRF_COOKIE_SECURE=1`
- `SECURE_SSL_REDIRECT=1`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=1`
- `SECURE_HSTS_PRELOAD=1`

If you attach a custom domain, add it to both `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

For uploaded media persistence, add a Render Disk mounted at:
- `/opt/render/project/src/media`

## API Endpoints
- `GET /api/shayaris/` - list shayaris (filters: `q`, `category`, `author`, `sort=popular|latest|oldest`)
- `POST /api/shayaris/` - create shayari (auth required)
- `POST /api/shayaris/{id}/like/` - like/unlike (auth required)
- `POST /api/shayaris/{id}/save/` - save/unsave (auth required)
- `GET /api/categories/`
- `POST /api/translate/`

JWT:
- `POST /api/token/` (username/password)
- `POST /api/token/refresh/`

## Translation Integration
The translation endpoint is pluggable. Choose one of the providers below.

### Option A: HuggingFace Inference API (default LLM provider)
Set environment variables:
```
TRANSLATION_PROVIDER=hf
HF_API_TOKEN=your_hf_token
```
Optional overrides per language pair:
```
HF_MODEL_HI_EN=Helsinki-NLP/opus-mt-hi-en
HF_MODEL_EN_HI=Helsinki-NLP/opus-mt-en-hi
HF_MODEL_HI_UR=Helsinki-NLP/opus-mt-hi-ur
HF_MODEL_UR_HI=Helsinki-NLP/opus-mt-ur-hi
HF_MODEL_EN_UR=Helsinki-NLP/opus-mt-en-ur
HF_MODEL_UR_EN=Helsinki-NLP/opus-mt-ur-en
```
The backend calls the HuggingFace Inference API and returns `translation` as JSON.

### Option B: Custom LLM HTTP Provider
If you have your own LLM endpoint, set:
```
TRANSLATION_PROVIDER=http
LLM_API_URL=https://your-llm.example.com/translate
LLM_API_KEY=your-key
```
The endpoint should accept JSON:
```json
{
  "text": "...",
  "source_lang": "hi",
  "target_lang": "en",
  "style": "poetic"
}
```
And return:
```json
{ "translation": "..." }
```

### Triggering Translation (Frontend)
Buttons with `.btn-translate` call `/api/translate/` via fetch. The JS lives in:
- `static/js/app.js`

It cycles translation targets based on the shayari language and updates the UI on success.

## Security Notes
- Use strong `SECRET_KEY` and set `DEBUG=0` in production.
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Session and CSRF cookies can be secured via env vars in `settings.py`.

## Tests
Basic tests can be added in `shayari/tests.py`. (Optional)

---
# lafzloom
# lafzloom
