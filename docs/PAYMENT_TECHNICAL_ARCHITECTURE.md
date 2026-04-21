# Payment System - Technical Implementation Guide

## Architecture Overview

The payment system integrates with the existing order workflow using Django's class-based and function-based views with OneToOneField relationships to ensure data integrity.

```
┌─────────────────────────────────────────────────────────────┐
│                    BUYER FLOW                               │
├─────────────────────────────────────────────────────────────┤
│ buyer/dashboard          → View pending payments            │
│ buyer/orders             → Click "Pay Now" button           │
│ buyer/payment/<id>/      → Select payment method            │
│ buyer/payment/cod/<id>/  → View COD breakdown              │
│ payment/success/<id>/    → Confirmation receipt            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  PAYMENT MODELS                             │
├─────────────────────────────────────────────────────────────┤
│ Payment (OneToOne with Order)                              │
│ ├─ order: OneToOneField                                   │
│ ├─ payment_method: CharField (cod/sslcommerz)            │
│ ├─ status: CharField (pending/completed/failed)          │
│ ├─ total_amount: DecimalField                            │
│ ├─ paid_amount: DecimalField                             │
│ └─ timestamps: DateTimeField                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   FARMER FLOW                               │
├─────────────────────────────────────────────────────────────┤
│ farmer/orders            → View order with payment badge   │
│ farmer/order/<id>/       → See payment status card         │
│ order_detail@farmer      → Decide when to ship            │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
AgriGenie/
├── payment/
│   ├── models.py          # Payment, PaymentGatewayConfig, PaymentLog
│   ├── views.py           # Payment gateway logic (pre-existing)
│   ├── admin.py           # Admin interface
│   └── migrations/
│
├── buyer/
│   ├── views.py           # 4 NEW payment views added here
│   │   ├── buyer_payment_choice()           # ~Line 427
│   │   ├── buyer_initiate_cod_payment()     # ~Line 457
│   │   ├── check_order_payment_status()     # ~Line 513
│   │   └── payment_success_detail()         # ~Line 539
│   │
│   └── templates/buyer/
│       ├── payment_method_choice.html       # NEW
│       ├── cod_payment_details.html         # NEW
│       ├── payment_status.html              # NEW
│       ├── payment_success_detail.html      # NEW
│       ├── dashboard.html                   # UPDATED
│       └── orders.html                      # UPDATED
│
├── farmer/
│   ├── views.py           # order_detail() UPDATED
│   │   └── order_detail()                   # ~Line 651-700
│   │
│   └── templates/farmer/
│       └── order_detail.html                # UPDATED
│
├── urls.py                # 4 NEW payment routes added
└── docs/
    ├── BUYER_PAYMENT_INTEGRATION.md         # Integration guide
    ├── PAYMENT_INTEGRATION_COMPLETE.md      # Testing checklist
    └── PAYMENT_QUICK_REFERENCE.md           # This file
```

## View Implementation Details

### 1. buyer_payment_choice() - Payment Method Selection

**Location**: buyer/views.py ~Line 427

**Purpose**: Render payment method selection UI and create Payment record

**Flow**:
1. GET request → Display radio selection between COD and Online
2. POST request → Validate and create Payment object

**Code Anatomy**:
```python
@login_required
def buyer_payment_choice(request, order_id):
    # 1. Get Order by ID
    order = get_object_or_404(Order, id=order_id)
    
    # 2. Verify buyer is accessing own order
    if request.user != order.buyer:
        messages.error(request, 'Unauthorized access')
        return redirect('buyer_dashboard')
    
    # 3. Check if order is accepted (payment requirement)
    if order.status != 'accepted':
        messages.error(request, 'Order must be accepted by farmer first')
        return redirect('order_detail', order_id=order_id)
    
    # 4. Check if payment already exists
    try:
        existing_payment = Payment.objects.get(order=order)
        return redirect('payment_success_detail', payment_id=existing_payment.id)
    except Payment.DoesNotExist:
        pass  # Proceed to create new
    
    # 5. Handle POST - create payment
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'cod':
            # Calculate 20/80 split for COD
            payment = Payment.objects.create(
                order=order,
                payment_method='cod',
                status='pending',
                total_amount=order.total_price,
                upfront_amount=order.total_price * Decimal('0.20'),
                remaining_amount=order.total_price * Decimal('0.80'),
            )
            return redirect('buyer_initiate_cod_payment', order_id=order_id)
        
        elif payment_method == 'sslcommerz':
            # Create payment for online gateway
            payment = Payment.objects.create(
                order=order,
                payment_method='sslcommerz',
                status='pending',
                total_amount=order.total_price,
            )
            # Redirect to SSLCommerz gateway (in payment app)
            return redirect('sslcommerz_payment', payment_id=payment.id)
    
    # GET - Render selection form
    context = {'order': order}
    return render(request, 'buyer/payment_method_choice.html', context)
```

**Key Design Decisions**:
- **OneToOne Check**: Uses try/except to prevent duplicate payments
- **Decimal Usage**: Uses Decimal for money calculations (not float)
- **Status Validation**: Ensures order.status == 'accepted'
- **User Verification**: Checks request.user == order.buyer

---

### 2. buyer_initiate_cod_payment() - COD Details Display

**Location**: buyer/views.py ~Line 457

**Purpose**: Display COD payment breakdown and instructions

**Logic**:
```python
@login_required
def buyer_initiate_cod_payment(request, order_id):
    # Get Order and Payment
    order = get_object_or_404(Order, id=order_id)
    payment = get_object_or_404(Payment, order=order)
    
    # Verify payment method is COD
    if payment.payment_method != 'cod':
        messages.error(request, 'This is not a COD payment')
        return redirect('buyer_payment_choice', order_id=order_id)
    
    # For COD: Mark status as "pending" (buyer can fulfill anytime)
    # No actual payment processing needed here
    
    context = {
        'order': order,
        'payment': payment,
        'upfront_amount': payment.upfront_amount,
        'remaining_amount': payment.remaining_amount,
        'total_amount': payment.total_amount,
    }
    return render(request, 'buyer/cod_payment_details.html', context)
```

**Template Context**:
- Order details for display
- Payment breakdown (upfront/remaining)
- Farmer contact information
- Instructions for payment process

---

### 3. check_order_payment_status() - Status Checker

**Location**: buyer/views.py ~Line 513

**Purpose**: Get Current payment status (AJAX-compatible)

**Dual Response Mode**:
```python
@login_required
def check_order_payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Verify user is buyer or farmer
    if request.user not in [order.buyer, order.farmer]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        payment = Payment.objects.get(order=order)
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON for AJAX
            return JsonResponse({
                'status': payment.status,
                'payment_method': payment.payment_method,
                'total_amount': str(payment.total_amount),
                'paid_amount': str(payment.paid_amount),
                'remaining_amount': str(payment.remaining_amount),
            })
        else:
            # Return HTML for browser
            context = {'order': order, 'payment': payment}
            return render(request, 'buyer/payment_status.html', context)
    
    except Payment.DoesNotExist:
        # No payment found
        return redirect('buyer_payment_choice', order_id=order_id)
```

**AJAX Response Format**:
```json
{
  "status": "completed",
  "payment_method": "cod",
  "total_amount": "5000.00",
  "paid_amount": "1000.00",
  "remaining_amount": "4000.00"
}
```

---

### 4. payment_success_detail() - Confirmation Page

**Location**: buyer/views.py ~Line 539

**Purpose**: Display payment confirmation receipt

**Key Features**:
```python
@login_required
def payment_success_detail(request, payment_id):
    # Get Payment by UUID (not ID!)
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    
    # Verify user is buyer or farmer
    if request.user not in [order.buyer, order.farmer]:
        messages.error(request, 'Unauthorized access')
        return redirect('buyer_dashboard')
    
    # Get related objects for context
    farmer = order.farmer
    crop_listings = order.crop_listings.all()
    
    context = {
        'payment': payment,
        'order': order,
        'farmer': farmer,
        'crop_listings': crop_listings,
        'payment_status_display': payment.get_status_display(),
        'payment_method_display': payment.get_payment_method_display(),
    }
    return render(request, 'buyer/payment_success_detail.html', context)
```

**UUID Instead of Integer ID**:
- Payment.id is UUIDField (not auto-increment)
- Security: UUIDs are not sequential/guessable
- URL looks like: `/payment/success/550e8400-e29b-41d4-a716-446655440000/`

---

### 5. farmer/order_detail() - Modified for Payment

**Location**: farmer/views.py ~Line 651-700

**Changes Made**:
```python
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Verify user is farmer who owns this order
    if request.user != order.farmer:
        messages.error(request, 'Unauthorized access')
        return redirect('farmer_dashboard')
    
    # NEW: Get payment if exists
    payment = None
    try:
        payment = Payment.objects.get(order=order)
    except Payment.DoesNotExist:
        pass
    
    # Rest of view logic...
    context = {
        'order': order,
        'payment': payment,  # NEW: Pass to template
        # ... other context
    }
    return render(request, 'farmer/order_detail.html', context)
```

**Template Usage**:
```html
{% if payment %}
    <div class="payment-status-card">
        <h4>Payment Status</h4>
        <p>Method: {{ payment.get_payment_method_display }}</p>
        <p>Status: <span class="badge">{{ payment.get_status_display }}</span></p>
        <p>Amount: ৳{{ payment.total_amount|floatformat:2 }}</p>
    </div>
{% endif %}
```

---

### 6. buyer_dashboard() - Modified with Payment Stats

**Location**: buyer/views.py ~Line 20

**Additions**:
```python
@login_required
def buyer_dashboard(request):
    buyer = request.user
    
    # NEW: Get pending payments
    pending_payments = Payment.objects.filter(
        order__buyer=buyer,
        status='pending'
    )
    orders_pending_payment = pending_payments.values_list('order_id', flat=True)
    
    # Context for template
    context = {
        'pending_payments_count': pending_payments.count(),
        'orders_pending_payment': orders_pending_payment,
        # ... other context
    }
    return render(request, 'buyer/dashboard.html', context)
```

---

## URL Routing

**File**: urls.py (Main urlpatterns)

```python
# Payment URLs - Added at Line ~115
urlpatterns = [
    # ... existing patterns
    
    # Buyer payment flow
    path('buyer/payment-status/<int:order_id>/', 
         views.check_order_payment_status, 
         name='check_order_payment_status'),
    
    path('buyer/payment/<int:order_id>/', 
         views.buyer_payment_choice, 
         name='buyer_payment_choice'),
    
    path('buyer/payment/cod/<int:order_id>/', 
         views.buyer_initiate_cod_payment, 
         name='buyer_initiate_cod_payment'),
    
    # Universal payment success page
    path('payment/success/<str:payment_id>/', 
         views.payment_success_detail, 
         name='payment_success_detail'),
]
```

**URL Parameter Types**:
- `<int:order_id>` - Order ID is integer
- `<str:payment_id>` - Payment ID is UUID string

---

## Template Rendering Logic

### payment_method_choice.html

**Key Sections**:
```html
<!-- Order Summary Component -->
<div class="order-summary">
    <h5>{{ order.crop_listings.first.crop_name }}</h5>
    <p>Quantity: {{ order.quantity }} kg</p>
    <p>Total: ৳{{ order.total_price|floatformat:2 }}</p>
</div>

<!-- Payment Options Form -->
<form method="POST">
    {% csrf_token %}
    <label>
        <input type="radio" name="payment_method" value="cod" required>
        <div class="payment-option">
            <h6>Cash on Delivery (COD)</h6>
            <p>20% upfront: ৳{{ upfront|floatformat:2 }}</p>
            <p>80% at delivery: ৳{{ remaining|floatformat:2 }}</p>
        </div>
    </label>
    
    <label>
        <input type="radio" name="payment_method" value="sslcommerz" required>
        <div class="payment-option">
            <h6>Online Payment</h6>
            <p>Pay 100% now: ৳{{ order.total_price|floatformat:2 }}</p>
        </div>
    </label>
    
    <button type="submit">Continue to Payment</button>
</form>
```

**JavaScript Functionality**:
- Dynamic amount calculation
- Visual feedback on selection
- Form validation

### cod_payment_details.html

**Display Elements**:
1. **Order Info**: Crop details, quantity, total
2. **Payment Breakdown**: Grid showing upfront/remaining split
3. **Steps Timeline**: 5-step instruction process
4. **Important Notes**: Alerts and warnings
5. **Farmer Contact**: Click-to-contact button

### payment_status.html

**Reactive Components**:
```html
<!-- Timeline Visualization -->
<div class="timeline">
    <div class="timeline-item completed">
        <span>Order Placed</span>
    </div>
    <div class="timeline-item completed">
        <span>Farmer Accepted</span>
    </div>
    <div class="timeline-item {{ payment.status|default:'pending' }}">
        <span>Payment {{ payment.get_status_display }}</span>
    </div>
</div>

<!-- Status-Specific Alerts -->
{% if payment.status == 'pending' %}
    <div class="alert alert-warning">
        Payment pending - Complete payment to proceed
    </div>
{% elif payment.status == 'failed' %}
    <div class="alert alert-danger">
        Payment failed - {{ payment.error_message }}
    </div>
{% elif payment.status == 'completed' %}
    <div class="alert alert-success">
        Payment confirmed - Farmer will ship soon
    </div>
{% endif %}
```

### payment_success_detail.html

**Receipt Components**:
1. **Success Banner**: Green checkmark badge
2. **Confirmation Box**: Order details
3. **Amount Breakdown**: Itemized costs
4. **Seller Info**: Farmer details and photo
5. **Next Steps**: 5-step process guide
6. **Print Function**: CSS for print-friendly layout

---

## Authorization & Security

### Multi-Layer Protection

**1. View-Level (@login_required)**
```python
@login_required
def buyer_payment_choice(request, order_id):
    # Only logged-in users can access
```

**2. Business Logic Verification**
```python
# Verify user is buyer
if request.user != order.buyer:
    return redirect('buyer_dashboard')

# Verify order accepted
if order.status != 'accepted':
    messages.error(request, 'Order not accepted yet')
    return redirect('order_detail', order_id=order_id)
```

**3. Database Constraint**
```python
# OneToOneField ensures one payment per order
payment = Payment.objects.get(order=order)  # Unique
```

**4. CSRF Protection**
```html
<form method="POST">
    {% csrf_token %}  <!-- Prevents cross-site attacks -->
</form>
```

---

## Error Handling Patterns

### Pattern 1: Resource Not Found
```python
try:
    payment = Payment.objects.get(order=order)
except Payment.DoesNotExist:
    messages.error(request, 'Payment not found')
    return redirect('buyer_payment_choice', order_id=order_id)
```

### Pattern 2: Invalid State
```python
if order.status != 'accepted':
    messages.error(request, 'Order must be accepted first')
    return redirect('order_detail', order_id=order_id)
```

### Pattern 3: Unauthorized Access
```python
if request.user not in [order.buyer, order.farmer]:
    messages.error(request, 'You are not authorized')
    return redirect('buyer_dashboard')
```

---

## Testing Scenarios

### Scenario 1: Complete COD Flow
```
1. buyer_dashboard → See pending payments
2. buyer/orders → Click "Pay Now"
3. buyer/payment/123 → Select COD
4. buyer/payment/cod/123 → Review breakdown
5. Farmer sees payment status
6. payment/success/UUID → Confirmation
```

### Scenario 2: SSLCommerz Flow  
```
1. buyer/payment/123 → Select Online
2. Redirected to SSLCommerz gateway
3. Complete payment on SSLCommerz
4. Webhook updates Payment.status to 'completed'
5. Redirect to payment/success/UUID
```

### Scenario 3: Farmer Order Review
```
1. farmer/order/123 → Accept order
2. Farmer sees payment status card
3. Can plan fulfillment based on payment status
```

---

## Database Query Optimization

### Avoid N+1 Queries
```python
# SLOW: Causes multiple queries
orders = Order.objects.all()
for order in orders:
    payment = order.payment  # Query per order

# FAST: Prefetch related
orders = Order.objects.select_related('payment').all()
for order in orders:
    payment = order.payment  # No additional queries
```

### Efficient Filtering
```python
# Get pending payments for user
pending = Payment.objects.filter(
    order__buyer=request.user,
    status='pending'
).select_related('order')

# Get completion statistics
from django.db.models import Count, Q
stats = Payment.objects.filter(
    order__buyer=request.user
).aggregate(
    total=Count('id'),
    completed=Count('id', filter=Q(status='completed')),
    pending=Count('id', filter=Q(status='pending')),
)
```

---

## Common Issues & Solutions

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| "Payment not found" on success page | Payment wasn't created | Check buyer_payment_choice POST handler |
| Duplicate payment records | Multiple form submissions | Use OneToOneField constraint (already implemented) |
| COD amounts not splitting correctly | Float arithmetic | Use Decimal class (already implemented) |
| Farmer can't see payment status | Payment context missing | Check payment = Payment.objects.get() in order_detail |
| "Access denied" error | Wrong user account | Verify request.user == buyer or farmer |
| UUID format error in URL | Treating UUID as string | Use `payment.id` (UUID field) not `payment.pk` |

---

## Deployment Checklist

- [ ] All migrations applied: `python manage.py migrate`
- [ ] Static files collected: `python manage.py collectstatic --noinput`
- [ ] Settings.py configured for production
- [ ] SSLCommerz credentials in database
- [ ] Email backend configured
- [ ] CSRF trusted hosts configured
- [ ] ALLOWED_HOSTS includes domain
- [ ] Debug = False in production
- [ ] SECRET_KEY is environment variable
- [ ] Logging configured appropriately

---

**Document Version**: 1.0
**Last Updated**: April 21, 2026
**Status**: ✅ Production Ready
