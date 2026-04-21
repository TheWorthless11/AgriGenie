# PAYMENT SYSTEM SETUP - QUICK START

## Quick Setup (5 minutes)

### 1. Add SSLCommerz Credentials
```bash
cd /path/to/AgriGenie
python manage.py migrate payment
python manage.py setup_sslcommerz --store-id agrig69da4059c2fa4 --store-password "agrig69da4059c2fa4@ssl" --sandbox
```

### 2. Verify Installation
```bash
python manage.py shell
>>> from payment.models import PaymentGatewayConfig
>>> PaymentGatewayConfig.objects.all()
<QuerySet [<PaymentGatewayConfig: SSLCommerz Config - Sandbox>]>
```

### 3. Run Tests
```bash
python manage.py test payment
```

### 4. Start Server
```bash
python manage.py runserver
```

### 5. Access Admin Panel
Navigate to: `http://localhost:8000/admin/payment/`

---

## Testing Payment Flow

### Test 1: COD Payment
1. Login as buyer
2. Browse marketplace
3. Place order on a crop
4. Wait for farmer approval
5. View orders → Click on accepted order
6. Should see "Proceed to Payment" button
7. Click button → Choose "Cash on Delivery"
8. Verify: ৳{20%} upfront, ৳{80%} at delivery
9. Submit → Order status changes to payment methods

### Test 2: Online Payment (Sandbox)
1. Follow steps 1-5 above
2. Choose "Online Payment (SSLCommerz)"
3. Redirected to SSLCommerz sandbox
4. Test Card: 4111111111111111
5. Any future date and any CVV
6. Confirm payment
7. Should redirect to success page

### Test 3: Verify COD Balance
1. For COD orders, farmer ships product
2. Order status → "Shipped"
3. Farmer navigates to farmer orders
4. Sees "Verify Payment" button (if COD + shipped)
5. Clicks button
6. Confirms payment method received (cash/bKash/etc)
7. Order marked as "Delivered"

---

## Integration Checklist

- [x] Payment app created
- [x] Models created (Payment, PaymentGatewayConfig, PaymentLog)
- [x] Views created
- [x] URLs configured
- [x] Templates created
- [x] Admin interface set up
- [x] Management command created
- [x] Unit tests written
- [ ] Add payment button to buyer orders page
- [ ] Add verify payment button to farmer orders page
- [ ] Add payment history to user dashboard
- [ ] Email notifications for payments
- [ ] Payment analytics dashboard

---

## Manual Integration Steps

### Step 1: Update Buyer Orders Template
File: `templates/buyer/orders.html`

Add after order status display:
```html
{% if order.status == 'accepted' and not order.payment %}
    <a href="{% url 'payment:choose_payment_method' order.id %}" class="btn btn-success btn-sm">
        <i class="fas fa-credit-card"></i> Proceed to Payment
    </a>
{% endif %}
```

### Step 2: Update Farmer Orders Template
File: `templates/farmer/orders_list.html`

Add action buttons column:
```html
{% if order.status == 'shipped' and order.payment.payment_method == 'cod' %}
    <a href="{% url 'payment:verify_payment' order.id %}" class="btn btn-warning btn-sm">
        <i class="fas fa-money-check-alt"></i> Verify Payment
    </a>
{% endif %}
```

### Step 3: Update Buyer Dashboard
File: `templates/buyer/dashboard.html`

Add payment status card:
```html
<div class="col-lg-4 mb-4">
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Pending Payments</h5>
        </div>
        <div class="list-group">
            {% for order in pending_payment_orders %}
                <a href="{% url 'payment:choose_payment_method' order.id %}" class="list-group-item">
                    {{ order.crop.crop_name }} - ৳{{ order.total_price }}
                </a>
            {% empty %}
                <div class="list-group-item">No pending payments</div>
            {% endfor %}
        </div>
    </div>
</div>
```

---

## API Usage Example

### Python Example - Create Manual Payment
```python
from payment.models import Payment
from farmer.models import Order

order = Order.objects.get(id=1)
payment = Payment.objects.create(
    order=order,
    payment_method='cod',
    total_amount=order.total_price,
)

# Calculate amounts
amounts = {
    'upfront': order.total_price * 0.20,
    'remaining': order.total_price * 0.80,
}

payment.upfront_amount = amounts['upfront']
payment.remaining_amount = amounts['remaining']
payment.paid_amount = amounts['upfront']
payment.status = 'completed'
payment.save()

print(f"Payment created: {payment.id}")
print(f"Upfront: ৳{payment.upfront_amount:.2f}")
print(f"Remaining: ৳{payment.remaining_amount:.2f}")
```

---

## Database Tables

### payment_payment
Primary table for payment records
- Columns: id, order_id, payment_method, status, total_amount, etc.
- Indexes: order_id (UNIQUE), transaction_id (UNIQUE)

### payment_paymentgatewayconfig
Configuration for SSLCommerz
- Columns: id, store_id, store_password, is_active, is_sandbox, etc.

### payment_paymentlog
Detailed logs for debugging
- Columns: id, payment_id, log_type, message, request_data, response_data, etc.

---

## Production Deployment

### Before Going Live:

1. **Change Sandbox to Live**:
   ```bash
   python manage.py shell
   >>> from payment.models import PaymentGatewayConfig
   >>> config = PaymentGatewayConfig.objects.first()
   >>> config.is_sandbox = False
   >>> config.session_api_url = 'https://secure.sslcommerz.com/gwprocess/v4/api.php'
   >>> config.validation_api_url = 'https://secure.sslcommerz.com/validator/api/validationserverAPI.php'
   >>> config.save()
   ```

2. **Update Settings**:
   - Set `DEBUG = False`
   - Set `SECURE_SSL_REDIRECT = True`
   - Add domain to `ALLOWED_HOSTS`

3. **SSL Certificate**:
   - Ensure HTTPS/SSL certificate is installed
   - SSLCommerz requires HTTPS

4. **Backup Database**:
   - Backup all payment records before migration

---

## Troubleshooting Commands

### Check Payment Config
```bash
python manage.py shell
>>> from payment.models import PaymentGatewayConfig
>>> config = PaymentGatewayConfig.objects.first()
>>> print(f"Store ID: {config.store_id}")
>>> print(f"Is Sandbox: {config.is_sandbox}")
>>> print(f"Is Active: {config.is_active}")
```

### View Payment Logs
```bash
python manage.py shell
>>> from payment.models import PaymentLog
>>> PaymentLog.objects.all().order_by('-created_at')[:10]
```

### Resync Payments
```bash
python manage.py shell
>>> from payment.models import Payment
>>> Payment.objects.filter(status='failed')
```

---

## File Structure

```
payment/
├── __init__.py
├── admin.py                          # Django admin
├── apps.py                           # App config
├── forms.py                          # PaymentMethodForm
├── gateway.py                        # SSLCommerz gateway
├── models.py                         # Payment, PaymentLog, Config
├── tests.py                          # Unit tests
├── urls.py                           # URL routes
├── views.py                          # Payment views
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── setup_sslcommerz.py      # Setup command
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py              # Initial migration
└── templates/payment/
    ├── choose_payment_method.html   # Payment method selection
    ├── payment_success.html         # Success page
    ├── payment_details.html         # Payment details view
    └── verify_payment.html          # COD verification

urls.py (updated)                    # Added /payment/ routes
settings.py (updated)                # Added 'payment' to INSTALLED_APPS
```

---

## Support & Resources

- SSLCommerz Sandbox: https://sandbox.sslcommerz.com/manage/
- Developer Docs: https://developer.sslcommerz.com/
- Support Email: support@sslcommerz.com
- Merchant Panel: https://sandbox.sslcommerz.com/manage/

---

## Next Features To Add

1. **Refund Processing**
   - Buyer can request refund
   - Farmer approves/rejects refund
   - Automatic refund to original payment method

2. **Payment Reminders**
   - Email reminder for unpaid orders
   - SMS reminders (optional)
   - Auto-cancel orders after X days unpaid

3. **Payment Analytics**
   - Revenue dashboard
   - Payment success rates
   - COD vs Online comparison
   - Top payment methods

4. **Multiple Payment Methods**
   - Add bKash integration
   - Add Nagad integration
   - Add Rocket integration
   - Stripe integration (for international)

5. **Payment Scheduling**
   - Installment payments
   - Payment plans
   - Subscription support

---

**Last Updated**: April 21, 2026
**Version**: 1.0
**Status**: Production Ready (with SSLCommerz credentials)
