from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from users.models import CustomUser, FarmerProfile, BuyerProfile, Notification
from users.forms import CustomUserCreationForm, CustomUserChangeForm, FarmerProfileForm, BuyerProfileForm, CustomAuthenticationForm, DynamicRegistrationForm
from farmer.models import Crop, Order, Message
from marketplace.models import CropListing


def register(request):
    """
    Dynamic user registration view
    Handles both Farmer and Buyer registration with role-specific fields
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        print(f"DEBUG REGISTER: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG REGISTER: Role: {request.POST.get('role')}")
        form = DynamicRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            print("DEBUG REGISTER: Form is valid, saving user...")
            user = form.save()
            
            # Create role-specific profile
            if user.role == 'farmer':
                # Create basic farmer profile
                FarmerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'farm_name': f"{user.first_name}'s Farm",
                        'farm_size': 0,
                        'farm_location': f"{user.upazila}, {user.district}",
                        'soil_type': 'Not specified',
                        'experience_years': 0,
                        'registration_number': f"FR-{user.id:06d}",
                    }
                )
            elif user.role == 'buyer':
                # Create basic buyer profile
                BuyerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': user.first_name,
                        'business_type': 'Individual',
                    }
                )
            
            # Create approval request for admin review
            from admin_panel.models import UserApproval
            UserApproval.objects.get_or_create(
                user=user,
                defaults={'status': 'pending'}
            )
            
            # Notify all admins about the new pending approval
            admin_users = CustomUser.objects.filter(role='admin')
            for admin_user in admin_users:
                Notification.objects.create(
                    user=admin_user,
                    notification_type='system',
                    title='New User Approval Request',
                    message=f'New {user.get_role_display()} "{user.username}" ({user.get_full_name()}) has registered and is awaiting approval.'
                )
            
            messages.success(request, f'Account created successfully for {user.first_name}! Your account is pending admin approval. You can browse the platform but certain actions are restricted until approved.')
            return redirect('login')
        else:
            print(f"DEBUG REGISTER: Form errors: {form.errors}")
            # Return errors for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = DynamicRegistrationForm()
    
    context = {'form': form, 'title': 'Register'}
    return render(request, 'users/register.html', context)


def login_view(request):
    """
    User login view - Role-based authentication
    
    Supports:
    - Farmer login with Phone + PIN or Password
    - Buyer login with Email + Password
    
    Database Integration:
    - CustomUser model stores: role, auth_type, pin_hash, phone_number, email
    - Farmer: Uses phone_number as identifier, can use PIN (hashed) or password
    - Buyer: Uses email as identifier, password only
    
    Security:
    - PINs are hashed using Django's make_password/check_password (Bcrypt-compatible)
    - Passwords use Django's built-in authentication (PBKDF2)
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Get the role from the form
        role = request.POST.get('role', 'farmer')
        
        user = None
        
        if role == 'farmer':
            # Farmer login - Phone/Email + PIN or Password
            login_method = request.POST.get('farmer_login_method', 'phone')
            auth_type = request.POST.get('farmer_auth_type', 'pin')
            
            if login_method == 'phone':
                # Login with phone number
                phone_number = request.POST.get('phone_number', '').strip()
                
                # Normalize phone number for lookup
                # Try multiple formats: +880, 880, 0, raw number
                phone_variants = [
                    phone_number,
                    phone_number.replace('+', ''),
                    f'+{phone_number}' if not phone_number.startswith('+') else phone_number,
                    phone_number.replace('+880', '0'),
                    phone_number.replace('880', '0') if phone_number.startswith('880') else phone_number,
                ]
                
                # Find user by phone number
                for phone in phone_variants:
                    try:
                        user = CustomUser.objects.get(phone_number=phone, role='farmer')
                        break
                    except CustomUser.DoesNotExist:
                        continue
            else:
                # Login with email
                farmer_email = request.POST.get('farmer_email', '').strip().lower()
                try:
                    user = CustomUser.objects.get(email=farmer_email, role='farmer')
                except CustomUser.DoesNotExist:
                    user = None
            
            if user:
                if auth_type == 'pin':
                    # PIN authentication
                    pin = request.POST.get('pin', '')
                    
                    # Check if user has PIN set up
                    if not user.pin_hash:
                        messages.error(request, 'Your account uses password authentication. Please switch to Password login.')
                    elif user.check_pin(pin):
                        # Set the backend attribute required by Django's login()
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                        
                        # Force session to be saved with new session key (required for ASGI/Daphne)
                        request.session.modified = True
                        request.session.cycle_key()  # Regenerate session key for security
                        
                        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                        
                        # Create redirect response and ensure session cookie is set
                        from django.http import HttpResponseRedirect
                        from django.urls import reverse
                        response = HttpResponseRedirect(reverse('dashboard'))
                        
                        # Explicitly set the session cookie on the response (required for ASGI/Daphne with custom auth)
                        from django.conf import settings
                        response.set_cookie(
                            settings.SESSION_COOKIE_NAME,
                            request.session.session_key,
                            max_age=getattr(settings, 'SESSION_COOKIE_AGE', 1209600),
                            path=getattr(settings, 'SESSION_COOKIE_PATH', '/'),
                            domain=getattr(settings, 'SESSION_COOKIE_DOMAIN', None),
                            secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
                            httponly=getattr(settings, 'SESSION_COOKIE_HTTPONLY', True),
                            samesite=getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
                        )
                        
                        return response
                    else:
                        messages.error(request, 'Invalid PIN. Please try again.')
                else:
                    # Password authentication for farmer
                    password = request.POST.get('farmer_password', '')
                    authenticated_user = authenticate(username=user.username, password=password)
                    if authenticated_user is not None:
                        login(request, authenticated_user)
                        request.session.modified = True
                        request.session.cycle_key()
                        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                        from django.http import HttpResponseRedirect
                        from django.urls import reverse
                        from django.conf import settings
                        response = HttpResponseRedirect(reverse('dashboard'))
                        response.set_cookie(
                            settings.SESSION_COOKIE_NAME,
                            request.session.session_key,
                            max_age=getattr(settings, 'SESSION_COOKIE_AGE', 1209600),
                            path=getattr(settings, 'SESSION_COOKIE_PATH', '/'),
                            domain=getattr(settings, 'SESSION_COOKIE_DOMAIN', None),
                            secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
                            httponly=getattr(settings, 'SESSION_COOKIE_HTTPONLY', True),
                            samesite=getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
                        )
                        return response
                    else:
                        messages.error(request, 'Invalid password. Please try again.')
            else:
                if login_method == 'phone':
                    messages.error(request, 'No farmer account found with this phone number.')
                else:
                    messages.error(request, 'No farmer account found with this email address.')
        
        elif role == 'buyer':
            # Buyer login - Email + Password
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            
            try:
                user = CustomUser.objects.get(email=email, role='buyer')
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    request.session.modified = True
                    request.session.cycle_key()
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    
                    from django.http import HttpResponseRedirect
                    from django.urls import reverse
                    from django.conf import settings
                    response = HttpResponseRedirect(reverse('dashboard'))
                    response.set_cookie(
                        settings.SESSION_COOKIE_NAME,
                        request.session.session_key,
                        max_age=getattr(settings, 'SESSION_COOKIE_AGE', 1209600),
                        path=getattr(settings, 'SESSION_COOKIE_PATH', '/'),
                        domain=getattr(settings, 'SESSION_COOKIE_DOMAIN', None),
                        secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
                        httponly=getattr(settings, 'SESSION_COOKIE_HTTPONLY', True),
                        samesite=getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
                    )
                    return response
                else:
                    messages.error(request, 'Invalid password. Please try again.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No buyer account found with this email address.')
    
    context = {
        'title': 'Login',
        'selected_role': request.POST.get('role', 'farmer') if request.method == 'POST' else 'farmer',
    }
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

    # New Google users who haven't picked a role yet
    if user.role == 'pending':
        return redirect('google_role_select')

    context = {
        'user': user,
        'title': 'Dashboard'
    }
    
    if user.role == 'farmer':
        farmer_profile = FarmerProfile.objects.filter(user=user).first()
        crops = Crop.objects.filter(farmer=user).count()
        orders = Order.objects.filter(farmer=user).count()
        messages_count = Message.objects.filter(recipient=user, is_read=False).count()
        is_approved = farmer_profile.is_approved if farmer_profile else False
        
        context.update({
            'farmer_profile': farmer_profile,
            'crops_count': crops,
            'orders_count': orders,
            'unread_messages': messages_count,
            'is_approved': is_approved,
        })
        return render(request, 'farmer/dashboard.html', context)
    
    elif user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=user).first()
        orders = Order.objects.filter(buyer=user).count()
        wishlist_count = user.wishlist_items.count()
        messages_count = Message.objects.filter(recipient=user, is_read=False).count()
        is_approved = buyer_profile.is_approved if buyer_profile else False
        
        context.update({
            'buyer_profile': buyer_profile,
            'orders_count': orders,
            'wishlist_count': wishlist_count,
            'unread_messages': messages_count,
            'is_approved': is_approved,
            'total_spent': buyer_profile.total_spent if buyer_profile else 0,
            'active_orders_count': Order.objects.filter(buyer=user, status__in=['pending', 'accepted', 'shipped']).count(),
            'saved_crops_count': 0,
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


# ============================================
# FORGOT CREDENTIAL SYSTEM VIEWS
# ============================================
# 
# This system provides secure credential recovery for both roles:
# - Farmer: Phone OTP → Reset PIN or Password
# - Buyer: Email Link → Reset Password
#
# Security Features:
# - Never reveals if phone/email exists (prevents enumeration)
# - Rate limiting on OTP requests
# - Secure crypto tokens for email reset
# - OTP expires in 5 minutes, email token in 15 minutes
# - Max 3 OTP verification attempts
# ============================================

from users.models import OTPVerification, PasswordResetToken
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import re


def forgot_credential(request):
    """
    Main forgot credential page.
    Shows role selection (Farmer/Buyer) and appropriate form.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {'title': 'Forgot PIN/Password'}
    return render(request, 'users/forgot_credential.html', context)


@csrf_protect
@require_http_methods(["POST"])
def send_otp(request):
    """
    Send OTP to farmer's phone number.
    
    Endpoint: POST /send-otp
    Request: { phone_number: string }
    Response: { success: bool, message: string }
    
    Security:
    - Rate limited (1/min, 5/hour)
    - Never reveals if phone exists
    - OTP expires in 5 minutes
    """
    phone_number = request.POST.get('phone_number', '').strip()
    
    # Normalize phone number (remove spaces, dashes)
    phone_number = re.sub(r'[\s\-]', '', phone_number)
    
    # Validate phone format
    if not re.match(r'^(\+?880|0)?1[3-9]\d{8}$', phone_number):
        return JsonResponse({
            'success': False,
            'message': 'Please enter a valid phone number.'
        }, status=400)
    
    # Check rate limiting
    can_send, rate_limit_msg = OTPVerification.can_send_otp(phone_number)
    if not can_send:
        return JsonResponse({
            'success': False,
            'message': rate_limit_msg
        }, status=429)
    
    # Check if farmer exists with this phone (silently)
    # Try multiple phone formats
    phone_variants = [
        phone_number,
        phone_number.replace('+', ''),
        f'+{phone_number}' if not phone_number.startswith('+') else phone_number,
        phone_number.replace('+880', '0'),
        phone_number.replace('880', '0') if phone_number.startswith('880') else phone_number,
    ]
    
    user = None
    for phone in phone_variants:
        try:
            user = CustomUser.objects.get(phone_number=phone, role='farmer')
            break
        except CustomUser.DoesNotExist:
            continue
    
    # Generate OTP (even if user doesn't exist - security measure)
    otp = OTPVerification.generate_otp(phone_number, purpose='reset')
    
    # If user exists, send OTP via SMS
    if user:
        # TODO: Integrate with SMS API (Twilio, Nexmo, etc.)
        # For now, we'll print to console (development)
        print(f"=== OTP FOR {phone_number} ===")
        print(f"=== CODE: {otp.otp_code} ===")
        print(f"=== EXPIRES: {otp.expires_at} ===")
        
        # Example SMS integration:
        # send_sms(
        #     to=phone_number,
        #     message=f"Your AgriGenie verification code is: {otp.otp_code}. Valid for 5 minutes."
        # )
    
    # Always return success (don't reveal if phone exists)
    return JsonResponse({
        'success': True,
        'message': 'If this account exists, a verification code has been sent to your phone.',
        'phone_number': phone_number  # Return normalized phone for frontend
    })


@csrf_protect
@require_http_methods(["POST"])
def verify_otp(request):
    """
    Verify OTP code entered by user.
    
    Endpoint: POST /verify-otp
    Request: { phone_number: string, otp_code: string }
    Response: { success: bool, message: string, verified: bool }
    
    Security:
    - Max 3 attempts per OTP
    - OTP expires in 5 minutes
    - Invalidates OTP after successful verification
    """
    phone_number = request.POST.get('phone_number', '').strip()
    otp_code = request.POST.get('otp_code', '').strip()
    
    # Normalize phone number
    phone_number = re.sub(r'[\s\-]', '', phone_number)
    
    # Validate inputs
    if not phone_number or not otp_code:
        return JsonResponse({
            'success': False,
            'message': 'Phone number and OTP are required.'
        }, status=400)
    
    if not re.match(r'^\d{6}$', otp_code):
        return JsonResponse({
            'success': False,
            'message': 'Invalid OTP format. Please enter 6 digits.'
        }, status=400)
    
    # Find OTP record
    try:
        otp = OTPVerification.objects.filter(
            phone_number=phone_number,
            is_verified=False
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No pending verification found. Please request a new code.'
        }, status=400)
    
    # Check if expired
    if otp.is_expired():
        return JsonResponse({
            'success': False,
            'message': 'Verification code has expired. Please request a new one.'
        }, status=400)
    
    # Check max attempts
    if otp.is_max_attempts():
        return JsonResponse({
            'success': False,
            'message': 'Maximum attempts exceeded. Please request a new code.'
        }, status=400)
    
    # Verify OTP
    if otp.otp_code != otp_code:
        otp.increment_attempts()
        remaining = 3 - otp.attempts
        return JsonResponse({
            'success': False,
            'message': f'Invalid code. {remaining} attempt(s) remaining.'
        }, status=400)
    
    # OTP verified successfully
    otp.is_verified = True
    otp.save()
    
    # Store verification in session for next step
    request.session['otp_verified_phone'] = phone_number
    request.session['otp_verified_at'] = str(otp.created_at)
    request.session.modified = True
    request.session.save()
    
    # Return response with session cookie explicitly set (for ASGI/Daphne)
    response = JsonResponse({
        'success': True,
        'message': 'Phone verified successfully!',
        'verified': True
    })
    
    # Ensure session cookie is set on the response
    from django.conf import settings
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        request.session.session_key,
        max_age=settings.SESSION_COOKIE_AGE,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    
    return response


@csrf_protect
@require_http_methods(["POST"])
def reset_farmer_credential(request):
    """
    Reset farmer's PIN or password after OTP verification.
    
    Endpoint: POST /reset-credential
    Request: { 
        reset_type: 'pin'|'password',
        new_credential: string,
        confirm_credential: string 
    }
    Response: { success: bool, message: string }
    
    Security:
    - Requires prior OTP verification (session check)
    - Validates PIN (4-6 digits) or password (8+ chars, mixed)
    - Hashes credential before saving
    """
    # Check OTP verification
    verified_phone = request.session.get('otp_verified_phone')
    if not verified_phone:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please verify your phone again.'
        }, status=401)
    
    reset_type = request.POST.get('reset_type', '')
    new_credential = request.POST.get('new_credential', '')
    confirm_credential = request.POST.get('confirm_credential', '')
    
    # Validate inputs
    if reset_type not in ['pin', 'password']:
        return JsonResponse({
            'success': False,
            'message': 'Invalid reset type.'
        }, status=400)
    
    if new_credential != confirm_credential:
        return JsonResponse({
            'success': False,
            'message': 'Credentials do not match.'
        }, status=400)
    
    # Validate credential format
    if reset_type == 'pin':
        if not re.match(r'^\d{4,6}$', new_credential):
            return JsonResponse({
                'success': False,
                'message': 'PIN must be 4-6 digits only.'
            }, status=400)
    else:
        # Password validation
        if len(new_credential) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters.'
            }, status=400)
        if not re.search(r'[A-Z]', new_credential):
            return JsonResponse({
                'success': False,
                'message': 'Password must contain an uppercase letter.'
            }, status=400)
        if not re.search(r'[a-z]', new_credential):
            return JsonResponse({
                'success': False,
                'message': 'Password must contain a lowercase letter.'
            }, status=400)
        if not re.search(r'\d', new_credential):
            return JsonResponse({
                'success': False,
                'message': 'Password must contain a number.'
            }, status=400)
    
    # Find user by phone
    phone_variants = [
        verified_phone,
        verified_phone.replace('+', ''),
        f'+{verified_phone}' if not verified_phone.startswith('+') else verified_phone,
        verified_phone.replace('+880', '0'),
        verified_phone.replace('880', '0') if verified_phone.startswith('880') else verified_phone,
    ]
    
    user = None
    for phone in phone_variants:
        try:
            user = CustomUser.objects.get(phone_number=phone, role='farmer')
            break
        except CustomUser.DoesNotExist:
            continue
    
    if not user:
        # Clear session
        request.session.pop('otp_verified_phone', None)
        request.session.pop('otp_verified_at', None)
        return JsonResponse({
            'success': False,
            'message': 'Account not found. Please try again.'
        }, status=404)
    
    # Update credential
    if reset_type == 'pin':
        user.set_pin(new_credential)
        user.auth_type = 'pin'
        success_msg = 'PIN reset successfully! You can now login with your new PIN.'
    else:
        user.set_password(new_credential)
        user.auth_type = 'password'
        success_msg = 'Password reset successfully! You can now login with your new password.'
    
    user.save()
    
    # Clear session
    request.session.pop('otp_verified_phone', None)
    request.session.pop('otp_verified_at', None)
    
    # Clean up OTP records
    OTPVerification.objects.filter(phone_number=verified_phone).delete()
    
    return JsonResponse({
        'success': True,
        'message': success_msg
    })


@csrf_protect
@require_http_methods(["POST"])
def forgot_password_email(request):
    """
    Send password reset link to buyer's email.
    
    Endpoint: POST /forgot-password
    Request: { email: string }
    Response: { success: bool, message: string }
    
    Security:
    - Never reveals if email exists
    - Token expires in 15 minutes
    - Single-use token
    """
    email = request.POST.get('email', '').strip().lower()
    
    # Validate email format
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return JsonResponse({
            'success': False,
            'message': 'Please enter a valid email address.'
        }, status=400)
    
    # Find buyer with this email (silently)
    try:
        user = CustomUser.objects.get(email=email, role='buyer')
        
        # Generate reset token
        reset_token = PasswordResetToken.generate_token(user)
        
        # Build reset URL
        reset_url = request.build_absolute_uri(
            reverse('reset_password_token', kwargs={'token': reset_token.token})
        )
        
        # Send email
        try:
            send_mail(
                subject='Reset Your AgriGenie Password',
                message=f'''Hello {user.first_name or user.username},

You requested to reset your password for your AgriGenie account.

Click the link below to reset your password:
{reset_url}

This link will expire in 15 minutes.

If you did not request this, please ignore this email.

Best regards,
AgriGenie Team''',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@agrigenie.com'),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email send error: {e}")
            # For development, print the link
            print(f"=== PASSWORD RESET LINK ===")
            print(f"=== EMAIL: {email} ===")
            print(f"=== URL: {reset_url} ===")
            print(f"=== EXPIRES: {reset_token.expires_at} ===")
    
    except CustomUser.DoesNotExist:
        pass  # Silent - don't reveal if email exists
    
    # Always return success (security measure)
    return JsonResponse({
        'success': True,
        'message': 'If this email exists in our system, a password reset link has been sent.'
    })


def reset_password_token(request, token):
    """
    Display password reset form for valid token.
    
    Endpoint: GET /reset-password/<token>
    Shows form if token is valid, error if expired/invalid.
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'This reset link has expired or already been used. Please request a new one.')
            return redirect('forgot_credential')
        
        context = {
            'title': 'Reset Password',
            'token': token,
            'user_email': reset_token.user.email
        }
        return render(request, 'users/reset_password.html', context)
    
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid reset link. Please request a new one.')
        return redirect('forgot_credential')


@csrf_protect
@require_http_methods(["POST"])
def reset_password_submit(request):
    """
    Process password reset form submission.
    
    Endpoint: POST /reset-password
    Request: { token: string, new_password: string, confirm_password: string }
    Response: Redirect to login on success
    
    Security:
    - Validates token existence and expiry
    - Validates password strength
    - Hashes password before saving
    - Deletes token after use
    """
    token = request.POST.get('token', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')
    
    # Validate token
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'This reset link has expired. Please request a new one.')
            return redirect('forgot_credential')
    
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid reset link. Please request a new one.')
        return redirect('forgot_credential')
    
    # Validate passwords match
    if new_password != confirm_password:
        messages.error(request, 'Passwords do not match.')
        return redirect('reset_password_token', token=token)
    
    # Validate password strength
    if len(new_password) < 8:
        messages.error(request, 'Password must be at least 8 characters.')
        return redirect('reset_password_token', token=token)
    
    if not re.search(r'[A-Z]', new_password):
        messages.error(request, 'Password must contain an uppercase letter.')
        return redirect('reset_password_token', token=token)
    
    if not re.search(r'[a-z]', new_password):
        messages.error(request, 'Password must contain a lowercase letter.')
        return redirect('reset_password_token', token=token)
    
    if not re.search(r'\d', new_password):
        messages.error(request, 'Password must contain a number.')
        return redirect('reset_password_token', token=token)
    
    # Update password
    user = reset_token.user
    user.set_password(new_password)
    user.save()
    
    # Mark token as used and delete
    reset_token.mark_used()
    reset_token.delete()
    
    messages.success(request, 'Password reset successfully! You can now login with your new password.')
    return redirect('login')


@login_required(login_url='login')
def google_role_select(request):
    """
    After a new Google sign-in, ask the user to pick Farmer or Buyer.
    Farmers are redirected to complete their profile; buyers go straight to dashboard.
    """
    from django.conf import settings as django_settings
    user = request.user

    if request.method == 'POST':
        role = request.POST.get('role', '')
        if role not in ('farmer', 'buyer'):
            return render(request, 'users/google_role_select.html', {'error': 'Please select a valid role.'})

        user.role = role
        user.save()

        if role == 'buyer':
            from users.models import BuyerProfile
            BuyerProfile.objects.get_or_create(user=user)
            response = redirect('dashboard')
        else:
            response = redirect('profile_edit')

        # ASGI/Daphne session cookie fix
        response.set_cookie(
            django_settings.SESSION_COOKIE_NAME,
            request.session.session_key,
            max_age=django_settings.SESSION_COOKIE_AGE,
            path=django_settings.SESSION_COOKIE_PATH,
            domain=django_settings.SESSION_COOKIE_DOMAIN,
            secure=django_settings.SESSION_COOKIE_SECURE,
            httponly=django_settings.SESSION_COOKIE_HTTPONLY,
            samesite=django_settings.SESSION_COOKIE_SAMESITE,
        )
        return response

    return render(request, 'users/google_role_select.html')


@login_required(login_url='login')
def submit_report(request):
    """Submit a report/feedback about the website"""
    from admin_panel.models import UserReport
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        
        if subject and description and report_type:
            UserReport.objects.create(
                user=request.user,
                report_type=report_type,
                subject=subject,
                description=description,
                priority=priority,
            )
            # Notify admins
            admins = CustomUser.objects.filter(role='admin')
            for admin_user in admins:
                Notification.objects.create(
                    user=admin_user,
                    notification_type='system',
                    title=f'New Report: {subject}',
                    message=f'{request.user.username} submitted a {report_type} report: {subject}'
                )
            messages.success(request, 'Your report has been submitted successfully! An admin will review it shortly.')
            return redirect('my_reports')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'report_types': UserReport.REPORT_TYPES,
        'priority_choices': UserReport.PRIORITY_CHOICES,
        'title': 'Submit a Report',
    }
    return render(request, 'users/submit_report.html', context)


@login_required(login_url='login')
def my_reports(request):
    """View user's submitted reports"""
    from admin_panel.models import UserReport
    
    reports = UserReport.objects.filter(user=request.user)
    
    context = {
        'reports': reports,
        'title': 'My Reports',
    }
    return render(request, 'users/my_reports.html', context)
