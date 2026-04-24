import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction as db_transaction

from farmer.models import Order
from users.models import Notification
from .models import Payment
from .forms import PaymentMethodForm
from .gateway import SSLCommerzGateway, calculate_cod_amounts

logger = logging.getLogger(__name__)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def choose_payment_method(request, order_id):
    """Buyer chooses payment method after farmer approves order"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    # Check if order is accepted by farmer
    if order.status != 'accepted':
        messages.error(request, 'Order must be accepted by farmer before payment.')
        return redirect('buyer_orders')
    
    # Check if payment already exists
    if hasattr(order, 'payment'):
        messages.warning(request, 'Payment for this order is already processed.')
        return redirect('order_detail', order_id=order.id)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Create payment record
            with db_transaction.atomic():
                payment = Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    total_amount=order.total_price,
                )
                
                if payment_method == 'cod':
                    # Calculate 20% upfront, 80% at delivery
                    amounts = calculate_cod_amounts(order.total_price)
                    payment.upfront_amount = amounts['upfront']
                    payment.remaining_amount = amounts['remaining']
                    payment.paid_amount = amounts['upfront']
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    # Notify farmer about payment method
                    Notification.objects.create(
                        user=order.farmer,
                        notification_type='payment',
                        title=f'Payment Method Selected - Order {order.id}',
                        message=f'Buyer chose Cash on Delivery. Upfront: ৳{amounts["upfront"]:.2f}, Balance: ৳{amounts["remaining"]:.2f} at delivery'
                    )
                    
                    messages.success(
                        request, 
                        f'Cash on Delivery selected! Pay ৳{amounts["upfront"]:.2f} upfront, ৳{amounts["remaining"]:.2f} at delivery.'
                    )
                    return redirect('order_payment_success', order_id=order.id)
                
                elif payment_method == 'sslcommerz':
                    # Prepare for online payment
                    return redirect('initiate_sslcommerz_payment', order_id=order.id)
    else:
        form = PaymentMethodForm()
    
    context = {
        'order': order,
        'form': form,
        'total_amount': order.total_price,
    }
    return render(request, 'payment/choose_payment_method.html', context)


@login_required(login_url='login')
def initiate_sslcommerz_payment(request, order_id):
    """Initiate SSLCommerz payment"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    try:
        payment = get_object_or_404(Payment, order=order)
        
        if payment.payment_method != 'sslcommerz':
            messages.error(request, 'Invalid payment method.')
            return redirect('buyer_orders')
        
        # Initialize SSLCommerz gateway
        gateway = SSLCommerzGateway()
        
        if not gateway.config:
            messages.error(request, 'Payment gateway not configured. Please contact support.')
            logger.error("SSLCommerz gateway not configured")
            return redirect('buyer_orders')
        
        # Initiate payment
        result = gateway.initiate_payment(payment, request)
        
        if result['success']:
            messages.info(request, 'Redirecting to payment gateway...')
            return redirect(result['gateway_url'])
        else:
            messages.error(request, f"Payment initiation failed: {result.get('error', 'Unknown error')}")
            payment.status = 'failed'
            payment.save()
            return redirect('buyer_orders')
    
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
        return redirect('buyer_orders')
    except Exception as e:
        logger.error(f"Error initiating SSLCommerz payment: {str(e)}")
        messages.error(request, 'An error occurred. Please try again.')
        return redirect('buyer_orders')


@require_http_methods(["POST", "GET"])
def payment_success(request):
    """Handle successful payment from SSLCommerz"""
    try:
        validation_id = request.POST.get('val_id') or request.GET.get('val_id')
        
        if not validation_id:
            messages.error(request, 'Invalid payment response.')
            return redirect('buyer_orders')
        
        # Initialize gateway
        gateway = SSLCommerzGateway()
        
        # Validate payment with SSLCommerz - find payment first by validation_id in progress
        payment = Payment.objects.filter(ssl_session_id__isnull=False, status='initiating').first()
        
        if not payment:
            messages.error(request, 'Payment record not found.')
            return redirect('buyer_orders')
        
        validation_result = gateway.validate_payment(payment, validation_id)
        
        if validation_result['success']:
            transaction_id = validation_result.get('tran_id')
            
            # Payment is already updated in gateway.validate_payment()
            order = payment.order
            
            # Update order status
            order.status = 'paid'
            order.save()
            
            # Create notification for buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='payment',
                title=f'Payment Successful - Order {order.id}',
                message=f'Your payment of ৳{order.total_price:.2f} has been confirmed. Order is ready for shipment.'
            )
            
            # Create notification for farmer
            Notification.objects.create(
                user=order.farmer,
                notification_type='payment',
                title=f'Payment Received - Order {order.id}',
                message=f'Payment of ৳{order.total_price:.2f} received from buyer. Please prepare for shipment.'
            )
            
            messages.success(request, 'Payment successful! Your order is confirmed.')
            return redirect('order_payment_success', order_id=order.id)
        else:
            messages.error(request, 'Payment validation failed. Please contact support.')
            return redirect('buyer_orders')
    
    except Exception as e:
        logger.error(f"Error in payment success handler: {str(e)}")
        messages.error(request, 'An error occurred processing your payment.')
        return redirect('buyer_orders')


@require_http_methods(["POST", "GET"])
def payment_failed(request):
    """Handle failed payment from SSLCommerz"""
    try:
        validation_id = request.POST.get('val_id') or request.GET.get('val_id')
        
        if validation_id:
            # Find and update payment status
            payment = Payment.objects.filter(ssl_validation_id=validation_id).first()
            if payment:
                payment.status = 'failed'
                payment.save()
        
        messages.error(request, 'Payment failed. Please try again or choose a different payment method.')
        return redirect('buyer_orders')
    
    except Exception as e:
        logger.error(f"Error in payment failed handler: {str(e)}")
        return redirect('buyer_orders')


@require_http_methods(["POST", "GET"])
def payment_cancelled(request):
    """Handle cancelled payment from SSLCommerz"""
    try:
        messages.warning(request, 'Payment was cancelled. You can try again later.')
        return redirect('buyer_orders')
    except Exception as e:
        logger.error(f"Error in payment cancelled handler: {str(e)}")
        return redirect('buyer_orders')


@login_required(login_url='login')
def order_payment_success(request, order_id):
    """Display order payment success page"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    if not hasattr(order, 'payment'):
        messages.error(request, 'Payment record not found for this order.')
        return redirect('buyer_orders')
    
    payment = order.payment
    
    context = {
        'order': order,
        'payment': payment,
        'upfront_amount': payment.upfront_amount,
        'remaining_amount': payment.remaining_amount,
    }
    
    return render(request, 'payment/payment_success.html', context)


@login_required(login_url='login')
def payment_details(request, payment_id):
    """View payment details"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Check authorization
    if payment.order.buyer != request.user and payment.order.farmer != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    context = {
        'payment': payment,
        'order': payment.order,
    }
    
    return render(request, 'payment/payment_details.html', context)


@login_required(login_url='login')
def verify_payment(request, order_id):
    """Manual verification of payment (for COD orders)"""
    order = get_object_or_404(Order, id=order_id)
    
    # Only farmer can verify COD payments
    if order.farmer != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if not hasattr(order, 'payment'):
        messages.error(request, 'No payment record for this order.')
        return redirect('farmer_orders')
    
    payment = order.payment
    
    if payment.payment_method != 'cod':
        messages.error(request, 'This operation is only for COD orders.')
        return redirect('farmer_orders')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm_delivery_payment':
            # Farmer confirms receipt of remaining balance
            payment.paid_amount = payment.total_amount
            payment.remaining_amount = 0
            payment.save()
            
            order.status = 'delivered'
            order.save()
            
            # Notify buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='payment',
                title=f'Payment Complete - Order {order.id}',
                message=f'Payment of ৳{payment.remaining_amount:.2f} received. Order completed.'
            )
            
            messages.success(request, 'Remaining payment confirmed. Order marked as delivered.')
            return redirect('order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'payment': payment,
    }
    
    return render(request, 'payment/verify_payment.html', context)
