import json
import os
import ctypes
import re
from datetime import datetime


DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
SALES_FILE = os.path.join(DATA_DIR, "sales.json")
RECEIPTS_DIR = os.path.join(DATA_DIR, "receipts")
TAX_RATE = 0.08


class RetroColors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    DIM = "\033[2m"
    BOLD = "\033[1m"


def enable_ansi_on_windows():
    if os.name != "nt":
        return

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()

    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        mode.value |= 0x0004
        kernel32.SetConsoleMode(handle, mode)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def fmt_money(value):
    return f"${value:,.2f}"


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return fallback


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def default_products():
    return [
        {"id": 1001, "name": "Coffee", "price": 2.50, "stock": 80},
        {"id": 1002, "name": "Tea", "price": 2.20, "stock": 60},
        {"id": 1003, "name": "Bagel", "price": 3.75, "stock": 45},
        {"id": 1004, "name": "Sandwich", "price": 6.50, "stock": 40},
        {"id": 1005, "name": "Muffin", "price": 2.95, "stock": 50},
    ]


def header(title):
    print(RetroColors.GREEN + RetroColors.BOLD + "=" * 74)
    print(" TERMINAL POS v1.0".ljust(73) + "|")
    print("=" * 74)
    print(f" {title}".ljust(73) + "|")
    print("=" * 74 + RetroColors.RESET)


def pause(message="Press ENTER to continue..."):
    input(RetroColors.DIM + message + RetroColors.RESET)


def ask_int(prompt, allow_blank=False):
    while True:
        value = input(prompt).strip()
        if allow_blank and value == "":
            return None
        try:
            return int(value)
        except ValueError:
            print("Invalid number.")


def ask_float(prompt, allow_blank=False):
    while True:
        value = input(prompt).strip()
        if allow_blank and value == "":
            return None
        try:
            return float(value)
        except ValueError:
            print("Invalid amount.")


def normalize_text(value):
    return value.strip()


def mask_card_number(card_number):
    digits = re.sub(r"\D", "", card_number)
    if len(digits) < 4:
        return "****"
    return f"**** **** **** {digits[-4:]}"


def luhn_check(card_number):
    digits = re.sub(r"\D", "", card_number)
    if not digits.isdigit() or len(digits) < 13 or len(digits) > 19:
        return False

    total = 0
    reverse_digits = digits[::-1]
    for index, char in enumerate(reverse_digits):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate_expiry(expiry_text):
    match = re.fullmatch(r"(0[1-9]|1[0-2])/(\d{2})", expiry_text.strip())
    if not match:
        return False

    month = int(match.group(1))
    year = 2000 + int(match.group(2))
    current = datetime.now()
    return (year > current.year) or (year == current.year and month >= current.month)


def validate_upi_id(upi_id):
    return bool(re.fullmatch(r"[A-Za-z0-9.\-_]{2,}@[A-Za-z0-9]{2,}", upi_id.strip()))


def validate_mobile_number(number):
    digits = re.sub(r"\D", "", number)
    return len(digits) == 10


def choose_payment_method(total):
    while True:
        print("\nPayment methods:")
        print("1) Cash")
        print("2) Card")
        print("3) UPI")
        print("4) Wallet")
        print("5) Net Banking")
        method = input("Choose payment method: ").strip()

        if method == "1":
            while True:
                cash = ask_float(f"Cash received ({fmt_money(total)} due): ")
                if cash < total:
                    print("Insufficient cash.")
                    continue
                return {
                    "method": "Cash",
                    "paid": round(cash, 2),
                    "reference": "CASH",
                    "details": {"cash": round(cash, 2)},
                }

        if method == "2":
            cardholder = normalize_text(input("Cardholder name: "))
            card_number = normalize_text(input("Card number: "))
            expiry = normalize_text(input("Expiry (MM/YY): "))
            cvv = normalize_text(input("CVV: "))

            if not cardholder:
                print("Cardholder name is required.")
                continue
            if not luhn_check(card_number):
                print("Card number failed validation.")
                continue
            if not validate_expiry(expiry):
                print("Card is expired or expiry is invalid.")
                continue
            if not re.fullmatch(r"\d{3,4}", cvv):
                print("CVV must be 3 or 4 digits.")
                continue

            auth_code = datetime.now().strftime("%H%M%S")
            return {
                "method": "Card",
                "paid": round(total, 2),
                "reference": f"CARD-{auth_code}",
                "details": {
                    "cardholder": cardholder,
                    "card_masked": mask_card_number(card_number),
                    "expiry": expiry,
                },
            }

        if method == "3":
            upi_id = normalize_text(input("UPI ID: "))
            if not validate_upi_id(upi_id):
                print("UPI ID format is invalid.")
                continue

            confirmation = normalize_text(input(f"Approve UPI payment of {fmt_money(total)}? (Y/N): ")).lower()
            if confirmation not in {"y", "yes"}:
                print("UPI payment cancelled.")
                continue

            reference = f"UPI-{datetime.now().strftime('%H%M%S')}"
            return {
                "method": "UPI",
                "paid": round(total, 2),
                "reference": reference,
                "details": {"upi_id": upi_id},
            }

        if method == "4":
            provider = normalize_text(input("Wallet provider (Paytm/PhonePe/AmazonPay/etc): "))
            mobile = normalize_text(input("Wallet mobile number: "))
            if not provider:
                print("Wallet provider is required.")
                continue
            if not validate_mobile_number(mobile):
                print("Mobile number must be 10 digits.")
                continue

            confirmation = normalize_text(input(f"Approve wallet payment of {fmt_money(total)}? (Y/N): ")).lower()
            if confirmation not in {"y", "yes"}:
                print("Wallet payment cancelled.")
                continue

            reference = f"WALLET-{datetime.now().strftime('%H%M%S')}"
            return {
                "method": "Wallet",
                "paid": round(total, 2),
                "reference": reference,
                "details": {"provider": provider, "mobile": mobile},
            }

        if method == "5":
            bank_name = normalize_text(input("Bank name: "))
            account_last4 = normalize_text(input("Account last 4 digits: "))
            if not bank_name:
                print("Bank name is required.")
                continue
            if not re.fullmatch(r"\d{4}", account_last4):
                print("Account last 4 digits must be numeric.")
                continue

            confirmation = normalize_text(input(f"Confirm net banking payment of {fmt_money(total)}? (Y/N): ")).lower()
            if confirmation not in {"y", "yes"}:
                print("Net banking payment cancelled.")
                continue

            reference = f"NET-{datetime.now().strftime('%H%M%S')}"
            return {
                "method": "Net Banking",
                "paid": round(total, 2),
                "reference": reference,
                "details": {"bank_name": bank_name, "account_last4": account_last4},
            }

        print("Unknown payment method.")


def find_product(products, product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None


def show_products(products):
    print("ID     ITEM                 PRICE      STOCK")
    print("-" * 44)
    for product in products:
        print(
            f"{product['id']:<6} {product['name']:<20} "
            f"{fmt_money(product['price']):>8}   {product['stock']:>6}"
        )


def show_cart(cart):
    if not cart:
        print("Cart is empty.")
        return
    print("ID     ITEM                 QTY    UNIT      TOTAL")
    print("-" * 56)
    for item in cart:
        line_total = item["qty"] * item["price"]
        print(
            f"{item['id']:<6} {item['name']:<20} {item['qty']:>3}  "
            f"{fmt_money(item['price']):>8}  {fmt_money(line_total):>8}"
        )


def calc_totals(cart):
    subtotal = sum(item["qty"] * item["price"] for item in cart)
    tax = subtotal * TAX_RATE
    total = subtotal + tax
    return subtotal, tax, total


def build_receipt_lines(transaction):
    lines = []
    lines.append("=" * 56)
    lines.append("TERMINAL POS v1.0")
    lines.append("ITEMIZED BILL")
    lines.append("=" * 56)
    lines.append(f"Date/Time : {transaction['timestamp']}")
    lines.append(f"Reference : {transaction['payment_reference']}")
    lines.append(f"Payment   : {transaction['payment_method']}")
    lines.append("-" * 56)
    lines.append("ITEM                 QTY    UNIT      TOTAL")
    lines.append("-" * 56)

    for item in transaction["items"]:
        name = item["name"][:20]
        line_total = item["qty"] * item["price"]
        lines.append(
            f"{name:<20} {item['qty']:>3}  {fmt_money(item['price']):>8}  {fmt_money(line_total):>8}"
        )

    lines.append("-" * 56)
    lines.append(f"SUBTOTAL : {fmt_money(transaction['subtotal'])}")
    lines.append(f"TAX 8%   : {fmt_money(transaction['tax'])}")
    lines.append(f"TOTAL    : {fmt_money(transaction['total'])}")
    lines.append(f"PAID     : {fmt_money(transaction['cash'])}")
    lines.append(f"CHANGE   : {fmt_money(transaction['change'])}")

    details = transaction.get("payment_details", {})
    if transaction["payment_method"] == "Card":
        lines.append(f"Card     : {details.get('card_masked', 'N/A')}")
    elif transaction["payment_method"] == "UPI":
        lines.append(f"UPI ID   : {details.get('upi_id', 'N/A')}")
    elif transaction["payment_method"] == "Wallet":
        lines.append(f"Wallet   : {details.get('provider', 'N/A')}")
        lines.append(f"Mobile   : {details.get('mobile', 'N/A')}")
    elif transaction["payment_method"] == "Net Banking":
        lines.append(f"Bank     : {details.get('bank_name', 'N/A')}")
        lines.append(f"Acct L4  : {details.get('account_last4', 'N/A')}")

    lines.append("=" * 56)
    lines.append("Thank you for shopping with us.")
    lines.append("=" * 56)
    return lines


def save_receipt(transaction):
    os.makedirs(RECEIPTS_DIR, exist_ok=True)

    timestamp_token = datetime.now().strftime("%Y%m%d_%H%M%S")
    reference_token = re.sub(r"[^A-Za-z0-9]+", "", transaction["payment_reference"])
    if not reference_token:
        reference_token = "PAY"

    filename = f"receipt_{timestamp_token}_{reference_token}.txt"
    receipt_path = os.path.join(RECEIPTS_DIR, filename)

    with open(receipt_path, "w", encoding="utf-8") as file:
        file.write("\n".join(build_receipt_lines(transaction)) + "\n")

    return receipt_path


def run_sale(products, sales):
    cart = []

    while True:
        clear_screen()
        header("POS SALE SCREEN")
        print("Available inventory:")
        show_products(products)
        print("\nCurrent cart:")
        show_cart(cart)

        subtotal, tax, total = calc_totals(cart)
        print("\n" + "-" * 56)
        print(f"SUBTOTAL: {fmt_money(subtotal)}")
        print(f"TAX 8% : {fmt_money(tax)}")
        print(f"TOTAL   : {fmt_money(total)}")
        print("-" * 56)
        print("\n1) Add item  2) Remove item  3) Checkout  4) Cancel sale")

        choice = input("Select option: ").strip()

        if choice == "1":
            product_id = ask_int("Enter product ID: ")
            qty = ask_int("Enter quantity: ")
            product = find_product(products, product_id)

            if product is None:
                pause("Item not found. Press ENTER...")
                continue
            if qty <= 0:
                pause("Quantity must be greater than zero. Press ENTER...")
                continue
            if qty > product["stock"]:
                pause("Not enough stock. Press ENTER...")
                continue

            existing = find_product(cart, product_id)
            if existing:
                if existing["qty"] + qty > product["stock"]:
                    pause("Exceeds stock limit. Press ENTER...")
                    continue
                existing["qty"] += qty
            else:
                cart.append(
                    {
                        "id": product["id"],
                        "name": product["name"],
                        "price": product["price"],
                        "qty": qty,
                    }
                )

        elif choice == "2":
            if not cart:
                pause("Cart is already empty. Press ENTER...")
                continue
            product_id = ask_int("Enter product ID to remove: ")
            qty = ask_int("Enter quantity to remove: ")
            item = find_product(cart, product_id)
            if item is None:
                pause("Item not in cart. Press ENTER...")
                continue
            if qty <= 0:
                pause("Quantity must be greater than zero. Press ENTER...")
                continue
            if qty >= item["qty"]:
                cart = [entry for entry in cart if entry["id"] != product_id]
            else:
                item["qty"] -= qty

        elif choice == "3":
            if not cart:
                pause("Cannot checkout an empty cart. Press ENTER...")
                continue

            payment = choose_payment_method(total)
            cash = payment["paid"]
            change = cash - total
            for item in cart:
                product = find_product(products, item["id"])
                product["stock"] -= item["qty"]

            transaction = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "items": cart,
                "subtotal": round(subtotal, 2),
                "tax": round(tax, 2),
                "total": round(total, 2),
                "payment_method": payment["method"],
                "payment_reference": payment["reference"],
                "payment_details": payment["details"],
                "cash": round(cash, 2),
                "change": round(change, 2),
            }
            sales.append(transaction)
            receipt_path = save_receipt(transaction)
            transaction["receipt_file"] = os.path.basename(receipt_path)
            save_json(PRODUCTS_FILE, products)
            save_json(SALES_FILE, sales)

            clear_screen()
            header("TRANSACTION APPROVED")
            print(f"Amount due : {fmt_money(total)}")
            print(f"Payment    : {payment['method']}")
            print(f"Reference  : {payment['reference']}")
            if payment["method"] == "Cash":
                print(f"Cash paid  : {fmt_money(cash)}")
            elif payment["method"] == "Card":
                print(f"Card       : {payment['details']['card_masked']}")
            elif payment["method"] == "UPI":
                print(f"UPI ID     : {payment['details']['upi_id']}")
            elif payment["method"] == "Wallet":
                print(f"Wallet     : {payment['details']['provider']}")
                print(f"Mobile     : {payment['details']['mobile']}")
            elif payment["method"] == "Net Banking":
                print(f"Bank       : {payment['details']['bank_name']}")
                print(f"Acct last4 : {payment['details']['account_last4']}")
            print(f"Change due : {fmt_money(change)}")
            print(f"Receipt    : {os.path.basename(receipt_path)}")
            print(f"Saved at   : {receipt_path}")
            print("\nBill preview:")
            for line in build_receipt_lines(transaction):
                print(line)
            pause()
            return

        elif choice == "4":
            return
        else:
            pause("Unknown option. Press ENTER...")


def manage_inventory(products):
    while True:
        clear_screen()
        header("INVENTORY CONTROL")
        show_products(products)

        print("\n1) Add new product")
        print("2) Restock product")
        print("3) Update price")
        print("4) Remove product")
        print("5) Back to main menu")

        choice = input("Select option: ").strip()

        if choice == "1":
            product_id = ask_int("New product ID: ")
            if find_product(products, product_id):
                pause("ID already exists. Press ENTER...")
                continue

            name = input("Product name: ").strip()
            price = ask_float("Unit price: ")
            stock = ask_int("Opening stock: ")

            if not name:
                pause("Name cannot be blank. Press ENTER...")
                continue
            if price <= 0 or stock < 0:
                pause("Invalid price or stock. Press ENTER...")
                continue

            products.append(
                {
                    "id": product_id,
                    "name": name,
                    "price": round(price, 2),
                    "stock": stock,
                }
            )
            products.sort(key=lambda p: p["id"])
            save_json(PRODUCTS_FILE, products)
            pause("Product added. Press ENTER...")

        elif choice == "2":
            product_id = ask_int("Product ID: ")
            qty = ask_int("Quantity to add: ")
            product = find_product(products, product_id)
            if product is None:
                pause("Item not found. Press ENTER...")
                continue
            if qty <= 0:
                pause("Quantity must be greater than zero. Press ENTER...")
                continue
            product["stock"] += qty
            save_json(PRODUCTS_FILE, products)
            pause("Stock updated. Press ENTER...")

        elif choice == "3":
            product_id = ask_int("Product ID: ")
            new_price = ask_float("New unit price: ")
            product = find_product(products, product_id)
            if product is None:
                pause("Item not found. Press ENTER...")
                continue
            if new_price <= 0:
                pause("Price must be greater than zero. Press ENTER...")
                continue
            product["price"] = round(new_price, 2)
            save_json(PRODUCTS_FILE, products)
            pause("Price updated. Press ENTER...")

        elif choice == "4":
            product_id = ask_int("Product ID to remove: ")
            product = find_product(products, product_id)
            if product is None:
                pause("Item not found. Press ENTER...")
                continue

            confirm = normalize_text(input(f"Delete {product['name']} from inventory? (Y/N): ")).lower()
            if confirm not in {"y", "yes"}:
                pause("Deletion cancelled. Press ENTER...")
                continue

            products[:] = [entry for entry in products if entry["id"] != product_id]
            save_json(PRODUCTS_FILE, products)
            pause("Product removed. Press ENTER...")

        elif choice == "5":
            return
        else:
            pause("Unknown option. Press ENTER...")


def sales_dashboard(sales):
    while True:
        clear_screen()
        header("SALES DASHBOARD")

        if not sales:
            print("No sales recorded yet.")
        else:
            total_revenue = sum(record["total"] for record in sales)
            total_tax = sum(record["tax"] for record in sales)
            total_transactions = len(sales)

            print(f"Transactions : {total_transactions}")
            print(f"Gross sales  : {fmt_money(total_revenue)}")
            print(f"Tax collected: {fmt_money(total_tax)}")
            print("\nRecent transactions:")
            print("TIME                 TOTAL      CASH       CHANGE")
            print("-" * 56)

            for record in sales[-10:]:
                print(
                    f"{record['timestamp']:<19} {fmt_money(record['total']):>8}   "
                    f"{fmt_money(record['cash']):>8}   {fmt_money(record['change']):>8}"
                )

        print("\n1) Back to main menu")
        print("2) Clear sales history")
        choice = input("Select option: ").strip()

        if choice == "1":
            return

        if choice == "2":
            if not sales:
                pause("No sales to clear. Press ENTER...")
                continue

            confirm = normalize_text(input("Clear ALL sales history? This cannot be undone. (Y/N): ")).lower()
            if confirm not in {"y", "yes"}:
                pause("Clear action cancelled. Press ENTER...")
                continue

            sales.clear()
            save_json(SALES_FILE, sales)
            pause("Sales history cleared. Press ENTER...")
            continue

        pause("Unknown option. Press ENTER...")


def main():
    enable_ansi_on_windows()

    products = load_json(PRODUCTS_FILE, default_products())
    sales = load_json(SALES_FILE, [])

    if not os.path.exists(PRODUCTS_FILE):
        save_json(PRODUCTS_FILE, products)
    if not os.path.exists(SALES_FILE):
        save_json(SALES_FILE, sales)

    while True:
        clear_screen()
        header("MAIN MENU")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"System date/time: {now}")
        print("\n1) New sale")
        print("2) Inventory control")
        print("3) Sales dashboard")
        print("4) Exit terminal")

        choice = input("Select option: ").strip()

        if choice == "1":
            run_sale(products, sales)
        elif choice == "2":
            manage_inventory(products)
        elif choice == "3":
            sales_dashboard(sales)
        elif choice == "4":
            clear_screen()
            print("Session closed.")
            break
        else:
            pause("Unknown option. Press ENTER...")


if __name__ == "__main__":
    main()
