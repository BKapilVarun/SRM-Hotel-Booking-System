# AURORA GRAND - Luxury Hotel & Food Booking Engine

An all-in-one unified web application for **Luxury Hotel Room Bookings** and **Gourmet Food / Dining Orders**, with **Customer Reviews**, **Email & SMS Receipt Dispatch**, and **Owner Authentication**.

---

## 🌟 Key Features

### 1. Unified 3-in-1 Customer Experience
- 🏨 **Suites & Villas**: Browse suites (Presidential Penthouse, Oceanfront Villas, Royal Suites) with live night calculation, guest selection, and room reservation.
- 🍽️ **Gourmet Dining & Room Service**: Michelin-inspired dishes with custom service preferences (In-Room Dining or Restaurant Table reservation), serving time selection, and an interactive dining cart tray.
- ✨ **The Imperial Stay & Dine Pass (Unified 2-in-1 Flow)**: Choose your room suite and curate your welcome gourmet dining course together in a single screen, checking out with one click.
- ⭐ **Customer Reviews & Testimonials**: Customers can read genuine reviews from verified guests and share their own reviews through an interactive modal.

### 2. Dual Excel Database Storage
- Room reservations are automatically appended to:  
  `excel_data/hotel_bookings.xlsx` (Sheet: *Room Bookings*)
- Food & dining orders are automatically appended to:  
  `excel_data/food_orders.xlsx` (Sheet: *Culinary Orders*)
- Customer reviews are appended to:  
  `excel_data/customer_reviews.xlsx` (Sheet: *Guest Reviews*)
- If booked via the unified pass, both entries cross-reference each other's ID (`Linked Food Order ID` / `Linked Room Booking ID`).

### 3. Strict Viewer Privacy & Owner Authentication
- **Zero Public Visibility**: Public viewers and visitors **cannot see booking lists or guest data**.
- **Owner Management Portal**: Accessible at [`http://127.0.0.1:5000/owner`](http://127.0.0.1:5000/owner).
  - Protected by authentication.
  - **Default Credentials**:
    - **Username**: `admin`
    - **Password**: `aurora2026`
  - Features real-time KPI metrics (Suites Reserved, Room Revenue, Food Orders, Dining Revenue, Combined Revenue), searchable data tables from the Excel files, and download buttons.

### 4. Automatic Receipt Delivery (Email & SMS)
Whenever a guest reserves a room or orders food:
- 📧 **Official HTML Receipt** is dispatched to the customer's email address.
- 📱 **Instant SMS Confirmation** is sent to the customer's mobile phone number.
- Dispatched logs and formatted receipts are recorded in `outbox/dispatches.log`.
- Real SMTP (Gmail, Outlook, custom mail servers) can be configured via environment variables (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`).

---

## 🚀 How to Run the Project

### Option 1: 1-Click Launch (Windows)
Double-click:
```bash
run.bat
```
This automatically starts the server and opens `http://127.0.0.1:5000` in your web browser.

### Option 2: Command Line
1. Ensure dependencies are installed:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Start the web application:
   ```bash
   python app.py
   ```
3. Open your browser:
   - **Customer Portal**: `http://127.0.0.1:5000`
   - **Owner Portal**: `http://127.0.0.1:5000/owner`

---

## 🔐 Owner Management Access

Navigate to:
```
http://127.0.0.1:5000/owner
```
- **Username**: `admin`
- **Password**: `aurora2026`

Once authenticated, the owner can view:
1. All hotel room bookings (guest names, phone, email, dates, total fees).
2. All food orders (items, quantities, room/table numbers, serving times).
3. Direct download links for `hotel_bookings.xlsx` and `food_orders.xlsx`.

---

## 📊 Viewing the Excel Databases Directly

To view the stored records on Windows:
- Double-click **`open_excel_sheets.bat`** to instantly open both spreadsheets in Microsoft Excel.
- Or browse to the `excel_data/` folder:
  - `excel_data/hotel_bookings.xlsx`
  - `excel_data/food_orders.xlsx`
  - `excel_data/customer_reviews.xlsx`
