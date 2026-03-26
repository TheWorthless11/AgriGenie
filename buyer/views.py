from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta
from buyer.models import PurchaseRequest, WishlistItem, SavedCrop, BuyerRating
from farmer.models import Crop, Order, Message
from marketplace.models import CropListing, Review
from users.models import Notification, CustomUser, BuyerProfile
from farmer.forms import OrderForm, MessageForm


def is_buyer_approved(user):
    """Check if a buyer is approved by admin"""
    profile = BuyerProfile.objects.filter(user=user).first()
    return profile and profile.is_approved


@login_required(login_url='login')
def buyer_dashboard(request):
    """Buyer dashboard"""
    if request.user.role != 'buyer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    orders = Order.objects.filter(buyer=request.user)
    recent_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    wishlist_items = WishlistItem.objects.filter(buyer=request.user)
    
    context = {
        'orders': orders,
        'recent_messages': recent_messages,
        'wishlist_items': wishlist_items,
        'orders_count': orders.count(),
        'wishlist_count': wishlist_items.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'is_approved': is_buyer_approved(request.user),
    }
    return render(request, 'buyer/dashboard.html', context)


@login_required(login_url='login')
def marketplace(request):
    """Marketplace - Browse crops with new listing alerts"""
    if request.user.role != 'buyer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    crops = Crop.objects.filter(is_available=True).select_related('farmer').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    new_crops = crops.filter(created_at__gte=timezone.now() - timedelta(days=1))
    
    # Search and filter
    search_query = request.GET.get('q')
    crop_type = request.GET.get('crop_type')
    location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if search_query:
        crops = crops.filter(
            Q(crop_name__icontains=search_query) |
            Q(crop_type__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if crop_type:
        crops = crops.filter(crop_type=crop_type)
    
    if location:
        crops = crops.filter(location__icontains=location)
    
    if min_price:
        crops = crops.filter(price_per_unit__gte=float(min_price))
    
    if max_price:
        crops = crops.filter(price_per_unit__lte=float(max_price))
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(crops, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'crops': page_obj,
        'new_crops_count': new_crops.count(),
        'search_query': search_query,
        'saved_crop_ids': list(SavedCrop.objects.filter(buyer=request.user).values_list('crop_id', flat=True)),
        'title': 'Marketplace'
    }
    return render(request, 'buyer/marketplace.html', context)


@login_required(login_url='login')
def crop_detail(request, crop_id):
    """View crop details"""
    crop = get_object_or_404(Crop, id=crop_id, is_available=True)
    
    # Update view count
    try:
        listing = CropListing.objects.get(crop=crop)
        listing.views_count += 1
        listing.save()
    except CropListing.DoesNotExist:
        pass
    
    reviews = Review.objects.filter(crop=crop).select_related('reviewer')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    is_in_wishlist = WishlistItem.objects.filter(buyer=request.user, crop=crop).exists()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'place_order':
            form = OrderForm(request.POST)
            if form.is_valid():
                order = form.save(commit=False)
                order.crop = crop
                order.buyer = request.user
                order.farmer = crop.farmer
                order.total_price = order.quantity * crop.price_per_unit
                order.save()
                
                # Create notification for farmer
                Notification.objects.create(
                    user=crop.farmer,
                    notification_type='order',
                    title=f'New Order: {crop.crop_name}',
                    message=f'{request.user.username} ordered {order.quantity} {crop.unit} of {crop.crop_name}'
                )
                
                messages.success(request, 'Order placed successfully!')
                return redirect('buyer_orders')
        
        elif action == 'add_to_wishlist':
            WishlistItem.objects.get_or_create(buyer=request.user, crop=crop)
            messages.success(request, 'Added to wishlist!')
            return redirect('crop_detail', crop_id=crop.id)
        
        elif action == 'remove_from_wishlist':
            WishlistItem.objects.filter(buyer=request.user, crop=crop).delete()
            messages.success(request, 'Removed from wishlist!')
            return redirect('crop_detail', crop_id=crop.id)
    
    order_form = OrderForm()
    
    context = {
        'crop': crop,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'order_form': order_form,
        'is_in_wishlist': is_in_wishlist,
        'farmer': crop.farmer,
        'title': crop.crop_name
    }
    return render(request, 'buyer/crop_detail.html', context)


@login_required(login_url='login')
def buyer_orders(request):
    """View buyer's orders"""
    if request.user.role != 'buyer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    all_orders = Order.objects.filter(buyer=request.user)
    pending_count = all_orders.filter(status='pending').count()
    delivered_count = all_orders.filter(status='delivered').count()
    
    orders = all_orders.order_by('-order_date')
    status_filter = request.GET.get('status')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Get buyer's total spent
    from users.models import BuyerProfile
    buyer_profile = BuyerProfile.objects.filter(user=request.user).first()
    
    context = {
        'orders': orders,
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'total_spent': buyer_profile.total_spent if buyer_profile else 0,
        'title': 'My Orders',
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'buyer/orders.html', context)


@login_required(login_url='login')
def confirm_receipt(request, order_id):
    """Confirm receipt of order"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    if order.status == 'delivered':
        order.is_confirmed_by_buyer = True
        order.confirmation_date = timezone.now()
        order.save()
        
        # Add to buyer's total spent
        from users.models import BuyerProfile
        buyer_profile, _ = BuyerProfile.objects.get_or_create(user=request.user)
        buyer_profile.total_spent += order.total_price
        buyer_profile.save()
        
        # Create notification for farmer
        Notification.objects.create(
            user=order.farmer,
            notification_type='order',
            title='Order Confirmed',
            message=f'Buyer confirmed receipt of {order.crop.crop_name}'
        )
        
        messages.success(request, f'Order confirmed! ৳{order.total_price:.2f} added to your total spending.')
    
    return redirect('buyer_orders')


@login_required(login_url='login')
def wishlist(request):
    """View wishlist"""
    if request.user.role != 'buyer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    wishlist_items = WishlistItem.objects.filter(buyer=request.user).select_related('crop')
    
    context = {
        'wishlist_items': wishlist_items,
        'title': 'My Wishlist'
    }
    return render(request, 'buyer/wishlist.html', context)


@login_required(login_url='login')
def saved_crops(request):
    """View saved crops"""
    if request.user.role != 'buyer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    saved = SavedCrop.objects.filter(buyer=request.user).select_related('crop')
    
    context = {
        'saved_crops': saved,
        'title': 'Saved Crops'
    }
    return render(request, 'buyer/saved_crops.html', context)


@login_required(login_url='login')
def contact_farmer(request, farmer_id):
    """Contact farmer"""
    if not is_buyer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot contact farmers until approved.')
        return redirect('marketplace')
    
    farmer = get_object_or_404(CustomUser, id=farmer_id, role='farmer')
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = farmer
            message.save()
            
            # Create notification
            Notification.objects.create(
                user=farmer,
                notification_type='message',
                title=f'Message from {request.user.username}',
                message=form.cleaned_data.get('subject')
            )
            
            messages.success(request, 'Message sent to farmer!')
            return redirect('buyer_dashboard')
    else:
        form = MessageForm()
    
    context = {
        'form': form,
        'farmer': farmer,
        'title': f'Contact {farmer.username}'
    }
    return render(request, 'buyer/contact_farmer.html', context)


@login_required(login_url='login')
def leave_review(request, crop_id):
    """Leave review for a crop"""
    if not is_buyer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot leave reviews until approved.')
        return redirect('crop_detail', crop_id=crop_id)
    
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check if buyer has ordered this crop
    has_ordered = Order.objects.filter(buyer=request.user, crop=crop, status='delivered').exists()
    
    if not has_ordered:
        messages.error(request, 'You can only review crops you have ordered!')
        return redirect('crop_detail', crop_id=crop.id)
    
    existing_review = Review.objects.filter(crop=crop, reviewer=request.user).first()
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        review_text = request.POST.get('review')
        
        if existing_review:
            existing_review.rating = rating
            existing_review.title = title
            existing_review.review_text = review_text
            existing_review.save()
            messages.success(request, 'Review updated!')
        else:
            Review.objects.create(
                crop=crop,
                reviewer=request.user,
                rating=rating,
                title=title,
                review_text=review_text,
                verified_purchase=True
            )
            messages.success(request, 'Review posted successfully!')
        
        return redirect('crop_detail', crop_id=crop.id)
    
    context = {
        'crop': crop,
        'existing_review': existing_review,
        'title': f'Review {crop.crop_name}'
    }
    return render(request, 'buyer/leave_review.html', context)


@login_required(login_url='login')
def purchase_history(request):
    """View purchase history"""
    if request.user.role != 'buyer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    orders = Order.objects.filter(buyer=request.user, status='delivered').order_by('-delivery_date')
    
    context = {
        'orders': orders,
        'title': 'Purchase History'
    }
    return render(request, 'buyer/purchase_history.html', context)


@login_required(login_url='login')
def place_order(request, crop_id):
    """Place order for a crop"""
    if request.user.role != 'buyer':
        messages.error(request, 'Only buyers can place orders!')
        return redirect('dashboard')
    
    if not is_buyer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot place orders until approved.')
        return redirect('crop_detail', crop_id=crop_id)
    
    crop = get_object_or_404(Crop, id=crop_id, is_available=True)
    
    if request.method == 'POST':
        try:
            quantity = float(request.POST.get('quantity', 0))
            delivery_date_str = request.POST.get('delivery_date')
            special_requirements = request.POST.get('special_requirements', '')
            
            if quantity <= 0:
                messages.error(request, 'Quantity must be greater than 0')
                return redirect('crop_detail', crop_id=crop_id)
            
            if quantity > crop.quantity:
                messages.error(request, f'Only {crop.quantity} {crop.unit} available')
                return redirect('crop_detail', crop_id=crop_id)
            
            from datetime import datetime
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
            
            # Create order
            total_price = quantity * crop.price_per_unit
            order = Order.objects.create(
                crop=crop,
                buyer=request.user,
                farmer=crop.farmer,
                quantity=quantity,
                total_price=total_price,
                delivery_date=delivery_date,
                special_requirements=special_requirements,
                status='pending'
            )
            
            # Create notification for farmer
            from users.models import Notification
            Notification.objects.create(
                user=crop.farmer,
                notification_type='order',
                title=f'New Order: {crop.crop_name}',
                message=f'{request.user.username} ordered {quantity} {crop.unit} of {crop.crop_name}'
            )
            
            messages.success(request, 'Order placed successfully! The farmer will respond shortly.')
            return redirect('order_detail', order_id=order.id)
            
        except ValueError:
            messages.error(request, 'Invalid input. Please check your entries.')
            return redirect('crop_detail', crop_id=crop_id)
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
            return redirect('crop_detail', crop_id=crop_id)
    
    return redirect('crop_detail', crop_id=crop_id)


@login_required(login_url='login')
def cancel_order(request, order_id):
    """Cancel a pending order"""
    if request.method != 'POST':
        return redirect('buyer_orders')

    from farmer.models import Order
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    if order.status != 'pending':
        messages.error(request, 'Only pending orders can be cancelled.')
        return redirect('buyer_orders')

    order.status = 'cancelled'
    order.save()

    # Restore quantity if order was accepted before cancellation
    if order.status == 'cancelled':
        # Only restore if it was previously accepted (quantity was deducted)
        pass  # Pending orders don't deduct quantity, no restore needed

    # Notify farmer
    from users.models import Notification
    Notification.objects.create(
        user=order.farmer,
        notification_type='order',
        title=f'Order Cancelled: {order.crop.crop_name}',
        message=f'{request.user.username} cancelled their order for {order.quantity} {order.crop.unit} of {order.crop.crop_name}'
    )

    messages.success(request, 'Order cancelled successfully.')
    return redirect('buyer_orders')
