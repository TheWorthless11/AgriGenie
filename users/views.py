from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from users.models import CustomUser, FarmerProfile, BuyerProfile, Notification
from users.forms import CustomUserCreationForm, CustomUserChangeForm, FarmerProfileForm, BuyerProfileForm, CustomAuthenticationForm
from farmer.models import Crop, Order, Message
from marketplace.models import CropListing


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}!')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form, 'title': 'Register'}
    return render(request, 'users/register.html', context)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = CustomAuthenticationForm()
    
    context = {'form': form, 'title': 'Login'}
    return render(request, 'users/login.html', context)


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    """User dashboard view"""
    user = request.user
    context = {
        'user': user,
        'title': 'Dashboard'
    }
    
    if user.role == 'farmer':
        farmer_profile = FarmerProfile.objects.filter(user=user).first()
        crops = Crop.objects.filter(farmer=user).count()
        orders = Order.objects.filter(farmer=user).count()
        messages_count = Message.objects.filter(recipient=user, is_read=False).count()
        
        context.update({
            'farmer_profile': farmer_profile,
            'crops_count': crops,
            'orders_count': orders,
            'unread_messages': messages_count,
        })
        return render(request, 'farmer/dashboard.html', context)
    
    elif user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=user).first()
        orders = Order.objects.filter(buyer=user).count()
        wishlist_count = user.wishlist_items.count()
        messages_count = Message.objects.filter(recipient=user, is_read=False).count()
        
        context.update({
            'buyer_profile': buyer_profile,
            'orders_count': orders,
            'wishlist_count': wishlist_count,
            'unread_messages': messages_count,
        })
        return render(request, 'buyer/dashboard.html', context)
    
    elif user.role == 'admin':
        total_users = CustomUser.objects.count()
        total_farmers = CustomUser.objects.filter(role='farmer').count()
        total_buyers = CustomUser.objects.filter(role='buyer').count()
        total_crops = Crop.objects.count()
        total_orders = Order.objects.count()
        
        context.update({
            'total_users': total_users,
            'total_farmers': total_farmers,
            'total_buyers': total_buyers,
            'total_crops': total_crops,
            'total_orders': total_orders,
        })
        return render(request, 'admin_panel/dashboard.html', context)
    
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def profile_view(request, username=None):
    """View user profile"""
    if username:
        user = get_object_or_404(CustomUser, username=username)
    else:
        user = request.user
    
    context = {'profile_user': user}
    
    if user.role == 'farmer':
        farmer_profile = FarmerProfile.objects.filter(user=user).first()
        crops = Crop.objects.filter(farmer=user, is_available=True).count()
        rating = farmer_profile.rating if farmer_profile else 0
        context.update({
            'farmer_profile': farmer_profile,
            'crops_count': crops,
            'rating': rating,
        })
    
    elif user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=user).first()
        context.update({'buyer_profile': buyer_profile})
    
    return render(request, 'users/profile.html', context)


@login_required(login_url='login')
def profile_edit(request):
    """Edit user profile"""
    user = request.user
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            
            # Handle role-specific profile
            if user.role == 'farmer' and request.POST.get('farm_name'):
                farmer_profile, created = FarmerProfile.objects.get_or_create(user=user)
                farmer_form = FarmerProfileForm(request.POST, instance=farmer_profile)
                if farmer_form.is_valid():
                    farmer_form.save()
            
            elif user.role == 'buyer' and request.POST.get('company_name'):
                buyer_profile, created = BuyerProfile.objects.get_or_create(user=user)
                buyer_form = BuyerProfileForm(request.POST, instance=buyer_profile)
                if buyer_form.is_valid():
                    buyer_form.save()
            
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=user)
    
    context = {'form': form, 'title': 'Edit Profile'}
    
    if user.role == 'farmer':
        farmer_profile = FarmerProfile.objects.filter(user=user).first()
        if farmer_profile:
            farmer_form = FarmerProfileForm(instance=farmer_profile)
            context['farmer_form'] = farmer_form
    
    elif user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=user).first()
        if buyer_profile:
            buyer_form = BuyerProfileForm(instance=buyer_profile)
            context['buyer_form'] = buyer_form
    
    return render(request, 'users/profile_edit.html', context)


@login_required(login_url='login')
def notifications_view(request):
    """View user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            notifications.filter(is_read=False).update(is_read=True)
            messages.success(request, 'All notifications marked as read!')
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'title': 'Notifications'
    }
    return render(request, 'users/notifications.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read!')
    return redirect('notifications')


def home(request):
    """Home page view"""
    featured_crops = CropListing.objects.filter(is_featured=True)[:6]
    latest_crops = Crop.objects.filter(is_available=True).order_by('-created_at')[:6]
    total_farmers = CustomUser.objects.filter(role='farmer').count()
    total_crops = Crop.objects.filter(is_available=True).count()
    
    context = {
        'featured_crops': featured_crops,
        'latest_crops': latest_crops,
        'total_farmers': total_farmers,
        'total_crops': total_crops,
        'title': 'AgriGenie - Home'
    }
    return render(request, 'home.html', context)
