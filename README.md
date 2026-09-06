# AvisBagel - Production-Ready Django Bagel Store

Django 5 web application for a bagel bakery with:
- Public website pages
- Product catalog
- Bundle builder
- Session cart with HTMX updates
- Checkout and order snapshots
- Blog
- Email notifications and newsletter signup
- English-first UI + Hebrew RTL toggle retained for later rollout
- Scheduled Drop ordering with shared bagel capacity
- Automatic editable 1/6/12 bagel pricing and specialty upcharges
- Pickup-only checkout and staff production dashboard

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
    bundles/ (legacy models retained for existing data; not publicly routed)
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

- `BUCKET`
- `ENDPOINT`
- `ACCESS_KEY_ID`
- `SECRET_ACCESS_KEY`
- `REGION`
- `AWS_S3_SIGNATURE_VERSION`
- `AWS_S3_ADDRESSING_STYLE`

These names match Railway Bucket variable references directly. Standard
`AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, and `AWS_S3_REGION_NAME` variables are also accepted.
In `prod` mode, uploaded media files use S3-compatible object storage.
In `dev` mode, media is stored locally under `bagel_shop/media/`.

## Core Flows Implemented

- Browse products (`/he/menu/` or `/en/menu/`)
- Add to cart via HTMX
- Update cart quantities and remove items via HTMX partials
- Build a mixed bagel order with automatic deal pricing
- Checkout and place order
- Order + order item snapshot creation
- Payment intent record for pay-on-pickup/cash
- Order confirmation email (console backend in development)
- Newsletter signup persistence
- Publish scheduled Drops and choose their available products
- Prevent ordering before opening, after cutoff, or after sell-out
- Lock shared Drop capacity during final checkout validation
- Enforce a configurable maximum bagel quantity per order
- Release capacity when an order is canceled
- View production totals and export Drop orders as Excel (`/en/drops/staff/`)
- Create/edit Drops from the staff UI, select products, duplicate next week's Drop,
  extend the cutoff, adjust capacity, and update order statuses
- Show live customer pricing, deal savings, specialty upcharges, and order-cap feedback
- Capture catering and coordinated large-order inquiries
- Print a production/pickup sheet or export order details to Excel
- Search customer history and identify repeat customers
- Restrict private order confirmations to the customer session or staff
- Record deduplicated low-capacity and sold-out alert events
- Manage products, product photos, categories, deal pricing, inquiries, and
  subscribers from the dedicated staff workspace
- Search and filter all orders in the staff workspace, inspect complete order and
  pickup details, and update fulfillment status without opening Django admin
- Block stale, extras-only, over-cap, and over-capacity carts before checkout
- Safely prevent canceled orders from being reactivated after their capacity was resold
- Require at least one active bagel before a Drop can be published
- Preview and send each Drop announcement once to active subscribers
- Paginate growing staff lists and export orders, customers, products,
  subscribers, and inquiries as Excel workbooks

Seed the current nine-flavor client menu with:

```bash
python manage.py seed_abu_avi_menu
```

Create or refresh the complete client demo (9 bagels, Cream Cheese and Jams
categories, one live Drop, 20 unique customers/orders, 20 subscribers, and
sample inquiries, and three blog posts) with:

```bash
python manage.py seed_demo_data
```

The demo command is idempotent and only updates records using its dedicated
`DEMO` identifiers; it does not erase genuine orders or customers.

Bagel pricing tiers are editable in Django admin under **Bagel price tiers**.

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
4. Add a Railway Bucket and reference its `BUCKET`, `ENDPOINT`,
   `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`, and `REGION` variables in the web service
5. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your Railway domain
6. Run migrations after deploy:
   - `python manage.py migrate`
7. Collect static files:
   - `python manage.py collectstatic --noinput`
8. Create a staff login with `python manage.py createsuperuser`
9. For a client preview, run `python manage.py seed_demo_data`

## Notes

- Payments app includes Stripe webhook skeleton for future integration.
- Session cart supports anonymous users.
- Views are intentionally thin; order/cart/domain logic lives in service modules.
