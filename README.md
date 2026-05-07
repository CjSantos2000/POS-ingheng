# POS Ingheng

Intermediate POS system for a school supply and general merchandise store, built with Django and MySQL. The implementation prioritizes barcode scan speed, rapid transaction flow, and a keyboard-first cashier UI.

## Highlights

- Barcode-first cashier screen tuned for keyboard wedge scanners.
- Session/cache-backed cart so scans do not write to the database until checkout.
- Atomic checkout with row locking to prevent overselling under concurrent cashiers.
- Inventory CRUD, CSV/XLSX import, CSV export, low-stock monitoring, receipts, and sales reporting.
- REST endpoints for product lookup and mobile inventory updates.
- Optional camera scanning using the browser Barcode Detector API when supported.

## Documentation

- Full system guide: [docs/SYSTEM_GUIDE.md](docs/SYSTEM_GUIDE.md)
- Sample seed import file: [seed_data/products.csv](seed_data/products.csv)

## Tech Stack

- Python 3.12
- Django 5
- Django REST framework
- MySQL 8
- PyMySQL
- openpyxl
- reportlab

## Database Schema

Core tables:

- `posapp_user`: custom Django user with `role` field (`admin`, `cashier`).
- `posapp_product`: inventory master with indexed `barcode`, indexed `name`, stock and reorder data.
- `posapp_customer`: optional customer records.
- `posapp_saletransaction`: checkout header with indexed `receipt_number` and `created_at`.
- `posapp_saleitem`: checkout line items.
- `posapp_stockmovement`: audit trail for imports, manual updates, and sales deductions.

Performance-related indexes are defined on barcode, product name/activity, category/activity, receipt number, and transaction date.

## Barcode Handling

USB barcode scanners that act as keyboards are the default path:

1. Cashier lands on the terminal page with focus on the barcode field.
2. Scanner types the barcode and usually sends Enter.
3. Frontend posts the barcode to `/terminal/scan/`.
4. Server performs an indexed barcode lookup and updates the in-memory cart.
5. Response returns the updated line and totals immediately.

This keeps the scan path short and avoids transaction table writes until checkout. For camera-based scanning, the page includes optional browser-side detection with `BarcodeDetector` when available.

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust database settings.
4. Run MySQL and create the database if needed.
5. Apply migrations:

```powershell
python manage.py migrate
```

6. Load sample data:

```powershell
python manage.py seed_pos_data
```

7. Start the server:

```powershell
python manage.py runserver
```

Default seeded accounts:

- Admin: `admin` / `admin12345`
- Cashier: `cashier` / `cashier12345`

## Docker Setup

1. Copy `.env.example` to `.env`.
2. Start services:

```powershell
docker compose up --build
```

3. Open `http://127.0.0.1:8000`.
4. If you need host access to container MySQL, use `127.0.0.1:3307` (container port remains 3306).

## Inventory Import Format

Supported file types: CSV and XLSX.

Columns:

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

See [seed_data/products.csv](seed_data/products.csv) for a working sample.

## API Endpoints

- `GET /api/products/?q=term`
- `GET /api/products/<id>/`
- `PATCH /api/products/<id>/`
- `POST /api/scan/` with JSON `{ "barcode": "..." }`

## Reporting

- Dashboard summary
- Daily and date-range sales report
- Top-selling products
- Low-stock view

## Notes On Performance

- Barcode lookups use an indexed `barcode` column.
- Terminal scans load only the minimum product fields needed for scan-time response.
- Active cart state is stored in cache to avoid repeated writes during scanning.
- Checkout uses `select_for_update()` and bulk inserts for sale items and stock movements.
- Product search is constrained and paginated at the view layer for quick operator feedback.

For full operating instructions, deployment workflow, barcode scanner handling, and troubleshooting, see [docs/SYSTEM_GUIDE.md](docs/SYSTEM_GUIDE.md).

