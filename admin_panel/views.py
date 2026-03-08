from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from admin_panel.models import UserApproval, SystemAlert, SystemReport, AIDiseaseMonitor, AIPricePredictor, ActivityLog
from users.models import CustomUser, FarmerProfile, BuyerProfile, Notification
from farmer.models import Crop, Order, CropDisease
from marketplace.models import CropListing


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == 'admin'


@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    total_users = CustomUser.objects.count()
    total_farmers = CustomUser.objects.filter(role='farmer').count()
    total_buyers = CustomUser.objects.filter(role='buyer').count()
    pending_approvals = UserApproval.objects.filter(status='pending').count()
    
    total_crops = Crop.objects.count()
    active_crops = Crop.objects.filter(is_available=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Calculate revenue from delivered orders
    total_revenue = sum([order.total_price for order in Order.objects.filter(status='delivered')])
    
    # Recent activities
    recent_activities = ActivityLog.objects.all().order_by('-timestamp')[:10]
    
    # AI Model Statistics
    disease_monitor = AIDiseaseMonitor.objects.first()
    price_predictor = AIPricePredictor.objects.first()
    
    # Today's statistics
    today = timezone.now().date()
    today_orders = Order.objects.filter(order_date__date=today).count()
    today_crops = Crop.objects.filter(created_at__date=today).count()
    
    context = {
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'pending_approvals': pending_approvals,
        'total_crops': total_crops,
        'active_crops': active_crops,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'recent_activities': recent_activities,
        'disease_monitor': disease_monitor,
        'price_predictor': price_predictor,
        'today_orders': today_orders,
        'today_crops': today_crops,
        'title': 'Admin Dashboard'
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def user_approvals(request):
    """Manage user approvals"""
    approvals = UserApproval.objects.all().select_related('user').order_by('-created_at')
    status_filter = request.GET.get('status')
    role_filter = request.GET.get('role')
    
    if status_filter:
        approvals = approvals.filter(status=status_filter)
    
    if role_filter:
        approvals = approvals.filter(user__role=role_filter)
    
    context = {
        'approvals': approvals,
        'status_choices': [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        'role_choices': [('farmer', 'Farmer'), ('buyer', 'Buyer')],
        'title': 'User Approvals'
    }
    return render(request, 'admin_panel/user_approvals.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def approve_user(request, approval_id):
    """Approve a user"""
    approval = get_object_or_404(UserApproval, id=approval_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            approval.status = 'approved'
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            
            # Update user profile
            user = approval.user
            if user.role == 'farmer':
                farmer_profile = FarmerProfile.objects.filter(user=user).first()
                if farmer_profile:
                    farmer_profile.is_approved = True
                    farmer_profile.save()
            elif user.role == 'buyer':
                buyer_profile = BuyerProfile.objects.filter(user=user).first()
                if buyer_profile:
                    buyer_profile.is_approved = True
                    buyer_profile.save()
            
            # Send notification
            Notification.objects.create(
                user=user,
                notification_type='system',
                title='Account Approved',
                message=f'Your {user.get_role_display()} account has been approved!'
            )
            
            messages.success(request, f'{user.username} approved successfully!')
        
        elif action == 'reject':
            reason = request.POST.get('reason', 'No reason provided')
            approval.status = 'rejected'
            approval.reason_for_rejection = reason
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            
            # Send notification
            Notification.objects.create(
                user=approval.user,
                notification_type='system',
                title='Account Rejected',
                message=f'Your {approval.user.get_role_display()} account was rejected. Reason: {reason}'
            )
            
            messages.success(request, f'{approval.user.username} rejected!')
        
        return redirect('user_approvals')
    
    context = {'approval': approval, 'title': 'Review User Approval'}
    return render(request, 'admin_panel/approval_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def reject_user(request, approval_id):
    """Reject a user"""
    approval = get_object_or_404(UserApproval, id=approval_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided')
        approval.status = 'rejected'
        approval.reason_for_rejection = reason
        approval.reviewed_by = request.user
        approval.reviewed_at = timezone.now()
        approval.save()
        
        # Send notification to user
        Notification.objects.create(
            user=approval.user,
            notification_type='system',
            title='Account Rejected',
            message=f'Your {approval.user.get_role_display()} account was rejected. Reason: {reason}'
        )
        
        messages.success(request, f'{approval.user.username} has been rejected.')
        return redirect('user_approvals')
    
    context = {'approval': approval, 'title': 'Reject User'}
    return render(request, 'admin_panel/reject_user.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def user_management(request):
    """Manage users"""
    users = CustomUser.objects.all().order_by('-created_at')
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    from django.core.paginator import Paginator
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'role_choices': CustomUser.ROLE_CHOICES,
        'title': 'User Management'
    }
    return render(request, 'admin_panel/user_management.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'{user.username} activated!')
        
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'{user.username} deactivated!')
        
        elif action == 'verify':
            user.is_verified = True
            user.save()
            messages.success(request, f'{user.username} verified!')
        
        return redirect('user_detail', user_id=user.id)
    
    # Get user statistics
    if user.role == 'farmer':
        crops_count = Crop.objects.filter(farmer=user).count()
        orders_count = Order.objects.filter(farmer=user).count()
        profile = FarmerProfile.objects.filter(user=user).first()
        context = {
            'user': user,
            'profile': profile,
            'crops_count': crops_count,
            'orders_count': orders_count,
            'title': f'{user.username} - Details'
        }
    elif user.role == 'buyer':
        orders_count = Order.objects.filter(buyer=user).count()
        profile = BuyerProfile.objects.filter(user=user).first()
        context = {
            'user': user,
            'profile': profile,
            'orders_count': orders_count,
            'title': f'{user.username} - Details'
        }
    else:
        context = {'user': user, 'title': f'{user.username} - Details'}
    
    return render(request, 'admin_panel/user_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def crop_management(request):
    """Manage crop listings"""
    crops = Crop.objects.all().select_related('farmer').order_by('-created_at')
    status_filter = request.GET.get('status')
    
    if status_filter == 'available':
        crops = crops.filter(is_available=True)
    elif status_filter == 'unavailable':
        crops = crops.filter(is_available=False)
    
    from django.core.paginator import Paginator
    paginator = Paginator(crops, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'crops': page_obj,
        'title': 'Crop Management'
    }
    return render(request, 'admin_panel/crop_management.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def crop_detail_admin(request, crop_id):
    """View and manage crop"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove':
            crop_name = crop.crop_name
            crop.delete()
            messages.success(request, f'{crop_name} removed!')
            return redirect('crop_management')
        
        elif action == 'toggle_availability':
            crop.is_available = not crop.is_available
            crop.save()
            messages.success(request, f'Availability updated!')
            return redirect('crop_detail_admin', crop_id=crop.id)
    
    # Get related information
    orders = Order.objects.filter(crop=crop)
    reviews = crop.reviews.all()
    
    context = {
        'crop': crop,
        'orders': orders,
        'reviews': reviews,
        'orders_count': orders.count(),
        'title': f'{crop.crop_name} - Management'
    }
    return render(request, 'admin_panel/crop_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def system_alerts_admin(request):
    """Manage system alerts"""
    alerts = SystemAlert.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            title = request.POST.get('title')
            message = request.POST.get('message')
            alert_type = request.POST.get('type')
            all_users = request.POST.get('all_users') == 'on'
            
            alert = SystemAlert.objects.create(
                title=title,
                message=message,
                alert_type=alert_type,
                all_users=all_users,
                created_by=request.user
            )
            messages.success(request, 'Alert created successfully!')
            return redirect('system_alerts_admin')
    
    context = {
        'alerts': alerts,
        'alert_types': SystemAlert.ALERT_TYPES,
        'title': 'System Alerts'
    }
    return render(request, 'admin_panel/system_alerts.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def system_reports(request):
    """View system reports"""
    reports = SystemReport.objects.all().order_by('-generated_at')
    
    # Generate stats
    total_users = CustomUser.objects.count()
    total_farmers = CustomUser.objects.filter(role='farmer').count()
    total_buyers = CustomUser.objects.filter(role='buyer').count()
    total_crops = Crop.objects.count()
    total_orders = Order.objects.count()
    total_revenue = sum([order.total_price for order in Order.objects.filter(status='delivered')])
    
    # Last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_orders = Order.objects.filter(order_date__gte=seven_days_ago).count()
    recent_crops = Crop.objects.filter(created_at__gte=seven_days_ago).count()
    recent_users = CustomUser.objects.filter(created_at__gte=seven_days_ago).count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'generate_report':
            report = SystemReport.objects.create(
                title=f'Report {timezone.now().strftime("%Y-%m-%d")}',
                report_type='user_stats',
                total_users=total_users,
                total_farmers=total_farmers,
                total_buyers=total_buyers,
                total_crops_listed=total_crops,
                total_orders=total_orders,
                total_revenue=total_revenue,
                generated_by=request.user
            )
            messages.success(request, 'Report generated successfully!')
    
    context = {
        'reports': reports,
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'total_crops': total_crops,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'recent_crops': recent_crops,
        'recent_users': recent_users,
        'title': 'System Reports'
    }
    return render(request, 'admin_panel/system_reports.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def ai_monitoring(request):
    """Monitor AI models performance"""
    disease_monitor = AIDiseaseMonitor.objects.first()
    price_predictor = AIPricePredictor.objects.first()
    
    # Get recent disease detections
    recent_diseases = CropDisease.objects.all().order_by('-detected_date')[:10]
    
    # Recent price predictions (placeholder — CropPrice model removed)
    recent_prices = []
    
    context = {
        'disease_monitor': disease_monitor,
        'price_predictor': price_predictor,
        'recent_diseases': recent_diseases,
        'recent_prices': recent_prices,
        'title': 'AI Monitoring'
    }
    return render(request, 'admin_panel/ai_monitoring.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def activity_logs(request):
    """View activity logs"""
    logs = ActivityLog.objects.all().order_by('-timestamp')
    action_filter = request.GET.get('action')
    user_filter = request.GET.get('user')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj,
        'action_choices': ActivityLog.ACTION_TYPES,
        'title': 'Activity Logs'
    }
    return render(request, 'admin_panel/activity_logs.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def crop_management(request):
    """Manage crop listings"""
    crops = Crop.objects.all().select_related('farmer').order_by('-created_at')
    search_query = request.GET.get('search')
    
    if search_query:
        crops = crops.filter(
            Q(crop_name__icontains=search_query) |
            Q(farmer__username__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    from django.core.paginator import Paginator
    paginator = Paginator(crops, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'crops': page_obj,
        'title': 'Crop Management'
    }
    return render(request, 'admin_panel/crop_management.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_crop_detail(request, crop_id):
    """View crop details for moderation"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    context = {
        'crop': crop,
        'orders': crop.orders.all(),
        'listing': crop.listing if hasattr(crop, 'listing') else None,
        'title': f'Crop: {crop.crop_name}'
    }
    return render(request, 'admin_panel/crop_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_remove_crop(request, crop_id):
    """Remove inappropriate crop"""
    crop = get_object_or_404(Crop, id=crop_id)
    crop.delete()
    messages.success(request, f'Crop "{crop.crop_name}" has been removed.')
    return redirect('crop_management')


# ========== MASTER CROP MANAGEMENT ==========

@login_required(login_url='login')
@user_passes_test(is_admin)
def master_crops_list(request):
    """View and manage all master crop templates"""
    from admin_panel.models import MasterCrop
    
    master_crops = MasterCrop.objects.all().order_by('crop_name')
    
    # Filters
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    
    if category_filter:
        master_crops = master_crops.filter(category=category_filter)
    
    if status_filter == 'active':
        master_crops = master_crops.filter(is_active=True)
    elif status_filter == 'inactive':
        master_crops = master_crops.filter(is_active=False)
    
    # Count listings for each master crop
    for crop in master_crops:
        crop.listings_count = crop.listings.count()
    
    context = {
        'master_crops': master_crops,
        'title': 'Master Crop Templates',
        'categories': MasterCrop.CROP_CATEGORIES,
    }
    return render(request, 'admin_panel/master_crops_list.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def add_master_crop(request):
    """Admin adds a new master crop template"""
    from admin_panel.forms import MasterCropForm
    
    if request.method == 'POST':
        form = MasterCropForm(request.POST, request.FILES)
        if form.is_valid():
            master_crop = form.save(commit=False)
            master_crop.created_by = request.user
            master_crop.save()
            messages.success(request, f'Master Crop "{master_crop.crop_name}" created successfully! Farmers can now list this crop.')
            return redirect('master_crops_list')
    else:
        form = MasterCropForm()
    
    context = {
        'form': form,
        'title': 'Add Master Crop Template',
    }
    return render(request, 'admin_panel/add_master_crop.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_master_crop(request, crop_id):
    """Edit an existing master crop template"""
    from admin_panel.models import MasterCrop
    from admin_panel.forms import MasterCropForm
    
    master_crop = get_object_or_404(MasterCrop, id=crop_id)
    
    if request.method == 'POST':
        form = MasterCropForm(request.POST, request.FILES, instance=master_crop)
        if form.is_valid():
            form.save()
            messages.success(request, f'Master Crop "{master_crop.crop_name}" updated successfully!')
            return redirect('master_crops_list')
    else:
        form = MasterCropForm(instance=master_crop)
    
    context = {
        'form': form,
        'master_crop': master_crop,
        'title': f'Edit Master Crop: {master_crop.crop_name}',
    }
    return render(request, 'admin_panel/edit_master_crop.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_master_crop(request, crop_id):
    """Delete a master crop template"""
    from admin_panel.models import MasterCrop
    
    master_crop = get_object_or_404(MasterCrop, id=crop_id)
    
    # Check if there are any active listings using this master crop
    listings_count = master_crop.listings.count()
    
    if request.method == 'POST':
        if listings_count > 0:
            messages.error(request, f'Cannot delete "{master_crop.crop_name}" - {listings_count} farmer listing(s) are using this crop. Please deactivate it instead.')
        else:
            crop_name = master_crop.crop_name
            master_crop.delete()
            messages.success(request, f'Master Crop "{crop_name}" deleted successfully!')
        return redirect('master_crops_list')
    
    context = {
        'master_crop': master_crop,
        'listings_count': listings_count,
        'title': f'Delete Master Crop: {master_crop.crop_name}',
    }
    return render(request, 'admin_panel/delete_master_crop.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def toggle_master_crop_status(request, crop_id):
    """Toggle active/inactive status of a master crop"""
    from admin_panel.models import MasterCrop
    
    master_crop = get_object_or_404(MasterCrop, id=crop_id)
    master_crop.is_active = not master_crop.is_active
    master_crop.save()
    
    status = "activated" if master_crop.is_active else "deactivated"
    messages.success(request, f'Master Crop "{master_crop.crop_name}" has been {status}.')
    return redirect('master_crops_list')
