# POS Ingheng System Guide

## 1. System Overview

POS Ingheng is a barcode-first point-of-sale system designed for a school supply and general merchandise store. The system is optimized for fast cashier operation, especially when using barcode scanners for rapid item entry during checkout.

Primary goals:

- Fast barcode scanning and cart updates.
- Minimal delay between scan and line-item display.
- Simple, keyboard-first operation for cashiers.
- Reliable stock deduction and transaction logging.
- Easy inventory import, reporting, and day-to-day administration.

## 2. Main Features

### Sales and Checkout

- Barcode-driven sales terminal.
- Automatic line-item creation when a barcode is scanned.
- Quantity automatically increases when the same barcode is scanned again.
- Running subtotal, tax, discount, and total calculation.
- Fast sale finalization.
- Receipt view in browser and PDF receipt generation.

### Inventory Management

- Product creation, update, and editing.
- CSV and Excel product import.
- CSV product export.
- Stock quantity tracking.
- Low-stock monitoring based on reorder level.

### User Management

- Login-based access control.
- Admin role for inventory, reports, and overall management.
- Cashier role for daily sales processing.

### Reports and Monitoring

- Dashboard metrics.
- Transaction history.
- Daily or custom date-range sales reporting.
- Top-selling products.
- Low-stock alerts.

### Integration and Extensibility

- MySQL-ready database configuration.
- SQLite fallback for fast local development.
- REST API endpoints for product access and barcode scan integration.
- Optional browser camera barcode scanning when supported.

## 3. User Roles

### Admin

Admin users can:

- Access product management.
- Import and export product data.
- View reports and low-stock alerts.
- Manage product pricing and stock.
- Access Django admin if enabled.

### Cashier

Cashier users can:

- Log in to the terminal.
- Scan products and process sales.
- View transactions.
- Manage customers if customer tracking is used.

## 4. System Workflow

### 4.1 Product Setup Workflow

1. Admin logs in.
2. Admin adds products manually or imports them from CSV or XLSX.
3. Each product must have a unique barcode and SKU.
4. Selling price, cost price, stock quantity, and reorder level are set.
5. Products become available for scanning at the terminal.

### 4.2 Sales Workflow

1. Cashier opens the terminal page.
2. Cursor remains focused on the barcode field.
3. Cashier scans an item using a USB scanner or camera-based scanning.
4. System looks up the barcode and adds the item to the cart.
5. If the same barcode is scanned again, quantity increases.
6. Cashier optionally adjusts quantity, selects customer, adds discount, and chooses payment method.
7. Cashier clicks checkout.
8. System creates the transaction, inserts line items, deducts stock, and generates a receipt.

### 4.3 Reporting Workflow

1. Admin opens the reports page.
2. Admin selects a date range if needed.
3. System shows sales totals, item counts, and top products.
4. Admin reviews low-stock items from the dashboard or the low-stock page.

## 5. Project Structure

Main files and folders:

- `config/`: Django project configuration.
- `posapp/`: Main POS application.
- `posapp/models.py`: Database models.
- `posapp/services.py`: Performance-sensitive POS logic such as cart and checkout flow.
- `posapp/views.py`: Web and API view logic.
- `posapp/templates/`: HTML templates.
- `posapp/static/`: CSS and JavaScript assets.
- `seed_data/`: Sample import data.
- `docs/`: System documentation.

## 6. Installation Guide

### 6.1 Prerequisites

Install the following:

- Python 3.12 or newer.
- MySQL 8 for production-style deployment.
- Pip.
- Virtual environment tooling.
- Docker and Docker Compose if containerized deployment is preferred.

### 6.2 Local Installation

1. Create a virtual environment.
2. Activate the virtual environment.
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env`.
5. Update database settings inside `.env`.
6. Run migrations:

```powershell
python manage.py migrate
```

7. Seed sample data:

```powershell
python manage.py seed_pos_data
```

8. Start the development server:

```powershell
python manage.py runserver
```

9. Open the application in the browser at `http://127.0.0.1:8000`.

### 6.3 Docker Installation

1. Copy `.env.example` to `.env`.
2. Update `.env` values.
3. Start services:

```powershell
docker compose up --build
```

4. Open `http://127.0.0.1:8000`.

## 7. Environment Configuration

Important environment variables:

- `DJANGO_SECRET_KEY`: Django secret key.
- `DJANGO_DEBUG`: `True` or `False`.
- `DJANGO_ALLOWED_HOSTS`: Allowed hostnames.
- `DJANGO_TIME_ZONE`: Time zone used by Django.
- `DB_ENGINE`: `mysql` or `sqlite`.
- `DB_NAME`: Database name.
- `DB_USER`: Database username.
- `DB_PASSWORD`: Database password.
- `DB_HOST`: Database host.
- `DB_PORT`: Database port.
- `POS_TAX_RATE`: Decimal tax rate, for example `0.10` for 10%.
- `POS_LOW_STOCK_DEFAULT`: Default low-stock threshold.

## 8. Database Design Summary

### User

The user table extends Django authentication and adds a `role` field.

### Product

Key fields:

- SKU
- Barcode
- Name
- Category
- Cost price
- Selling price
- Stock quantity
- Reorder level
- Active status

Performance notes:

- Barcode is indexed for very fast scan lookup.
- Name and category are indexed for inventory search and filtering.

### SaleTransaction

Stores each completed sale, including cashier, totals, payment method, and receipt number.

### SaleItem

Stores each item sold under a transaction.

### StockMovement

Stores inventory changes caused by imports, sales, or manual adjustments.

### Customer

Optional table for customer information.

## 9. Barcode Scanner Guide

### 9.1 Recommended Scanner Type

The easiest and fastest setup is a generic USB barcode scanner that works as a keyboard input device. This is often called a keyboard wedge scanner.

### 9.2 How It Works In This System

1. The scanner sends barcode text into the focused input field.
2. The scanner usually sends an Enter key after the barcode.
3. The terminal JavaScript catches the Enter key and posts the barcode to the scan endpoint.
4. The backend performs an indexed lookup and updates the in-memory cart.

### 9.3 Why This Is Fast

- The lookup uses the `barcode` index.
- The cart is held in cache instead of writing to the database on every scan.
- The server only loads the minimum product fields required for scan response.
- Actual database writes occur during checkout, not during every scan.

### 9.4 Camera-Based Scanning

The terminal includes optional support for browser camera scanning when the browser supports the `BarcodeDetector` API.

Notes:

- This feature depends on browser support.
- It is useful for mobile or tablet scenarios.
- USB scanners remain the preferred production method for maximum speed.

### 9.5 Barcode Testing Procedure

Use this checklist when validating scanner behavior:

1. Open the terminal page.
2. Ensure the barcode field is focused.
3. Scan a known product barcode.
4. Confirm the item appears in the cart in under one second.
5. Scan the same barcode again.
6. Confirm the quantity increases instead of creating a duplicate product line.
7. Scan an unknown barcode.
8. Confirm the UI shows a clear not-found message.
9. Checkout and verify stock decreases correctly.

## 10. Inventory Management Guide

### 10.1 Adding Products Manually

1. Log in as admin.
2. Open Products.
3. Click Add Product.
4. Fill in SKU, barcode, name, pricing, stock quantity, and reorder level.
5. Save.

### 10.2 Importing Products

Use CSV or XLSX with these columns:

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

Recommended steps:

1. Start from the sample file in `seed_data/products.csv`.
2. Keep all barcodes unique.
3. Verify selling prices before import.
4. Import through the product import page.
5. Review a few products after import.

### 10.3 Exporting Products

Admins can export current products as CSV for backup, bulk editing, or auditing.

### 10.4 Low-Stock Monitoring

Products appear in low-stock alerts when `stock_quantity <= reorder_level`.

## 11. Sales Terminal Guide

### 11.1 Terminal Layout

The terminal page has three main sections:

- Barcode scan input and optional camera area.
- Current cart with quantity editing.
- Checkout section with totals and payment settings.

### 11.2 Best Practices For Cashiers

- Keep hands on scanner and keyboard.
- Avoid using the mouse unless necessary.
- Confirm the cursor remains in the barcode field between scans.
- Use quantity editing only when correcting mistakes.
- Clear the cart only when a sale is canceled.

### 11.3 Checkout Notes

During checkout:

- The system validates cart contents.
- Product rows are locked while stock is checked.
- Sale items are inserted in bulk.
- Stock movements are written in bulk.
- The cart is cleared after successful completion.

## 12. Receipt Guide

After checkout, the system provides:

- On-screen receipt view.
- PDF receipt output.

Receipt contents include:

- Receipt number.
- Cashier.
- Date and time.
- Sold items.
- Quantities.
- Totals.
- Payment method.

## 13. Reports Guide

Available reporting features:

- Gross sales totals.
- Transaction count.
- Item count sold.
- Top-selling products.
- Low-stock alert list.

Use reports to:

- Review daily performance.
- Monitor fast-moving items.
- Plan restocking.
- Compare selling periods.

## 14. API Guide

### 14.1 Product Search

`GET /api/products/?q=term`

Returns matching active products for search or mobile inventory tools.

### 14.2 Product Detail And Update

`GET /api/products/<id>/`

`PATCH /api/products/<id>/`

Admins can update product details through the API.

### 14.3 Barcode Scan API

`POST /api/scan/`

Example request body:

```json
{
  "barcode": "8851010000010"
}
```

Example response body:

```json
{
  "item": {
    "product_id": 1,
    "barcode": "8851010000010",
    "name": "Exercise Notebook",
    "unit_price": "0.75",
    "quantity": 1,
    "subtotal": "0.75",
    "stock_quantity": 150
  },
  "totals": {
    "subtotal": "0.75",
    "tax": "0.00",
    "total": "0.75"
  }
}
```

## 15. Performance Guide

The system prioritizes barcode and checkout speed using the following design choices:

- Indexed barcode lookups.
- Cache-based active cart.
- Reduced per-scan database writes.
- Limited fields loaded during scan processing.
- Bulk creation of sale items and stock movements.
- Row locking only during final checkout.

Recommended production practices:

- Use MySQL instead of SQLite.
- Use SSD storage.
- Use a stable local network if deployed over LAN.
- Use a USB scanner for the main cashier terminal.
- Replace local memory cache with Redis if running multiple app instances.

## 16. Security Guide

Recommended security steps before production use:

- Change the default passwords created by the seed command.
- Set `DJANGO_DEBUG=False`.
- Use a strong `DJANGO_SECRET_KEY`.
- Restrict `DJANGO_ALLOWED_HOSTS`.
- Place the system behind HTTPS in production.
- Limit admin account access.
- Back up the MySQL database regularly.

## 17. Backup And Maintenance

### Backup Recommendations

- Back up the MySQL database daily.
- Export product CSV regularly.
- Keep a copy of `.env` in secure storage.

### Maintenance Checklist

- Review low-stock items daily.
- Review transaction history daily.
- Check barcode scanner operation before store opening.
- Update prices and stock promptly.
- Apply security updates to Python packages and Docker images.

## 18. Troubleshooting

### Scanner Does Not Add Products

Check the following:

- The barcode field is focused.
- The product barcode exists in the database.
- The product is active.
- The scanner is configured to send Enter after the barcode.

### Item Not Found After Scan

Possible causes:

- Wrong barcode in the product record.
- Scanner reading a damaged label.
- Imported barcode includes extra spaces or formatting.

### Checkout Fails

Possible causes:

- Cart is empty.
- Stock is insufficient.
- Product became inactive.
- Database connection issue.

### Import Fails

Possible causes:

- Missing `barcode` column.
- Invalid numeric values in pricing or stock columns.
- Unsupported file format.

### Slow Performance

Review the following:

- Confirm MySQL is being used.
- Confirm barcode values are unique and indexed.
- Check server CPU and disk usage.
- Avoid hosting development and production traffic on the same weak machine.

## 19. Default Seed Accounts

When sample data is loaded, the following users are created:

- Admin: `admin` / `admin12345`
- Cashier: `cashier` / `cashier12345`

Change these passwords immediately in any non-test environment.

## 20. Future Enhancements

Potential next improvements:

- Dedicated customer sales history.
- Barcode label generation and printing.
- Receipt printer formatting for thermal printers.
- Redis cache for multi-terminal deployments.
- Offline sync support.
- Expanded mobile inventory API.
- Audit log for manual stock adjustments.

## 21. Quick Start Checklist

For a first working system:

1. Install dependencies.
2. Configure `.env`.
3. Run migrations.
4. Seed sample data.
5. Log in as admin and verify products.
6. Log in as cashier and test barcode scanning.
7. Complete a test sale.
8. Verify stock deduction and receipt generation.
9. Change default passwords.
