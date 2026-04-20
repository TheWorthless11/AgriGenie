from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db.models import Q, Avg, Count
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.sessions.models import Session
from django.utils import timezone
from users.models import (
    CustomUser,
    FarmerProfile,
    BuyerProfile,
    Notification,
    FarmerSettings,
    FarmerPaymentMethod,
)
from users.forms import (
    CustomUserCreationForm,
    CustomUserChangeForm,
    FarmerProfileForm,
    FarmerProfileBasicForm,
    BuyerProfileForm,
    CustomAuthenticationForm,
    DynamicRegistrationForm,
    AdminProfileUpdateForm,
    FarmerAccountSettingsForm,
    FarmerPreferenceSettingsForm,
    FarmerNotificationSettingsForm,
    FarmerAISettingsForm,
    FarmerPaymentMethodForm,
)
from farmer.models import Crop, Order, Message
from marketplace.models import CropListing
from admin_panel.models import ActivityLog
import json


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _describe_device(user_agent):
    ua = (user_agent or '').lower()

    platform = 'Unknown OS'
    if 'windows' in ua:
        platform = 'Windows'
    elif 'android' in ua:
        platform = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        platform = 'iOS'
    elif 'mac os' in ua or 'macintosh' in ua:
        platform = 'macOS'
    elif 'linux' in ua:
        platform = 'Linux'

    browser = 'Browser'
    if 'edg' in ua:
        browser = 'Edge'
    elif 'chrome' in ua and 'edg' not in ua:
        browser = 'Chrome'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'firefox' in ua:
        browser = 'Firefox'

    return f'{platform} / {browser}'


def _log_activity(user, action, description='', request=None):
    """Best-effort activity logging used by profile/admin UX sections."""
    if not user or not user.is_authenticated:
        return

    try:
        ActivityLog.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=_client_ip(request) if request else None,
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''),
        )
    except Exception:
        # Logging must never block core user flows.
        pass


def _active_sessions_for_user(user, current_session_key=None):
    sessions = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()).order_by('-expire_date'):
        try:
            session_data = session.get_decoded()
        except Exception:
            continue

        if str(session_data.get('_auth_user_id')) != str(user.id):
            continue

        sessions.append({
            'session_key': session.session_key,
            'expires_at': session.expire_date,
            'is_current': bool(current_session_key and session.session_key == current_session_key),
        })

    return sessions


def _profile_completion_percent(user):
    checkpoints = [
        bool(user.first_name),
        bool(user.last_name),
        bool(user.email),
        bool(user.phone_number),
        bool(user.profile_picture),
    ]
    return round((sum(checkpoints) / len(checkpoints)) * 100)


def start_google_login(request):
    """
    Start Google OAuth from a guaranteed-clean session.

    Flushes any stale / corrupted session data, creates a fresh session,
    explicitly saves it to the DB, and sets the cookie on the redirect
    response so the next hop (allauth's login view) inherits a valid,
    persisted session that can safely store the OAuth state.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    # 1. Wipe every trace of the old (possibly corrupted) session.
    request.session.flush()

    # 2. Seed the fresh session with a marker so it is non-empty and
    #    Django's SessionMiddleware will actually persist it + set the cookie.
    request.session['_google_oauth'] = True
    request.session.save()

    # 3. Build redirect, then force-set the cookie ourselves as well
    #    (belt-and-suspenders for Daphne / ASGI).
    from django.conf import settings as _s
    target = f"{reverse('google_login')}?process=login"
    response = redirect(target)
    response.set_cookie(
        _s.SESSION_COOKIE_NAME,
        request.session.session_key,
        max_age=_s.SESSION_COOKIE_AGE,
        path=_s.SESSION_COOKIE_PATH,
        domain=_s.SESSION_COOKIE_DOMAIN,
        secure=_s.SESSION_COOKIE_SECURE,
        httponly=_s.SESSION_COOKIE_HTTPONLY,
        samesite=_s.SESSION_COOKIE_SAMESITE,
    )
    return response


def register(request):
    """
    Dynamic user registration view
    Handles both Farmer and Buyer registration with role-specific fields
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        print(f"DEBUG REGISTER: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG REGISTER: FILES data keys: {list(request.FILES.keys())}")
        print(f"DEBUG REGISTER: Role: {request.POST.get('role')}")
        form = DynamicRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            print("DEBUG REGISTER: Form is valid, saving user...")
            user = form.save()
            
            # Create role-specific profile
            if user.role == 'farmer':
                # Create basic farmer profile
                farmer_profile, _ = FarmerProfile.objects.get_or_create(
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
                # Farmers get full access immediately.
                farmer_profile.is_approved = True
                farmer_profile.save(update_fields=['is_approved'])
            elif user.role == 'buyer':
                # Create basic buyer profile
                BuyerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': user.first_name,
                        'business_type': 'Individual',
                    }
                )

                # Buyers require super-admin approval with required documents.
                from admin_panel.models import UserApproval
                UserApproval.objects.get_or_create(
                    user=user,
                    defaults={
                        'status': 'pending',
                        'legal_paper_photo': form.cleaned_data.get('legal_paper_photo'),
                        'company_photo': form.cleaned_data.get('company_photo'),
                    }
                )
            
            messages.success(request, f'Account created successfully for {user.first_name}!')
            # Auto-login and redirect to onboarding wizard
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            request.session.modified = True
            request.session.cycle_key()
            print(f"DEBUG REGISTER: User logged in: {request.user.is_authenticated}, session key: {request.session.session_key}")

            from django.http import HttpResponseRedirect
            from django.urls import reverse
            from django.conf import settings as django_settings

            if user.role == 'farmer':
                target = reverse('farmer_onboarding')
            elif user.role == 'buyer':
                target = reverse('buyer_onboarding')
            else:
                target = reverse('login')

            print(f"DEBUG REGISTER: Redirecting to {target}")
            response = HttpResponseRedirect(target)

            response.set_cookie(
                django_settings.SESSION_COOKIE_NAME,
                request.session.session_key,
                max_age=getattr(django_settings, 'SESSION_COOKIE_AGE', 1209600),
                path=getattr(django_settings, 'SESSION_COOKIE_PATH', '/'),
                domain=getattr(django_settings, 'SESSION_COOKIE_DOMAIN', None),
                secure=getattr(django_settings, 'SESSION_COOKIE_SECURE', False),
                httponly=getattr(django_settings, 'SESSION_COOKIE_HTTPONLY', True),
                samesite=getattr(django_settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
            )
            return response
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
                        _log_activity(user, 'login', 'Logged in successfully using PIN authentication.', request)
                        
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
                        _log_activity(authenticated_user, 'login', 'Logged in successfully using password authentication.', request)
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
                    _log_activity(authenticated_user, 'login', 'Buyer logged in successfully.', request)
                    
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


@login_required(login_url='login')
def farmer_onboarding(request):
    """Farmer onboarding wizard — collects farm identity & preferences after registration."""
    if request.user.role != 'farmer':
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            user = request.user

            # Profile picture
            if request.FILES.get('profile_picture'):
                user.profile_picture = request.FILES['profile_picture']

            # Location fields
            city = request.POST.get('city', '').strip()
            district = request.POST.get('district', '').strip()
            postal_code = request.POST.get('postal_code', '').strip()
            street = request.POST.get('street_address', '').strip()
            country = request.POST.get('country', 'Bangladesh').strip()

            user.upazila = city
            user.district = district
            user.country = country
            user.location = ', '.join(filter(None, [street, city, district, postal_code, country]))
            user.save()

            # Update farmer profile
            farm_name = request.POST.get('farm_name', '').strip() or f"{user.first_name}'s Farm"
            measurement = request.POST.get('measurement_system', 'metric')
            currency = request.POST.get('currency', 'BDT')
            timezone = request.POST.get('timezone', 'Asia/Dhaka')

            fp, _ = FarmerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'farm_name': farm_name,
                    'farm_size': 0,
                    'farm_location': user.location or '',
                    'soil_type': 'Not specified',
                    'experience_years': 0,
                    'registration_number': f"FR-{user.id:06d}",
                }
            )
            fp.farm_name = farm_name
            fp.farm_location = user.location or ''
            
            # Handle NID submission
            nid_number = request.POST.get('nid_number', '').strip()
            nid_card_photo = request.FILES.get('nid_card_photo')
            
            if nid_number and nid_card_photo:
                from admin_panel.models import UserApproval
                
                # Create or update UserApproval for farmer
                approval, _ = UserApproval.objects.get_or_create(
                    user=user,
                    defaults={'status': 'pending'}
                )
                approval.nid_number = nid_number
                approval.nid_card_photo = nid_card_photo
                approval.status = 'pending'
                approval.reason_for_rejection = ''
                approval.reviewed_by = None
                approval.reviewed_at = None
                try:
                    approval.save()
                except IntegrityError:
                    return JsonResponse({
                        'success': False,
                        'error': 'The provided NID is already linked to another approval request.'
                    }, status=400)
                
                # Update farmer profile approval status
                fp.approval_status = 'pending'
                
                # Notify super admins about new farmer submission
                admin_users = CustomUser.objects.filter(role='admin', is_superuser=True)
                for admin_user in admin_users:
                    Notification.objects.create(
                        user=admin_user,
                        notification_type='system',
                        title='New Farmer NID Submission',
                        message=f'Farmer "{user.get_full_name() or user.username}" submitted NID for approval.'
                    )
            else:
                # No NID submitted, mark as not_submitted
                fp.approval_status = 'not_submitted'
            
            fp.save()

            return JsonResponse({'success': True})
        
        except Exception as e:
            import traceback
            print(f"ERROR in farmer_onboarding: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=500)

    context = {
        'google_maps_key': getattr(__import__('django.conf', fromlist=['settings']).settings, 'GOOGLE_MAPS_API_KEY', ''),
    }
    return render(request, 'users/farmer_onboarding.html', context)


@login_required(login_url='login')
def buyer_onboarding(request):
    """Buyer onboarding wizard — collects location, preferences & account type."""
    if request.user.role != 'buyer':
        return redirect('dashboard')

    if request.method == 'POST':
        user = request.user

        # Profile picture
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']

        # Location fields
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        street = request.POST.get('street_address', '').strip()
        country = request.POST.get('country', 'Bangladesh').strip()

        user.upazila = city
        user.district = district
        user.country = country
        user.location = ', '.join(filter(None, [street, city, district, postal_code, country]))
        user.preferences = request.POST.get('preferences', '')
        user.save()

        # Update buyer profile
        account_type = request.POST.get('account_type', 'household')
        business_type = 'Individual' if account_type == 'household' else 'Wholesaler'

        bp, _ = BuyerProfile.objects.get_or_create(
            user=user,
            defaults={
                'company_name': user.first_name,
                'business_type': business_type,
            }
        )
        bp.business_type = business_type
        bp.save()

        return JsonResponse({'success': True})

    context = {
        'google_maps_key': getattr(__import__('django.conf', fromlist=['settings']).settings, 'GOOGLE_MAPS_API_KEY', ''),
    }
    return render(request, 'users/buyer_onboarding.html', context)


def logout_view(request):
    """User logout view"""
    if request.user.is_authenticated:
        _log_activity(request.user, 'logout', 'User logged out.', request)
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('login')


@never_cache
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
        # Keep farmer dashboard data in one place to avoid context drift.
        from farmer.views import farmer_dashboard

        return farmer_dashboard(request)
    
    elif user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=user).first()
        orders = Order.objects.filter(buyer=user).count()
        wishlist_count = user.wishlist_items.count()
        messages_count = Message.objects.filter(recipient=user, is_read=False).count()
        is_approved = buyer_profile.is_approved if buyer_profile else False

        from admin_panel.models import UserApproval
        approval_request = getattr(user, 'approval_request', None)
        if not is_approved and approval_request is None:
            approval_request, _ = UserApproval.objects.get_or_create(
                user=user,
                defaults={'status': 'pending'}
            )

        documents_submitted = bool(
            approval_request and approval_request.legal_paper_photo and approval_request.company_photo
        )
        
        context.update({
            'buyer_profile': buyer_profile,
            'orders_count': orders,
            'wishlist_count': wishlist_count,
            'unread_messages': messages_count,
            'is_approved': is_approved,
            'approval_request': approval_request,
            'documents_submitted': documents_submitted,
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
def submit_buyer_approval_documents(request):
    """Allow pending buyers to submit or replace approval photos for super-admin review."""
    if request.user.role != 'buyer':
        messages.error(request, 'Only buyers can submit approval documents.')
        return redirect('dashboard')

    buyer_profile, _ = BuyerProfile.objects.get_or_create(user=request.user)
    if buyer_profile.is_approved:
        messages.info(request, 'Your buyer account is already approved.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('dashboard')

    legal_paper_photo = request.FILES.get('legal_paper_photo')
    company_photo = request.FILES.get('company_photo')

    if not legal_paper_photo or not company_photo:
        messages.error(request, 'Please upload both legal papers photo and company photo.')
        return redirect('dashboard')

    from admin_panel.models import UserApproval
    approval, _ = UserApproval.objects.get_or_create(user=request.user, defaults={'status': 'pending'})
    approval.legal_paper_photo = legal_paper_photo
    approval.company_photo = company_photo
    approval.status = 'pending'
    approval.reason_for_rejection = ''
    approval.reviewed_by = None
    approval.reviewed_at = None
    approval.save()

    admin_users = CustomUser.objects.filter(role='admin')
    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            notification_type='system',
            title='Buyer Documents Submitted',
            message=f'Buyer "{request.user.username}" submitted approval documents for review.'
        )

    messages.success(request, 'Your documents were submitted successfully. Awaiting super admin review.')
    return redirect('dashboard')


@never_cache
@login_required(login_url='login')
def profile_view(request, username=None):
    """View user profile"""
    if username:
        profile_user = get_object_or_404(CustomUser, username=username)
    else:
        profile_user = request.user
    
    context = {
        'profile_user': profile_user,
        'can_edit_profile': request.user.id == profile_user.id,
    }

    if profile_user.role == 'admin':
        current_session_key = request.session.session_key if request.user.id == profile_user.id else None
        active_sessions = _active_sessions_for_user(profile_user, current_session_key=current_session_key)
        current_device = _describe_device(request.META.get('HTTP_USER_AGENT', ''))
        role_label = 'Super Admin' if profile_user.is_superuser else 'Admin'

        context.update({
            'role_label': role_label,
            'last_login_time': profile_user.last_login,
            'account_created': profile_user.created_at,
            'profile_completion': _profile_completion_percent(profile_user),
            'recent_activities': ActivityLog.objects.filter(user=profile_user).order_by('-timestamp')[:8],
            'active_sessions': active_sessions[:5],
            'active_sessions_count': len(active_sessions),
            'current_device': current_device,
            'can_manage_security': request.user.id == profile_user.id,
        })
        return render(request, 'users/admin_profile.html', context)
    
    if profile_user.role == 'farmer':
        farmer_profile = FarmerProfile.objects.filter(user=profile_user).first()
        crops = Crop.objects.filter(farmer=profile_user).count()
        completed_orders = (
            Order.objects.filter(
                Q(farmer=profile_user) | Q(crop__farmer=profile_user),
                status='delivered',
            )
            .distinct()
            .count()
        )
        rating = farmer_profile.rating if farmer_profile else 0

        experience_years = farmer_profile.experience_years if farmer_profile else 0
        if experience_years >= 10:
            farmer_badge = 'Expert'
            badge_class = 'badge-expert'
        elif experience_years >= 4:
            farmer_badge = 'Intermediate'
            badge_class = 'badge-intermediate'
        else:
            farmer_badge = 'Beginner'
            badge_class = 'badge-beginner'

        profile_location = profile_user.get_full_location() if profile_user.get_full_location() else ''
        if not profile_location and farmer_profile and farmer_profile.farm_location:
            profile_location = farmer_profile.farm_location
        if not profile_location:
            profile_location = 'Not set'

        latest_irrigation_record = profile_user.irrigation_records.order_by('-date', '-created_at').first()
        irrigation_type = latest_irrigation_record.get_method_display() if latest_irrigation_record else 'Not specified'

        context.update({
            'farmer_profile': farmer_profile,
            'crops_count': crops,
            'total_crops_listed': crops,
            'total_orders_completed': completed_orders,
            'rating': rating,
            'farmer_badge': farmer_badge,
            'badge_class': badge_class,
            'profile_location': profile_location,
            'irrigation_type': irrigation_type,
        })
        return render(request, 'users/farmer_profile.html', context)
    
    elif profile_user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=profile_user).first()
        context.update({'buyer_profile': buyer_profile})
    
    return render(request, 'users/profile.html', context)


@login_required(login_url='login')
def profile_edit(request):
    """Edit user profile"""
    user = request.user
    form_class = AdminProfileUpdateForm if user.role == 'admin' else CustomUserChangeForm
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            _log_activity(user, 'update_profile', 'Updated account profile details.', request)
            messages.success(request, 'Profile updated successfully!')

            if user.role == 'admin':
                return redirect('profile')
            
            # Handle role-specific profile
            if user.role == 'farmer' and request.POST.get('farm_name'):
                farmer_profile, _ = FarmerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'farm_name': request.POST.get('farm_name') or f"{user.username}'s Farm",
                        'farm_size': 0,
                        'farm_location': request.POST.get('farm_location') or (user.get_full_location() or user.location or ''),
                        'soil_type': 'Not specified',
                        'experience_years': 0,
                        'registration_number': f'FR-{user.id:06d}',
                    },
                )
                farmer_form = FarmerProfileBasicForm(request.POST, instance=farmer_profile)
                if farmer_form.is_valid():
                    farmer_form.save()
                else:
                    for _, errs in farmer_form.errors.items():
                        for err in errs:
                            messages.error(request, err)
            
            elif user.role == 'buyer' and request.POST.get('company_name'):
                buyer_profile, created = BuyerProfile.objects.get_or_create(user=user)
                buyer_form = BuyerProfileForm(request.POST, instance=buyer_profile)
                if buyer_form.is_valid():
                    buyer_form.save()
            
            return redirect('profile')
    else:
        form = form_class(instance=user)
    
    context = {
        'form': form,
        'title': 'Edit Profile',
        'is_admin_profile_edit': user.role == 'admin',
    }
    
    if user.role == 'farmer':
        farmer_profile, _ = FarmerProfile.objects.get_or_create(
            user=user,
            defaults={
                'farm_name': f"{user.username}'s Farm",
                'farm_size': 0,
                'farm_location': user.get_full_location() or user.location or '',
                'soil_type': 'Not specified',
                'experience_years': 0,
                'registration_number': f'FR-{user.id:06d}',
            },
        )
        farmer_form = FarmerProfileBasicForm(instance=farmer_profile)
        context['farmer_form'] = farmer_form
    
    elif user.role == 'buyer':
        buyer_profile = BuyerProfile.objects.filter(user=user).first()
        if buyer_profile:
            buyer_form = BuyerProfileForm(instance=buyer_profile)
            context['buyer_form'] = buyer_form
    
    return render(request, 'users/profile_edit.html', context)


@never_cache
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def farmer_settings(request):
    """Modern multi-section settings page for farmer accounts."""
    if request.user.role != 'farmer':
        messages.error(request, 'Only farmer accounts can access this page.')
        return redirect('dashboard')

    user = request.user

    farmer_profile, _ = FarmerProfile.objects.get_or_create(
        user=user,
        defaults={
            'farm_name': f"{user.first_name}'s Farm" if user.first_name else f"{user.username}'s Farm",
            'farm_size': 0,
            'farm_location': user.get_full_location() or user.location or '',
            'soil_type': 'Not specified',
            'experience_years': 0,
            'registration_number': f'FR-{user.id:06d}',
        },
    )
    settings_obj, _ = FarmerSettings.objects.get_or_create(user=user)

    tab_for_action = {
        'save_account': 'account',
        'save_security': 'security',
        'change_password': 'security',
        'save_preferences': 'preferences',
        'save_notifications': 'notifications',
        'save_ai': 'ai',
        'save_payment_method': 'payment',
        'delete_payment_method': 'payment',
        'download_data': 'privacy',
        'delete_account': 'privacy',
    }
    valid_tabs = {'account', 'security', 'preferences', 'notifications', 'ai', 'payment', 'privacy'}

    def _styled_password_form(form):
        for field in form.fields.values():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing_class + ' form-control').strip()
        return form

    active_tab = request.GET.get('tab', 'account')
    if active_tab not in valid_tabs:
        active_tab = 'account'

    account_form = FarmerAccountSettingsForm(instance=user)
    password_form = _styled_password_form(PasswordChangeForm(user))
    preference_form = FarmerPreferenceSettingsForm(instance=settings_obj)
    notification_form = FarmerNotificationSettingsForm(instance=settings_obj)
    ai_form = FarmerAISettingsForm(instance=settings_obj)
    payment_form = FarmerPaymentMethodForm()

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        active_tab = tab_for_action.get(action, active_tab)

        if action == 'save_account':
            account_form = FarmerAccountSettingsForm(request.POST, request.FILES, instance=user)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, 'Account settings updated successfully.')
                return redirect(f'{request.path}?tab=account')
            messages.error(request, 'Please correct the highlighted account fields.')

        elif action == 'save_security':
            user.two_factor_enabled = bool(request.POST.get('two_factor_enabled'))
            user.save(update_fields=['two_factor_enabled'])
            status_text = 'enabled' if user.two_factor_enabled else 'disabled'
            messages.success(request, f'Two-factor authentication {status_text}.')
            return redirect(f'{request.path}?tab=security')

        elif action == 'change_password':
            password_form = _styled_password_form(PasswordChangeForm(user, request.POST))
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                _log_activity(user, 'update_profile', 'Changed password from farmer settings page.', request)
                messages.success(request, 'Password changed successfully.')
                return redirect(f'{request.path}?tab=security')
            messages.error(request, 'Please correct the password fields and try again.')

        elif action == 'save_preferences':
            preference_form = FarmerPreferenceSettingsForm(request.POST, instance=settings_obj)
            if preference_form.is_valid():
                preference_form.save()
                messages.success(request, 'Farm preferences saved.')
                return redirect(f'{request.path}?tab=preferences')
            messages.error(request, 'Please correct the farm preference values.')

        elif action == 'save_notifications':
            notification_form = FarmerNotificationSettingsForm(request.POST, instance=settings_obj)
            if notification_form.is_valid():
                notification_form.save()
                messages.success(request, 'Notification preferences updated.')
                return redirect(f'{request.path}?tab=notifications')
            messages.error(request, 'Unable to save notification preferences.')

        elif action == 'save_ai':
            ai_form = FarmerAISettingsForm(request.POST, instance=settings_obj)
            if ai_form.is_valid():
                ai_form.save()
                messages.success(request, 'AI settings updated.')
                return redirect(f'{request.path}?tab=ai')
            messages.error(request, 'Please review AI settings and try again.')

        elif action == 'save_payment_method':
            method_id = (request.POST.get('method_id') or '').strip()
            method_instance = None
            if method_id:
                method_instance = get_object_or_404(FarmerPaymentMethod, id=method_id, user=user)

            payment_form = FarmerPaymentMethodForm(request.POST, instance=method_instance)
            if payment_form.is_valid():
                payment_method = payment_form.save(commit=False)
                payment_method.user = user
                payment_method.save()
                messages.success(request, 'Payment method saved successfully.')
                return redirect(f'{request.path}?tab=payment')
            messages.error(request, 'Please correct payment method details.')

        elif action == 'delete_payment_method':
            method_id = (request.POST.get('method_id') or '').strip()
            payment_method = get_object_or_404(FarmerPaymentMethod, id=method_id, user=user)
            payment_method.delete()
            messages.success(request, 'Payment method removed.')
            return redirect(f'{request.path}?tab=payment')

        elif action == 'download_data':
            export_orders = (
                Order.objects.filter(Q(farmer=user) | Q(crop__farmer=user))
                .select_related('buyer', 'crop')
                .distinct()
                .order_by('-order_date')[:100]
            )

            payload = {
                'exported_at': timezone.now().isoformat(),
                'account': {
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'location': user.get_full_location() or user.location,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                },
                'farm_information': {
                    'farm_name': farmer_profile.farm_name,
                    'farm_size': farmer_profile.farm_size,
                    'farm_location': farmer_profile.farm_location,
                    'soil_type': farmer_profile.soil_type,
                    'experience_years': farmer_profile.experience_years,
                    'rating': farmer_profile.rating,
                },
                'preferences': {
                    'quantity_unit': settings_obj.quantity_unit,
                    'farm_size_unit': settings_obj.farm_size_unit,
                    'default_crop_type': settings_obj.default_crop_type,
                    'language': settings_obj.language,
                },
                'notifications': {
                    'email_notifications': settings_obj.email_notifications,
                    'sms_alerts': settings_obj.sms_alerts,
                    'order_updates': settings_obj.order_updates,
                    'ai_alerts': settings_obj.ai_alerts,
                },
                'ai_settings': {
                    'disease_detection_enabled': settings_obj.disease_detection_enabled,
                    'auto_recommendations': settings_obj.auto_recommendations,
                    'risk_sensitivity': settings_obj.risk_sensitivity,
                },
                'payment_methods': list(
                    FarmerPaymentMethod.objects.filter(user=user).values(
                        'method_type',
                        'account_name',
                        'account_number',
                        'bank_name',
                        'is_active',
                        'created_at',
                    )
                ),
                'transaction_history': [
                    {
                        'order_id': order.id,
                        'crop': order.crop.crop_name if order.crop else None,
                        'buyer': order.buyer.username if order.buyer else None,
                        'quantity': order.quantity,
                        'total_price': order.total_price,
                        'status': order.status,
                        'order_date': order.order_date.isoformat() if order.order_date else None,
                    }
                    for order in export_orders
                ],
            }

            response = HttpResponse(
                json.dumps(payload, indent=2, default=str),
                content_type='application/json',
            )
            filename = f"agrigenie_farmer_data_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        elif action == 'delete_account':
            confirm_text = (request.POST.get('delete_confirmation') or '').strip()
            delete_password = request.POST.get('delete_password') or ''

            if confirm_text != 'DELETE_ACCOUNT':
                messages.error(request, 'Please type DELETE_ACCOUNT to confirm account deletion.')
            elif not user.check_password(delete_password):
                messages.error(request, 'Incorrect password. Account deletion cancelled.')
            else:
                username = user.username
                _log_activity(user, 'security_logout', 'Account deleted from farmer settings.', request)
                logout(request)
                user.delete()
                messages.success(request, f'Account {username} deleted successfully.')
                return redirect('home')

        else:
            messages.error(request, 'Unknown action requested.')

    last_login_activity = ActivityLog.objects.filter(user=user, action='login').order_by('-timestamp')[:5]
    payment_methods = FarmerPaymentMethod.objects.filter(user=user, is_active=True)
    transactions = (
        Order.objects.filter(Q(farmer=user) | Q(crop__farmer=user))
        .select_related('buyer', 'crop')
        .distinct()
        .order_by('-order_date')[:12]
    )

    context = {
        'title': 'Farmer Settings',
        'active_tab': active_tab,
        'account_form': account_form,
        'password_form': password_form,
        'preference_form': preference_form,
        'notification_form': notification_form,
        'ai_form': ai_form,
        'payment_form': payment_form,
        'farmer_profile': farmer_profile,
        'last_login_activity': last_login_activity,
        'payment_methods': payment_methods,
        'transactions': transactions,
    }
    return render(request, 'users/farmer_settings.html', context)


@never_cache
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def buyer_settings(request):
    """Modern multi-section settings page for buyer accounts."""
    if request.user.role != 'buyer':
        messages.error(request, 'Only buyer accounts can access this page.')
        return redirect('dashboard')

    user = request.user

    buyer_profile, _ = BuyerProfile.objects.get_or_create(
        user=user,
        defaults={
            'company_name': user.first_name or user.username,
            'business_type': 'Individual',
            'registration_number': '',
        },
    )

    tab_for_action = {
        'save_account': 'account',
        'save_security': 'security',
        'change_password': 'security',
        'save_business': 'business',
        'download_data': 'privacy',
        'delete_account': 'privacy',
    }
    valid_tabs = {'account', 'security', 'business', 'privacy'}

    def _styled_password_form(form):
        for field in form.fields.values():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing_class + ' form-control').strip()
        return form

    active_tab = request.GET.get('tab', 'account')
    if active_tab not in valid_tabs:
        active_tab = 'account'

    account_form = FarmerAccountSettingsForm(instance=user)
    password_form = _styled_password_form(PasswordChangeForm(user))
    business_form = BuyerProfileForm(instance=buyer_profile)

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        active_tab = tab_for_action.get(action, active_tab)

        if action == 'save_account':
            account_form = FarmerAccountSettingsForm(request.POST, request.FILES, instance=user)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, 'Account settings updated successfully.')
                return redirect(f'{request.path}?tab=account')
            messages.error(request, 'Please correct the highlighted account fields.')

        elif action == 'save_security':
            user.two_factor_enabled = bool(request.POST.get('two_factor_enabled'))
            user.save(update_fields=['two_factor_enabled'])
            status_text = 'enabled' if user.two_factor_enabled else 'disabled'
            messages.success(request, f'Two-factor authentication {status_text}.')
            return redirect(f'{request.path}?tab=security')

        elif action == 'change_password':
            password_form = _styled_password_form(PasswordChangeForm(user, request.POST))
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                _log_activity(user, 'update_profile', 'Changed password from buyer settings page.', request)
                messages.success(request, 'Password changed successfully.')
                return redirect(f'{request.path}?tab=security')
            messages.error(request, 'Please correct the password fields and try again.')

        elif action == 'save_business':
            business_form = BuyerProfileForm(request.POST, instance=buyer_profile)
            if business_form.is_valid():
                business_form.save()
                messages.success(request, 'Business details updated successfully.')
                return redirect(f'{request.path}?tab=business')
            messages.error(request, 'Please correct the business details fields.')

        elif action == 'download_data':
            purchase_orders = (
                Order.objects.filter(buyer=user)
                .select_related('crop', 'crop__farmer')
                .order_by('-order_date')[:100]
            )

            payload = {
                'exported_at': timezone.now().isoformat(),
                'account': {
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'location': user.get_full_location() or user.location,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                },
                'business_information': {
                    'company_name': buyer_profile.company_name,
                    'business_type': buyer_profile.business_type,
                    'registration_number': buyer_profile.registration_number,
                    'is_approved': buyer_profile.is_approved,
                    'rating': buyer_profile.rating,
                    'total_spent': buyer_profile.total_spent,
                },
                'preferences': user.preferences,
                'purchase_history': [
                    {
                        'order_id': order.id,
                        'crop': order.crop.crop_name if order.crop else None,
                        'farmer': order.crop.farmer.username if order.crop and order.crop.farmer else None,
                        'quantity': order.quantity,
                        'total_price': order.total_price,
                        'status': order.status,
                        'order_date': order.order_date.isoformat() if order.order_date else None,
                    }
                    for order in purchase_orders
                ],
            }

            response = HttpResponse(
                json.dumps(payload, indent=2, default=str),
                content_type='application/json',
            )
            filename = f"agrigenie_buyer_data_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        elif action == 'delete_account':
            confirm_text = (request.POST.get('delete_confirmation') or '').strip()
            delete_password = request.POST.get('delete_password') or ''

            if confirm_text != 'DELETE_ACCOUNT':
                messages.error(request, 'Please type DELETE_ACCOUNT to confirm account deletion.')
            elif not user.check_password(delete_password):
                messages.error(request, 'Incorrect password. Account deletion cancelled.')
            else:
                username = user.username
                _log_activity(user, 'security_logout', 'Account deleted from buyer settings.', request)
                logout(request)
                user.delete()
                messages.success(request, f'Account {username} deleted successfully.')
                return redirect('home')

        else:
            messages.error(request, 'Unknown action requested.')

    last_login_activity = ActivityLog.objects.filter(user=user, action='login').order_by('-timestamp')[:5]

    context = {
        'title': 'Buyer Settings',
        'active_tab': active_tab,
        'account_form': account_form,
        'password_form': password_form,
        'business_form': business_form,
        'buyer_profile': buyer_profile,
        'last_login_activity': last_login_activity,
    }
    return render(request, 'users/buyer_settings.html', context)


@login_required(login_url='login')
def change_password_view(request):
    """Allow authenticated users to change password from profile security section."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            _log_activity(request.user, 'update_profile', 'Changed account password.', request)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    for field in form.fields.values():
        existing_class = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = (existing_class + ' form-control').strip()

    return render(request, 'users/change_password.html', {
        'form': form,
        'title': 'Change Password',
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def toggle_two_factor(request):
    """Simple profile-level two-factor toggle state."""
    request.user.two_factor_enabled = not request.user.two_factor_enabled
    request.user.save(update_fields=['two_factor_enabled'])

    state = 'enabled' if request.user.two_factor_enabled else 'disabled'
    _log_activity(request.user, 'toggle_2fa', f'Two-factor authentication {state}.', request)
    messages.success(request, f'Two-factor authentication {state}.')
    return redirect('profile')


@login_required(login_url='login')
@require_http_methods(["POST"])
def logout_all_devices(request):
    """Terminate all active sessions for the current user."""
    user = request.user
    terminated = 0

    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        try:
            session_data = session.get_decoded()
        except Exception:
            continue

        if str(session_data.get('_auth_user_id')) == str(user.id):
            session.delete()
            terminated += 1

    _log_activity(user, 'security_logout', f'Ended {terminated} active session(s).', request)
    logout(request)
    messages.success(request, f'Logged out from {terminated} session(s). Please sign in again.')
    return redirect('login')


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

            from admin_panel.models import UserApproval
            UserApproval.objects.get_or_create(user=user, defaults={'status': 'pending'})

            admin_users = CustomUser.objects.filter(role='admin')
            for admin_user in admin_users:
                Notification.objects.create(
                    user=admin_user,
                    notification_type='system',
                    title='New Buyer Approval Request',
                    message=f'New buyer "{user.username}" selected role via Google sign-in and is awaiting approval.'
                )

            response = redirect('dashboard')
        else:
            farmer_profile, _ = FarmerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'farm_name': f"{user.first_name or user.username}'s Farm",
                    'farm_size': 0,
                    'farm_location': f"{user.upazila}, {user.district}" if user.upazila and user.district else 'Not specified',
                    'soil_type': 'Not specified',
                    'experience_years': 0,
                    'registration_number': f"FR-{user.id:06d}",
                }
            )
            farmer_profile.is_approved = True
            farmer_profile.save(update_fields=['is_approved'])
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
