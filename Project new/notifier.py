import os
import json
import smtplib
import ssl
import urllib.request
import urllib.parse
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.json")
OUTBOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outbox")
DISPATCH_LOG = os.path.join(OUTBOX_DIR, "dispatches.log")

DEFAULT_CONFIG = {
    "smtp_enabled": False,
    "smtp_provider": "gmail",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "use_ssl": True,
    "sender_email": "",
    "sender_name": "THE SRM GRAND",
    "sender_password": "",
    "sms_enabled": False,
    "sms_provider": "fast2sms",
    "fast2sms_api_key": "",
    "twilio_sid": "",
    "twilio_token": "",
    "twilio_from": ""
}

def load_config():
    """Loads email and SMS configuration from JSON."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(new_config):
    """Saves updated email and SMS configuration to JSON."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2)

def init_notifier():
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    if not os.path.exists(DISPATCH_LOG):
        with open(DISPATCH_LOG, "w", encoding="utf-8") as f:
            f.write(f"=== THE SRM GRAND DISPATCH NOTIFICATION LOG ===\nInitialized: {datetime.now()}\n\n")

def _log_dispatch(entry_type, recipient, title, content, status="DISPATCHED"):
    init_notifier()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = (
        f"\n{'='*60}\n"
        f"[{timestamp}] TYPE: {entry_type.upper()} | STATUS: {status}\n"
        f"RECIPIENT: {recipient}\n"
        f"SUBJECT / TITLE: {title}\n"
        f"CONTENT:\n{content}\n"
        f"{'='*60}\n"
    )
    with open(DISPATCH_LOG, "a", encoding="utf-8") as f:
        f.write(log_text)

# ==============================================================
# REAL EMAIL TRANSMISSION VIA SMTP (RFC 2046 MULTIPART/ALTERNATIVE)
# ==============================================================
def deliver_email(to_email, subject, html_content, text_fallback=None, attachment_html=None, attachment_filename=None):
    """
    Connects to the configured SMTP server and sends a real email to the customer.
    Delivers a clean, visually rendered luxury HTML receipt directly in the customer's inbox.
    Guarantees no raw code is shown, and no unwanted file attachments are triggered.
    Returns (success_boolean, status_message).
    """
    cfg = load_config()
    sender_email = cfg.get("sender_email", "").strip()
    sender_password = cfg.get("sender_password", "").strip()
    smtp_server = cfg.get("smtp_server", "smtp.gmail.com").strip()
    smtp_port = int(cfg.get("smtp_port", 465))
    use_ssl = cfg.get("use_ssl", True)
    sender_name = cfg.get("sender_name", "THE SRM GRAND")

    to_email = (to_email or "").strip()
    if not to_email or "@" not in to_email:
        return False, "Invalid recipient email address"

    # If sender credentials are not configured yet, record in outbox with instructions
    if not sender_email or not sender_password:
        msg = "SMTP not configured yet. Please enter Sender Email and Password in the Owner Portal."
        _log_dispatch("EMAIL", to_email, subject, html_content, status="QUEUED_OFFLINE (Configure in Owner Portal)")
        return False, msg

    try:
        # Standard RFC-compliant multipart/alternative
        # Part 1: text/plain fallback (for plain text readers)
        # Part 2: text/html rich visual folio (rendered automatically by Gmail, Outlook, Apple Mail)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        msg["Reply-To"] = sender_email
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain="thesrmgrand.com")

        if text_fallback:
            part_plain = MIMEText(text_fallback, "plain", "utf-8")
            msg.attach(part_plain)

        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_html)

        if use_ssl or smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=15) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

        _log_dispatch("EMAIL", to_email, subject, f"Delivered to {to_email} via {smtp_server}", status="DELIVERED_ONLINE")
        return True, f"Real email receipt successfully delivered to {to_email}!"

    except smtplib.SMTPAuthenticationError as e:
        err_msg = (
            f"Authentication failed for {sender_email}. "
            "For Gmail, you MUST use an App Password (16 letters) instead of your regular password. "
            "Visit Google Account -> Security -> 2-Step Verification -> App passwords."
        )
        _log_dispatch("EMAIL_ERROR", to_email, subject, f"Auth Error: {e}\n{err_msg}", status="FAILED")
        return False, err_msg
    except Exception as e:
        err_msg = f"SMTP transmission error: {str(e)}"
        _log_dispatch("EMAIL_ERROR", to_email, subject, err_msg, status="FAILED")
        return False, err_msg

# ==============================================================
# REAL SMS TRANSMISSION VIA PROVIDERS
# ==============================================================
def deliver_sms(to_phone, message_text):
    """
    Sends real SMS via Fast2SMS, Twilio, or logs to outbox.
    Returns (success_boolean, status_message).
    """
    cfg = load_config()
    to_phone = to_phone.strip()

    if not to_phone:
        return False, "Invalid phone number"

    # Provider 1: Fast2SMS (popular, fast)
    fast2sms_key = cfg.get("fast2sms_api_key", "").strip()
    if cfg.get("sms_enabled") and cfg.get("sms_provider") == "fast2sms" and fast2sms_key:
        try:
            clean_digits = "".join([c for c in to_phone if c.isdigit()])[-10:]
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = urllib.parse.urlencode({
                "authorization": fast2sms_key,
                "message": message_text,
                "language": "english",
                "route": "q",
                "numbers": clean_digits
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"cache-control": "no-cache"})
            with urllib.request.urlopen(req, timeout=10) as res:
                body = res.read().decode("utf-8")
                _log_dispatch("SMS", to_phone, "Fast2SMS Dispatch", f"Response: {body}\nMessage: {message_text}", status="DELIVERED_ONLINE")
                return True, f"SMS dispatched to {to_phone} via Fast2SMS!"
        except Exception as e:
            _log_dispatch("SMS_ERROR", to_phone, "Fast2SMS Error", str(e), status="FAILED")
            return False, f"Fast2SMS error: {str(e)}"

    # Provider 2: Twilio
    twilio_sid = cfg.get("twilio_sid", "").strip()
    twilio_token = cfg.get("twilio_token", "").strip()
    twilio_from = cfg.get("twilio_from", "").strip()
    if cfg.get("sms_enabled") and cfg.get("sms_provider") == "twilio" and twilio_sid and twilio_token and twilio_from:
        try:
            import base64
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            data = urllib.parse.urlencode({
                "To": to_phone,
                "From": twilio_from,
                "Body": message_text
            }).encode("utf-8")
            auth_str = f"{twilio_sid}:{twilio_token}"
            auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            req = urllib.request.Request(url, data=data, headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            })
            with urllib.request.urlopen(req, timeout=10) as res:
                _log_dispatch("SMS", to_phone, "Twilio Dispatch", message_text, status="DELIVERED_ONLINE")
                return True, f"SMS dispatched to {to_phone} via Twilio!"
        except Exception as e:
            _log_dispatch("SMS_ERROR", to_phone, "Twilio Error", str(e), status="FAILED")
            return False, f"Twilio error: {str(e)}"

    # If SMS provider not yet configured
    _log_dispatch("SMS", to_phone, "Reservation SMS Alert", message_text, status="LOGGED_IN_OUTBOX")
    return True, f"SMS logged to outbox. (Configure Twilio or Fast2SMS API key in Owner Portal to send real cellular SMS)"

# ==============================================================
# BOOKING RECEIPT DISPATCHERS (100% INLINED LUXURY EMAIL RECEIPTS)
# ==============================================================
def send_room_receipt(data, booking_id):
    """Composes and dispatches room booking receipt via real email and SMS."""
    guest_name = data.get("guest_name", "Valued Guest")
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    room_type = data.get("room_type", "Luxury Suite")
    check_in = data.get("check_in", "")
    check_out = data.get("check_out", "")
    nights = data.get("nights", 1)
    total_amount = float(data.get("total_amount", 0))

    tracking_url = f"http://127.0.0.1:5000/?track={booking_id}"
    
    sms_text = (
        f"THE SRM GRAND: Suite Reservation Confirmed for {guest_name}!\n"
        f"Ref Code: {booking_id}\n"
        f"Suite: {room_type} ({nights} Nights)\n"
        f"Dates: {check_in} to {check_out}\n"
        f"Total: ${total_amount:.2f}\n"
        f"Live Concierge Tracking: {tracking_url}\n"
        f"Receipt sent to {email}. We look forward to your stay!"
    )

    text_fallback = (
        f"============================================================\n"
        f"              THE SRM GRAND PALACE RESORT\n"
        f"         OFFICIAL RESERVATION FOLIO & RECEIPT\n"
        f"============================================================\n"
        f"Confirmation Code: {booking_id}\n"
        f"Reservation Status: CONFIRMED & GUARANTEED\n"
        f"Primary Guest:     {guest_name}\n"
        f"Accommodations:    {room_type}\n"
        f"Check-In Date:     {check_in} (from 3:00 PM)\n"
        f"Check-Out Date:    {check_out} (until 12:00 PM)\n"
        f"Total Duration:    {nights} Night(s)\n"
        f"Primary Phone:     {phone}\n"
        f"Guest Email:       {email}\n"
        f"------------------------------------------------------------\n"
        f"TOTAL CHARGE:      ${total_amount:.2f} (Taxes & Butler Included)\n"
        f"Payment Status:    Guaranteed\n"
        f"------------------------------------------------------------\n"
        f"LIVE CONCIERGE TRACKER:\n"
        f"{tracking_url}\n\n"
        f"Concierge Hotline: +1 (800) 555-SRM-GRAND\n"
        f"We look forward to welcoming you to The SRM Grand.\n"
        f"============================================================\n"
    )

    email_html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>The SRM Grand - Official Reservation Folio</title>
</head>
<body style="margin: 0; padding: 0; background-color: #060913; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#060913" style="background-color: #060913; margin: 0; padding: 25px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <tr>
            <td align="center" valign="top">
                <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#0d1424" style="width: 100%; max-width: 600px; background-color: #0d1424; border: 1px solid #d4af37; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.6);">
                    <!-- Brand Banner -->
                    <tr>
                        <td align="center" bgcolor="#141c30" style="background-color: #141c30; padding: 32px 20px; border-bottom: 2px solid #d4af37;">
                            <div style="font-size: 26px; font-weight: bold; color: #d4af37; letter-spacing: 3px; margin: 0 0 6px 0; text-transform: uppercase;">THE SRM GRAND</div>
                            <div style="font-size: 11px; color: #cbd5e1; letter-spacing: 2px; text-transform: uppercase; margin: 0;">PALACE SUITES & HAUTE CUISINE</div>
                            <div style="margin-top: 10px; font-size: 12px; color: #94a3b8; letter-spacing: 1px;">OFFICIAL RESERVATION FOLIO & GUEST INVOICE</div>
                        </td>
                    </tr>

                    <!-- Status & Ref Badge Bar -->
                    <tr>
                        <td style="padding: 24px 28px 12px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                     <td align="left" valign="middle">
                                         <span style="display: inline-block; background-color: #064e3b; color: #34d399; border: 1px solid #10b981; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;">&#10003; RESERVATION CONFIRMED</span>
                                     </td>
                                     <td align="right" valign="middle">
                                         <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px;">Folio Reference</div>
                                         <span style="display: inline-block; background-color: #1a2238; color: #f5d77f; border: 1px solid #d4af37; padding: 4px 10px; border-radius: 4px; font-family: 'Courier New', Courier, monospace; font-size: 14px; font-weight: bold;">{booking_id}</span>
                                     </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Salutation -->
                    <tr>
                        <td style="padding: 10px 28px 16px 28px;">
                            <h2 style="margin: 0 0 8px 0; color: #ffffff; font-size: 20px; font-weight: 600;">Dear {guest_name},</h2>
                            <p style="margin: 0; color: #cbd5e1; font-size: 14px; line-height: 1.6;">
                                Thank you for choosing The SRM Grand Palace Resort. Your luxury accommodation is confirmed and guaranteed in our private guest ledger. Below is your official receipt:
                            </p>
                        </td>
                    </tr>

                    <!-- Itemized Details Table -->
                    <tr>
                        <td style="padding: 0 28px 20px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse; background-color: #121a2d; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b;">
                                <tr bgcolor="#162035">
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b; width: 40%;">Accommodation:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{room_type}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Check-In Date:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{check_in} (from 3:00 PM)</td>
                                </tr>
                                <tr bgcolor="#162035">
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Check-Out Date:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{check_out} (until 12:00 PM)</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Stay Duration:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{nights} Night(s)</td>
                                </tr>
                                <tr bgcolor="#162035">
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Primary Guest Phone:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{phone}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px;">Guest Email Folio:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; text-align: right;">{email}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Total Amount Highlight Box -->
                    <tr>
                        <td style="padding: 0 28px 25px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: rgba(212, 175, 55, 0.1); border: 1.5px solid #d4af37; border-radius: 8px; padding: 16px 20px;">
                                <tr>
                                    <td align="left" valign="middle">
                                        <div style="color: #cbd5e1; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Total Accommodation Fee:</div>
                                        <div style="color: #94a3b8; font-size: 11px; margin-top: 3px;">Taxes, valet parking & 24/7 Butler Service included</div>
                                    </td>
                                    <td align="right" valign="middle">
                                        <div style="color: #f5d77f; font-size: 28px; font-weight: bold; letter-spacing: 1px;">${total_amount:.2f}</div>
                                        <div style="color: #34d399; font-size: 12px; font-weight: 600;">&#10003; Guaranteed & Confirmed</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Live Real-Time Tracking Card -->
                    <tr>
                        <td style="padding: 0 28px 25px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #141d33; border: 1px solid #d4af37; border-radius: 10px; padding: 22px 20px; text-align: center;">
                                <tr>
                                    <td align="center">
                                        <div style="color: #d4af37; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px;">&#128225; LIVE VIP CONCIERGE TRACKER</div>
                                        <p style="margin: 0 0 16px 0; color: #e2e8f0; font-size: 13px; line-height: 1.5;">
                                            Track your suite preparation, housekeeping status, VIP butler allocation, and ready-for-checkin milestone live in real time:
                                        </p>
                                        <table border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                                            <tr>
                                                <td align="center" bgcolor="#d4af37" style="background-color: #d4af37; border-radius: 30px;">
                                                    <a href="{tracking_url}" target="_blank" style="display: inline-block; background-color: #d4af37; color: #070a14 !important; font-weight: bold; font-size: 14px; text-decoration: none; padding: 14px 32px; border-radius: 30px; letter-spacing: 1px; font-family: Arial, sans-serif;">
                                                        &#128269; TRACK YOUR RESERVATION LIVE &rarr;
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                        <div style="margin-top: 12px; font-size: 12px; color: #94a3b8;">
                                            Direct Tracking Code: <strong style="color: #f5d77f; font-family: 'Courier New', Courier, monospace;">{booking_id}</strong>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Confidentiality Notice & Footer -->
                    <tr>
                        <td bgcolor="#080c16" style="background-color: #080c16; padding: 24px 28px; border-top: 1px solid #1e293b; text-align: center;">
                            <div style="color: #94a3b8; font-size: 12px; line-height: 1.6; margin-bottom: 10px;">
                                <strong style="color: #d4af37;">Confidentiality Notice:</strong> All booking records are stored in private property ledgers. Guest details are never exposed to public viewers.
                            </div>
                            <div style="color: #64748b; font-size: 11px;">
                                &copy; 2026 The SRM Grand Palace Resort & Spa &bull; Concierge: +1 (800) 555-SRM-GRAND<br>
                                Oceanfront Sanctuary Enclave &bull; 24/7 Butler Desk
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    email_ok, email_msg = deliver_email(
        email, 
        f"The SRM Grand - Reservation Receipt [{booking_id}]", 
        email_html, 
        text_fallback
    )
    sms_ok, sms_msg = deliver_sms(phone, sms_text)

    return {
        "email_sent": email_ok,
        "email_recipient": email,
        "email_status": email_msg,
        "sms_sent": sms_ok,
        "sms_recipient": phone,
        "sms_status": sms_msg,
        "sms_preview": sms_text,
        "tracking_url": tracking_url
    }

def send_food_receipt(data, order_id):
    """Composes and dispatches food order receipt via real email and SMS."""
    customer_name = data.get("customer_name", "Valued Guest")
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    service_type = data.get("service_type", "Room Service")
    dest_num = data.get("destination_number", "Suite")
    preferred_time = data.get("preferred_time", "ASAP")
    dietary_notes = data.get("dietary_notes", "Standard")
    grand_total = float(data.get("grand_total", 0))
    subtotal = float(data.get("subtotal", 0))
    tax_service = float(data.get("tax_service", 0))
    items = data.get("items", [])
    
    if isinstance(items, list):
        items_summary = ", ".join([f"{item.get('name', 'Dish')} (x{item.get('qty', 1)})" for item in items])
        items_rows_html = "".join([
            f"""<tr bgcolor="{'#162035' if idx % 2 == 0 else '#121a2d'}">
                <td style="padding: 10px 14px; color: #ffffff; font-size: 13px; border-bottom: 1px solid #1e293b;">{item.get('name', 'Dish')}</td>
                <td style="padding: 10px 14px; color: #cbd5e1; font-size: 13px; border-bottom: 1px solid #1e293b; text-align: center;">x{item.get('qty', 1)}</td>
                <td style="padding: 10px 14px; color: #f5d77f; font-size: 13px; border-bottom: 1px solid #1e293b; text-align: right; font-weight: bold;">${(float(item.get('price', 0)) * int(item.get('qty', 1))):.2f}</td>
            </tr>"""
            for idx, item in enumerate(items)
        ])
    else:
        items_summary = str(items)
        items_rows_html = f"""<tr><td colspan="3" style="padding: 10px 14px; color: #fff;">{items_summary}</td></tr>"""

    tracking_url = f"http://127.0.0.1:5000/?track={order_id}"

    sms_text = (
        f"THE SRM GRAND DINING: Order #{order_id} Confirmed for {customer_name}!\n"
        f"Delivery: {service_type} ({dest_num})\n"
        f"Time: {preferred_time}\n"
        f"Items: {items_summary}\n"
        f"Total: ${grand_total:.2f}\n"
        f"Live Kitchen Tracking: {tracking_url}\n"
        f"Our brigade is currently preparing your order."
    )

    text_fallback = (
        f"============================================================\n"
        f"              THE SRM GRAND PALACE & DINING\n"
        f"        OFFICIAL CULINARY DINING & ROOM RECEIPT\n"
        f"============================================================\n"
        f"Order Reference:   {order_id}\n"
        f"Status:            CONFIRMED & PREPARING\n"
        f"Guest Name:        {customer_name}\n"
        f"Service Mode:      {service_type} ({dest_num})\n"
        f"Serving Time:      {preferred_time}\n"
        f"Dietary Notes:     {dietary_notes}\n"
        f"Contact Phone:     {phone}\n"
        f"------------------------------------------------------------\n"
        f"DISHES ORDERED:\n"
        f"{items_summary}\n"
        f"------------------------------------------------------------\n"
        f"Subtotal:          ${subtotal:.2f}\n"
        f"Service Fee (10%): ${tax_service:.2f}\n"
        f"GRAND TOTAL:       ${grand_total:.2f}\n"
        f"------------------------------------------------------------\n"
        f"LIVE KITCHEN TRACKER:\n"
        f"{tracking_url}\n\n"
        f"Concierge Dining Desk: +1 (800) 555-SRM-GRAND\n"
        f"Bon Appétit! Michelin-Inspired Gastronomy\n"
        f"============================================================\n"
    )

    email_html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>The SRM Grand - Culinary Dining Receipt</title>
</head>
<body style="margin: 0; padding: 0; background-color: #060913; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#060913" style="background-color: #060913; margin: 0; padding: 25px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <tr>
            <td align="center" valign="top">
                <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#0d1424" style="width: 100%; max-width: 600px; background-color: #0d1424; border: 1px solid #d4af37; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.6);">
                    <!-- Brand Banner -->
                    <tr>
                        <td align="center" bgcolor="#141c30" style="background-color: #141c30; padding: 32px 20px; border-bottom: 2px solid #d4af37;">
                            <div style="font-size: 26px; font-weight: bold; color: #d4af37; letter-spacing: 3px; margin: 0 0 6px 0; text-transform: uppercase;">THE SRM GRAND</div>
                            <div style="font-size: 11px; color: #cbd5e1; letter-spacing: 2px; text-transform: uppercase; margin: 0;">HAUTE CUISINE & IN-ROOM DINING</div>
                            <div style="margin-top: 10px; font-size: 12px; color: #94a3b8; letter-spacing: 1px;">OFFICIAL CULINARY RECEIPT & SERVICE VOUCHER</div>
                        </td>
                    </tr>

                    <!-- Status & Ref Badge Bar -->
                    <tr>
                        <td style="padding: 24px 28px 12px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left" valign="middle">
                                        <span style="display: inline-block; background-color: #78350f; color: #fde68a; border: 1px solid #f59e0b; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;">&#127860; ORDER CONFIRMED</span>
                                    </td>
                                    <td align="right" valign="middle">
                                        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px;">Order Reference</div>
                                        <span style="display: inline-block; background-color: #1a2238; color: #fbbf24; border: 1px solid #f59e0b; padding: 4px 10px; border-radius: 4px; font-family: 'Courier New', Courier, monospace; font-size: 14px; font-weight: bold;">{order_id}</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Salutation -->
                    <tr>
                        <td style="padding: 10px 28px 16px 28px;">
                            <h2 style="margin: 0 0 8px 0; color: #ffffff; font-size: 20px; font-weight: 600;">Dear {customer_name},</h2>
                            <p style="margin: 0; color: #cbd5e1; font-size: 14px; line-height: 1.6;">
                                Your dining order has been received and transmitted to our executive chef brigade. Below is your itemized order receipt:
                            </p>
                        </td>
                    </tr>

                    <!-- Order Details Summary -->
                    <tr>
                        <td style="padding: 0 28px 15px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse; background-color: #121a2d; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b;">
                                <tr bgcolor="#162035">
                                    <td style="padding: 10px 14px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b; width: 40%;">Service Mode:</td>
                                    <td style="padding: 10px 14px; color: #ffffff; font-size: 13px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{service_type} ({dest_num})</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 14px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Serving Schedule:</td>
                                    <td style="padding: 10px 14px; color: #ffffff; font-size: 13px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{preferred_time}</td>
                                </tr>
                                <tr bgcolor="#162035">
                                    <td style="padding: 10px 14px; color: #94a3b8; font-size: 13px;">Chef / Dietary Notes:</td>
                                    <td style="padding: 10px 14px; color: #ffffff; font-size: 13px; font-weight: bold; text-align: right;">{dietary_notes}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Itemized Dishes Table -->
                    <tr>
                        <td style="padding: 0 28px 20px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse; background-color: #121a2d; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b;">
                                <tr bgcolor="#1a2238">
                                    <td style="padding: 10px 14px; color: #d4af37; font-size: 12px; font-weight: bold; text-transform: uppercase;">Dish / Creation</td>
                                    <td style="padding: 10px 14px; color: #d4af37; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: center;">Qty</td>
                                    <td style="padding: 10px 14px; color: #d4af37; font-size: 12px; font-weight: bold; text-transform: uppercase; text-align: right;">Amount</td>
                                </tr>
                                {items_rows_html}
                            </table>
                        </td>
                    </tr>

                    <!-- Total Amount Highlight Box -->
                    <tr>
                        <td style="padding: 0 28px 25px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: rgba(245, 158, 11, 0.1); border: 1.5px solid #f59e0b; border-radius: 8px; padding: 16px 20px;">
                                <tr>
                                    <td align="left" valign="middle">
                                        <div style="color: #cbd5e1; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Grand Total:</div>
                                        <div style="color: #94a3b8; font-size: 11px; margin-top: 3px;">Includes 10% Michelin service & private butler delivery</div>
                                    </td>
                                    <td align="right" valign="middle">
                                        <div style="color: #f5d77f; font-size: 28px; font-weight: bold; letter-spacing: 1px;">${grand_total:.2f}</div>
                                        <div style="color: #34d399; font-size: 12px; font-weight: 600;">&#10003; Order Confirmed</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Live Kitchen Tracking Card -->
                    <tr>
                        <td style="padding: 0 28px 25px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #141d33; border: 1px solid #f59e0b; border-radius: 10px; padding: 22px 20px; text-align: center;">
                                <tr>
                                    <td align="center">
                                        <div style="color: #fbbf24; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px;">&#128225; LIVE KITCHEN & BUTLER TRACKER</div>
                                        <p style="margin: 0 0 16px 0; color: #e2e8f0; font-size: 13px; line-height: 1.5;">
                                             Track kitchen preparation, artisan garnishing, and butler delivery to your suite in real time:
                                        </p>
                                        <table border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                                            <tr>
                                                <td align="center" bgcolor="#f59e0b" style="background-color: #f59e0b; border-radius: 30px;">
                                                    <a href="{tracking_url}" target="_blank" style="display: inline-block; background-color: #f59e0b; color: #070a14 !important; font-weight: bold; font-size: 14px; text-decoration: none; padding: 14px 32px; border-radius: 30px; letter-spacing: 1px; font-family: Arial, sans-serif;">
                                                        <span style="color: #070a14 !important; font-weight: bold; text-decoration: none;">&#127869; TRACK CULINARY ORDER LIVE &rarr;</span>
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                        <div style="margin-top: 12px; font-size: 12px; color: #94a3b8;">
                                            Direct Tracking Code: <strong style="color: #fbbf24; font-family: 'Courier New', Courier, monospace;">{order_id}</strong>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td bgcolor="#080c16" style="background-color: #080c16; padding: 24px 28px; border-top: 1px solid #1e293b; text-align: center;">
                            <div style="color: #94a3b8; font-size: 12px; line-height: 1.6; margin-bottom: 8px;">
                                <strong style="color: #d4af37;">The SRM Grand Culinary Brigade</strong> &bull; Concierge Dining: +1 (800) 555-SRM-GRAND
                            </div>
                            <div style="color: #64748b; font-size: 11px;">
                                &copy; 2026 The SRM Grand Haute Cuisine & In-Room Dining. Bon Appétit!
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    email_ok, email_msg = deliver_email(
        email, 
        f"The SRM Grand - Dining Receipt [{order_id}]", 
        email_html, 
        text_fallback
    ) if email else (False, "No email provided")
    sms_ok, sms_msg = deliver_sms(phone, sms_text)

    return {
        "email_sent": email_ok,
        "email_recipient": email or "N/A",
        "email_status": email_msg,
        "sms_sent": sms_ok,
        "sms_recipient": phone,
        "sms_status": sms_msg,
        "sms_preview": sms_text,
        "tracking_url": tracking_url
    }

def send_unified_receipt(receipt, payload):
    """Composes and dispatches combined Stay & Dine receipt."""
    room_data = payload.get("room", {})
    food_data = payload.get("food", {})

    guest_name = room_data.get("guest_name", "Valued Guest")
    phone = room_data.get("phone", "").strip()
    email = room_data.get("email", "").strip()
    room_id = receipt.get("room_booking_id", "AUR-RM")
    food_id = receipt.get("food_order_id", "AUR-FD")
    combined_total = float(receipt.get("combined_total", 0))

    room_tracking_url = f"http://127.0.0.1:5000/?track={room_id}"
    food_tracking_url = f"http://127.0.0.1:5000/?track={food_id}"

    sms_text = (
        f"THE SRM GRAND: Imperial Stay & Dine Confirmed for {guest_name}!\n"
        f"Room Ref: {room_id} | Dining Ref: {food_id}\n"
        f"Suite: {room_data.get('room_type')} ({room_data.get('nights')} Nights)\n"
        f"Serving Time: {food_data.get('preferred_time')}\n"
        f"Combined Total: ${combined_total:.2f}\n"
        f"Suite Tracking: {room_tracking_url}\n"
        f"Dining Tracking: {food_tracking_url}\n"
        f"Official receipt delivered to {email}."
    )

    text_fallback = (
        f"============================================================\n"
        f"              THE SRM GRAND PALACE RESORT\n"
        f"      THE IMPERIAL STAY & DINE EXPERIENCE RECEIPT\n"
        f"============================================================\n"
        f"Suite Booking Ref: {room_id}\n"
        f"Dining Order Ref:  {food_id}\n"
        f"Status:            DUAL RESERVATION CONFIRMED\n"
        f"Primary Guest:     {guest_name}\n"
        f"Accommodations:    {room_data.get('room_type')} ({room_data.get('nights')} Nights)\n"
        f"Stay Duration:     {room_data.get('check_in')} to {room_data.get('check_out')}\n"
        f"Dining Serving:    {food_data.get('preferred_time')}\n"
        f"Contact Phone:     {phone}\n"
        f"Guest Email:       {email}\n"
        f"------------------------------------------------------------\n"
        f"COMBINED TOTAL:    ${combined_total:.2f} (Suite + Dining Package)\n"
        f"------------------------------------------------------------\n"
        f"LIVE SUITE TRACKER:  {room_tracking_url}\n"
        f"LIVE DINING TRACKER: {food_tracking_url}\n\n"
        f"Concierge Desk: +1 (800) 555-SRM-GRAND\n"
        f"============================================================\n"
    )

    email_html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>The SRM Grand - Imperial Stay & Dine Folio</title>
</head>
<body style="margin: 0; padding: 0; background-color: #060913; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#060913" style="background-color: #060913; margin: 0; padding: 25px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <tr>
            <td align="center" valign="top">
                <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#0d1424" style="width: 100%; max-width: 600px; background-color: #0d1424; border: 1px solid #d4af37; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.6);">
                    <!-- Brand Banner -->
                    <tr>
                        <td align="center" bgcolor="#141c30" style="background-color: #141c30; padding: 32px 20px; border-bottom: 2px solid #d4af37;">
                            <div style="font-size: 26px; font-weight: bold; color: #d4af37; letter-spacing: 3px; margin: 0 0 6px 0; text-transform: uppercase;">THE SRM GRAND</div>
                            <div style="font-size: 11px; color: #cbd5e1; letter-spacing: 2px; text-transform: uppercase; margin: 0;">THE IMPERIAL STAY & DINE EXPERIENCE</div>
                            <div style="margin-top: 10px; font-size: 12px; color: #94a3b8; letter-spacing: 1px;">COMBINED LUXURY RESIDENCE & HAUTE CUISINE FOLIO</div>
                        </td>
                    </tr>

                    <!-- Status Bar -->
                    <tr>
                        <td style="padding: 24px 28px 12px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="left">
                                        <span style="display: inline-block; background-color: #064e3b; color: #34d399; border: 1px solid #10b981; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold;">&#10024; DUAL RESERVATION CONFIRMED</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Salutation -->
                    <tr>
                        <td style="padding: 10px 28px 16px 28px;">
                            <h2 style="margin: 0 0 8px 0; color: #ffffff; font-size: 20px; font-weight: 600;">Dear {guest_name},</h2>
                            <p style="margin: 0; color: #cbd5e1; font-size: 14px; line-height: 1.6;">
                                Your combined luxury Suite stay and curated Haute Cuisine dining pass has been confirmed. Below is your itemized folio:
                            </p>
                        </td>
                    </tr>

                    <!-- References Table -->
                    <tr>
                        <td style="padding: 0 28px 20px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse; background-color: #121a2d; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b;">
                                <tr bgcolor="#162035">
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Suite Booking Reference:</td>
                                    <td style="padding: 12px 16px; color: #d4af37; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right; font-family: monospace;">{room_id}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Dining Order Reference:</td>
                                    <td style="padding: 12px 16px; color: #fbbf24; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right; font-family: monospace;">{food_id}</td>
                                </tr>
                                <tr bgcolor="#162035">
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Selected Residence:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{room_data.get('room_type')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px; border-bottom: 1px solid #1e293b;">Stay Duration:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; border-bottom: 1px solid #1e293b; text-align: right;">{room_data.get('check_in')} to {room_data.get('check_out')} ({room_data.get('nights')} Nights)</td>
                                </tr>
                                <tr bgcolor="#162035">
                                    <td style="padding: 12px 16px; color: #94a3b8; font-size: 13px;">Dining Serving Time:</td>
                                    <td style="padding: 12px 16px; color: #ffffff; font-size: 14px; font-weight: bold; text-align: right;">{food_data.get('preferred_time')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Grand Combined Total -->
                    <tr>
                        <td style="padding: 0 28px 25px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: rgba(212, 175, 55, 0.12); border: 1.5px solid #d4af37; border-radius: 8px; padding: 16px 20px;">
                                <tr>
                                    <td align="left" valign="middle">
                                        <div style="color: #cbd5e1; font-size: 13px; text-transform: uppercase;">Combined Experience Total:</div>
                                        <div style="color: #94a3b8; font-size: 11px; margin-top: 3px;">Full accommodations, multi-course dining & VIP Butler included</div>
                                    </td>
                                    <td align="right" valign="middle">
                                        <div style="color: #f5d77f; font-size: 28px; font-weight: bold; letter-spacing: 1px;">${combined_total:.2f}</div>
                                        <div style="color: #34d399; font-size: 12px; font-weight: 600;">&#10003; Dual Confirmation</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Live Experience Tracking -->
                    <tr>
                        <td style="padding: 0 28px 25px 28px;">
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #141d33; border: 1px solid #d4af37; border-radius: 10px; padding: 22px 20px; text-align: center;">
                                <tr>
                                    <td align="center">
                                        <div style="color: #d4af37; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px;">&#128225; LIVE STAY & DINE TRACKER</div>
                                        <p style="margin: 0 0 16px 0; color: #e2e8f0; font-size: 13px; line-height: 1.5;">
                                            Track your suite preparation and kitchen order progress in real time:
                                        </p>
                                        <table border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="padding: 4px 8px;">
                                                    <a href="{room_tracking_url}" target="_blank" style="display: inline-block; background-color: #d4af37; color: #070a14 !important; font-weight: bold; font-size: 13px; text-decoration: none; padding: 12px 24px; border-radius: 30px; letter-spacing: 0.5px; font-family: Arial, sans-serif;">
                                                        <span style="color: #070a14 !important; font-weight: bold; text-decoration: none;">&#128269; Track Suite ({room_id})</span>
                                                    </a>
                                                </td>
                                                <td style="padding: 4px 8px;">
                                                    <a href="{food_tracking_url}" target="_blank" style="display: inline-block; background-color: #f59e0b; color: #070a14 !important; font-weight: bold; font-size: 13px; text-decoration: none; padding: 12px 24px; border-radius: 30px; letter-spacing: 0.5px; font-family: Arial, sans-serif;">
                                                        <span style="color: #070a14 !important; font-weight: bold; text-decoration: none;">&#127869; Track Dining ({food_id})</span>
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td bgcolor="#080c16" style="background-color: #080c16; padding: 24px 28px; border-top: 1px solid #1e293b; text-align: center;">
                            <div style="color: #94a3b8; font-size: 12px; line-height: 1.6; margin-bottom: 8px;">
                                <strong style="color: #d4af37;">The SRM Grand Palace Resort & Dining</strong> &bull; Concierge: +1 (800) 555-SRM-GRAND
                            </div>
                            <div style="color: #64748b; font-size: 11px;">
                                &copy; 2026 The SRM Grand Luxury Properties. All records stored privately in property ledgers.
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    email_ok, email_msg = deliver_email(
        email, 
        f"The SRM Grand - Stay & Dine Receipt [{room_id}]", 
        email_html, 
        text_fallback
    )
    sms_ok, sms_msg = deliver_sms(phone, sms_text)

    return {
        "email_sent": email_ok,
        "email_recipient": email,
        "email_status": email_msg,
        "sms_sent": sms_ok,
        "sms_recipient": phone,
        "sms_status": sms_msg,
        "sms_preview": sms_text,
        "room_tracking_url": room_tracking_url,
        "food_tracking_url": food_tracking_url
    }

def send_test_email(target_email):
    """Sends an immediate test email to check SMTP credentials."""
    test_subject = "The SRM Grand - SMTP Configuration Test"
    test_html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>The SRM Grand - System Test</title>
</head>
<body style="margin: 0; padding: 0; background-color: #060913; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#060913" style="background-color: #060913; margin: 0; padding: 25px 0; font-family: Arial, Helvetica, sans-serif;">
        <tr>
            <td align="center" valign="top">
                <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#0d1424" style="width: 100%; max-width: 600px; background-color: #0d1424; border: 1px solid #d4af37; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.6);">
                    <tr>
                        <td align="center" bgcolor="#141c30" style="background-color: #141c30; padding: 28px 20px; border-bottom: 2px solid #d4af37;">
                            <div style="font-size: 24px; font-weight: bold; color: #d4af37; letter-spacing: 2px; text-transform: uppercase;">THE SRM GRAND PALACE</div>
                            <div style="font-size: 11px; color: #cbd5e1; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px;">AUTOMATED DISPATCH SYSTEM TEST</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 28px;">
                            <div style="background-color: #064e3b; border: 1px solid #10b981; color: #34d399; padding: 10px 16px; border-radius: 6px; font-size: 13px; font-weight: bold; margin-bottom: 20px; display: inline-block;">
                                &#10003; SMTP GATEWAY ONLINE &amp; VERIFIED
                            </div>
                            <h2 style="color: #ffffff; font-size: 18px; margin: 0 0 10px 0;">Transmission Verified</h2>
                            <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin: 0 0 14px 0;">
                                Your email sending configuration is functioning properly. Customer booking receipts and dining folios are dispatched directly to recipient inboxes in this rich, mobile-responsive layout.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#080c16" style="background-color: #080c16; padding: 18px; border-top: 1px solid #1e293b; text-align: center; color: #64748b; font-size: 11px;">
                            &copy; 2026 The SRM Grand Luxury Properties &bull; Dispatch Engine Verified
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
    return deliver_email(target_email, test_subject, test_html, "The SRM Grand SMTP Test Successful!")

def send_test_sms(target_phone):
    """Sends an immediate test SMS to check SMS provider configuration."""
    msg = "THE SRM GRAND: Test SMS Notification. Your SMS gateway configuration is active!"
    return deliver_sms(target_phone, msg)
