# POS Ingheng

POS Ingheng is a barcode-first point-of-sale system for school supply and general merchandise stores.
It is built with Django 5.2 and optimized for fast cashier throughput, inventory control, and admin workflows.
All currency values are in Philippine Peso (PHP / P).

## Current Features

- Fast cashier terminal with scanner-friendly input and automatic scan submission.
- Session/cache-backed cart (items are finalized only on checkout).
- Stock-safe checkout flow that prevents overselling.
- Product management with SKU generation and optional barcode auto-generation.
- Inventory tools split by purpose:
	- Catalog import/update (products).
	- Stock-in import (quantity increases only, with stock movement history).
- Barcode label printing (single product, selected products, or all products).
- Receipt output options:
	- Standard receipt page.
	- Thermal receipt page.
	- A4 PDF and thermal PDF downloads.
- Reports: gross sales, transactions, items sold, top products, date filtering.
- Admin user management: create/edit cashier/admin accounts and activate/deactivate users.
- Product/customer APIs for authenticated internal usage.

## Tech Stack

- Python 3.12
- Django 5.2.1
- Django REST Framework 3.16
- SQLite (default local) or MySQL (via environment settings)
- PyMySQL
- openpyxl and pandas (import processing)
- reportlab (receipt and barcode PDFs)

## Project Notes

- Custom auth model: `posapp.User` with role (`admin` or `cashier`).
- Cache backend is local memory by default (`LocMemCache`).
- Scanner path uses indexed barcode lookups and minimal payload responses.
- Checkout and stock deduction are handled in an atomic flow.

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust values if needed.
4. Run migrations:

```powershell
python manage.py migrate
```

5. Seed products and default users:

```powershell
python manage.py seed_pos_data
```

6. Start the server:

```powershell
python manage.py runserver
```

### Windows one-click launcher

Use either launcher from the project root to start the server and open the login page automatically:

```powershell
run_pos.bat
```

or

```powershell
powershell -ExecutionPolicy Bypass -File .\run_pos.ps1
```

Default seeded accounts:

- Admin: `admin` / `admin12345`
- Cashier: `cashier` / `cashier12345`

## Database Configuration

The app supports two database modes via `DB_ENGINE` in `.env`:

- `sqlite` (default): uses `db.sqlite3`.
- `mysql`: uses environment-driven MySQL connection settings.

## Key Admin Routes

- `/products/` product list and management.
- `/products/import/` catalog import.
- `/products/stock-in/` stock-in import.
- `/products/export/` product export CSV.
- `/products/export/stock-template/` stock-in template CSV.
- `/products/export/stock-levels/` stock level export CSV.
- `/products/barcodes/` barcode label PDF generation.
- `/users/` account management.
- `/users/add/` create admin/cashier account.

## Import Formats

### Catalog Import (`/products/import/`)

Supported upload formats: CSV and Excel workbook.

Expected columns:

- `sku`
- `barcode`
- `name`
- `category`
- `description`
- `cost_price`
- `selling_price`
- `stock_quantity`
- `reorder_level`
- `is_active`

### Stock-In Import (`/products/stock-in/`)

Expected columns:

- `barcode` or `sku` (at least one)
- `stock_in_quantity`
- `reference` (optional)

Sample files are available in:

- `seed_data/products.csv`
- `seed_data/import_samples/`

## Management Commands

- Seed baseline data:

```powershell
python manage.py seed_pos_data
```

- Reset transactional and inventory data:

```powershell
python manage.py reset_pos_data
python manage.py reset_pos_data --yes
python manage.py reset_pos_data --yes --reseed
python manage.py reset_pos_data --yes --include-users
```

## API Endpoints

- `GET /api/products/?q=<term>&barcode=<code>`
- `GET /api/products/<id>/`
- `PATCH /api/products/<id>/`
- `POST /api/scan/` with JSON body `{ "barcode": "..." }`

## Documentation

- System guide: [docs/SYSTEM_GUIDE.md](docs/SYSTEM_GUIDE.md)

