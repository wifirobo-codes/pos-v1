# Terminal POS v1.0

A simple **Python-based terminal Point of Sale (POS) system** for small shops/cafés with:

- Product inventory management
- Cart and checkout flow
- Multiple payment methods (Cash, Card, UPI, Wallet, Net Banking)
- Tax calculation
- Receipt generation
- Sales history dashboard

---

## Features

- **Interactive terminal UI** with clean table-style output
- **Inventory controls**
  - Add new products
  - Restock existing products
  - Update prices
  - Remove products
- **Sales flow**
  - Add/remove cart items
  - Auto subtotal/tax/total calculation
  - Payment handling and validation
- **Supported payment methods**
  - Cash
  - Card (Luhn check + expiry + CVV validation)
  - UPI
  - Wallet
  - Net Banking
- **Automatic receipt generation** in `receipts/`
- **Persistent data storage** using JSON files:
  - `products.json`
  - `sales.json`

---

## Project Structure

```text
pos-v1/
├── pos_system.py
├── products.json
├── sales.json
├── receipts/
│   └── receipt_YYYYMMDD_HHMMSS_REFERENCE.txt
└── README.md
```

---

## Requirements

- Python **3.8+**
- No external dependencies (uses Python standard library only)

---

## How to Run

1. Clone this repository:
   ```bash
   git clone https://github.com/wifirobo-codes/pos-v1.git
   cd pos-v1
   ```

2. Run the POS system:
   ```bash
   python pos_system.py
   ```

---

## Main Menu

When you start the app, you’ll see:

1. **New sale** – start billing with cart and checkout  
2. **Inventory control** – manage products and stock  
3. **Sales dashboard** – view totals and recent transactions  
4. **Exit terminal**

---

## Data Files

### `products.json`
Stores current inventory.

Example:
```json
{
  "id": 1,
  "name": "Coffee",
  "price": 50.0,
  "stock": 96
}
```

### `sales.json`
Stores completed transactions with payment details and receipt filename.

### `receipts/`
Contains generated text receipts, for example:
`receipt_20260709_184454_CASH.txt`

---

## Tax Configuration

Tax is controlled in `pos_system.py`:

```python
TAX_RATE = 0.08
```

Change this value to match your local tax rules.

---

## Notes

- Product stock decreases automatically after successful checkout.
- Card numbers are validated and stored in masked format only in transaction details.
- If JSON files are missing, the app initializes them automatically.

---

## Future Improvements (Optional Ideas, If you want to make pull requests for this, feel free to do so)

- User login / cashier roles
- Daily/monthly sales reports export (CSV/PDF)
- Barcode input support
- Discount and coupon system
- SQLite/MySQL backend instead of JSON storage
- Unit tests for payment and billing logic

---

## If any issue is found please record it instantly
