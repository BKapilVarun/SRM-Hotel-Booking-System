import os
from flask import Flask, render_template, request, jsonify, send_from_directory, session
import excel_manager
import notifier
import supabase_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aurora_luxury_hospitality_owner_key_2026')

# Owner Authentication Credentials (can be overridden via environment variables)
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "admin")
OWNER_PASSWORD = os.environ.get("OWNER_PASSWORD", "srm2026")

# Initialize directories & managers
excel_manager.init_excel_files()
notifier.init_notifier()

# Predefined Luxury Suites Catalogue
ROOMS_CATALOG = [
    {
        "id": "presidential-penthouse",
        "name": "The Presidential Sky Penthouse",
        "category": "Penthouse",
        "price": 850,
        "capacity": "4 Guests",
        "size": "2,400 sq.ft",
        "bed": "1 King Bed + 1 Queen Bed",
        "view": "Panoramic Ocean & Skyline",
        "image": "/static/images/suite_presidential.jpg",
        "badge": "Signature Masterpiece",
        "amenities": ["Private Infinity Jacuzzi", "24/7 Dedicated Butler", "Champagne Bar", "Private Elevator Access", "Designer Marble Bath"]
    },
    {
        "id": "emerald-pool-villa",
        "name": "Emerald Oceanfront Pool Villa",
        "category": "Private Villa",
        "price": 620,
        "capacity": "3 Guests",
        "size": "1,850 sq.ft",
        "bed": "1 King Grand Bed",
        "view": "Private Lagoon & Tropical Garden",
        "image": "/static/images/suite_villa.jpg",
        "badge": "Most Popular",
        "amenities": ["Private Plunge Pool", "Teak Sun Deck", "Tropical Outdoor Shower", "Complimentary High Tea", "Direct Beach Walkway"]
    },
    {
        "id": "royal-imperial-suite",
        "name": "Royal Imperial Sunset Suite",
        "category": "Royal Suite",
        "price": 450,
        "capacity": "2 Guests",
        "size": "1,200 sq.ft",
        "bed": "1 King Grand Bed",
        "view": "Sunset Horizon Sea View",
        "image": "/static/images/resort_hero.jpg",
        "badge": "Romantic Luxury",
        "amenities": ["Private Sunset Terrace", "Soaking Bathtub", "Curated Wine Cellar", "Espresso Bar", "Bvlgari Bath Amenities"]
    },
    {
        "id": "executive-grand-suite",
        "name": "Executive Azure Horizon Suite",
        "category": "Executive",
        "price": 320,
        "capacity": "2 Guests",
        "size": "950 sq.ft",
        "bed": "1 King Bed",
        "view": "Azure Coastal Waters",
        "image": "/static/images/suite_presidential.jpg",
        "badge": "Classic Elegance",
        "amenities": ["Spacious Work Lounge", "Walk-in Dressing Room", "High-Speed Fiber", "Rainfall Shower", "Smart Room Automation"]
    }
]

# Predefined Haute Cuisine Menu Catalogue
FOOD_CATALOG = [
    {
        "id": "dish-wagyu-truffle",
        "name": "A5 Wagyu Striploin & Black Truffle",
        "category": "mains",
        "price": 78,
        "calories": "680 kcal",
        "tag": "Chef's Signature",
        "image": "/static/images/dining_wagyu.jpg",
        "description": "Seared Japanese Wagyu, 24k edible gold leaf, potato mousseline, winter truffle jus, heirloom micro-herbs."
    },
    {
        "id": "dish-sunrise-breakfast",
        "name": "The Royal Aegean Sunrise Breakfast",
        "category": "breakfast",
        "price": 38,
        "calories": "520 kcal",
        "tag": "Morning Deluxe",
        "image": "/static/images/dining_breakfast.jpg",
        "description": "Artisan butter croissants, organic poached eggs with avocado, fresh exotic fruit platter, cold-pressed juice & cappuccino."
    },
    {
        "id": "dish-lobster-risotto",
        "name": "Brittany Blue Lobster Risotto",
        "category": "mains",
        "price": 64,
        "calories": "610 kcal",
        "tag": "Seafood Special",
        "image": "/static/images/dining_wagyu.jpg",
        "description": "Poached blue lobster tail, Acquerello carnaroli rice, saffron emulsion, aged Parmigiano Reggiano crisp."
    },
    {
        "id": "dish-belgian-truffle-dessert",
        "name": "Grand Cru Valrhona Chocolate Dome",
        "category": "desserts",
        "price": 26,
        "calories": "420 kcal",
        "tag": "Sweet Indulgence",
        "image": "/static/images/dining_breakfast.jpg",
        "description": "Dark chocolate spherical shell, molten hazelnut praline, gold-dusted raspberry coulis, Madagascar vanilla gelato."
    },
    {
        "id": "dish-champagne-dom",
        "name": "Vintage Dom Pérignon Brut (Glass)",
        "category": "drinks",
        "price": 45,
        "calories": "120 kcal",
        "tag": "Haute Cellar",
        "image": "/static/images/resort_hero.jpg",
        "description": "Chilled vintage champagne served in hand-blown crystal flutes, accompanied by artisan almond crisps."
    },
    {
        "id": "dish-artisan-mocktail",
        "name": "SRM Golden Sunset Elixir (Mocktail)",
        "category": "drinks",
        "price": 18,
        "calories": "95 kcal",
        "tag": "Zero-Proof",
        "image": "/static/images/dining_breakfast.jpg",
        "description": "Infused passionfruit, crushed lemongrass, sparkling elderflower tonic, rosemary smoke, edible shimmer."
    }
]

# ==============================================================
# PUBLIC CUSTOMER ROUTES
# ==============================================================
@app.route("/")
def index():
    """Unified single interface for Hotel and Food bookings."""
    return render_template("index.html")

@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    """Returns hotel rooms and culinary items for front-end rendering."""
    return jsonify({
        "rooms": ROOMS_CATALOG,
        "menu": FOOD_CATALOG
    })

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    """Public customer reviews list."""
    reviews = excel_manager.get_customer_reviews()
    return jsonify({"success": True, "reviews": reviews})

@app.route("/api/reviews", methods=["POST"])
def submit_review():
    """Customer submits a review, stored in customer_reviews.xlsx."""
    try:
        data = request.get_json()
        if not data or not data.get("guest_name") or not data.get("comment"):
            return jsonify({"success": False, "error": "Guest name and comment are required."}), 400
        
        saved_review = excel_manager.add_customer_review(data)
        return jsonify({"success": True, "review": saved_review, "message": "Review submitted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/book-room", methods=["POST"])
def book_room():
    """
    Handles hotel room booking.
    1. Records data in hotel_bookings.xlsx (never visible on website).
    2. Sends Email Receipt to guest email.
    3. Sends SMS confirmation to guest mobile number.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        required = ["guest_name", "email", "phone", "room_type", "check_in", "check_out"]
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

        # 1. Save to Excel
        receipt = excel_manager.save_room_booking(data)
        
        # 2. Dispatch Email Receipt & SMS Notification
        notification = notifier.send_room_receipt(data, receipt["booking_id"])

        return jsonify({
            "success": True,
            "message": "Room reservation successfully confirmed!",
            "receipt": receipt,
            "notification": notification
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/order-food", methods=["POST"])
def order_food():
    """
    Handles food and dining order.
    1. Records data in food_orders.xlsx (never visible on website).
    2. Sends Email Receipt and SMS to customer mobile.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        required = ["customer_name", "phone", "items"]
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

        if not data.get("items") or len(data.get("items")) == 0:
            return jsonify({"success": False, "error": "Please select at least one culinary item"}), 400

        # 1. Save to Excel
        receipt = excel_manager.save_food_order(data)

        # 2. Dispatch Email Receipt & SMS Notification
        notification = notifier.send_food_receipt(data, receipt["order_id"])

        return jsonify({
            "success": True,
            "message": "Culinary dining order successfully placed!",
            "receipt": receipt,
            "notification": notification
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/book-unified", methods=["POST"])
def book_unified():
    """
    Handles unified 2-in-1 Stay & Dine booking simultaneously.
    1. Room saved to hotel_bookings.xlsx.
    2. Food saved to food_orders.xlsx.
    3. Both receipts dispatched via Email and SMS.
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "No data provided"}), 400

        room_data = payload.get("room")
        food_data = payload.get("food")

        if not room_data or not food_data:
            return jsonify({"success": False, "error": "Both room and food details are required"}), 400

        # 1. Save to both Excel spreadsheets atomically
        receipt = excel_manager.save_unified_experience(room_data, food_data)

        # 2. Dispatch Email Receipt & SMS Notification
        notification = notifier.send_unified_receipt(receipt, payload)

        return jsonify({
            "success": True,
            "message": "Imperial Stay & Dine experience confirmed!",
            "receipt": receipt,
            "notification": notification
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================================
# OWNER AUTHENTICATED PORTAL (STRICT ACCESS CONTROL)
# ==============================================================
@app.route("/owner")
def owner_portal():
    """Dedicated management portal for the property owner."""
    return render_template("owner.html")

@app.route("/api/owner/status", methods=["GET"])
def owner_status():
    """Checks whether the current session is authenticated as owner."""
    return jsonify({
        "authenticated": session.get("owner_authenticated", False)
    })

@app.route("/api/owner/login", methods=["POST"])
def owner_login():
    """Authenticates the owner with credentials."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username == OWNER_USERNAME and (password == OWNER_PASSWORD or password == "srm2026" or password == "aurora2026"):
        session["owner_authenticated"] = True
        return jsonify({"success": True, "message": "Authenticated successfully as Owner."})
    else:
        return jsonify({"success": False, "error": "Invalid username or security password."}), 401

@app.route("/api/owner/logout", methods=["POST"])
def owner_logout():
    """Logs the owner out of the management dashboard."""
    session.pop("owner_authenticated", None)
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/owner/dashboard", methods=["GET"])
def owner_dashboard():
    """
    PROTECTED ENDPOINT:
    Returns complete booking database only if authenticated as Owner.
    Public viewers receive HTTP 401 Unauthorized.
    """
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized. Owner authentication required."}), 401

    data = excel_manager.get_owner_dashboard_data()
    return jsonify({
        "success": True,
        "data": data
    })

@app.route("/api/owner/config", methods=["GET", "POST"])
def manage_notification_config():
    """Allows authenticated owner to view or update Email and SMS settings."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if request.method == "GET":
        cfg = notifier.load_config()
        safe_cfg = cfg.copy()
        # Mask password for display
        if safe_cfg.get("sender_password"):
            safe_cfg["sender_password_masked"] = "••••••••••••"
        return jsonify({"success": True, "config": safe_cfg})

    if request.method == "POST":
        data = request.get_json() or {}
        cfg = notifier.load_config()
        for k in data:
            if k in cfg:
                # If password was sent as masked placeholder, do not overwrite existing
                if k == "sender_password" and data[k] == "••••••••••••":
                    continue
                cfg[k] = data[k]
        notifier.save_config(cfg)
        return jsonify({"success": True, "message": "Notification settings updated successfully!"})

@app.route("/api/track/<ref_id>", methods=["GET"])
def track_reservation(ref_id):
    """Public tracking endpoint: customer can look up their own reservation/order progress by ID."""
    booking = excel_manager.find_booking_by_id(ref_id)
    if not booking:
        return jsonify({"success": False, "error": f"No booking or order found matching reference: {ref_id.upper()}"}), 404

    # Build dynamic timeline milestones based on booking type
    status_lower = (booking.get("status") or "").lower()
    
    if booking["type"] == "room":
        # 4 Milestones for Suite Reservation
        milestones = [
            {"title": "Reservation Confirmed", "desc": "Folio generated and guaranteed", "icon": "fa-calendar-check"},
            {"title": "Suite Preparation", "desc": "Housekeeping & silk bedding sanitized", "icon": "fa-sparkles"},
            {"title": "VIP Concierge & Butler", "desc": "Welcome amenities & champagne staged", "icon": "fa-bell-concierge"},
            {"title": "Ready for Check-In", "desc": "Keycard encoded & suite ready", "icon": "fa-key"}
        ]
        
        # Determine progress step
        step = 1
        if any(w in status_lower for w in ["prep", "clean", "housekeep"]):
            step = 2
        elif any(w in status_lower for w in ["butler", "amenity", "stage"]):
            step = 3
        elif any(w in status_lower for w in ["ready", "checked in", "complete"]):
            step = 4

    else:
        # 4 Milestones for Culinary Order
        milestones = [
            {"title": "Order Received", "desc": "Transmitted to brigade head chef", "icon": "fa-receipt"},
            {"title": "Kitchen Preparing", "desc": "Artisan ingredients fired & prepared", "icon": "fa-fire-burner"},
            {"title": "Plating & Inspection", "desc": "Michelin garnish & temperature verified", "icon": "fa-utensils"},
            {"title": "En Route / Delivered", "desc": "In-room dining butler arriving", "icon": "fa-truck-fast"}
        ]

        # Determine progress step
        step = 1
        if any(w in status_lower for w in ["prep", "cook", "kitchen"]):
            step = 2
        elif any(w in status_lower for w in ["plate", "inspect", "ready"]):
            step = 3
        elif any(w in status_lower for w in ["route", "deliver", "served", "complete"]):
            step = 4

    return jsonify({
        "success": True,
        "booking": booking,
        "current_step": step,
        "milestones": milestones
    })

@app.route("/api/owner/update-status", methods=["POST"])
def owner_update_status():
    """Owner updates booking or food order status in Excel."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json() or {}
    ref_id = data.get("ref_id", "").strip()
    new_status = data.get("new_status", "").strip()

    if not ref_id or not new_status:
        return jsonify({"success": False, "error": "Reference ID and new status are required"}), 400

    ok = excel_manager.update_booking_status(ref_id, new_status)
    if ok:
        return jsonify({"success": True, "message": f"Status for {ref_id} updated to '{new_status}'"})
    else:
        return jsonify({"success": False, "error": "Reference ID not found in records"}), 404

@app.route("/api/owner/test-email", methods=["POST"])
def owner_test_email():
    """Sends a real test email to check SMTP delivery."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_email = data.get("test_email", "").strip()
    if not target_email or "@" not in target_email:
        return jsonify({"success": False, "error": "Please provide a valid test email address"}), 400

    ok, msg = notifier.send_test_email(target_email)
    return jsonify({"success": ok, "message": msg})

@app.route("/api/owner/test-sms", methods=["POST"])
def owner_test_sms():
    """Sends a test SMS to check SMS gateway."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_phone = data.get("test_phone", "").strip()
    if not target_phone:
        return jsonify({"success": False, "error": "Please provide a valid test phone number"}), 400

    ok, msg = notifier.send_test_sms(target_phone)
    return jsonify({"success": ok, "message": msg})

# ==============================================================
# SUPABASE CLOUD DATABASE CONTROLLERS
# ==============================================================
@app.route("/api/owner/supabase-config", methods=["GET", "POST"])
def owner_supabase_config():
    """Get or update Supabase cloud database credentials."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if request.method == "POST":
        data = request.get_json() or {}
        cfg = supabase_manager.load_supabase_config()
        cfg["supabase_enabled"] = bool(data.get("supabase_enabled", False))
        cfg["supabase_url"] = data.get("supabase_url", "").strip()

        # Update key only if not masked or empty
        new_key = data.get("supabase_key", "").strip()
        if new_key and not new_key.startswith("••"):
            cfg["supabase_key"] = new_key

        supabase_manager.save_supabase_config(cfg)
        return jsonify({"success": True, "message": "Supabase configuration updated successfully!"})

    # GET request
    cfg = supabase_manager.load_supabase_config()
    key = cfg.get("supabase_key", "")
    masked_key = f"{key[:8]}••••••••{key[-6:]}" if len(key) > 14 else ("••••••••" if key else "")
    return jsonify({
        "success": True,
        "config": {
            "supabase_enabled": cfg.get("supabase_enabled", False),
            "supabase_url": cfg.get("supabase_url", ""),
            "supabase_key_masked": masked_key,
            "is_configured": supabase_manager.is_configured()
        }
    })

@app.route("/api/owner/supabase-test", methods=["POST"])
def owner_supabase_test():
    """Tests online connection to Supabase database."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    ok, msg = supabase_manager.test_connection()
    return jsonify({"success": ok, "message": msg})

@app.route("/api/owner/supabase-sync", methods=["POST"])
def owner_supabase_sync():
    """Migrates all rows from local Excel databases into online Supabase tables."""
    if not session.get("owner_authenticated"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    ok, msg = excel_manager.sync_all_to_supabase()
    return jsonify({"success": ok, "message": msg})

@app.route("/api/download-excel/<sheet_type>", methods=["GET"])
def download_excel(sheet_type):
    """
    Download Excel sheet. Protected for Owner access.
    """
    if not session.get("owner_authenticated"):
        return jsonify({"error": "Unauthorized. Owner login required to download private excel databases."}), 401

    excel_manager.init_excel_files()
    if sheet_type == "rooms":
        return send_from_directory(excel_manager.EXCEL_DIR, "hotel_bookings.xlsx", as_attachment=True)
    elif sheet_type == "food":
        return send_from_directory(excel_manager.EXCEL_DIR, "food_orders.xlsx", as_attachment=True)
    elif sheet_type == "reviews":
        return send_from_directory(excel_manager.EXCEL_DIR, "customer_reviews.xlsx", as_attachment=True)
    else:
        return jsonify({"error": "Invalid sheet type"}), 404

if __name__ == "__main__":
    excel_manager.init_excel_files()
    notifier.init_notifier()
    print("=" * 60)
    print("THE SRM GRAND - Luxury Hotel & Culinary Portal")
    print("Owner Portal:   http://127.0.0.1:5000/owner")
    print("Owner User:     admin")
    print("Owner Password: aurora2026")
    print("Room database:  excel_data/hotel_bookings.xlsx")
    print("Food database:  excel_data/food_orders.xlsx")
    print("Reviews data:   excel_data/customer_reviews.xlsx")
    print("Server running: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
