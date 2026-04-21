# SSLCommerz Payment Integration Guide

## Overview
This guide explains how the SSLCommerz payment system has been integrated into AgriGenie. The system supports two payment methods:

1. **Cash on Delivery (COD)**: 20% upfront, 80% at delivery
2. **Online Payment (SSLCommerz)**: Full payment upfront

## Payment Flow

### Step 1: Order Placement (Existing)
Buyer places order → Order status: `pending`

### Step 2: Farmer Approval (Existing)
Farmer approves order → Order status: `accepted`

### Step 3: NEW - Payment Method Selection
**NEW STEP** - Buyer chooses payment method:
- COD: Pay 20% now
- Online: Pay 100% now via SSLCommerz

### Step 4: Payment Processing
- **COD**: 20% payment recorded, order proceeds
- **Online**: Redirect to SSLCommerz → Payment confirmed → Order proceeds

### Step 5: Delivery
Order shipped and delivered

### Step 6: COD Balance Collection (Farmer)
- For COD orders: Farmer verifies receipt of 80% balance at delivery
- Farmer marks payment as received
- Order marked as completed

## Files Created

### 1. Payment App Structure
```
payment/
├── migrations/
│   └── 0001_initial.py       # Database migrations
├── management/
│   └── commands/
│       └── setup_sslcommerz.py  # Setup SSLCommerz credentials
├── admin.py                    # Django admin interface
├── apps.py                     # App configuration
├── forms.py                    # Payment method form
├── gateway.py                  # SSLCommerz gateway integration
├── models.py                   # Payment models
├── tests.py                    # Unit tests
├── urls.py                     # Payment URLs
├── views.py                    # Payment views
└── __init__.py
```

### 2. Models Created

#### Payment Model
- Tracks payment information for each order
- Fields:
  - `order`: OneToOneField to Order
  - `payment_method`: COD or SSLCommerz
  - `status`: pending, initiating, completed, failed, cancelled, refunded
  - `total_amount`: Total order amount
  - `paid_amount`: Amount actually paid
  - `upfront_amount`: 20% for COD
  - `remaining_amount`: 80% for COD
  - `transaction_id`: SSLCommerz transaction ID
  - `ssl_session_id`: SSLCommerz session
  - `ssl_validation_id`: SSLCommerz validation ID
  - Timestamps and refund fields

#### PaymentGatewayConfig Model
- Stores SSLCommerz credentials
- Fields:
  - `store_id`: Your SSLCommerz store ID
  - `store_password`: Your SSLCommerz API key
  - `is_sandbox`: Whether using sandbox mode
  - `is_active`: Activate/deactivate the gateway

#### PaymentLog Model
- Logs all payment gateway transactions
- For debugging and audit purposes

### 3. Views Created

#### choose_payment_method (payment/choose_payment_method.html)
- Buyer selects Payment method after farmer approves
- Shows COD breakdown: 20% upfront vs 80% at delivery
- Shows online payment benefits
- URL: `/payment/choose/<order_id>/`

#### initiate_sslcommerz_payment
- redirect to SSLCommerz payment gateway
- Only for online payment method
- URL: `/payment/initiate/<order_id>/`

#### payment_success
- Callback from SSLCommerz after successful payment
- Validates payment with SSLCommerz API
- Updates payment status to "completed"
- URL: `/payment/success/`

#### payment_failed
- Callback from SSLCommerz after failed payment
- Updates payment status to "failed"
- URL: `/payment/failed/`

#### order_payment_success (payment/payment_success.html)
- Shows payment success information
- Displays order and payment details
- Timeline of what happens next
- URL: `/payment/success-page/<order_id>/`

#### verify_payment
- Farmer verifies receipt of COD balance at delivery
- Farmer confirms payment method (cash, bKash, etc.)
- Marks order as delivered
- URL: `/payment/verify/<order_id>/`

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py migrate payment
```

### 2. Configure SSLCommerz Credentials

Using management command (Recommended):
```bash
python manage.py setup_sslcommerz \
  --store-id agrig69da4059c2fa4 \
  --store-password "agrig69da4059c2fa4@ssl" \
  --sandbox
```

Or via Django Admin:
1. Go to `/admin/payment/paymentgatewayconfig/`
2. Click "Add Payment Gateway Config"
3. Enter:
   - Store ID: `agrig69da4059c2fa4`
   - Store Password: `agrig69da4059c2fa4@ssl`
   - Check "Is Sandbox" for testing
   - Check "Is Active"
4. Save

### 3. Configure Allowed Hosts
Make sure your domain is in `ALLOWED_HOSTS` in settings.py

### 4. Update Order Detail View (Integration)

In `buyer/views.py`, update `crop_detail` view to show payment button after farmer accepts order:

```python
# After farmer accepts order
if order.status == 'accepted' and not hasattr(order, 'payment'):
    # Show "Proceed to Payment" button
    show_payment_button = True
```

Add to template context.

### 5. Update Order Templates

In `templates/buyer/orders.html`, add payment button for accepted orders:

```html
{% if order.status == 'accepted' and not order.payment %}
    <a href="{% url 'payment:choose_payment_method' order.id %}" class="btn btn-success">
        <i class="fas fa-credit-card"></i> Proceed to Payment
    </a>
{% endif %}
```

### 6. Update Farmer Order Templates

In `templates/farmer/orders_list.html`, add verification button for completed COD orders:

```html
{% if order.status == 'shipped' and order.payment.payment_method == 'cod' and not order.payment.refund_id %}
    <a href="{% url 'payment:verify_payment' order.id %}" class="btn btn-sm btn-warning">
        <i class="fas fa-money-check-alt"></i> Verify Payment
    </a>
{% endif %}
```

## Testing

### 1. Unit Tests
Run tests:
```bash
python manage.py test payment
```

### 2. Manual Testing - COD Flow
1. Create buyer and farmer accounts
2. Create crop listing
3. Buyer places order
4. Farmer accepts order
5. Buyer clicks "Proceed to Payment"
6. Choose "Cash on Delivery"
7. See ৳X upfront, ৳Y at delivery breakdown
8. Payment marked as completed
9. Farmer verifies delivery payment

### 3. Manual Testing - Online Payment Flow (Sandbox)
1. Follow steps 1-5 above
2. Choose "Online Payment (SSLCommerz)"
3. Redirected to SSLCommerz sandbox
4. Use test card: 4111111111111111 (any future date, any CVV)
5. Payment confirmed
6. Redirected back with success page
7. Order marked as paid

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/payment/choose/<order_id>/` | GET, POST | Choose payment method |
| `/payment/initiate/<order_id>/` | GET | Initiate SSLCommerz payment |
| `/payment/success/` | POST | SSLCommerz success callback |
| `/payment/failed/` | POST | SSLCommerz failed callback |
| `/payment/cancelled/` | POST | SSLCommerz cancelled callback |
| `/payment/success-page/<order_id>/` | GET | Show payment success info |
| `/payment/details/<payment_id>/` | GET | View payment details |
| `/payment/verify/<order_id>/` | GET, POST | Verify COD payment |

## Environment Variables

Add to `.env` file (optional - can also configure via admin):
```
SSLCOMMERZ_STORE_ID=agrig69da4059c2fa4
SSLCOMMERZ_STORE_PASSWORD=agrig69da4059c2fa4@ssl
SSLCOMMERZ_SANDBOX=True
```

## Troubleshooting

### Payment Gateway Not Configured
**Error**: "Payment gateway not configured"
**Solution**: Run `python manage.py setup_sslcommerz` command

### SSLCommerz Connection Error
**Error**: "Connection error: Unable to reach gateway"
**Solution**: 
- Check internet connection
- Verify ALLOWED_HOSTS includes your domain
- Check SSLCommerz credentials

### Payment Not Validating
**Error**: "Payment validation failed"
**Solution**:
- Verify SSLCommerz credentials in admin
- Check that order exists and is in "accepted" state
- Check SSLCommerz payment logs in admin

### Views Payment Details

Go to Django Admin `/admin/payment/`:
1. **Payments**: View all payment records
2. **Payment Logs**: View detailed transaction logs
3. **Payment Gateway Config**: Manage SSLCommerz credentials

## Security Considerations

1. **Store Password**: Never expose in frontend
   - Only server-side communication with SSLCommerz
   - Use environment variables for production

2. **Transaction ID**: SSLCommerz validates each transaction
   - Each payment has unique UUID
   - Transactions logged for audit

3. **HTTPS Required**: In production
   - SSLCommerz requires HTTPS
   - Configure in settings: `SECURE_SSL_REDIRECT = True`

4. **CSRF Protection**: Enabled on all payment views
   - All forms include `{% csrf_token %}`

## Next Steps

1. **Refund Integration**: Implement refund processing
   - SSLCommerz refund API
   - Refund triggering conditions

2. **Payment Analytics**: Track payment metrics
   - Success rates by method
   - Revenue tracking
   - COD vs Online comparison

3. **Email Notifications**: Send payment confirmations
   - Order confirmation email
   - Payment receipt email
   - Delayed payment reminders

4. **Mobile Payment**: Add mobile wallet support
   - bKash integration
   - Nagad integration
   - Other mobile wallets

## Contact Support

For SSLCommerz support:
- Email: support@sslcommerz.com
- Phone: +880-2-8316969
- Website: https://www.sslcommerz.com

## References

- SSLCommerz API Documentation: https://developer.sslcommerz.com/
- Payment Gateway URLs:
  - Sandbox Session: https://sandbox.sslcommerz.com/gwprocess/v4/api.php
  - Sandbox Validation: https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php
  - Live URLs: https://secure.sslcommerz.com/ (update after live setup)
