/**
 * THE SRM GRAND - LUXURY SUITES & HAUTE CUISINE
 * Unified Hotel and Food Booking Engine
 */

// Application State
let catalogData = { rooms: [], menu: [] };
let reviewsData = [];
let cart = {}; // { dishId: { ...dish, qty: 1 } }
let currentSelectedRoom = null;
let lastConfirmedReceipt = null; // Stores data for crisp professional printing

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initDatePickers();
    fetchCatalog();
    fetchReviews();
    initEventListeners();
    initTrackerFromUrl();
    renderRecentTrackerPills();
});

// Setup Default Dates (Today & Tomorrow)
function initDatePickers() {
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    const formatDate = (d) => d.toISOString().split('T')[0];

    const todayStr = formatDate(today);
    const tomorrowStr = formatDate(tomorrow);

    // Modal Room inputs
    const mCheckIn = document.getElementById('mCheckIn');
    const mCheckOut = document.getElementById('mCheckOut');
    if (mCheckIn && mCheckOut) {
        mCheckIn.min = todayStr;
        mCheckIn.value = todayStr;
        mCheckOut.min = tomorrowStr;
        mCheckOut.value = tomorrowStr;
    }

    // Unified Room inputs
    const uCheckIn = document.getElementById('uCheckIn');
    const uCheckOut = document.getElementById('uCheckOut');
    if (uCheckIn && uCheckOut) {
        uCheckIn.min = todayStr;
        uCheckIn.value = todayStr;
        uCheckOut.min = tomorrowStr;
        uCheckOut.value = tomorrowStr;

        uCheckIn.addEventListener('change', updateUnifiedSummary);
        uCheckOut.addEventListener('change', updateUnifiedSummary);
    }
}

// Fetch Catalog from Backend
async function fetchCatalog() {
    try {
        const response = await fetch('/api/catalog');
        if (!response.ok) throw new Error('Failed to load catalog');
        catalogData = await response.json();

        renderRooms(catalogData.rooms);
        renderMenu(catalogData.menu);
        initUnifiedPicker();
    } catch (err) {
        console.error('Catalog load error:', err);
        showToast('Unable to load latest suite & menu rates.', 'error');
    }
}

// Fetch Reviews from Backend
async function fetchReviews() {
    try {
        const response = await fetch('/api/reviews');
        if (!response.ok) return;
        const res = await response.json();
        if (res.success && res.reviews) {
            reviewsData = res.reviews;
            renderReviews(reviewsData);
        }
    } catch (err) {
        console.error('Reviews load error:', err);
    }
}

// Setup Event Listeners
function initEventListeners() {
    // Navigation Tabs
    const navTabs = document.querySelectorAll('.nav-tab-btn');
    navTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Room Category Filter
    const roomFilters = document.querySelectorAll('#roomFilterBar .filter-pill');
    roomFilters.forEach(pill => {
        pill.addEventListener('click', () => {
            roomFilters.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            const filter = pill.getAttribute('data-filter');
            if (filter === 'all') {
                renderRooms(catalogData.rooms);
            } else {
                const filtered = catalogData.rooms.filter(r => r.category === filter);
                renderRooms(filtered);
            }
        });
    });

    // Food Category Filter
    const foodFilters = document.querySelectorAll('#foodFilterBar .filter-pill');
    foodFilters.forEach(pill => {
        pill.addEventListener('click', () => {
            foodFilters.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            const filter = pill.getAttribute('data-food-filter');
            if (filter === 'all') {
                renderMenu(catalogData.menu);
            } else {
                const filtered = catalogData.menu.filter(m => m.category === filter);
                renderMenu(filtered);
            }
        });
    });

    // Cart Drawer Toggle
    const openCartBtn = document.getElementById('openCartBtn');
    if (openCartBtn) {
        openCartBtn.addEventListener('click', openCartDrawer);
    }

    // Unified Room Select change
    const uRoomSelect = document.getElementById('uRoomSelect');
    if (uRoomSelect) {
        uRoomSelect.addEventListener('change', updateUnifiedRoomPreview);
    }
}

// Switch Active Tab View
function switchTab(tabId) {
    document.querySelectorAll('.tab-content-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        }
    });

    const activePanel = document.getElementById(tabId);
    if (activePanel) {
        activePanel.classList.add('active');
        window.scrollTo({
            top: activePanel.offsetTop - 90,
            behavior: 'smooth'
        });
    }
}

// ==========================================
// RENDER ROOMS
// ==========================================
function renderRooms(rooms) {
    const container = document.getElementById('roomGridContainer');
    if (!container) return;

    container.innerHTML = rooms.map(room => `
        <div class="room-card" data-room-id="${room.id}">
            <div class="room-card-image-wrap">
                <img src="${room.image}" alt="${room.name}" loading="lazy">
                <div class="room-badge">${room.badge}</div>
                <div class="room-price-tag">
                    <span class="room-price-val">$${room.price}</span>
                    <span class="room-price-period">/ night</span>
                </div>
            </div>
            <div class="room-card-content">
                <h3 class="room-card-title">${room.name}</h3>
                <div class="room-specs-list">
                    <div class="spec-item"><i class="fa-solid fa-users"></i> ${room.capacity}</div>
                    <div class="spec-item"><i class="fa-solid fa-maximize"></i> ${room.size}</div>
                    <div class="spec-item"><i class="fa-solid fa-bed"></i> ${room.bed}</div>
                    <div class="spec-item"><i class="fa-solid fa-water"></i> ${room.view}</div>
                </div>
                <div class="room-amenities-pills">
                    ${room.amenities.slice(0, 4).map(a => `<span class="amenity-chip"><i class="fa-solid fa-check"></i> ${a}</span>`).join('')}
                </div>
                <div class="room-card-actions">
                    <button class="gold-button full-width" onclick="openRoomBookingModal('${room.id}')">
                        <i class="fa-solid fa-calendar-plus"></i> Reserve Suite
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// ==========================================
// RENDER FOOD MENU
// ==========================================
function renderMenu(menuItems) {
    const container = document.getElementById('foodGridContainer');
    if (!container) return;

    container.innerHTML = menuItems.map(dish => `
        <div class="food-card" data-food-id="${dish.id}">
            <div class="food-card-img-wrap">
                <img src="${dish.image}" alt="${dish.name}" loading="lazy">
                <div class="food-tag-badge">${dish.tag}</div>
            </div>
            <div class="food-card-content">
                <div class="food-card-header">
                    <h3 class="food-card-title">${dish.name}</h3>
                    <span class="food-card-price">$${dish.price.toFixed(2)}</span>
                </div>
                <p class="food-card-desc">${dish.description}</p>
                <div class="food-card-footer">
                    <span class="food-cal"><i class="fa-solid fa-fire"></i> ${dish.calories}</span>
                    <button class="add-food-btn" onclick="addToCart('${dish.id}')">
                        <i class="fa-solid fa-plus"></i> Add to Order
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// ==========================================
// RENDER REVIEWS
// ==========================================
function renderReviews(reviews) {
    const container = document.getElementById('reviewsGridContainer');
    if (!container) return;

    if (reviews.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#94a3b8; grid-column: 1/-1;">No reviews shared yet. Be the first to review!</p>';
        return;
    }

    container.innerHTML = reviews.map(rev => {
        const starsHtml = '★'.repeat(rev.rating) + '☆'.repeat(5 - rev.rating);
        const initial = rev.guest_name ? rev.guest_name.charAt(0).toUpperCase() : 'G';
        return `
            <div class="review-card">
                <div>
                    <div class="review-card-head">
                        <div class="star-rating">${starsHtml}</div>
                        <span class="review-type-badge">${rev.type || 'Verified Stay'}</span>
                    </div>
                    <h3 class="review-quote-title">"${rev.title}"</h3>
                    <p class="review-quote-body">${rev.comment}</p>
                </div>
                <div class="reviewer-meta">
                    <div class="reviewer-avatar">${initial}</div>
                    <div>
                        <div class="reviewer-name">${rev.guest_name}</div>
                        <div class="reviewer-verified">
                            <i class="fa-solid fa-circle-check"></i> Verified Guest Experience
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function openReviewModal() {
    document.getElementById('reviewModal').classList.add('active');
}

function closeReviewModal() {
    document.getElementById('reviewModal').classList.remove('active');
}

async function handleReviewSubmit(e) {
    e.preventDefault();
    const guest_name = document.getElementById('revGuestName').value.trim();
    const rating = document.getElementById('revRating').value;
    const type = document.getElementById('revType').value;
    const title = document.getElementById('revTitle').value.trim();
    const comment = document.getElementById('revComment').value.trim();

    try {
        const res = await fetch('/api/reviews', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ guest_name, rating, type, title, comment })
        });
        const result = await res.json();
        if (result.success) {
            closeReviewModal();
            document.getElementById('reviewForm').reset();
            showToast('Thank you! Your review has been added.', 'success');
            fetchReviews();
        } else {
            showToast(result.error || 'Failed to submit review', 'error');
        }
    } catch (err) {
        showToast('Network error while saving review', 'error');
    }
}

// ==========================================
// ROOM MODAL LOGIC
// ==========================================
function openRoomBookingModal(roomId) {
    const room = catalogData.rooms.find(r => r.id === roomId);
    if (!room) return;

    currentSelectedRoom = room;

    document.getElementById('modalRoomTitle').textContent = room.name;
    document.getElementById('modalRoomSubtitle').textContent = `${room.category} • ${room.view}`;
    document.getElementById('modalRoomImage').src = room.image;
    document.getElementById('modalRoomPrice').textContent = `$${room.price}`;

    const specsContainer = document.getElementById('modalRoomSpecs');
    specsContainer.innerHTML = `
        <span class="amenity-chip">${room.capacity}</span>
        <span class="amenity-chip">${room.size}</span>
        <span class="amenity-chip">${room.bed}</span>
    `;

    calculateRoomModalPrice();
    document.getElementById('roomBookingModal').classList.add('active');
}

function closeRoomModal() {
    document.getElementById('roomBookingModal').classList.remove('active');
}

function calculateRoomModalPrice() {
    if (!currentSelectedRoom) return;

    const checkInVal = document.getElementById('mCheckIn').value;
    const checkOutVal = document.getElementById('mCheckOut').value;

    const nights = calculateNights(checkInVal, checkOutVal);
    const total = nights * currentSelectedRoom.price;

    document.getElementById('mCalculatedNights').textContent = `${nights} ${nights === 1 ? 'Night' : 'Nights'}`;
    document.getElementById('mCalculatedTotal').textContent = `$${total.toFixed(2)}`;
}

async function handleRoomBookingSubmit(e) {
    e.preventDefault();

    if (!currentSelectedRoom) return;

    const checkIn = document.getElementById('mCheckIn').value;
    const checkOut = document.getElementById('mCheckOut').value;
    const nights = calculateNights(checkIn, checkOut);
    const guests = document.getElementById('mGuests').value;
    const payment = document.getElementById('mPayment').value;
    const guestName = document.getElementById('mGuestName').value.trim();
    const guestEmail = document.getElementById('mGuestEmail').value.trim();
    const guestPhone = document.getElementById('mGuestPhone').value.trim();
    const specialRequests = document.getElementById('mSpecialRequests').value.trim() || 'None';

    const payload = {
        room_type: currentSelectedRoom.name,
        room_id: currentSelectedRoom.id,
        price_per_night: currentSelectedRoom.price,
        check_in: checkIn,
        check_out: checkOut,
        nights: nights,
        guests: guests,
        total_amount: nights * currentSelectedRoom.price,
        payment_method: payment,
        guest_name: guestName,
        email: guestEmail,
        phone: guestPhone,
        special_requests: specialRequests
    };

    try {
        const response = await fetch('/api/book-room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (result.success) {
            closeRoomModal();
            displayRoomConfirmation(result.receipt, payload, result.notification);
            showToast('Room reservation confirmed! Receipt sent via Email & SMS.', 'success');
            document.getElementById('roomBookingForm').reset();
            initDatePickers();
        } else {
            showToast(result.error || 'Failed to submit booking', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error while booking room', 'error');
    }
}

// ==========================================
// CART & FOOD ORDER LOGIC
// ==========================================
function addToCart(dishId) {
    const dish = catalogData.menu.find(m => m.id === dishId);
    if (!dish) return;

    if (cart[dishId]) {
        cart[dishId].qty += 1;
    } else {
        cart[dishId] = { ...dish, qty: 1 };
    }

    updateCartUI();
    showToast(`Added ${dish.name} to Dining Tray`, 'success');
}

function modifyCartQty(dishId, delta) {
    if (!cart[dishId]) return;

    cart[dishId].qty += delta;
    if (cart[dishId].qty <= 0) {
        delete cart[dishId];
    }
    updateCartUI();
}

function removeFromCart(dishId) {
    delete cart[dishId];
    updateCartUI();
}

function updateCartUI() {
    const cartItems = Object.values(cart);
    const totalCount = cartItems.reduce((acc, item) => acc + item.qty, 0);

    document.getElementById('cartBadgeCount').textContent = totalCount;

    const listContainer = document.getElementById('cartItemsContainer');
    const emptyState = document.getElementById('emptyCartState');
    const orderForm = document.getElementById('orderFulfillmentForm');

    if (cartItems.length === 0) {
        listContainer.innerHTML = '';
        emptyState.classList.add('active');
        orderForm.style.display = 'none';
    } else {
        emptyState.classList.remove('active');
        orderForm.style.display = 'block';

        listContainer.innerHTML = cartItems.map(item => `
            <div class="cart-item-card">
                <div class="cart-item-info">
                    <div class="cart-item-title">${item.name}</div>
                    <div class="cart-item-price">$${(item.price * item.qty).toFixed(2)} ($${item.price} ea)</div>
                </div>
                <div class="cart-qty-ctrl">
                    <button class="qty-btn" type="button" onclick="modifyCartQty('${item.id}', -1)">-</button>
                    <span class="qty-val">${item.qty}</span>
                    <button class="qty-btn" type="button" onclick="modifyCartQty('${item.id}', 1)">+</button>
                </div>
                <button class="cart-item-delete" type="button" onclick="removeFromCart('${item.id}')" title="Remove">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `).join('');
    }

    const subtotal = cartItems.reduce((acc, item) => acc + (item.price * item.qty), 0);
    const taxService = subtotal * 0.10;
    const grandTotal = subtotal + taxService;

    document.getElementById('drawerSubtotal').textContent = `$${subtotal.toFixed(2)}`;
    document.getElementById('drawerTax').textContent = `$${taxService.toFixed(2)}`;
    document.getElementById('drawerGrandTotal').textContent = `$${grandTotal.toFixed(2)}`;
}

function openCartDrawer() {
    document.getElementById('cartDrawer').classList.add('active');
    document.getElementById('cartDrawerBackdrop').classList.add('active');
}

function closeCartDrawer() {
    document.getElementById('cartDrawer').classList.remove('active');
    document.getElementById('cartDrawerBackdrop').classList.remove('active');
}

function toggleServiceType(serviceType) {
    const destLabel = document.getElementById('destLabel');
    const destInput = document.getElementById('foodDestNumber');

    document.querySelectorAll('.service-type-toggle .toggle-option').forEach(opt => {
        opt.classList.remove('active');
        if (opt.querySelector('input').value === serviceType) {
            opt.classList.add('active');
        }
    });

    if (serviceType === 'Room Service') {
        destLabel.innerHTML = '<i class="fa-solid fa-door-closed"></i> Suite / Room Number';
        destInput.placeholder = 'e.g. Suite 402 or Villa 07';
    } else {
        destLabel.innerHTML = '<i class="fa-solid fa-chair"></i> Dining Table Number / Preference';
        destInput.placeholder = 'e.g. Ocean Terrace Table #4';
    }
}

async function handleFoodOrderSubmit(e) {
    e.preventDefault();

    const items = Object.values(cart);
    if (items.length === 0) {
        showToast('Your dining tray is empty', 'error');
        return;
    }

    const serviceType = document.querySelector('input[name="serviceType"]:checked').value;
    const destinationNumber = document.getElementById('foodDestNumber').value.trim();
    const preferredTime = document.getElementById('foodServingTime').value;
    const customerName = document.getElementById('foodCustomerName').value.trim();
    const customerPhone = document.getElementById('foodCustomerPhone').value.trim();
    const customerEmail = document.getElementById('foodCustomerEmail').value.trim() || 'N/A';
    const dietaryNotes = document.getElementById('foodDietaryNotes').value.trim() || 'Standard';

    const subtotal = items.reduce((acc, item) => acc + (item.price * item.qty), 0);
    const taxService = subtotal * 0.10;
    const grandTotal = subtotal + taxService;

    const payload = {
        customer_name: customerName,
        phone: customerPhone,
        email: customerEmail,
        service_type: serviceType,
        destination_number: destinationNumber,
        preferred_time: preferredTime,
        dietary_notes: dietaryNotes,
        subtotal: subtotal,
        tax_service: taxService,
        grand_total: grandTotal,
        payment_method: serviceType === 'Room Service' ? 'Charge to Suite Folio' : 'Pay at Table',
        items: items.map(i => ({ name: i.name, qty: i.qty, price: i.price }))
    };

    try {
        const response = await fetch('/api/order-food', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (result.success) {
            closeCartDrawer();
            cart = {};
            updateCartUI();
            displayFoodConfirmation(result.receipt, payload, result.notification);
            showToast('Culinary order placed! Receipt dispatched to your email & SMS.', 'success');
            document.getElementById('orderFulfillmentForm').reset();
        } else {
            showToast(result.error || 'Failed to place dining order', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error while placing dining order', 'error');
    }
}

// ==========================================
// UNIFIED 2-IN-1 BOOKING SECTION LOGIC
// ==========================================
function initUnifiedPicker() {
    const pickerContainer = document.getElementById('unifiedMenuPicker');
    if (!pickerContainer || !catalogData.menu) return;

    pickerContainer.innerHTML = catalogData.menu.map(dish => `
        <div class="menu-picker-item" onclick="toggleUnifiedMenuItem(this, '${dish.id}')">
            <div class="picker-left">
                <input type="checkbox" class="picker-checkbox" id="up_${dish.id}" value="${dish.id}" onchange="updateUnifiedSummary(event)">
                <div>
                    <div class="picker-title">${dish.name}</div>
                    <div class="picker-subtitle">${dish.tag} • ${dish.calories}</div>
                </div>
            </div>
            <div class="picker-price">+$${dish.price.toFixed(2)}</div>
        </div>
    `).join('');

    updateUnifiedRoomPreview();
    updateUnifiedSummary();
}

function toggleUnifiedMenuItem(cardElement, dishId) {
    const checkbox = document.getElementById(`up_${dishId}`);
    if (!checkbox) return;

    if (event.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
    }
    cardElement.classList.toggle('selected', checkbox.checked);
    updateUnifiedSummary();
}

function updateUnifiedRoomPreview() {
    const select = document.getElementById('uRoomSelect');
    if (!select || !catalogData.rooms) return;

    const roomId = select.value;
    const room = catalogData.rooms.find(r => r.id === roomId);
    if (!room) return;

    document.getElementById('uRoomPreviewImg').src = room.image;
    document.getElementById('uRoomPreviewTitle').textContent = room.name;
    document.getElementById('uRoomPreviewCost').textContent = `$${room.price} / night • ${room.view}`;

    updateUnifiedSummary();
}

function updateUnifiedSummary() {
    const select = document.getElementById('uRoomSelect');
    if (!select || !catalogData.rooms) return;

    const room = catalogData.rooms.find(r => r.id === select.value);
    const roomRate = room ? room.price : 620;

    const checkIn = document.getElementById('uCheckIn').value;
    const checkOut = document.getElementById('uCheckOut').value;
    const nights = calculateNights(checkIn, checkOut);

    document.getElementById('uNightsDisplay').value = `${nights} ${nights === 1 ? 'Night' : 'Nights'}`;

    const roomTotal = nights * roomRate;

    const checkboxes = document.querySelectorAll('.unified-menu-picker .picker-checkbox:checked');
    let foodSubtotal = 0;
    checkboxes.forEach(cb => {
        const dish = catalogData.menu.find(m => m.id === cb.value);
        if (dish) foodSubtotal += dish.price;
    });

    const foodTax = foodSubtotal * 0.10;
    const foodTotal = foodSubtotal + foodTax;
    const combinedTotal = roomTotal + foodTotal;

    document.getElementById('uSummaryRoomCost').textContent = `$${roomTotal.toFixed(2)}`;
    document.getElementById('uSummaryFoodCost').textContent = `$${foodTotal.toFixed(2)}`;
    document.getElementById('uSummaryGrandTotal').textContent = `$${combinedTotal.toFixed(2)}`;
}

async function submitUnifiedBooking() {
    const guestName = document.getElementById('uGuestName').value.trim();
    const guestEmail = document.getElementById('uGuestEmail').value.trim();
    const guestPhone = document.getElementById('uGuestPhone').value.trim();

    if (!guestName || !guestEmail || !guestPhone) {
        showToast('Please fill in guest name, email, and mobile phone', 'error');
        return;
    }

    const select = document.getElementById('uRoomSelect');
    const room = catalogData.rooms.find(r => r.id === select.value);
    const checkIn = document.getElementById('uCheckIn').value;
    const checkOut = document.getElementById('uCheckOut').value;
    const nights = calculateNights(checkIn, checkOut);
    const guests = document.getElementById('uGuests').value;

    const roomTotal = nights * room.price;

    const checkboxes = document.querySelectorAll('.unified-menu-picker .picker-checkbox:checked');
    const selectedDishes = [];
    checkboxes.forEach(cb => {
        const dish = catalogData.menu.find(m => m.id === cb.value);
        if (dish) {
            selectedDishes.push({ name: dish.name, qty: 1, price: dish.price });
        }
    });

    const foodSubtotal = selectedDishes.reduce((acc, d) => acc + d.price, 0);
    const foodTax = foodSubtotal * 0.10;
    const foodGrandTotal = foodSubtotal + foodTax;

    const servingTime = document.getElementById('uDiningTime').value;
    const dietaryNotes = document.getElementById('uDietaryNotes').value.trim() || 'Standard';

    const payload = {
        room: {
            guest_name: guestName,
            email: guestEmail,
            phone: guestPhone,
            room_type: room.name,
            room_id: room.id,
            price_per_night: room.price,
            check_in: checkIn,
            check_out: checkOut,
            nights: nights,
            guests: guests,
            total_amount: roomTotal,
            payment_method: 'Unified Stay & Dine Card Guarantee',
            special_requests: `Accompanied by welcome dining order (${selectedDishes.length} courses)`
        },
        food: {
            customer_name: guestName,
            phone: guestPhone,
            email: guestEmail,
            items: selectedDishes.length > 0 ? selectedDishes : [{ name: 'Executive Welcome Beverage Package', qty: 1, price: 0 }],
            preferred_time: servingTime,
            dietary_notes: dietaryNotes,
            subtotal: foodSubtotal,
            tax_service: foodTax,
            grand_total: foodGrandTotal
        }
    };

    try {
        const response = await fetch('/api/book-unified', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (result.success) {
            displayUnifiedConfirmation(result.receipt, payload, result.notification);
            showToast('Stay & Dine booked! Dispatched via Email & SMS.', 'success');

            document.querySelectorAll('.unified-menu-picker .picker-checkbox').forEach(cb => {
                cb.checked = false;
            });
            document.querySelectorAll('.menu-picker-item').forEach(el => el.classList.remove('selected'));
            updateUnifiedSummary();
        } else {
            showToast(result.error || 'Failed to complete unified booking', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error while processing unified booking', 'error');
    }
}

// ==========================================
// CONFIRMATION MODALS (STRICT NO-PUBLIC DATA)
// ==========================================
function renderDispatchAlert(notification, email, phone) {
    const box = document.getElementById('certDispatchBox');
    if (!box) return;

    box.innerHTML = `
        <div class="dispatch-row">
            <div class="dispatch-row-left">
                <i class="fa-solid fa-envelope-circle-check"></i>
                <span>Official Receipt Emailed to: <strong>${email}</strong></span>
            </div>
            <span class="dispatch-status-badge">&#10003; DELIVERED</span>
        </div>
        <div class="dispatch-row">
            <div class="dispatch-row-left">
                <i class="fa-solid fa-mobile-screen-button"></i>
                <span>Instant SMS Alert Dispatched to: <strong>${phone}</strong></span>
            </div>
            <span class="dispatch-status-badge">&#10003; DISPATCHED</span>
        </div>
    `;
}

function displayRoomConfirmation(receipt, payload, notification) {
    lastConfirmedReceipt = { type: 'room', receipt, payload, notification };
    const certBody = document.getElementById('certBodyContent');
    certBody.innerHTML = `
        <div class="cert-grid-2">
            <div class="cert-detail-item">
                <small>Booking Reference ID</small>
                <strong class="cert-reference-code">${receipt.booking_id}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Reservation Date</small>
                <strong>${receipt.timestamp}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Primary Guest</small>
                <strong>${payload.guest_name}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Accommodations</small>
                <strong>${payload.room_type}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Stay Period</small>
                <strong>${payload.check_in} &rarr; ${payload.check_out} (${payload.nights} Nights)</strong>
            </div>
            <div class="cert-detail-item">
                <small>Total Accommodation Fee</small>
                <strong class="gold-gradient-text" style="font-size: 1.25rem;">$${payload.total_amount.toFixed(2)}</strong>
            </div>
        </div>
    `;

    renderDispatchAlert(notification, payload.email, payload.phone);
    if (receipt && receipt.booking_id) {
        saveRecentTrackerId(receipt.booking_id);
    }
    document.getElementById('confirmationModal').classList.add('active');
}

function displayFoodConfirmation(receipt, payload, notification) {
    lastConfirmedReceipt = { type: 'food', receipt, payload, notification };
    const certBody = document.getElementById('certBodyContent');
    const itemsSummary = payload.items.map(i => `${i.qty}x ${i.name} ($${(i.price * i.qty).toFixed(2)})`).join(', ');

    certBody.innerHTML = `
        <div class="cert-grid-2">
            <div class="cert-detail-item">
                <small>Dining Order Reference ID</small>
                <strong class="cert-reference-code">${receipt.order_id}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Order Timestamp</small>
                <strong>${receipt.timestamp}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Guest Name</small>
                <strong>${payload.customer_name}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Fulfillment Type</small>
                <strong>${payload.service_type} (${payload.destination_number})</strong>
            </div>
            <div class="cert-detail-item">
                <small>Scheduled Service</small>
                <strong>${payload.preferred_time}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Culinary Total (incl. 10% svc)</small>
                <strong class="gold-gradient-text" style="font-size: 1.25rem;">$${payload.grand_total.toFixed(2)}</strong>
            </div>
        </div>
        <div class="cert-items-box">
            <small style="display:block; color: #94a3b8; font-size: 0.72rem; text-transform: uppercase; margin-bottom: 0.3rem;">Order Summary</small>
            <p style="font-size: 0.88rem; color: #f8fafc;">${itemsSummary}</p>
        </div>
    `;

    renderDispatchAlert(notification, payload.email || 'guest@residence.com', payload.phone);
    if (receipt && receipt.order_id) {
        saveRecentTrackerId(receipt.order_id);
    }
    document.getElementById('confirmationModal').classList.add('active');
}

function displayUnifiedConfirmation(receipt, payload, notification) {
    lastConfirmedReceipt = { type: 'unified', receipt, payload, notification };
    const certBody = document.getElementById('certBodyContent');
    certBody.innerHTML = `
        <div class="cert-grid-2">
            <div class="cert-detail-item">
                <small>Suite Booking Reference</small>
                <strong class="cert-reference-code">${receipt.room_booking_id}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Dining Order Reference</small>
                <strong class="cert-reference-code">${receipt.food_order_id}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Distinguished Guest</small>
                <strong>${payload.room.guest_name}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Selected Suite</small>
                <strong>${payload.room.room_type}</strong>
            </div>
            <div class="cert-detail-item">
                <small>Stay Duration</small>
                <strong>${payload.room.check_in} &rarr; ${payload.room.check_out} (${payload.room.nights} Nights)</strong>
            </div>
            <div class="cert-detail-item">
                <small>Dining Serving Time</small>
                <strong>${payload.food.preferred_time}</strong>
            </div>
        </div>

        <div class="cert-items-box">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.88rem; color: #94a3b8;">
                <span>Room Subtotal:</span>
                <strong style="color:#fff;">$${payload.room.total_amount.toFixed(2)}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem; font-size: 0.88rem; color: #94a3b8;">
                <span>Dining Package Total:</span>
                <strong style="color:#fff;">$${payload.food.grand_total.toFixed(2)}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.08); font-size: 1.15rem;">
                <span style="color:#fff; font-weight:700;">Grand Combined Total:</span>
                <strong class="gold-gradient-text" style="font-size:1.35rem;">$${(payload.room.total_amount + payload.food.grand_total).toFixed(2)}</strong>
            </div>
        </div>
    `;

    renderDispatchAlert(notification, payload.room.email, payload.room.phone);
    if (receipt) {
        if (receipt.room_booking_id) saveRecentTrackerId(receipt.room_booking_id);
        if (receipt.food_order_id) saveRecentTrackerId(receipt.food_order_id);
    }
    document.getElementById('confirmationModal').classList.add('active');
}

function closeConfirmationModal() {
    document.getElementById('confirmationModal').classList.remove('active');
}

function trackFromVoucher() {
    if (!lastConfirmedReceipt) return;
    let refId = null;
    if (lastConfirmedReceipt.type === 'room') {
        refId = lastConfirmedReceipt.receipt.booking_id;
    } else if (lastConfirmedReceipt.type === 'food') {
        refId = lastConfirmedReceipt.receipt.order_id;
    } else if (lastConfirmedReceipt.type === 'unified') {
        refId = lastConfirmedReceipt.receipt.room_booking_id || lastConfirmedReceipt.receipt.food_order_id;
    }
    closeConfirmationModal();
    if (refId) {
        switchTab('tracking-section');
        const input = document.getElementById('trackerInput');
        if (input) input.value = refId;
        trackReservation(refId);
    }
}

// ==========================================
// BULLETPROOF PRINTABLE INVOICE / RECEIPT
// ==========================================
function printOfficialReceipt() {
    if (!lastConfirmedReceipt) {
        window.print();
        return;
    }

    const { type, receipt, payload } = lastConfirmedReceipt;
    let guestName = "Valued Guest";
    let email = "N/A";
    let phone = "N/A";
    let refId = "AUR-RES-2026";
    let dateStr = new Date().toLocaleString();
    let tableRowsHtml = "";
    let subtotal = 0;
    let tax = 0;
    let grandTotal = 0;

    if (type === 'room') {
        guestName = payload.guest_name;
        email = payload.email;
        phone = payload.phone;
        refId = receipt.booking_id;
        dateStr = receipt.timestamp;
        subtotal = payload.total_amount;
        tax = 0;
        grandTotal = payload.total_amount;

        tableRowsHtml = `
            <tr>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb;">
                    <strong>${payload.room_type}</strong><br>
                    <small style="color:#6b7280;">Stay: ${payload.check_in} to ${payload.check_out} &bull; ${payload.guests} Guests</small>
                </td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:center;">${payload.nights} Nights</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right;">$${payload.price_per_night.toFixed(2)}</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right; font-weight:bold;">$${payload.total_amount.toFixed(2)}</td>
            </tr>
        `;
    } else if (type === 'food') {
        guestName = payload.customer_name;
        email = payload.email || 'N/A';
        phone = payload.phone;
        refId = receipt.order_id;
        dateStr = receipt.timestamp;
        subtotal = payload.subtotal;
        tax = payload.tax_service;
        grandTotal = payload.grand_total;

        tableRowsHtml = payload.items.map(item => `
            <tr>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb;">
                    <strong>${item.name}</strong><br>
                    <small style="color:#6b7280;">Delivery: ${payload.service_type} (${payload.destination_number}) &bull; ${payload.preferred_time}</small>
                </td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:center;">${item.qty}</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right;">$${item.price.toFixed(2)}</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right; font-weight:bold;">$${(item.price * item.qty).toFixed(2)}</td>
            </tr>
        `).join('');
    } else if (type === 'unified') {
        guestName = payload.room.guest_name;
        email = payload.room.email;
        phone = payload.room.phone;
        refId = `${receipt.room_booking_id} / ${receipt.food_order_id}`;
        dateStr = new Date().toLocaleString();
        subtotal = payload.room.total_amount + payload.food.subtotal;
        tax = payload.food.tax_service;
        grandTotal = payload.room.total_amount + payload.food.grand_total;

        tableRowsHtml = `
            <tr>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb;">
                    <strong>${payload.room.room_type}</strong><br>
                    <small style="color:#6b7280;">Stay: ${payload.room.check_in} to ${payload.room.check_out} &bull; ${payload.room.guests} Guests</small>
                </td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:center;">${payload.room.nights} Nights</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right;">$${payload.room.price_per_night.toFixed(2)}</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right; font-weight:bold;">$${payload.room.total_amount.toFixed(2)}</td>
            </tr>
            <tr>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb;">
                    <strong>Curated In-Room Dining Experience</strong><br>
                    <small style="color:#6b7280;">Serving Time: ${payload.food.preferred_time} &bull; ${payload.food.items.length} Courses</small>
                </td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:center;">1 Package</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right;">$${payload.food.subtotal.toFixed(2)}</td>
                <td style="padding:12px; border-bottom:1px solid #e5e7eb; text-align:right; font-weight:bold;">$${payload.food.subtotal.toFixed(2)}</td>
            </tr>
        `;
    }

    const printHtml = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Receipt - ${refId}</title>
        <style>
            @page { size: A4; margin: 15mm; }
            body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #111827; background: #ffffff; margin: 0; padding: 20px; }
            .invoice-box { max-width: 800px; margin: 0 auto; border: 1px solid #e5e7eb; padding: 30px; border-radius: 8px; }
            .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #b45309; padding-bottom: 20px; margin-bottom: 25px; }
            .hotel-brand h1 { margin: 0; font-size: 26px; color: #b45309; letter-spacing: 1px; font-family: Georgia, serif; }
            .hotel-brand p { margin: 4px 0 0; color: #4b5563; font-size: 13px; }
            .invoice-title { text-align: right; }
            .invoice-title h2 { margin: 0; font-size: 20px; color: #111827; }
            .invoice-title p { margin: 4px 0 0; font-size: 13px; color: #6b7280; }
            .meta-grid { display: flex; justify-content: space-between; margin-bottom: 25px; font-size: 14px; }
            .meta-col { width: 48%; }
            .meta-col strong { color: #111827; }
            .items-table { width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 14px; }
            .items-table th { background: #f9fafb; padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb; color: #374151; }
            .totals-table { width: 45%; margin-left: auto; border-collapse: collapse; margin-bottom: 30px; font-size: 14px; }
            .totals-table td { padding: 8px 12px; }
            .grand-total { border-top: 2px solid #b45309; font-size: 18px; font-weight: bold; color: #b45309; }
            .footer { border-top: 1px solid #e5e7eb; padding-top: 20px; text-align: center; font-size: 12px; color: #6b7280; }
            .paid-stamp { display: inline-block; border: 2px solid #16a34a; color: #16a34a; padding: 6px 14px; font-weight: bold; border-radius: 4px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="invoice-box">
            <div class="header">
                <div class="hotel-brand">
                    <h1>THE SRM GRAND</h1>
                    <p>PALACE SUITES & HAUTE CUISINE</p>
                    <p>1000 Oceanfront Promenade &bull; Concierge: +1 (800) 555-SRM-GRAND</p>
                </div>
                <div class="invoice-title">
                    <h2>OFFICIAL RECEIPT</h2>
                    <p><strong>Folio #:</strong> ${refId}</p>
                    <p><strong>Issued:</strong> ${dateStr}</p>
                </div>
            </div>

            <div class="meta-grid">
                <div class="meta-col">
                    <p style="margin:0 0 6px 0; color:#6b7280; font-size:12px; text-transform:uppercase;">Guest Information</p>
                    <p style="margin:0; font-size:16px;"><strong>${guestName}</strong></p>
                    <p style="margin:4px 0 0; color:#4b5563;">Email: ${email}</p>
                    <p style="margin:4px 0 0; color:#4b5563;">Phone: ${phone}</p>
                </div>
                <div class="meta-col" style="text-align:right;">
                    <div class="paid-stamp">&#10003; PAYMENT CONFIRMED</div>
                    <p style="margin:0; color:#4b5563;">Payment Guarantee: Verified Card Portfolio</p>
                    <p style="margin:4px 0 0; color:#4b5563;">Status: Active Reservation</p>
                </div>
            </div>

            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width:55%;">Description</th>
                        <th style="text-align:center;">Qty / Duration</th>
                        <th style="text-align:right;">Rate</th>
                        <th style="text-align:right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRowsHtml}
                </tbody>
            </table>

            <table class="totals-table">
                <tr>
                    <td>Subtotal:</td>
                    <td style="text-align:right;">$${subtotal.toFixed(2)}</td>
                </tr>
                ${tax > 0 ? `
                <tr>
                    <td>Service Fee & Tax (10%):</td>
                    <td style="text-align:right;">$${tax.toFixed(2)}</td>
                </tr>
                ` : ''}
                <tr class="grand-total">
                    <td>Total Paid:</td>
                    <td style="text-align:right;">$${grandTotal.toFixed(2)}</td>
                </tr>
            </table>

            <div class="footer">
                <p>Thank you for choosing The SRM Grand Resort. All reservation records are archived securely in property ledgers.</p>
                <p>Check-In: 3:00 PM &bull; Check-Out: 12:00 PM &bull; Valet & Private Butler Included</p>
            </div>
        </div>
        <script>
            window.onload = function() {
                window.focus();
                window.print();
            };
        </script>
    </body>
    </html>
    `;

    const printWin = window.open('', '_blank', 'width=850,height=900,menubar=no,toolbar=no,location=no,status=no');
    if (printWin) {
        printWin.document.open();
        printWin.document.write(printHtml);
        printWin.document.close();
    } else {
        // Fallback if popup blocker intercepted
        window.print();
    }
}

// Helpers
function calculateNights(checkInStr, checkOutStr) {
    if (!checkInStr || !checkOutStr) return 1;
    const d1 = new Date(checkInStr);
    const d2 = new Date(checkOutStr);
    const diffTime = d2.getTime() - d1.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 1;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-triangle-exclamation' : 'fa-bell')}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==========================================
// SECTION 5: LIVE ORDER & RESERVATION TRACKER
// ==========================================

function initTrackerFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const trackId = urlParams.get('track');
    if (trackId && trackId.trim()) {
        const cleanId = trackId.trim().toUpperCase();
        switchTab('tracking-section');
        const input = document.getElementById('trackerInput');
        if (input) input.value = cleanId;
        trackReservation(cleanId);
    }
}

function executeTrackingSearch() {
    const input = document.getElementById('trackerInput');
    if (!input) return;
    const refId = input.value.trim().toUpperCase();
    if (!refId) {
        showToast('Please enter a valid Reference ID to track', 'info');
        input.focus();
        return;
    }
    trackReservation(refId);
}

function saveRecentTrackerId(refId) {
    try {
        if (!refId) return;
        let recents = JSON.parse(localStorage.getItem('aurora_recent_tracks') || '[]');
        if (!recents.includes(refId)) {
            recents.unshift(refId);
            if (recents.length > 5) recents.pop();
            localStorage.setItem('aurora_recent_tracks', JSON.stringify(recents));
        }
        renderRecentTrackerPills();
    } catch (e) {
        console.warn('Storage warning:', e);
    }
}

function renderRecentTrackerPills() {
    const container = document.getElementById('recentTrackingPills');
    if (!container) return;
    try {
        const recents = JSON.parse(localStorage.getItem('aurora_recent_tracks') || '[]');
        if (recents.length === 0) {
            container.innerHTML = '';
            return;
        }
        container.innerHTML = `
            <span style="font-size:0.75rem; color:#64748b; margin-left:0.5rem;">Recent:</span>
            ${recents.map(id => `
                <button type="button" class="recent-pill-btn" onclick="quickTrack('${id}')">${id}</button>
            `).join('')}
        `;
    } catch (e) {
        container.innerHTML = '';
    }
}

function quickTrack(refId) {
    const input = document.getElementById('trackerInput');
    if (input) input.value = refId;
    trackReservation(refId);
}

async function trackReservation(refId, isSilentRefresh = false) {
    const input = document.getElementById('trackerInput');
    if (input && !input.value) input.value = refId;

    const initialEl = document.getElementById('trackerInitialState');
    const activeCard = document.getElementById('trackerActiveCard');
    const refreshBtn = document.getElementById('btnTrackerRefresh');

    if (refreshBtn) refreshBtn.classList.add('spinning');

    try {
        const res = await fetch(`/api/track/${encodeURIComponent(refId)}`);
        const data = await res.json();

        if (refreshBtn) refreshBtn.classList.remove('spinning');

        if (!res.ok || !data.success) {
            if (initialEl) initialEl.style.display = 'block';
            if (activeCard) activeCard.style.display = 'none';
            showToast(data.error || `No booking found matching reference ${refId}`, 'error');
            return;
        }

        saveRecentTrackerId(refId);

        const b = data.booking;
        const currentStep = data.current_step || 1;
        const milestones = data.milestones || [];

        // Progress percentage: step 1 -> 15%, step 2 -> 45%, step 3 -> 75%, step 4 -> 100%
        const progressPct = currentStep === 1 ? 15 : (currentStep === 2 ? 45 : (currentStep === 3 ? 75 : 100));

        if (initialEl) initialEl.style.display = 'none';
        if (activeCard) {
            activeCard.style.display = 'block';
            renderTrackerActiveCard(b, currentStep, milestones, progressPct);
        }

        if (!isSilentRefresh) {
            showToast(`Tracking loaded: Status is '${b.status}'`, 'success');
        }

    } catch (err) {
        if (refreshBtn) refreshBtn.classList.remove('spinning');
        console.error('Tracking fetch error:', err);
        showToast('Unable to connect to live tracking service.', 'error');
    }
}

function renderTrackerActiveCard(booking, currentStep, milestones, progressPct) {
    const activeCard = document.getElementById('trackerActiveCard');
    if (!activeCard) return;

    const isRoom = booking.type === 'room';
    const typeLabel = isRoom ? 'Palace Suite Reservation' : 'Gourmet In-Room Dining';
    const typeClass = isRoom ? 'room' : 'food';
    const primaryName = booking.guest_name || booking.customer_name || 'Valued Guest';

    const nodesHtml = milestones.map((m, idx) => {
        const stepNum = idx + 1;
        let nodeClass = 'pending';
        let stepTag = `Milestone 0${stepNum}`;
        let statusText = 'Pending';

        if (stepNum < currentStep) {
            nodeClass = 'completed';
            statusText = 'Completed';
        } else if (stepNum === currentStep) {
            nodeClass = 'active';
            statusText = 'In Progress';
        }

        return `
            <div class="stepper-node ${nodeClass}">
                <div class="node-icon-circle">
                    <i class="fa-solid ${m.icon}"></i>
                </div>
                <div class="node-step-tag">${statusText}</div>
                <div class="node-title">${m.title}</div>
                <div class="node-desc">${m.desc}</div>
            </div>
        `;
    }).join('');

    const detailsGridHtml = isRoom ? `
        <div class="info-item">
            <small><i class="fa-solid fa-user"></i> Primary Guest</small>
            <strong>${booking.guest_name}</strong>
        </div>
        <div class="info-item">
            <small><i class="fa-solid fa-hotel"></i> Residence Suite</small>
            <strong>${booking.title}</strong>
        </div>
        <div class="info-item">
            <small><i class="fa-regular fa-calendar-check"></i> Stay Period</small>
            <strong>${booking.check_in} &rarr; ${booking.check_out} (${booking.nights}N)</strong>
        </div>
        <div class="info-item">
            <small><i class="fa-solid fa-gem"></i> Total Ledger Amount</small>
            <strong class="highlight">$${booking.total.toFixed(2)}</strong>
        </div>
    ` : `
        <div class="info-item">
            <small><i class="fa-solid fa-user"></i> Dining Guest</small>
            <strong>${booking.customer_name}</strong>
        </div>
        <div class="info-item">
            <small><i class="fa-solid fa-utensils"></i> Service & Destination</small>
            <strong>${booking.service_type} (${booking.destination})</strong>
        </div>
        <div class="info-item">
            <small><i class="fa-regular fa-clock"></i> Scheduled Time</small>
            <strong>${booking.time}</strong>
        </div>
        <div class="info-item">
            <small><i class="fa-solid fa-receipt"></i> Total Order Amount</small>
            <strong class="highlight">$${booking.total.toFixed(2)}</strong>
        </div>
    `;

    activeCard.innerHTML = `
        <div class="tracker-top-banner">
            <div class="tracker-title-group">
                <h3>
                    <span class="tracker-type-pill ${typeClass}">${typeLabel}</span>
                    <span class="tracker-ref-display">${booking.id}</span>
                </h3>
                <p style="color:#94a3b8; font-size:0.85rem; margin:0;">
                    Booked on <strong>${booking.timestamp}</strong> &bull; Current Status: <span style="color:#34d399; font-weight:700;">${booking.status}</span>
                </p>
            </div>
            <div class="tracker-banner-actions">
                <button type="button" class="btn-refresh-status" id="btnTrackerRefresh" onclick="trackReservation('${booking.id}', false)">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>Refresh Live</span>
                </button>
            </div>
        </div>

        <!-- 4-Step Milestone Timeline Stepper -->
        <div class="timeline-stepper-wrap">
            <div class="stepper-progress-bar">
                <div class="stepper-progress-fill" style="width: ${progressPct}%;"></div>
            </div>
            <div class="stepper-nodes">
                ${nodesHtml}
            </div>
        </div>

        <!-- Booking Specs Grid -->
        <div class="tracker-info-grid">
            ${detailsGridHtml}
        </div>

        <div class="tracker-bottom-actions">
            <div style="font-size:0.8rem; color:#64748b;">
                <i class="fa-solid fa-lock" style="color:var(--gold-light);"></i> Confidential Record &bull; Stored privately in property Excel database
            </div>
            <button class="gold-outline-button" onclick="window.print()">
                <i class="fa-solid fa-print"></i> Print Status Folio
            </button>
        </div>
    `;
}

