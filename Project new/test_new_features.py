import urllib.request
import urllib.parse
import json
import http.cookiejar

BASE = "http://127.0.0.1:5000"

print("--- 1. Testing Customer Reviews API ---")
res = urllib.request.urlopen(f"{BASE}/api/reviews")
rev_data = json.loads(res.read())
print(f"Initial reviews count: {len(rev_data['reviews'])}")

# Submit a new review
new_rev_payload = json.dumps({
    "guest_name": "Marquess Julian Thorne",
    "rating": 5,
    "type": "Suite Stay & Dining",
    "title": "Perfection in Every Detail",
    "comment": "The sunset views and Wagyu tasting were transcendent. 10/10."
}).encode("utf-8")
req = urllib.request.Request(f"{BASE}/api/reviews", data=new_rev_payload, headers={"Content-Type": "application/json"})
res = urllib.request.urlopen(req)
add_rev_res = json.loads(res.read())
print(f"Added review result: {add_rev_res['success']}, ID: {add_rev_res['review']['id']}")

print("\n--- 2. Testing Room Booking & Email/SMS Dispatch ---")
room_payload = json.dumps({
    "guest_name": "Sir Ronald Sterling",
    "email": "ronald@sterling.co.uk",
    "phone": "+44 7700 900888",
    "room_type": "The Presidential Sky Penthouse",
    "price_per_night": 850,
    "check_in": "2026-12-24",
    "check_out": "2026-12-28",
    "nights": 4,
    "guests": 2,
    "total_amount": 3400,
    "payment_method": "Platinum Reserve Card",
    "special_requests": "Airport limousine pickup"
}).encode("utf-8")
req = urllib.request.Request(f"{BASE}/api/book-room", data=room_payload, headers={"Content-Type": "application/json"})
res = urllib.request.urlopen(req)
room_res = json.loads(res.read())
print(f"Room Booking ID: {room_res['receipt']['booking_id']}")
print(f"Receipt Emailed to: {room_res['notification']['email_recipient']} (Sent: {room_res['notification']['email_sent']})")
print(f"SMS Dispatched to: {room_res['notification']['sms_recipient']} (Sent: {room_res['notification']['sms_sent']})")

print("\n--- 3. Testing Public Access Control (Should be Blocked) ---")
try:
    urllib.request.urlopen(f"{BASE}/api/owner/dashboard")
    print("ERROR: Public viewer was able to access owner data!")
except urllib.error.HTTPError as e:
    print(f"CONFIRMED: Public access blocked with HTTP {e.code} ({e.reason})")

print("\n--- 4. Testing Owner Authentication & Dashboard Access ---")
# Set up cookie jar for session management
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Login with Owner Credentials
login_payload = json.dumps({
    "username": "admin",
    "password": "aurora2026"
}).encode("utf-8")
req_login = urllib.request.Request(f"{BASE}/api/owner/login", data=login_payload, headers={"Content-Type": "application/json"})
res_login = opener.open(req_login)
login_res = json.loads(res_login.read())
print("Owner Login Status:", login_res["success"], "-", login_res["message"])

# Fetch Protected Owner Dashboard Data
res_dash = opener.open(f"{BASE}/api/owner/dashboard")
dash_data = json.loads(res_dash.read())
stats = dash_data["data"]["stats"]
print("\n=== OWNER LEDGER OVERVIEW ===")
print(f"Total Suites Booked: {stats['total_room_bookings']}")
print(f"Total Room Revenue:  ${stats['total_room_revenue']:.2f}")
print(f"Total Food Orders:   {stats['total_food_orders']}")
print(f"Total Food Revenue:  ${stats['total_food_revenue']:.2f}")
print(f"Combined Revenue:    ${stats['total_combined_revenue']:.2f}")

# Logout
opener.open(urllib.request.Request(f"{BASE}/api/owner/logout", data=b"{}", headers={"Content-Type": "application/json"}))
print("\nOwner Logged Out.")

# Verify Protected again
try:
    opener.open(f"{BASE}/api/owner/dashboard")
    print("ERROR: Owner dashboard accessible after logout!")
except urllib.error.HTTPError as e:
    print(f"CONFIRMED: Access blocked after logout with HTTP {e.code}")
