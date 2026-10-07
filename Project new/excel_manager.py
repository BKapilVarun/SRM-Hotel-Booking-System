import os
import threading
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import supabase_manager

EXCEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "excel_data")
ROOMS_FILE = os.path.join(EXCEL_DIR, "hotel_bookings.xlsx")
FOOD_FILE = os.path.join(EXCEL_DIR, "food_orders.xlsx")
REVIEWS_FILE = os.path.join(EXCEL_DIR, "customer_reviews.xlsx")

file_lock = threading.Lock()

# Luxury Excel Styling
NAVY_HEADER_FILL = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
GOLD_HEADER_FILL = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")
EMERALD_HEADER_FILL = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
REGULAR_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center")
LEFT_ALIGN = Alignment(horizontal="left", vertical="center")
RIGHT_ALIGN = Alignment(horizontal="right", vertical="center")

THIN_BORDER = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)

ROOM_COLUMNS = [
    "Booking ID",
    "Timestamp",
    "Guest Name",
    "Email Address",
    "Phone Number",
    "Room / Suite Type",
    "Check-In Date",
    "Check-Out Date",
    "Nights",
    "Guests",
    "Rate/Night ($)",
    "Room Total ($)",
    "Payment Mode",
    "Special Requests",
    "Booking Status",
    "Linked Food Order ID"
]

FOOD_COLUMNS = [
    "Order ID",
    "Timestamp",
    "Customer Name",
    "Phone Number",
    "Email Address",
    "Service Type",
    "Room # / Table #",
    "Preferred Time",
    "Itemized Dishes",
    "Total Items",
    "Subtotal ($)",
    "Tax & Service ($)",
    "Grand Total ($)",
    "Payment Mode",
    "Dietary / Chef Notes",
    "Order Status",
    "Linked Room Booking ID"
]

REVIEW_COLUMNS = [
    "Review ID",
    "Timestamp",
    "Guest Name",
    "Rating (1-5)",
    "Experience Type",
    "Review Title",
    "Review Comments",
    "Status"
]

INITIAL_REVIEWS = [
    {
        "name": "Lady Eleanor Vance",
        "rating": 5,
        "type": "Suite Stay & Dining",
        "title": "An Unrivaled Sanctuary of Opulence",
        "comment": "The Presidential Sky Penthouse exceeded all expectations. Watching the sunset while savoring the A5 Wagyu prepared by the private chef was truly magical. Dedicated butler service was immaculate."
    },
    {
        "name": "Maximilian Sterling",
        "rating": 5,
        "type": "Emerald Pool Villa",
        "title": "Pure Tranquility and Flawless Privacy",
        "comment": "The private infinity plunge pool and direct beach walkway made our anniversary unforgettable. The royal breakfast delivered right to our sun deck was Michelin-star caliber."
    },
    {
        "name": "Dr. Sophia Laurent",
        "rating": 5,
        "type": "Haute Cuisine Dining",
        "title": "Gastronomy at its Absolute Finest",
        "comment": "The Brittany Blue Lobster Risotto paired with vintage Dom Pérignon was one of the finest meals we have ever experienced worldwide. The ambiance is second to none."
    }
]

def init_excel_files():
    """Ensure excel_data directory and sheets exist with styled headers."""
    os.makedirs(EXCEL_DIR, exist_ok=True)
    
    with file_lock:
        # 1. Initialize Hotel Bookings Excel
        if not os.path.exists(ROOMS_FILE):
            wb = Workbook()
            ws = wb.active
            ws.title = "Room Bookings"
            ws.views.sheetView[0].showGridLines = True
            ws.append(ROOM_COLUMNS)
            for col_num in range(1, len(ROOM_COLUMNS) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = NAVY_HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = CENTER_ALIGN
                cell.border = THIN_BORDER
            _auto_fit_columns(ws)
            wb.save(ROOMS_FILE)

        # 2. Initialize Food Orders Excel
        if not os.path.exists(FOOD_FILE):
            wb = Workbook()
            ws = wb.active
            ws.title = "Culinary Orders"
            ws.views.sheetView[0].showGridLines = True
            ws.append(FOOD_COLUMNS)
            for col_num in range(1, len(FOOD_COLUMNS) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = GOLD_HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = CENTER_ALIGN
                cell.border = THIN_BORDER
            _auto_fit_columns(ws)
            wb.save(FOOD_FILE)

        # 3. Initialize Customer Reviews Excel
        if not os.path.exists(REVIEWS_FILE):
            wb = Workbook()
            ws = wb.active
            ws.title = "Guest Reviews"
            ws.views.sheetView[0].showGridLines = True
            ws.append(REVIEW_COLUMNS)
            for col_num in range(1, len(REVIEW_COLUMNS) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = EMERALD_HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = CENTER_ALIGN
                cell.border = THIN_BORDER

            # Seed initial reviews
            for rev in INITIAL_REVIEWS:
                rev_id = f"REV-{os.urandom(2).hex().upper()}"
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                ws.append([rev_id, ts, rev["name"], rev["rating"], rev["type"], rev["title"], rev["comment"], "Approved"])

            _auto_fit_columns(ws)
            wb.save(REVIEWS_FILE)

def _auto_fit_columns(ws):
    """Adjusts column widths based on cell contents."""
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                if cell.value:
                    val_str = str(cell.value)
                    if len(val_str) > max_length:
                        max_length = len(val_str)
            except:
                pass
        ws.column_dimensions[col_letter].width = max(max_length + 4, 14)

def save_room_booking(data):
    """Appends a new hotel room booking into hotel_bookings.xlsx."""
    init_excel_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    booking_id = f"AUR-RM-{datetime.now().strftime('%m%d%H%M')}-{os.urandom(2).hex().upper()}"
    
    row_values = [
        booking_id,
        timestamp,
        data.get("guest_name", "N/A"),
        data.get("email", "N/A"),
        data.get("phone", "N/A"),
        data.get("room_type", "N/A"),
        data.get("check_in", "N/A"),
        data.get("check_out", "N/A"),
        int(data.get("nights", 1)),
        int(data.get("guests", 1)),
        float(data.get("price_per_night", 0)),
        float(data.get("total_amount", 0)),
        data.get("payment_method", "Pay upon Arrival"),
        data.get("special_requests", "None"),
        "Confirmed",
        data.get("linked_food_id", "N/A")
    ]

    with file_lock:
        wb = load_workbook(ROOMS_FILE)
        ws = wb.active
        ws.append(row_values)
        
        new_row = ws.max_row
        zebra_fill = PatternFill(start_color="F8FAFC" if new_row % 2 == 0 else "FFFFFF",
                                 end_color="F8FAFC" if new_row % 2 == 0 else "FFFFFF",
                                 fill_type="solid")
        
        for col_idx in range(1, len(row_values) + 1):
            c = ws.cell(row=new_row, column=col_idx)
            c.font = REGULAR_FONT
            c.fill = zebra_fill
            c.border = THIN_BORDER
            if col_idx in [1, 2, 7, 8, 9, 10, 15, 16]:
                c.alignment = CENTER_ALIGN
            elif col_idx in [11, 12]:
                c.alignment = RIGHT_ALIGN
            else:
                c.alignment = LEFT_ALIGN
                
        _auto_fit_columns(ws)
        wb.save(ROOMS_FILE)

    # Online Cloud Sync to Supabase
    try:
        supabase_manager.save_room_booking(data, booking_id, timestamp)
    except Exception as e:
        print(f"[Supabase Sync Error] {e}")
        
    return {
        "booking_id": booking_id,
        "timestamp": timestamp,
        "guest_name": data.get("guest_name"),
        "room_type": data.get("room_type"),
        "check_in": data.get("check_in"),
        "check_out": data.get("check_out"),
        "nights": data.get("nights"),
        "total_amount": data.get("total_amount")
    }

def save_food_order(data):
    """Appends a new culinary/food order into food_orders.xlsx."""
    init_excel_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = f"AUR-FD-{datetime.now().strftime('%m%d%H%M')}-{os.urandom(2).hex().upper()}"
    
    items = data.get("items", [])
    if isinstance(items, list):
        item_strings = [f"{item.get('name', 'Item')} (x{item.get('qty', 1)} - ${item.get('price', 0) * item.get('qty', 1):.2f})" for item in items]
        itemized_summary = "; ".join(item_strings)
        total_items_count = sum(item.get('qty', 1) for item in items)
    else:
        itemized_summary = str(items)
        total_items_count = int(data.get("total_items_count", 1))

    row_values = [
        order_id,
        timestamp,
        data.get("customer_name", "N/A"),
        data.get("phone", "N/A"),
        data.get("email", "N/A"),
        data.get("service_type", "Room Service"),
        data.get("destination_number", "Room Suite"),
        data.get("preferred_time", "Immediate"),
        itemized_summary,
        total_items_count,
        float(data.get("subtotal", 0)),
        float(data.get("tax_service", 0)),
        float(data.get("grand_total", 0)),
        data.get("payment_method", "Charge to Room / Upon Delivery"),
        data.get("dietary_notes", "Standard"),
        "Confirmed & Preparing",
        data.get("linked_room_id", "N/A")
    ]

    with file_lock:
        wb = load_workbook(FOOD_FILE)
        ws = wb.active
        ws.append(row_values)
        
        new_row = ws.max_row
        zebra_fill = PatternFill(start_color="FFFBEB" if new_row % 2 == 0 else "FFFFFF",
                                 end_color="FFFBEB" if new_row % 2 == 0 else "FFFFFF",
                                 fill_type="solid")
        
        for col_idx in range(1, len(row_values) + 1):
            c = ws.cell(row=new_row, column=col_idx)
            c.font = REGULAR_FONT
            c.fill = zebra_fill
            c.border = THIN_BORDER
            if col_idx in [1, 2, 6, 7, 8, 10, 16, 17]:
                c.alignment = CENTER_ALIGN
            elif col_idx in [11, 12, 13]:
                c.alignment = RIGHT_ALIGN
            else:
                c.alignment = LEFT_ALIGN
                
        _auto_fit_columns(ws)
        wb.save(FOOD_FILE)

    # Online Cloud Sync to Supabase
    try:
        supabase_manager.save_food_order(data, order_id, timestamp, itemized_summary, total_items_count)
    except Exception as e:
        print(f"[Supabase Sync Error] {e}")
        
    return {
        "order_id": order_id,
        "timestamp": timestamp,
        "customer_name": data.get("customer_name"),
        "service_type": data.get("service_type"),
        "items_summary": itemized_summary,
        "grand_total": data.get("grand_total")
    }

def save_unified_experience(room_data, food_data):
    """Saves room and food order atomically into respective Excel files."""
    room_id = f"AUR-RM-{datetime.now().strftime('%m%d%H%M')}-{os.urandom(2).hex().upper()}"
    food_id = f"AUR-FD-{datetime.now().strftime('%m%d%H%M')}-{os.urandom(2).hex().upper()}"
    
    room_data["linked_food_id"] = food_id
    food_data["linked_room_id"] = room_id
    food_data["destination_number"] = f"Assigned to {room_data.get('room_type', 'Suite')}"
    
    init_excel_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    room_row = [
        room_id,
        timestamp,
        room_data.get("guest_name", "N/A"),
        room_data.get("email", "N/A"),
        room_data.get("phone", "N/A"),
        room_data.get("room_type", "N/A"),
        room_data.get("check_in", "N/A"),
        room_data.get("check_out", "N/A"),
        int(room_data.get("nights", 1)),
        int(room_data.get("guests", 1)),
        float(room_data.get("price_per_night", 0)),
        float(room_data.get("total_amount", 0)),
        room_data.get("payment_method", "Pay upon Arrival"),
        room_data.get("special_requests", "None"),
        "Confirmed",
        food_id
    ]

    items = food_data.get("items", [])
    if isinstance(items, list):
        item_strings = [f"{item.get('name', 'Item')} (x{item.get('qty', 1)} - ${item.get('price', 0) * item.get('qty', 1):.2f})" for item in items]
        itemized_summary = "; ".join(item_strings)
        total_items_count = sum(item.get('qty', 1) for item in items)
    else:
        itemized_summary = str(items)
        total_items_count = int(food_data.get("total_items_count", 1))

    food_row = [
        food_id,
        timestamp,
        room_data.get("guest_name", "N/A"),
        room_data.get("phone", "N/A"),
        room_data.get("email", "N/A"),
        "Room Service Delivery",
        f"{room_data.get('room_type', 'Suite')}",
        food_data.get("preferred_time", "Evening Room Service"),
        itemized_summary,
        total_items_count,
        float(food_data.get("subtotal", 0)),
        float(food_data.get("tax_service", 0)),
        float(food_data.get("grand_total", 0)),
        "Room Charge Portfolio",
        food_data.get("dietary_notes", "Standard"),
        "Confirmed & Scheduled",
        room_id
    ]

    with file_lock:
        wb_r = load_workbook(ROOMS_FILE)
        ws_r = wb_r.active
        ws_r.append(room_row)
        _auto_fit_columns(ws_r)
        wb_r.save(ROOMS_FILE)

        wb_f = load_workbook(FOOD_FILE)
        ws_f = wb_f.active
        ws_f.append(food_row)
        _auto_fit_columns(ws_f)
        wb_f.save(FOOD_FILE)

    # Online Cloud Sync to Supabase
    try:
        supabase_manager.save_room_booking(room_data, room_id, timestamp)
        supabase_manager.save_food_order(food_data, food_id, timestamp, itemized_summary, total_items_count)
    except Exception as e:
        print(f"[Supabase Sync Error] {e}")

    return {
        "room_booking_id": room_id,
        "food_order_id": food_id,
        "guest_name": room_data.get("guest_name"),
        "room_type": room_data.get("room_type"),
        "check_in": room_data.get("check_in"),
        "check_out": room_data.get("check_out"),
        "food_items_count": total_items_count,
        "room_total": room_data.get("total_amount"),
        "food_total": food_data.get("grand_total"),
        "combined_total": float(room_data.get("total_amount", 0)) + float(food_data.get("grand_total", 0))
    }

# ==============================================================
# REVIEWS MANAGEMENT
# ==============================================================
def get_customer_reviews():
    """Returns list of approved customer reviews from Excel."""
    init_excel_files()
    reviews = []
    with file_lock:
        if os.path.exists(REVIEWS_FILE):
            wb = load_workbook(REVIEWS_FILE, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                rev_id = ws.cell(r, 1).value
                if not rev_id:
                    continue
                reviews.append({
                    "id": rev_id,
                    "timestamp": ws.cell(r, 2).value,
                    "guest_name": ws.cell(r, 3).value,
                    "rating": int(ws.cell(r, 4).value or 5),
                    "type": ws.cell(r, 5).value,
                    "title": ws.cell(r, 6).value,
                    "comment": ws.cell(r, 7).value
                })
    return reviews

def add_customer_review(data):
    """Appends a new customer review to customer_reviews.xlsx."""
    init_excel_files()
    rev_id = f"REV-{datetime.now().strftime('%m%d')}-{os.urandom(2).hex().upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    row = [
        rev_id,
        timestamp,
        data.get("guest_name", "Anonymous Guest"),
        int(data.get("rating", 5)),
        data.get("type", "Suite Stay & Dining"),
        data.get("title", "Exceptional Hospitality"),
        data.get("comment", ""),
        "Approved"
    ]

    with file_lock:
        wb = load_workbook(REVIEWS_FILE)
        ws = wb.active
        ws.append(row)
        _auto_fit_columns(ws)
        wb.save(REVIEWS_FILE)

    # Online Cloud Sync to Supabase
    try:
        supabase_manager.save_customer_review(data, rev_id, timestamp)
    except Exception as e:
        print(f"[Supabase Sync Error] {e}")

    return {
        "id": rev_id,
        "timestamp": timestamp,
        "guest_name": data.get("guest_name"),
        "rating": int(data.get("rating", 5)),
        "type": data.get("type"),
        "title": data.get("title"),
        "comment": data.get("comment")
    }

# ==============================================================
# OWNER AUTHENTICATED DASHBOARD DATA
# ==============================================================
def get_owner_dashboard_data():
    """
    STRICTLY FOR AUTHENTICATED OWNER:
    Reads both hotel_bookings.xlsx and food_orders.xlsx
    Returns aggregated metrics and full rows for admin view.
    """
    init_excel_files()
    rooms_data = []
    food_data = []
    total_room_revenue = 0.0
    total_food_revenue = 0.0

    with file_lock:
        # 1. Read Room Bookings
        if os.path.exists(ROOMS_FILE):
            wb_r = load_workbook(ROOMS_FILE, data_only=True)
            ws_r = wb_r.active
            for r in range(2, ws_r.max_row + 1):
                b_id = ws_r.cell(r, 1).value
                if not b_id:
                    continue
                tot = float(ws_r.cell(r, 12).value or 0)
                total_room_revenue += tot
                rooms_data.append({
                    "booking_id": b_id,
                    "timestamp": ws_r.cell(r, 2).value,
                    "guest_name": ws_r.cell(r, 3).value,
                    "email": ws_r.cell(r, 4).value,
                    "phone": ws_r.cell(r, 5).value,
                    "room_type": ws_r.cell(r, 6).value,
                    "check_in": ws_r.cell(r, 7).value,
                    "check_out": ws_r.cell(r, 8).value,
                    "nights": ws_r.cell(r, 9).value,
                    "guests": ws_r.cell(r, 10).value,
                    "rate": ws_r.cell(r, 11).value,
                    "total": tot,
                    "payment_mode": ws_r.cell(r, 13).value,
                    "special_requests": ws_r.cell(r, 14).value,
                    "status": ws_r.cell(r, 15).value,
                    "linked_food_id": ws_r.cell(r, 16).value
                })

        # 2. Read Food Orders
        if os.path.exists(FOOD_FILE):
            wb_f = load_workbook(FOOD_FILE, data_only=True)
            ws_f = wb_f.active
            for r in range(2, ws_f.max_row + 1):
                o_id = ws_f.cell(r, 1).value
                if not o_id:
                    continue
                tot = float(ws_f.cell(r, 13).value or 0)
                total_food_revenue += tot
                food_data.append({
                    "order_id": o_id,
                    "timestamp": ws_f.cell(r, 2).value,
                    "customer_name": ws_f.cell(r, 3).value,
                    "phone": ws_f.cell(r, 4).value,
                    "email": ws_f.cell(r, 5).value,
                    "service_type": ws_f.cell(r, 6).value,
                    "destination": ws_f.cell(r, 7).value,
                    "preferred_time": ws_f.cell(r, 8).value,
                    "dishes": ws_f.cell(r, 9).value,
                    "total_items": ws_f.cell(r, 10).value,
                    "subtotal": ws_f.cell(r, 11).value,
                    "tax_service": ws_f.cell(r, 12).value,
                    "grand_total": tot,
                    "payment_mode": ws_f.cell(r, 14).value,
                    "dietary": ws_f.cell(r, 15).value,
                    "status": ws_f.cell(r, 16).value,
                    "linked_room_id": ws_f.cell(r, 17).value
                })

    return {
        "stats": {
            "total_room_bookings": len(rooms_data),
            "total_food_orders": len(food_data),
            "total_room_revenue": total_room_revenue,
            "total_food_revenue": total_food_revenue,
            "total_combined_revenue": total_room_revenue + total_food_revenue
        },
        "room_bookings": list(reversed(rooms_data)),
        "food_orders": list(reversed(food_data))
    }

def find_booking_by_id(ref_id):
    """Searches hotel_bookings.xlsx and food_orders.xlsx for the specified reference code."""
    init_excel_files()
    ref_id = ref_id.strip().upper()
    with file_lock:
        # Check Hotel Bookings
        if os.path.exists(ROOMS_FILE):
            wb = load_workbook(ROOMS_FILE, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                b_id = str(ws.cell(r, 1).value or '').strip().upper()
                if b_id == ref_id:
                    status = ws.cell(r, 15).value or 'Confirmed'
                    return {
                        "type": "room",
                        "id": b_id,
                        "timestamp": str(ws.cell(r, 2).value),
                        "guest_name": ws.cell(r, 3).value,
                        "email": ws.cell(r, 4).value,
                        "phone": ws.cell(r, 5).value,
                        "title": ws.cell(r, 6).value,
                        "check_in": str(ws.cell(r, 7).value),
                        "check_out": str(ws.cell(r, 8).value),
                        "nights": ws.cell(r, 9).value,
                        "guests": ws.cell(r, 10).value,
                        "rate": float(ws.cell(r, 11).value or 0),
                        "total": float(ws.cell(r, 12).value or 0),
                        "status": status,
                        "linked_id": ws.cell(r, 16).value
                    }

        # Check Food Orders
        if os.path.exists(FOOD_FILE):
            wb = load_workbook(FOOD_FILE, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                o_id = str(ws.cell(r, 1).value or '').strip().upper()
                if o_id == ref_id:
                    status = ws.cell(r, 16).value or 'Confirmed & Preparing'
                    return {
                        "type": "food",
                        "id": o_id,
                        "timestamp": str(ws.cell(r, 2).value),
                        "customer_name": ws.cell(r, 3).value,
                        "phone": ws.cell(r, 4).value,
                        "email": ws.cell(r, 5).value,
                        "service_type": ws.cell(r, 6).value,
                        "destination": ws.cell(r, 7).value,
                        "time": ws.cell(r, 8).value,
                        "title": ws.cell(r, 9).value,
                        "total_items": ws.cell(r, 10).value,
                        "total": float(ws.cell(r, 13).value or 0),
                        "status": status,
                        "linked_id": ws.cell(r, 17).value
                    }
    # 3. Fallback to Supabase Cloud Database if not found in local Excel
    if supabase_manager.is_configured():
        try:
            cloud_res = supabase_manager.find_booking_by_id(ref_id)
            if cloud_res:
                return cloud_res
        except Exception as e:
            print(f"[Supabase Find Error] {e}")

    return None

def update_booking_status(ref_id, new_status):
    """Updates the status column for a room booking or food order in Excel and Supabase."""
    init_excel_files()
    ref_id = ref_id.strip().upper()
    excel_updated = False

    with file_lock:
        if os.path.exists(ROOMS_FILE):
            wb = load_workbook(ROOMS_FILE)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                b_id = str(ws.cell(r, 1).value or '').strip().upper()
                if b_id == ref_id:
                    ws.cell(r, 15).value = new_status
                    wb.save(ROOMS_FILE)
                    excel_updated = True
                    break
        if not excel_updated and os.path.exists(FOOD_FILE):
            wb = load_workbook(FOOD_FILE)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                o_id = str(ws.cell(r, 1).value or '').strip().upper()
                if o_id == ref_id:
                    ws.cell(r, 16).value = new_status
                    wb.save(FOOD_FILE)
                    excel_updated = True
                    break

    # Also update Supabase online
    try:
        supabase_manager.update_status(ref_id, new_status)
    except Exception as e:
        print(f"[Supabase Status Update Error] {e}")

    return excel_updated

def sync_all_to_supabase():
    """Reads all rows from all local Excel files and uploads them into Supabase cloud tables."""
    if not supabase_manager.is_configured():
        return False, "Supabase credentials not configured. Please enter your Supabase URL & Key in Owner Portal."

    init_excel_files()
    synced = {"rooms": 0, "food": 0, "reviews": 0}

    with file_lock:
        # 1. Sync Room Bookings
        if os.path.exists(ROOMS_FILE):
            wb = load_workbook(ROOMS_FILE, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                b_id = ws.cell(r, 1).value
                if not b_id:
                    continue
                room_d = {
                    "guest_name": ws.cell(r, 3).value or "N/A",
                    "email": ws.cell(r, 4).value or "N/A",
                    "phone": ws.cell(r, 5).value or "N/A",
                    "room_type": ws.cell(r, 6).value or "Luxury Suite",
                    "check_in": str(ws.cell(r, 7).value or ""),
                    "check_out": str(ws.cell(r, 8).value or ""),
                    "nights": int(ws.cell(r, 9).value or 1),
                    "guests": int(ws.cell(r, 10).value or 1),
                    "price_per_night": float(ws.cell(r, 11).value or 0),
                    "total_amount": float(ws.cell(r, 12).value or 0),
                    "payment_method": ws.cell(r, 13).value or "Pay upon Arrival",
                    "special_requests": ws.cell(r, 14).value or "None",
                    "linked_food_id": ws.cell(r, 16).value or "N/A"
                }
                ok, _ = supabase_manager.save_room_booking(room_d, str(b_id), str(ws.cell(r, 2).value or ""))
                if ok:
                    synced["rooms"] += 1

        # 2. Sync Food Orders
        if os.path.exists(FOOD_FILE):
            wb = load_workbook(FOOD_FILE, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                o_id = ws.cell(r, 1).value
                if not o_id:
                    continue
                food_d = {
                    "customer_name": ws.cell(r, 3).value or "Valued Guest",
                    "phone": ws.cell(r, 4).value or "N/A",
                    "email": ws.cell(r, 5).value or "N/A",
                    "service_type": ws.cell(r, 6).value or "Room Service",
                    "destination_number": ws.cell(r, 7).value or "Room Suite",
                    "preferred_time": ws.cell(r, 8).value or "Immediate",
                    "subtotal": float(ws.cell(r, 11).value or 0),
                    "tax_service": float(ws.cell(r, 12).value or 0),
                    "grand_total": float(ws.cell(r, 13).value or 0),
                    "payment_method": ws.cell(r, 14).value or "Charge to Room",
                    "dietary_notes": ws.cell(r, 15).value or "Standard",
                    "linked_room_id": ws.cell(r, 17).value or "N/A"
                }
                ok, _ = supabase_manager.save_food_order(
                    food_d, str(o_id), str(ws.cell(r, 2).value or ""), 
                    str(ws.cell(r, 9).value or ""), int(ws.cell(r, 10).value or 1)
                )
                if ok:
                    synced["food"] += 1

        # 3. Sync Customer Reviews
        if os.path.exists(REVIEWS_FILE):
            wb = load_workbook(REVIEWS_FILE, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                rev_id = ws.cell(r, 1).value
                if not rev_id:
                    continue
                rev_d = {
                    "guest_name": ws.cell(r, 3).value or "Guest",
                    "rating": int(ws.cell(r, 4).value or 5),
                    "type": ws.cell(r, 5).value or "Suite Stay",
                    "title": ws.cell(r, 6).value or "Review",
                    "comment": ws.cell(r, 7).value or ""
                }
                ok, _ = supabase_manager.save_customer_review(rev_d, str(rev_id), str(ws.cell(r, 2).value or ""))
                if ok:
                    synced["reviews"] += 1

    return True, f"Migration Complete: Synced {synced['rooms']} room reservations, {synced['food']} food orders, and {synced['reviews']} reviews into online Supabase database!"


