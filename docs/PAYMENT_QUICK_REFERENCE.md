# Payment Integration - Quick Reference

## Order Payment Flow

```
BUYER PLACES ORDER
    ↓
FARMER ACCEPTS BUYER'S ORDER
    ↓
BUYER GETS PAYMENT BUTTON
    ↓
BUYER CHOOSES PAYMENT METHOD
    ├─ COD (20% upfront)
    ├─ Online (100%)
    ↓
PAYMENT RECORDED IN DATABASE
    ↓
BUYER COMPLETES PAYMENT
    ↓
FARMER SEES PAYMENT STATUS
    ↓
FARMER SHIPS ORDER
```

## Key URLs

### Buyer Payment URLs
```
/buyer/payment-status/<order_id>/         # Check payment status (GET)
/buyer/payment/<order_id>/                # Choose payment method (GET/POST)
/buyer/payment/cod/<order_id>/            # View COD details (GET)
/payment/success/<payment_id>/            # View confirmation (GET)
```

## Controller Methods

### In `buyer/views.py`

```python
def buyer_payment_choice(request, order_id):
    """
    Render payment method selection form
    POST: Create payment record and redirect
    """

def buyer_initiate_cod_payment(request, order_id):
    """
    Show COD payment details (20% upfront, 80% at delivery)
    """

def check_order_payment_status(request, order_id):
    """
    Check payment status for an order
    AJAX support: Returns JSON
    """

def payment_success_detail(request, payment_id):
    """
    Show payment confirmation receipt
    """
```

### In `farmer/views.py`

```python
def order_detail(request, order_id):
    """
    Updated to include payment context
    Added: payment = Payment.objects.get(order=order)
    """
```

## Database Models

### Payment Model
```python
Payment
├─ id: UUID (primary key)
├─ order: OneToOneField → Order
├─ payment_method: 'cod' | 'sslcommerz'
├─ status: pending | initiating | completed | failed | cancelled | refunded
├─ total_amount: Float
├─ paid_amount: Float
├─ upfront_amount: Float (20% for COD)
├─ remaining_amount: Float (80% for COD)
└─ ... (timestamps, SSLCommerz fields)
```

## Template Structure

### payment_method_choice.html
- Order summary card
- COD option (20/80 split)
- Online option (100%)
- Comparison table
- Submit button

### cod_payment_details.html
- Order info
- Payment breakdown
- 5-step instructions
- Important notes
- Help section

### payment_status.html
- Timeline visualization
- Payment details
- Status-specific alerts
- Action buttons

### payment_success_detail.html
- Confirmation success badge
- Order & payment details
- Seller info with contact
- Delivery information
- Next steps
- Print button

## Integration Points

### Dashboard
- `orders_pending_payment` context
- Pending payments count
- Alert for payment action required

### Orders List
- "Pay Now" button for ACCEPTED orders
- Links to `buyer_payment_choice`

### Order Detail (Farmer)
- Payment status card
- Method and amounts display
- Status alerts

## Testing Payment Flow

### Step 1: Create Test Order
```
1. Login as buyer
2. Go to /buyer/marketplace/
3. Place order for a crop
4. Get order_id (123)
```

### Step 2: Accept as Farmer
```
1. Login as farmer
2. Navigate to /farmer/orders/
3. Find order and click "Accept"
4. Order status → ACCEPTED
```

### Step 3: Test Payment Button
```
1. Login as buyer
2. Go to /buyer/orders/
3. Find ACCEPTED order
4. Click "Pay Now" button
5. Should redirect to /buyer/payment/123/
```

### Step 4: Select Payment Method
```
1. Choose payment method
2. For COD: Show 20/80 breakdown
3. For Online: Redirect to SSLCommerz
```

### Step 5: View Payment Status
```
1. View order as farmer
2. Should see payment status card
3. Check payment method and amounts
```

## Common Code Snippets

### Get Order's Payment
```python
from payment.models import Payment
try:
    payment = Payment.objects.get(order=order)
except Payment.DoesNotExist:
    payment = None
```

### Create Payment (COD)
```python
payment = Payment.objects.create(
    order=order,
    payment_method='cod',
    status='pending',
    total_amount=order.total_price,
    upfront_amount=order.total_price * 0.20,
    remaining_amount=order.total_price * 0.80,
)
```

### Create Payment (Online)
```python
payment = Payment.objects.create(
    order=order,
    payment_method='sslcommerz',
    status='pending',
    total_amount=order.total_price,
)
```

### Check Payment Status in Template
```html
{% if payment %}
    <p>Payment Status: {{ payment.get_status_display }}</p>
    <p>Amount: ৳{{ payment.total_amount|floatformat:2 }}</p>
{% else %}
    <p>No payment found</p>
{% endif %}
```

## Debugging

### Check Payment Exists
```python
order = Order.objects.get(id=order_id)
try:
    payment = Payment.objects.get(order=order)
    print(f"Payment: {payment.status}, Amount: {payment.total_amount}")
except Payment.DoesNotExist:
    print("No payment for this order")
```

### View Payment in Admin
```
1. Go to /admin/payment/payment/
2. Filter by order_id
3. View details and status
```

### Check Database
```sql
-- List all payments
SELECT * FROM payment_payment;

-- Find payment for order
SELECT * FROM payment_payment WHERE order_id = 123;

-- Check payment status
SELECT status, payment_method FROM payment_payment WHERE order_id = 123;
```

## Key Business Logic

### 1. Payment Only Available After Farmer Accepts
```python
if order.status != 'accepted':
    messages.error(request, 'Order must be accepted first')
    return redirect('order_detail', order_id=order.id)
```

### 2. COD Split Calculation
```python
upfront = total_amount * 0.20    # 20% upfront
remaining = total_amount * 0.80  # 80% at delivery
```

### 3. One Payment Per Order
```python
# OneToOneField ensures only one payment
payment = Payment.objects.get(order=order)  # Unique
```

### 4. Payment Prevents Duplicate Records
```python
# Check if payment exists
try:
    existing_payment = Payment.objects.get(order=order)
    # Reuse existing
except Payment.DoesNotExist:
    # Create new payment
```

## Performance Tips

1. **Use select_related for Orders**
```python
orders = Order.objects.select_related('payment')
```

2. **Cache Payment Status in Dashboard**
```python
# Only fetch payments that exist
payments = Payment.objects.filter(order__buyer=request.user)
pending = payments.filter(status='pending').count()
```

3. **Use AJAX for Status Checks**
```javascript
// Check payment status without page reload
fetch(`/buyer/payment-status/${orderId}/`)
    .then(r => r.json())
    .then(data => updateStatus(data))
```

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Order not accepted" | Wrong order status | Wait for farmer to accept |
| "Payment not found" | PaymentDoesNotExist | Check if payment was created |
| "Access denied" | Not buyer/farmer | Use correct account |
| "404 on payment URL" | Wrong payment_id format | Use UUID not string |

## Status Flow

```
PENDING
  ↓ (User submits form)
INITIATING
  ↓ (Gateway processes)
COMPLETED ← SUCCESS
  ↑
FAILED ← SSLCommerz error
  ↓ (Retry)
CANCELLED ← User cancels
```

## Next Development Tasks

1. **Email Notifications**
   - Payment confirmation email
   - Payment reminder email (pending)
   - Order status update email

2. **Webhooks**
   - SSLCommerz webhook handling
   - Auto-update payment status

3. **Refunds**
   - Partial refund handling
   - Auto-refund on order cancellation

4. **Analytics**
   - Payment success rate dashboard
   - Revenue tracking
   - Payment method statistics

---

## Quick Troubleshooting Checklist

- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Views imported in urls.py
- [ ] Templates exist in correct directories
- [ ] SSLCommerz config set up in database
- [ ] Order status is ACCEPTED before payment
- [ ] User is logged in as buyer
- [ ] payment_id is valid UUID
- [ ] Order belongs to logged-in buyer

---

**Last Updated**: April 21, 2026
**Status**: ✅ Production Ready
