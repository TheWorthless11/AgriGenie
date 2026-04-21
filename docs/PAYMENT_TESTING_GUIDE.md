# Payment System - Complete Testing Checklist

## Pre-Testing Setup

### Environment Verification
- [ ] Python environment activated
- [ ] Django server running: `python manage.py runserver`
- [ ] Database migrations applied: `python manage.py migrate`
- [ ] Test accounts created (buyer + farmer)
- [ ] SSLCommerz credentials configured in admin
- [ ] Browser cache cleared (Ctrl+Shift+Delete)
- [ ] Network tab open (F12) for request monitoring
- [ ] Console open for JavaScript errors

### Test Data Preparation
```bash
# Create test crop listing
python manage.py shell
>>> from farmer.models import CropListing
>>> from users.models import CustomUser

# Get or create test farmer
farmer = CustomUser.objects.get(email='farmer@test.com')

# Get or create test crop listing
crop = CropListing.objects.create(
    farmer=farmer,
    crop_name='Rice',
    quantity=100,
    price_per_unit=50,
    unit='kg',
    description='Test rice'
)

# Create test buyer
buyer = CustomUser.objects.get(email='buyer@test.com')
```

---

## Section 1: Buyer Order Placement (Foundation Test)

### Test 1.1: Browse and Order Crop
**Prerequisites**: Buyer logged in, Farmer has active listings

1. **Navigate to marketplace**
   - [ ] Open `/buyer/marketplace/`
   - [ ] Verify crop listings display
   - [ ] Check crop details (name, quantity, price)

2. **Create order**
   - [ ] Click "Order" button on crop
   - [ ] Enter quantity in form
   - [ ] Verify total price calculation: `Total = Quantity × Price/kg`
   - [ ] Click "Place Order"
   - [ ] Should see success message
   - [ ] Database: Check `Order` table has new record with status='pending'

**Expected Result**: Order created with status='pending', buyer can see it in orders list

---

## Section 2: Farmer Order Management (Foundation Test)

### Test 2.1: Farmer Accepts Order
**Prerequisites**: Buyer has placed order, Farmer logged in

1. **View pending orders as farmer**
   - [ ] Login as farmer account
   - [ ] Navigate to `/farmer/orders/` (or orders page)
   - [ ] Should see buyer's order with status='pending'
   - [ ] Click order to view details

2. **Accept order as farmer**
   - [ ] In order detail page, click "Accept Order" button
   - [ ] Should see success message
   - [ ] Page should update: Order status → 'accepted'
   - [ ] Database: Check `Order` table, status changed to 'accepted'

**Expected Result**: Order status changed to 'accepted'. Ready for payment workflow.

---

## Section 3: Payment Button Visibility

### Test 3.1: Payment Button on Buyer Dashboard
**Prerequisites**: Order is ACCEPTED

1. **View buyer dashboard**
   - [ ] Login as buyer
   - [ ] Navigate to `/buyer/dashboard/`
   - [ ] Look for "Pending Payments" card in stats section
   - [ ] Should show count of orders awaiting payment
   - [ ] Should display alert: "You have X orders pending payment"

**Expected Result**: Dashboard shows payment-related alerts and statistics

### Test 3.2: Payment Button in Orders List
**Prerequisites**: Order is ACCEPTED

1. **View buyer orders**
   - [ ] Login as buyer
   - [ ] Navigate to `/buyer/orders/`
   - [ ] For ACCEPTED order, should see "Pay Now" button (yellow)
   - [ ] For other orders (pending/shipped), button should NOT show

2. **Click "Pay Now" button**
   - [ ] Button should redirect to `/buyer/payment/<order_id>/`
   - [ ] Network request shows GET to correct URL

**Expected Result**: "Pay Now" button appears only for ACCEPTED orders

---

## Section 4: Payment Method Selection

### Test 4.1: Access Payment Selection Page
**Prerequisites**: Order is ACCEPTED

1. **Navigate to payment selection**
   - [ ] Click "Pay Now" button from orders list
   - [ ] OR directly visit `/buyer/payment/<order_id>/`
   - [ ] Page should load without errors
   - [ ] Check browser console for JavaScript errors
   - [ ] Network tab: Request should return 200 OK

2. **Verify page content**
   - [ ] Order summary card displays:
     - [ ] Crop name
     - [ ] Quantity
     - [ ] Total price
   - [ ] Two payment option cards visible:
     - [ ] "Cash on Delivery (COD)" card
     - [ ] "Online Payment" card
   - [ ] COD card shows 20%/80% breakdown:
     - [ ] Upfront amount = total × 0.20
     - [ ] Remaining amount = total × 0.80

3. **Test page interactivity**
   - [ ] Click COD radio button → Card highlights
   - [ ] Click Online radio button → Card highlights
   - [ ] Submit button is active
   - [ ] Hover effects work on cards

**Expected Result**: Payment selection page loads correctly with both options visible

### Test 4.2: Calculate Amounts Correctly
**Use order total: ৳1000**

1. **Verify COD calculation**
   - [ ] Upfront amount shown: ৳200 (20%)
   - [ ] Remaining amount shown: ৳800 (80%)
   - [ ] Total in display: ৳1000
   - [ ] Manual check: 200 + 800 = 1000 ✓

2. **Test with different amounts**
   - [ ] Order total ৳500: Upfront ৳100, Remaining ৳400
   - [ ] Order total ৳5000: Upfront ৳1000, Remaining ৳4000
   - [ ] Order total ৳250: Upfront ৳50, Remaining ৳200

**Expected Result**: Correct percentage calculations on all amounts

---

## Section 5: COD Payment Flow

### Test 5.1: Select COD and View Details
**Prerequisites**: On payment selection page

1. **Select COD option**
   - [ ] Click COD radio button
   - [ ] Click "Continue to Payment" button
   - [ ] Should redirect to `/buyer/payment/cod/<order_id>/`

2. **Verify COD details page content**
   - [ ] Page title: Shows "Cash on Delivery"
   - [ ] Order info section displays:
     - [ ] Crop name and quantity
     - [ ] Total order amount
     - [ ] Farmer name with contact button
   - [ ] Payment breakdown section shows:
     - [ ] "Pay Now" box: Upfront amount (20%)
     - [ ] "Pay at Delivery" box: Remaining amount (80%)
   - [ ] Instructions section shows 5 steps
   - [ ] Important notes section has 4 key points

3. **Verify form elements**
   - [ ] Farmer contact button is clickable
   - [ ] "Confirm & Proceed" button present
   - [ ] Page is mobile-responsive

**Expected Result**: COD details page shows correct breakdown and instructions

### Test 5.2: Verify Database State After COD Selection
**Prerequisites**: COD selected and page displayed

1. **Check Payment model creation**
   - [ ] Open Django admin: `/admin/payment/payment/`
   - [ ] Filter by order_id
   - [ ] Should see Payment record with:
     - [ ] payment_method = 'cod'
     - [ ] status = 'pending'
     - [ ] total_amount = order.total_price
     - [ ] upfront_amount = total × 0.20
     - [ ] remaining_amount = total × 0.80
     - [ ] paid_amount = 0 (not yet paid)

2. **SQL verification** (if direct DB access available)
   ```sql
   SELECT * FROM payment_payment WHERE order_id = <order_id>;
   -- Verify: upfront_amount = total_amount * 0.20
   ```

**Expected Result**: Payment record created with correct amounts

---

## Section 6: Online Payment (SSLCommerz) Flow

### Test 6.1: Select Online Payment
**Prerequisites**: On payment selection page, SSLCommerz configured

1. **Select Online option**
   - [ ] Click Online/SSLCommerz radio button
   - [ ] Click "Continue to Payment" button
   - [ ] Should redirect (likely to SSLCommerz gateway)
   - [ ] Check network tab for payment gateway request

2. **Verify Payment model creation**
   - [ ] Admin: Check Payment record created with:
     - [ ] payment_method = 'sslcommerz'
     - [ ] status = 'pending' or 'initiating'
     - [ ] total_amount = full order price (100%)

**Expected Result**: Payment created for full amount, redirects to gateway

### Test 6.2: Complete SSLCommerz Payment (Optional - requires gateway access)
**Prerequisites**: SSLCommerz account with test credentials

1. **Test payment gateway redirect**
   - [ ] Verify redirect to SSLCommerz secure domain: `sslcommerz.com`
   - [ ] Note: May show error if live/test mode mismatch
   - [ ] Check browser security (HTTPS, not blocked)

2. **Simulate payment completion** (if webhook available)
   - [ ] After completion, should redirect back to app
   - [ ] Should see success page: `/payment/success/<payment_id>/`
   - [ ] Payment status should update to 'completed'

**Expected Result**: Successful redirect flow to payment gateway

---

## Section 7: Payment Status Tracking

### Test 7.1: Check Payment Status (AJAX)
**Prerequisites**: Payment created

1. **Test AJAX status check**
   - [ ] Navigate to `/buyer/payment-status/<order_id>/`
   - [ ] With header `X-Requested-With: XMLHttpRequest`
   - [ ] Should return JSON response:
     ```json
     {
       "status": "pending",
       "payment_method": "cod",
       "total_amount": "1000.0",
       "paid_amount": "0.0",
       "remaining_amount": "800.0"
     }
     ```

2. **Test browser view**
   - [ ] Navigate to same URL as regular GET request
   - [ ] Should load `payment_status.html` template
   - [ ] Display timeline visualization
   - [ ] Show status badges

**Expected Result**: AJAX returns JSON, browser view renders template

### Test 7.2: Payment Status Page Display
**Prerequisites**: Payment created

1. **View payment status page**
   - [ ] URL: `/buyer/payment-status/<order_id>/`
   - [ ] Should show timeline:
     - [ ] Order placed ✓
     - [ ] Farmer accepted ✓
     - [ ] Payment status (pending/completed/failed)
   - [ ] Should show payment details card:
     - [ ] Payment method (COD/Online)
     - [ ] Status badge (color-coded)
     - [ ] Current amounts

2. **Test status-specific alerts**
   - [ ] For PENDING payment: Show "Complete payment to proceed"
   - [ ] For COMPLETED payment: Show "Payment confirmed"
   - [ ] For FAILED payment: Show error message

**Expected Result**: Timeline and status information display correctly

---

## Section 8: Success Page & Confirmation

### Test 8.1: View Payment Success Confirmation
**Prerequisites**: Payment status is 'completed'

1. **Access success page**
   - [ ] Method 1: Direct URL `/payment/success/<payment_id>/`
   - [ ] Method 2: After SSLCommerz redirect
   - [ ] Should load without errors
   - [ ] Green success badge visible at top

2. **Verify confirmation content**
   - [ ] Success badge with checkmark
   - [ ] Order confirmation box:
     - [ ] Order ID
     - [ ] Crop details
     - [ ] Quantity
   - [ ] Payment confirmation:
     - [ ] Payment ID (UUID)
     - [ ] Payment method
     - [ ] Total amount paid
     - [ ] Payment date/time
   - [ ] Amount breakdown:
     - [ ] Crop cost
     - [ ] Any fees/taxes
     - [ ] Total amount
   - [ ] Seller information:
     - [ ] Farmer name
     - [ ] Farmer photo
     - [ ] "Contact Farmer" button
   - [ ] Delivery section:
     - [ ] Estimated delivery date
     - [ ] Delivery instructions (if any)
   - [ ] "What happens next" section (5 steps)
   - [ ] Important notes
   - [ ] "Print Receipt" button

3. **Test print functionality**
   - [ ] Click "Print Receipt" or use Ctrl+P
   - [ ] Print preview should show receipt format
   - [ ] All information should be visible
   - [ ] No unnecessary buttons in print

**Expected Result**: Complete confirmation page with all details

### Test 8.2: Authorization on Success Page
**Prerequisites**: Payment exists

1. **Test buyer access**
   - [ ] Login as buyer who made order
   - [ ] Can view `/payment/success/<payment_id>/` ✓

2. **Test farmer access**
   - [ ] Login as farmer who owns order
   - [ ] Can view `/payment/success/<payment_id>/` ✓

3. **Test unauthorized access**
   - [ ] Login as different buyer
   - [ ] Access `/payment/success/<payment_id>/`
   - [ ] Should get "Unauthorized" error
   - [ ] Should redirect to dashboard

**Expected Result**: Only buyer and farmer can view success page

---

## Section 9: Farmer Payment Visibility

### Test 9.1: Farmer Views Payment Status in Order
**Prerequisites**: Order accepted, payment created

1. **Login as farmer**
   - [ ] Access `/farmer/orders/`
   - [ ] Click on order with payment

2. **Verify order detail page**
   - [ ] New payment status card visible
   - [ ] Shows payment method:
     - [ ] COD with emoji ₹
     - [ ] Online with emoji 💳
   - [ ] Shows payment status badge:
     - [ ] Color-coded (pending=yellow, completed=green, failed=red)
   - [ ] Shows amounts:
     - [ ] Total amount
     - [ ] Paid amount
     - [ ] For COD: breakdown of upfront/remaining
   - [ ] Shows alerts based on payment state:
     - [ ] If pending: "Waiting for buyer payment"
     - [ ] If completed: "Payment confirmed - ready to ship"
     - [ ] If failed: "Payment failed - contact buyer"

**Expected Result**: Farmer can see complete payment information for planning fulfillment

### Test 9.2: Farmer Cannot Modify Payment
**Prerequisites**: Order with payment, logged in as farmer

1. **Verify read-only access**
   - [ ] Farmer can view payment details ✓
   - [ ] Farmer cannot edit payment details (no edit button)
   - [ ] Farmer cannot delete payment
   - [ ] Farmer can only see payment status for their orders

**Expected Result**: Farmer has read-only access to payment information

---

## Section 10: Dashboard Integration

### Test 10.1: Buyer Dashboard Payment Stats
**Prerequisites**: Buyer has multiple orders, some with pending payments

1. **View buyer dashboard**
   - [ ] Login as buyer
   - [ ] Navigate to `/buyer/dashboard/`
   - [ ] Look for "Pending Payments" stat card
   - [ ] Should show count of orders awaiting payment
   - [ ] Should display alert box (yellow):
     - [ ] "You have X orders pending payment"
     - [ ] "View Orders" button or link

2. **Test stat calculation**
   - If 3 orders are pending payment:
     - [ ] Stat card shows: "3"
     - [ ] Alert shows: "You have 3 orders pending payment"

3. **Test link to orders**
   - [ ] Click "View Orders" in alert
   - [ ] Should navigate to `/buyer/orders/`
   - [ ] Orders with pending payments should be visible

**Expected Result**: Dashboard accurately displays payment statistics

### Test 10.2: Stat Updates After Payment
**Prerequisites**: Order with pending payment showing on dashboard

1. **Complete payment**
   - [ ] Manually update Payment.status to 'completed' in admin
   - [ ] Or go through SSLCommerz flow

2. **Refresh dashboard**
   - [ ] Navigate back to dashboard
   - [ ] Pending payment count should decrease
   - [ ] Alert should update or disappear (if no pending)

**Expected Result**: Dashboard stats update when payment status changes

---

## Section 11: Error Handling & Edge Cases

### Test 11.1: Access Payment Before Order Accepted
**Prerequisites**: Order is PENDING (not accepted)

1. **Try to access payment selection**
   - [ ] Navigate to `/buyer/payment/<order_id>/`
   - [ ] Should show error: "Order must be accepted first"
   - [ ] Should redirect to order detail page
   - [ ] No Payment record should be created

**Expected Result**: Cannot access payment if order not accepted

### Test 11.2: Try to Create Duplicate Payment
**Prerequisites**: Order already has Payment record

1. **Manually create order with existing payment**
   - [ ] Find order with existing payment
   - [ ] Try to access `/buyer/payment/<order_id>/`
   - [ ] Should detect existing payment
   - [ ] Should redirect to success page instead of selection

**Expected Result**: One payment per order enforced

### Test 11.3: Access Payment with Wrong User
**Prerequisites**: Payment exists, logged in as different buyer

1. **Try unauthorized access**
   - [ ] Login as different buyer
   - [ ] Access payment related URLs
   - [ ] Should get "Unauthorized" message
   - [ ] Should redirect to dashboard

**Expected Result**: Authorization checks prevent cross-user access

### Test 11.4: Invalid Payment UUID
**Prerequisites**: Payment system working

1. **Access non-existent payment**
   - [ ] Try to access `/payment/success/invalid-uuid-format/`
   - [ ] Should show 404 error page
   - [ ] Browser console should not have JavaScript errors

**Expected Result**: Invalid UUIDs handled gracefully

### Test 11.5: Order Status Changes During Payment
**Prerequisites**: Payment in progress, order status modified

1. **Scenario: Order cancelled while payment pending**
   - [ ] Start payment process
   - [ ] (Simulate) Cancel order via admin
   - [ ] Check payment still exists (should have order reference)
   - [ ] Verify no orphaned payments

**Expected Result**: Payment data remains consistent even if order modified

---

## Section 12: Performance & Load Testing

### Test 12.1: Payment Status AJAX Performance
**Prerequisites**: AJAX endpoints working

1. **Measure response time**
   - [ ] Open DevTools Network tab
   - [ ] Get payment status: `/buyer/payment-status/<order_id>/`
   - [ ] Check response time (should be < 500ms)
   - [ ] Check response size (should be < 5KB for JSON)

2. **Database query efficiency**
   - [ ] Enable Django SQL logging
   - [ ] Execute payment status check
   - [ ] Should execute minimal queries (≤ 5 queries expected)

**Expected Result**: AJAX calls respond quickly with minimal database impact

### Test 12.2: Dashboard Load Time with Many Orders
**Prerequisites**: Buyer has 50+ orders

1. **Check dashboard load time**
   - [ ] Navigate to dashboard
   - [ ] Measure page load (Time to Interactive)
   - [ ] Should be < 2 seconds
   - [ ] No layout shifts

2. **Check query count**
   - [ ] Enable query counter middleware
   - [ ] Page load should not exceed 20 queries

**Expected Result**: Dashboard remains performant with many orders

---

## Section 13: Mobile Responsiveness

### Test 13.1: Payment Selection Page on Mobile
**Prerequisites**: Using device or DevTools mobile emulation

1. **Test layout on small screen (375px)**
   - [ ] Page loads without horizontal scroll
   - [ ] Order summary card readable
   - [ ] Payment option cards stack vertically
   - [ ] Buttons are large enough to tap (>44px)
   - [ ] Text is readable (not too small)

2. **Test layout on tablet (768px)**
   - [ ] Payment options displayed side-by-side or optimally
   - [ ] All forms inputs readable and usable

**Expected Result**: Responsive design works on all screen sizes

### Test 13.2: Payment Status Timeline on Mobile
**Prerequisites**: Mobile view, timeline present

1. **Verify timeline renders correctly**
   - [ ] Timeline displays vertically (not horizontally)
   - [ ] Timeline items readable
   - [ ] Status badges visible
   - [ ] Buttons clickable

**Expected Result**: Timeline responsive on mobile

---

## Section 14: Browser Compatibility

### Test 14.1: Test on Different Browsers
- [ ] **Chrome Latest** - Payment flow works
- [ ] **Firefox Latest** - Payment flow works
- [ ] **Safari Latest** - Payment flow works
- [ ] **Edge Latest** - Payment flow works
- [ ] **Mobile Safari** (iOS) - Payment flow works
- [ ] **Chrome Mobile** (Android) - Payment flow works

### Test 14.2: JavaScript Features
- [ ] Radio button selection works
- [ ] Form submission works
- [ ] Print functionality works
- [ ] No console errors visible

**Expected Result**: All browsers support payment features

---

## Section 15: Database Integrity

### Test 15.1: Verify Foreign Key Relationships
**Prerequisites**: Multiple payments exist

1. **Check OneToOne relationship**
   ```python
   from payment.models import Payment
   from farmer.models import Order
   
   # Get payment
   payment = Payment.objects.first()
   order = payment.order
   
   # Verify relationship
   assert order.payment == payment  # Should work
   ```

2. **Verify uniqueness**
   ```python
   # Only one payment per order
   order = Order.objects.first()
   payments = Payment.objects.filter(order=order)
   assert payments.count() == 1 or 0  # Never > 1
   ```

**Expected Result**: Database relationships enforced correctly

### Test 15.2: Check Data Consistency
**Prerequisites**: Multiple completed payments

1. **Verify amount calculations**
   ```python
   for payment in Payment.objects.filter(status='completed'):
       # For COD payments
       if payment.payment_method == 'cod':
           upfront = payment.total_amount * 0.20
           remaining = payment.total_amount * 0.80
           assert abs(payment.upfront_amount - upfront) < 0.01
           assert abs(payment.remaining_amount - remaining) < 0.01
   ```

2. **Verify status transitions**
   - [ ] None have status not in valid choices
   - [ ] Timestamps make logical sense (created < updated)

**Expected Result**: All payment data consistent and valid

---

## Final Verification Checklist

### Before Deployment
- [ ] All tests passed (Sections 1-15)
- [ ] No JavaScript console errors
- [ ] No Python errors in server logs
- [ ] Database migrations clean
- [ ] Static files collected
- [ ] Settings.py production-ready
- [ ] SSL certificates configured (https)
- [ ] Email notifications configured
- [ ] Backup database available

### Post-Deployment
- [ ] Monitor error logs for first 24 hours
- [ ] Verify payment confirmation emails send
- [ ] Test SSLCommerz webhook connectivity
- [ ] Check farmer order fulfillment workflow
- [ ] Verify farmer notifications about payments
- [ ] Monitor transaction success rate

### Performance Baselines (Post-Deployment)
- [ ] Dashboard load time: < 2s
- [ ] Payment status check: < 500ms
- [ ] Payment success page: < 1s
- [ ] Error rate: < 0.1%
- [ ] No database query timeouts

---

## Test Results Summary Template

```
TEST EXECUTION REPORT
======================
Date Tested: ___________
Tester: ________________
Environment: [DEV/STAGING/PRODUCTION]

RESULTS BY SECTION:
Section 1 (Buyer Order): ☐ PASS ☐ FAIL
Section 2 (Farmer Accept): ☐ PASS ☐ FAIL
Section 3 (Payment Visibility): ☐ PASS ☐ FAIL
Section 4 (Payment Selection): ☐ PASS ☐ FAIL
Section 5 (COD Flow): ☐ PASS ☐ FAIL
Section 6 (Online Flow): ☐ PASS ☐ FAIL
Section 7 (Status Tracking): ☐ PASS ☐ FAIL
Section 8 (Success Page): ☐ PASS ☐ FAIL
Section 9 (Farmer Visibility): ☐ PASS ☐ FAIL
Section 10 (Dashboard): ☐ PASS ☐ FAIL
Section 11 (Error Handling): ☐ PASS ☐ FAIL
Section 12 (Performance): ☐ PASS ☐ FAIL
Section 13 (Mobile): ☐ PASS ☐ FAIL
Section 14 (Browsers): ☐ PASS ☐ FAIL
Section 15 (Database): ☐ PASS ☐ FAIL

Issues Found: ___________________
Recommendations: ___________________
Approval: ______________________
```

---

**Testing Guide Version**: 1.0
**Last Updated**: April 21, 2026  
**Total Tests**: 50+
**Estimated Time**: 2-3 hours for full execution
