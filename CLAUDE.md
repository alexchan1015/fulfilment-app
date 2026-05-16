# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PulseLabz Dashboard is a Django 2.0.5 / Python 3.6 order fulfillment application. It aggregates orders from Best Buy CA Marketplace and WooCommerce (pulselabz.com), fulfills them through Newegg's marketplace API, and logs results to a Google Sheets spreadsheet. The Django project is named `scraper`; the sole app is `chair`.

## Development Setup

```bash
python -m venv env
source env/bin/activate       # Windows: env\Scripts\activate.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Two secret files are required locally (not in the repo):
- `secrets.py` — exports `BESTBUY_KEY`, `CARRIER_CODE`, `NEWEGG_KEY`, `NEWEGG_AUTH`, `SG_KEY`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `WC_KEY`, `WC_SECRET`
- `pulselabz.json` — Google service-account credentials dict

In production (Heroku) these are provided as environment variables instead. The settings file tries `secrets.py`/`pulselabz.json` first and falls back to `os.environ`.

The database defaults to SQLite (`db.sqlite3`) locally; in any environment that sets `DATABASE_URL` it switches to PostgreSQL via `dj-database-url`.

## Commands

```bash
# Run dev server
python manage.py runserver

# Apply migrations after model changes
python manage.py migrate

# Create a new migration after model changes
python manage.py makemigrations

# Pull latest orders from Best Buy + WooCommerce (also auto-accepts eligible orders)
python manage.py grab_orders

# Process pending Newegg shipping reports and request new ones if needed
python manage.py handle_reports
```

There are no automated tests in this codebase.

## Architecture

### Order flow

1. **Ingest** — Orders are pulled from two sources:
   - Best Buy CA (`chair/order_processing/bestbuy.py` → `grab_orders`) via REST API
   - WooCommerce (`chair/order_processing/woocommerce.py` → `grab_orders_woocommerce`) via the `woocommerce` SDK

2. **Product mapping** — `chair/product_info.py` contains `PRODUCT_INFO`, a dict that maps the human-readable product name (as it appears on Best Buy / WooCommerce) to a `(newegg_item_number, part_number)` tuple. The `part_number` (e.g. `"G-BK"`) is used as Newegg's `SellerPartNumber` when creating a shipment order. This mapping must be updated whenever a new product is listed.

3. **Fulfillment** — `chair/order_processing/newegg.py` submits `MultiChannel_Order_DATA` feed requests to Newegg CA's marketplace API (`SELLER_ID = 'AFG1'`). After Newegg processes the shipment, the feed result contains the tracking number.

4. **Tracking** — Once a tracking number is available it is pushed back to Best Buy (`send_tracking_bestbuy`) and optionally emailed to the customer (`chair/order_processing/emails.py`).

5. **Reporting** — `chair/order_processing/google_sheets_upload.py` writes order details into a specific Google Sheet (identified at call time by `sheets_key`). Column layout in the sheet is hardcoded in `post_order_info`.

### Models (`chair/models.py`)

| Model | Purpose |
|---|---|
| `Order` | One row per order-line. Tracks `source` (`bestbuy`/`woocommerce`), fulfillment booleans (`newegg_shipped`, `bestbuy_filled`, `uploaded`), and `newegg_feed` (the feed request ID used to retrieve tracking). |
| `Customer` | Shipping address; linked to `Order` via FK. |
| `OrderStatus` | Per-product settings row (one per SKU). `auto_fulfill=True` means orders for that product are accepted on Best Buy automatically when ingested. |
| `Report` | Tracks Newegg report request IDs and whether they have been processed. |

### Views / URL structure (`chair/views.py`, `scraper/urls.py`)

All views require login. They return `JsonResponse` for AJAX calls from the dashboard. Key endpoints:

| URL | Action |
|---|---|
| `/dashboard/` | Main page; renders pending + completed orders |
| `/orders/grab_latest/` | Triggers `grab_orders` + `grab_orders_woocommerce` |
| `/orders/accept/<order_id>/` | Accepts a Best Buy order |
| `/orders/reject/<order_id>/` | Rejects a Best Buy order |
| `/orders/newegg_fulfill/<order_id>/` | Ships order through Newegg |
| `/orders/get_report/` | Requests an unshipped + shipped report from Newegg |
| `/orders/parse_report/<report_id>/` | Parses a Newegg report to extract tracking numbers |
| `/orders/update_tracking/<order_id>/` | Sends tracking info back to Best Buy |
| `/orders/upload/<order_id>/<sheets_key>` | Logs order to Google Sheets |
| `/orders/fulfill/<product_name>/on\|off` | Toggles auto-fulfillment for a product |

### Management commands

- `grab_orders` — scheduled entry point for pulling new orders; also runs auto-accept logic and prunes old `Report` rows (keeps latest 10).
- `handle_reports` — scheduled entry point for closing the fulfillment loop: parses outstanding reports, then requests a new report if any orders are shipped-but-untracked.

### Templates

- `templates/` — base layout and Django auth templates (login, password reset)
- `chair/templates/dashboard/dashboard.html` — main dashboard UI
- `chair/templates/dashboard/order_sent_mail.html` — customer shipping notification email

### Static assets

Served via WhiteNoise. Source lives in `chair/static/`; `python manage.py collectstatic` writes to `static/` at the repo root for production.

## Deployment

Deployed on Heroku. `Procfile` runs `gunicorn scraper.wsgi`. Pushes to GitHub trigger automatic Heroku deploys. All secrets are set as Heroku config vars.
