-- ================================================================
-- THE SRM GRAND - SUPABASE CLOUD DATABASE SCHEMA
-- Instructions:
-- 1. Log in to your Supabase Dashboard (https://supabase.com)
-- 2. Click on your project -> Go to "SQL Editor" on the left menu
-- 3. Click "New Query", paste this entire script, and click "Run"
-- ================================================================

-- 1. HOTEL ROOM BOOKINGS TABLE
CREATE TABLE IF NOT EXISTS public.hotel_bookings (
    id BIGSERIAL PRIMARY KEY,
    booking_id TEXT UNIQUE NOT NULL,
    timestamp TEXT,
    guest_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    room_type TEXT,
    check_in TEXT,
    check_out TEXT,
    nights INTEGER DEFAULT 1,
    guests INTEGER DEFAULT 1,
    rate NUMERIC(10, 2) DEFAULT 0.00,
    total NUMERIC(10, 2) DEFAULT 0.00,
    payment_mode TEXT DEFAULT 'Pay upon Arrival',
    special_requests TEXT DEFAULT 'None',
    status TEXT DEFAULT 'Confirmed',
    linked_food_id TEXT DEFAULT 'N/A',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. CULINARY FOOD ORDERS TABLE
CREATE TABLE IF NOT EXISTS public.food_orders (
    id BIGSERIAL PRIMARY KEY,
    order_id TEXT UNIQUE NOT NULL,
    timestamp TEXT,
    customer_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    service_type TEXT DEFAULT 'Room Service',
    destination TEXT DEFAULT 'Room Suite',
    preferred_time TEXT DEFAULT 'Immediate',
    itemized_dishes TEXT,
    total_items INTEGER DEFAULT 1,
    subtotal NUMERIC(10, 2) DEFAULT 0.00,
    tax_service NUMERIC(10, 2) DEFAULT 0.00,
    grand_total NUMERIC(10, 2) DEFAULT 0.00,
    payment_mode TEXT DEFAULT 'Charge to Room / Upon Delivery',
    dietary_notes TEXT DEFAULT 'Standard',
    status TEXT DEFAULT 'Confirmed & Preparing',
    linked_room_id TEXT DEFAULT 'N/A',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. CUSTOMER REVIEWS TABLE
CREATE TABLE IF NOT EXISTS public.customer_reviews (
    id BIGSERIAL PRIMARY KEY,
    review_id TEXT UNIQUE NOT NULL,
    timestamp TEXT,
    guest_name TEXT NOT NULL,
    rating INTEGER DEFAULT 5,
    type TEXT DEFAULT 'Suite Stay & Dining',
    title TEXT DEFAULT 'Exceptional Hospitality',
    comment TEXT,
    status TEXT DEFAULT 'Approved',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CREATE INDEXES FOR FAST LOOKUP & LIVE TRACKING
CREATE INDEX IF NOT EXISTS idx_hotel_bookings_ref ON public.hotel_bookings (booking_id);
CREATE INDEX IF NOT EXISTS idx_food_orders_ref ON public.food_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_customer_reviews_ref ON public.customer_reviews (review_id);

-- ENABLE ROW LEVEL SECURITY (RLS)
ALTER TABLE public.hotel_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.food_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customer_reviews ENABLE ROW LEVEL SECURITY;

-- DROP OLD POLICIES IF EXIST (IDEMPOTENT)
DROP POLICY IF EXISTS "Allow all for anon on hotel_bookings" ON public.hotel_bookings;
DROP POLICY IF EXISTS "Allow all for anon on food_orders" ON public.food_orders;
DROP POLICY IF EXISTS "Allow all for anon on customer_reviews" ON public.customer_reviews;

-- CREATE OPEN POLICIES FOR SECURE API KEY ACCESS
CREATE POLICY "Allow all for anon on hotel_bookings" 
ON public.hotel_bookings 
FOR ALL 
TO anon, authenticated, service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow all for anon on food_orders" 
ON public.food_orders 
FOR ALL 
TO anon, authenticated, service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow all for anon on customer_reviews" 
ON public.customer_reviews 
FOR ALL 
TO anon, authenticated, service_role 
USING (true) 
WITH CHECK (true);

-- RELOAD POSTGREST API SCHEMA CACHE
NOTIFY pgrst, 'reload schema';

-- SUCCESS MESSAGE
SELECT 'THE SRM GRAND: Database Schema Initialized Successfully!' AS result;
