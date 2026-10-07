"""
THE SRM GRAND - SUPABASE CLOUD DATABASE ADAPTER
Provides zero-dependency REST integration with Supabase (PostgreSQL).
Saves room bookings, culinary orders, and customer reviews to Supabase online.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supabase_config.json")

DEFAULT_CONFIG = {
    "supabase_enabled": False,
    "supabase_url": "",
    "supabase_key": ""
}

def load_supabase_config():
    """Loads Supabase credentials from JSON or Environment Variables."""
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except Exception as e:
            print(f"[Supabase] Config load error: {e}")

    # Environment variables override config file (ideal for cloud deployment on Render/Railway)
    env_url = os.environ.get("SUPABASE_URL", "").strip()
    env_key = os.environ.get("SUPABASE_KEY", "").strip()
    if env_url:
        cfg["supabase_url"] = env_url
        cfg["supabase_enabled"] = True
    if env_key:
        cfg["supabase_key"] = env_key

    return cfg

def _clean_supabase_url(url_str):
    """Normalizes Supabase URL, stripping any trailing slashes or accidental /rest/v1 suffixes."""
    if not url_str:
        return ""
    u = url_str.strip().rstrip("/")
    if u.endswith("/rest/v1"):
        u = u[:-8].rstrip("/")
    return u

def save_supabase_config(new_config):
    """Persists Supabase credentials."""
    if "supabase_url" in new_config:
        new_config["supabase_url"] = _clean_supabase_url(new_config["supabase_url"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2)

def is_configured():
    """Checks if valid Supabase URL and Key are active."""
    cfg = load_supabase_config()
    return bool(cfg.get("supabase_enabled") and cfg.get("supabase_url") and cfg.get("supabase_key"))

def _send_request(endpoint, method="GET", payload=None):
    """
    Executes an authenticated REST call to Supabase PostgREST API using standard urllib.
    Zero external dependencies needed.
    """
    cfg = load_supabase_config()
    base_url = _clean_supabase_url(cfg.get("supabase_url", ""))
    api_key = cfg.get("supabase_key", "").strip()

    if not base_url or not api_key:
        return False, "Supabase credentials not configured."

    url = f"{base_url}/rest/v1/{endpoint}"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            parsed = json.loads(res_body) if res_body else []
            return True, parsed
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        return False, f"Supabase HTTP {e.code}: {err_msg}"
    except Exception as e:
        return False, f"Supabase Connection Error: {str(e)}"

def test_connection():
    """Tests Supabase connection and checks if tables are reachable."""
    if not is_configured():
        return False, "Supabase URL and Key are required. Please configure in the Owner Portal."
    
    ok, res = _send_request("hotel_bookings?select=count", method="GET")
    if ok:
        return True, "Successfully connected to online Supabase database! Tables are online."
    else:
        # Check if table not created
        if "404" in str(res) or "relation" in str(res).lower() or "not found" in str(res).lower():
            return False, f"Connected to Supabase, but tables are missing. Please execute the SQL schema in your Supabase SQL Editor. ({res})"
        return False, f"Failed to connect: {res}"

# ==============================================================
# DATA INSERTION (REAL-TIME ONLINE SYNC)
# ==============================================================
def save_room_booking(room_data, booking_id, timestamp):
    """Uploads room reservation record to Supabase online table."""
    if not is_configured():
        return False, "Supabase offline / unconfigured"

    payload = {
        "booking_id": booking_id,
        "timestamp": timestamp,
        "guest_name": room_data.get("guest_name", "N/A"),
        "email": room_data.get("email", "N/A"),
        "phone": room_data.get("phone", "N/A"),
        "room_type": room_data.get("room_type", "N/A"),
        "check_in": room_data.get("check_in", "N/A"),
        "check_out": room_data.get("check_out", "N/A"),
        "nights": int(room_data.get("nights", 1)),
        "guests": int(room_data.get("guests", 1)),
        "rate": float(room_data.get("price_per_night", 0)),
        "total": float(room_data.get("total_amount", 0)),
        "payment_mode": room_data.get("payment_method", "Pay upon Arrival"),
        "special_requests": room_data.get("special_requests", "None"),
        "status": "Confirmed",
        "linked_food_id": room_data.get("linked_food_id", "N/A")
    }

    ok, res = _send_request("hotel_bookings", method="POST", payload=payload)
    if ok:
        print(f"[Supabase] Room booking {booking_id} saved to cloud!")
        return True, res
    else:
        print(f"[Supabase] Room booking cloud error: {res}")
        return False, res

def save_food_order(food_data, order_id, timestamp, itemized_summary, total_items_count):
    """Uploads food order record to Supabase online table."""
    if not is_configured():
        return False, "Supabase offline / unconfigured"

    payload = {
        "order_id": order_id,
        "timestamp": timestamp,
        "customer_name": food_data.get("customer_name", "N/A"),
        "phone": food_data.get("phone", "N/A"),
        "email": food_data.get("email", "N/A"),
        "service_type": food_data.get("service_type", "Room Service"),
        "destination": food_data.get("destination_number", "Room Suite"),
        "preferred_time": food_data.get("preferred_time", "Immediate"),
        "itemized_dishes": itemized_summary,
        "total_items": int(total_items_count),
        "subtotal": float(food_data.get("subtotal", 0)),
        "tax_service": float(food_data.get("tax_service", 0)),
        "grand_total": float(food_data.get("grand_total", 0)),
        "payment_mode": food_data.get("payment_method", "Charge to Room / Upon Delivery"),
        "dietary_notes": food_data.get("dietary_notes", "Standard"),
        "status": "Confirmed & Preparing",
        "linked_room_id": food_data.get("linked_room_id", "N/A")
    }

    ok, res = _send_request("food_orders", method="POST", payload=payload)
    if ok:
        print(f"[Supabase] Food order {order_id} saved to cloud!")
        return True, res
    else:
        print(f"[Supabase] Food order cloud error: {res}")
        return False, res

def save_customer_review(review_data, rev_id, timestamp):
    """Uploads customer review to Supabase online table."""
    if not is_configured():
        return False, "Supabase offline / unconfigured"

    payload = {
        "review_id": rev_id,
        "timestamp": timestamp,
        "guest_name": review_data.get("guest_name", "Anonymous Guest"),
        "rating": int(review_data.get("rating", 5)),
        "type": review_data.get("type", "Suite Stay & Dining"),
        "title": review_data.get("title", "Exceptional Hospitality"),
        "comment": review_data.get("comment", ""),
        "status": "Approved"
    }

    ok, res = _send_request("customer_reviews", method="POST", payload=payload)
    if ok:
        print(f"[Supabase] Review {rev_id} saved to cloud!")
        return True, res
    else:
        print(f"[Supabase] Review cloud error: {res}")
        return False, res

def update_status(ref_id, new_status):
    """Updates booking status in Supabase."""
    if not is_configured():
        return False, "Supabase offline / unconfigured"

    ref_id = ref_id.strip().upper()
    if "AUR-RM" in ref_id:
        endpoint = f"hotel_bookings?booking_id=eq.{ref_id}"
        payload = {"status": new_status}
    elif "AUR-FD" in ref_id:
        endpoint = f"food_orders?order_id=eq.{ref_id}"
        payload = {"status": new_status}
    else:
        return False, "Invalid reference prefix"

    ok, res = _send_request(endpoint, method="PATCH", payload=payload)
    return ok, res

def find_booking_by_id(ref_id):
    """Queries online Supabase database for tracking reference code."""
    if not is_configured():
        return None

    ref_id = ref_id.strip().upper()
    if "AUR-RM" in ref_id:
        ok, res = _send_request(f"hotel_bookings?booking_id=eq.{ref_id}&select=*")
        if ok and isinstance(res, list) and len(res) > 0:
            b = res[0]
            return {
                "type": "room",
                "id": b.get("booking_id"),
                "title": b.get("room_type"),
                "guest_name": b.get("guest_name"),
                "email": b.get("email"),
                "phone": b.get("phone"),
                "check_in": b.get("check_in"),
                "check_out": b.get("check_out"),
                "nights": b.get("nights"),
                "guests": b.get("guests"),
                "rate": float(b.get("rate", 0)),
                "total": float(b.get("total", 0)),
                "status": b.get("status", "Confirmed"),
                "timestamp": b.get("timestamp"),
                "linked_id": b.get("linked_food_id", "N/A")
            }
    elif "AUR-FD" in ref_id:
        ok, res = _send_request(f"food_orders?order_id=eq.{ref_id}&select=*")
        if ok and isinstance(res, list) and len(res) > 0:
            o = res[0]
            return {
                "type": "food",
                "id": o.get("order_id"),
                "title": f"Culinary Order ({o.get('service_type')})",
                "guest_name": o.get("customer_name"),
                "email": o.get("email"),
                "phone": o.get("phone"),
                "destination": o.get("destination"),
                "preferred_time": o.get("preferred_time"),
                "dishes": o.get("itemized_dishes"),
                "total_items": o.get("total_items"),
                "total": float(o.get("grand_total", 0)),
                "status": o.get("status", "Confirmed & Preparing"),
                "timestamp": o.get("timestamp"),
                "linked_id": o.get("linked_room_id", "N/A")
            }
    return None

def fetch_all_reviews():
    """Fetches customer reviews from Supabase."""
    if not is_configured():
        return None

    ok, res = _send_request("customer_reviews?select=*&order=created_at.desc")
    if ok and isinstance(res, list):
        return [
            {
                "id": r.get("review_id"),
                "timestamp": r.get("timestamp"),
                "guest_name": r.get("guest_name"),
                "rating": int(r.get("rating", 5)),
                "type": r.get("type"),
                "title": r.get("title"),
                "comment": r.get("comment")
            }
            for r in res
        ]
    return None
