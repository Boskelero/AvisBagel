# AvisBagel - Production-Ready Django Bagel Store

Django 5 web application for a bagel bakery with:
- Public website pages
- Product catalog
- Bundle builder
- Session cart with HTMX updates
- Checkout and order snapshots
- Blog
- Email notifications and newsletter signup
- Hebrew-first RTL UI + English LTR toggle

## Stack
- Python 3.11+
- Django 5.2+
- HTMX + Django templates
- Bootstrap 5 (CDN, RTL/LTR aware)
- WhiteNoise static serving
- `python-decouple` for environment variables
- PostgreSQL-ready via `DATABASE_URL`
- Railway Object Storage ready with `django-storages` + `boto3`

## Project Structure

```text
bagel_shop/
  config/ (settings split)
  apps/
    core/
    pages/
    blog/
    catalog/
    bundles/
    accounts/
    cart/
    checkout/
    orders/
    payments/
    notifications/
  templates/
  static/
  media/
  locale/
manage.py
requirements.txt
.env.example
Procfile
```

## Setup

1. Create and activate virtualenv

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```bash
pip install -r requirements-dev.txt
```

Production installs should use only:

```bash
pip install -r requirements.txt
```

3. Create `.env` from template

```bash
copy .env.example .env
```

4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create admin user

```bash
python manage.py createsuperuser
```

6. Seed sample data

```bash
python manage.py seed_store
```

7. Run server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/he/` (Hebrew default) or `http://127.0.0.1:8000/en/`.

## Live Reload In Development

- Uses `django-browser-reload` and `django-watchfiles`.
- Enabled only in `DJANGO_ENV=dev` (`bagel_shop/config/settings/dev.py`).
- Disabled in production (`prod.py` does not include these apps/middleware).
- Reload endpoint: `/__reload__/` (debug only).

After saving code or templates while running `python manage.py runserver`, browser tabs refresh automatically.

## Internationalization

- Default language: Hebrew (`he`)
- Secondary language: English (`en`)
- Locale files: `bagel_shop/locale/he/LC_MESSAGES/django.po`, `bagel_shop/locale/en/LC_MESSAGES/django.po`

Compile translations if GNU gettext is installed:

```bash
python manage.py compilemessages
```

## Key Environment Variables

- `DJANGO_ENV` = `dev` or `prod`
- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`

### Railway Object Storage (production)

- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_REGION_NAME`
- `AWS_S3_SIGNATURE_VERSION`
- `AWS_S3_ADDRESSING_STYLE`

In `prod` mode, uploaded media files use S3-compatible object storage.
In `dev` mode, media is stored locally under `bagel_shop/media/`.

## Core Flows Implemented

- Browse products (`/he/menu/` or `/en/menu/`)
- Add to cart via HTMX
- Update cart quantities and remove items via HTMX partials
- Build bundles and add to cart
- Checkout and place order
- Order + order item snapshot creation
- Payment intent record for pay-on-pickup/cash
- Order confirmation email (console backend in development)
- Newsletter signup persistence

## Admin

Use `/admin/` to manage:
- Categories, products, images
- Bundle templates and rules
- Orders and statuses
- Blog posts
- Newsletter subscribers
- Payment intents

## Railway Deployment Notes

1. Set service start command from `Procfile`:
   - `gunicorn bagel_shop.config.wsgi:application --log-file -`
2. Set `DJANGO_ENV=prod`
3. Set `DATABASE_URL` from Railway PostgreSQL plugin
4. Set object storage environment variables from Railway bucket
5. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your Railway domain
6. Run migrations after deploy:
   - `python manage.py migrate`
7. Collect static files:
   - `python manage.py collectstatic --noinput`

## Notes

- Payments app includes Stripe webhook skeleton for future integration.
- Session cart supports anonymous users.
- Views are intentionally thin; order/cart/domain logic lives in service modules.
