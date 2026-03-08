from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from admin_panel.models import UserApproval, SystemAlert, SystemReport, AIDiseaseMonitor, AIPricePredictor, ActivityLog, UserReport, MasterCrop
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
    
    # User reports
    pending_reports = UserReport.objects.filter(status='pending').count()
    
    context = {
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'pending_approvals': pending_approvals,
        'pending_reports': pending_reports,
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
    """Manage user approvals - defaults to showing only pending"""
    approvals = UserApproval.objects.all().select_related('user').order_by('-created_at')
    status_filter = request.GET.get('status', 'pending')  # Default to pending only
    role_filter = request.GET.get('role')
    
    if status_filter and status_filter != 'all':
        approvals = approvals.filter(status=status_filter)
    
    if role_filter:
        approvals = approvals.filter(user__role=role_filter)
    
    pending_count = UserApproval.objects.filter(status='pending').count()
    
    context = {
        'approvals': approvals,
        'pending_count': pending_count,
        'status_filter': status_filter,
        'status_choices': [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('all', 'All')],
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
            
            # Update user profile (create if missing)
            user = approval.user
            if user.role == 'farmer':
                farmer_profile, created = FarmerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'farm_name': f"{user.first_name}'s Farm",
                        'farm_size': 0,
                        'farm_location': f"{user.upazila}, {user.district}" if hasattr(user, 'upazila') else 'Unknown',
                        'soil_type': 'Not specified',
                        'experience_years': 0,
                        'registration_number': f"FR-{user.id:06d}",
                    }
                )
                farmer_profile.is_approved = True
                farmer_profile.save()
            elif user.role == 'buyer':
                buyer_profile, created = BuyerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': user.first_name or user.username,
                        'business_type': 'Individual',
                    }
                )
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
            
            # Send notifications to users
            from users.models import Notification, CustomUser
            if all_users:
                users_to_notify = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id)
            else:
                # Get specific target users from form
                target_user_ids = request.POST.getlist('target_users')
                if target_user_ids:
                    users_to_notify = CustomUser.objects.filter(id__in=target_user_ids, is_active=True)
                    alert.target_users.set(users_to_notify)
                else:
                    users_to_notify = CustomUser.objects.none()
            
            # Create notification for each user
            notifications = []
            for user in users_to_notify:
                notifications.append(Notification(
                    user=user,
                    notification_type='system',
                    title=f'[{alert.get_alert_type_display()}] {title}',
                    message=message
                ))
            if notifications:
                Notification.objects.bulk_create(notifications)
            
            messages.success(request, f'Alert created and sent to {len(notifications)} user(s)!')
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
    """View user-submitted reports about the website"""
    # Filter by status/type if provided
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    
    user_reports = UserReport.objects.all()
    if status_filter:
        user_reports = user_reports.filter(status=status_filter)
    if type_filter:
        user_reports = user_reports.filter(report_type=type_filter)
    
    # Stats
    total_reports = UserReport.objects.count()
    pending_reports = UserReport.objects.filter(status='pending').count()
    reviewing_reports = UserReport.objects.filter(status='reviewing').count()
    resolved_reports = UserReport.objects.filter(status='resolved').count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        report_id = request.POST.get('report_id')
        
        if report_id:
            report = get_object_or_404(UserReport, id=report_id)
            
            if action == 'respond':
                admin_response = request.POST.get('admin_response', '')
                new_status = request.POST.get('new_status', 'reviewing')
                report.admin_response = admin_response
                report.status = new_status
                report.responded_by = request.user
                report.save()
                
                # Notify the user
                Notification.objects.create(
                    user=report.user,
                    notification_type='system',
                    title=f'Report Update: {report.subject}',
                    message=f'Your report has been updated to "{report.get_status_display()}". Admin response: {admin_response[:100]}'
                )
                messages.success(request, f'Response sent to {report.user.username}!')
            
            elif action == 'update_status':
                new_status = request.POST.get('new_status')
                if new_status:
                    report.status = new_status
                    report.save()
                    messages.success(request, f'Report status updated to {report.get_status_display()}!')
            
            elif action == 'delete':
                report.delete()
                messages.success(request, 'Report deleted!')
        
        return redirect('admin_reports')
    
    context = {
        'user_reports': user_reports,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'reviewing_reports': reviewing_reports,
        'resolved_reports': resolved_reports,
        'report_types': UserReport.REPORT_TYPES,
        'status_choices': UserReport.STATUS_CHOICES,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'title': 'User Reports'
    }
    return render(request, 'admin_panel/system_reports.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def ai_monitoring(request):
    """Monitor AI models performance — diseases it can detect & price predictions"""
    import json
    import math
    import random
    from datetime import datetime, timedelta
    from ai_models.disease_detection import DiseaseDetectionModel

    # ── Detectable diseases ──────────────────────────────────────
    disease_list = []
    type_icons = {
        'bacterial': 'fa-bacterium',
        'fungal': 'fa-disease',
        'viral': 'fa-virus',
        'pest': 'fa-spider',
        'healthy': 'fa-leaf',
    }
    type_colors = {
        'bacterial': 'danger',
        'fungal': 'warning',
        'viral': 'info',
        'pest': 'secondary',
        'healthy': 'success',
    }
    for idx, info in DiseaseDetectionModel.DISEASE_MAPPING.items():
        name = info['name']
        dtype = info['type']
        crop = name.split(' ')[0]  # Pepper / Potato / Tomato
        if crop == 'Pepper':
            crop = 'Pepper Bell'
        treatment = DiseaseDetectionModel.TREATMENT_RECOMMENDATIONS.get(name, 'N/A')
        disease_list.append({
            'name': name,
            'type': dtype,
            'type_label': dtype.capitalize(),
            'crop': crop,
            'treatment': treatment,
            'icon': type_icons.get(dtype, 'fa-question'),
            'color': type_colors.get(dtype, 'dark'),
        })

    # Count by type for summary badges
    type_counts = {}
    for d in disease_list:
        t = d['type_label']
        type_counts[t] = type_counts.get(t, 0) + 1

    # ── Price predictions for master crops (past 1 year) ─────────
    master_crops = MasterCrop.objects.filter(is_active=True)
    today = datetime.now().date()
    one_year_ago = today - timedelta(days=365)

    # Base prices per category (₹/kg) — realistic Indian market ranges
    base_prices = {
        'vegetables': 35,
        'fruits': 60,
        'grains': 25,
        'pulses': 80,
        'spices': 150,
        'cash_crops': 45,
        'other': 40,
    }
    seasonal_weights = {
        1: 1.10, 2: 1.15, 3: 1.20,
        4: 1.00, 5: 0.90, 6: 0.80,
        7: 0.75, 8: 0.70, 9: 0.80,
        10: 1.00, 11: 1.15, 12: 1.20,
    }

    crop_price_data = []  # list of {crop_name, monthly_prices:[{month_label, price}], avg, min, max}
    for mc in master_crops:
        base = base_prices.get(mc.category, 40)
        random.seed(hash(mc.crop_name))  # deterministic per crop
        monthly_prices = []
        prices_only = []
        for m_offset in range(12):
            dt = one_year_ago + timedelta(days=m_offset * 30)
            month_num = dt.month
            seasonal = seasonal_weights.get(month_num, 1.0)
            noise = random.uniform(-0.08, 0.08)
            price = round(base * seasonal * (1 + noise), 2)
            label = dt.strftime('%b %Y')
            monthly_prices.append({'month': label, 'price': price})
            prices_only.append(price)

        crop_price_data.append({
            'crop_name': mc.crop_name,
            'category': mc.get_category_display(),
            'monthly_prices': monthly_prices,
            'avg_price': round(sum(prices_only) / len(prices_only), 2),
            'min_price': round(min(prices_only), 2),
            'max_price': round(max(prices_only), 2),
        })

    # JSON data for Chart.js
    chart_labels = [p['month'] for p in crop_price_data[0]['monthly_prices']] if crop_price_data else []
    chart_datasets = []
    palette = ['#0d6efd', '#198754', '#dc3545', '#ffc107', '#0dcaf0', '#6f42c1']
    for i, cpd in enumerate(crop_price_data):
        chart_datasets.append({
            'label': cpd['crop_name'],
            'data': [p['price'] for p in cpd['monthly_prices']],
            'borderColor': palette[i % len(palette)],
            'backgroundColor': palette[i % len(palette)] + '22',
            'fill': True,
            'tension': 0.3,
        })

    # ── Recent disease detections (keep existing) ────────────────
    recent_diseases = CropDisease.objects.all().order_by('-detected_date')[:10]

    context = {
        'disease_list': disease_list,
        'type_counts': type_counts,
        'crop_price_data': crop_price_data,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_datasets_json': json.dumps(chart_datasets),
        'recent_diseases': recent_diseases,
        'title': 'AI Monitoring',
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


@login_required(login_url='login')
@user_passes_test(is_admin)
def user_management(request):
    """View and manage all users"""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filters
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('q', '')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    context = {
        'users': users,
        'total_users': CustomUser.objects.count(),
        'total_farmers': CustomUser.objects.filter(role='farmer').count(),
        'total_buyers': CustomUser.objects.filter(role='buyer').count(),
        'total_admins': CustomUser.objects.filter(role='admin').count(),
        'role_filter': role_filter,
        'search_query': search_query,
        'title': 'User Management',
    }
    return render(request, 'admin_panel/user_management.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """Delete a user"""
    user_to_delete = get_object_or_404(CustomUser, id=user_id)
    
    if user_to_delete == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_management')
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User "{username}" has been deleted successfully.')
        return redirect('user_management')
    
    context = {
        'user_to_delete': user_to_delete,
        'title': f'Delete User - {user_to_delete.username}',
    }
    return render(request, 'admin_panel/delete_user_confirm.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def toggle_user_approval(request, user_id):
    """Approve or revoke approval for a user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        if user.role == 'farmer':
            profile = FarmerProfile.objects.filter(user=user).first()
            if profile:
                profile.is_approved = not profile.is_approved
                profile.save()
                status = "approved" if profile.is_approved else "revoked"
                
                # Update UserApproval record
                approval, _ = UserApproval.objects.get_or_create(user=user)
                approval.status = 'approved' if profile.is_approved else 'rejected'
                approval.reviewed_by = request.user
                approval.reviewed_at = timezone.now()
                approval.save()
                
                # Notify user
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title=f'Account {status.title()}',
                    message=f'Your farmer account has been {status} by admin.'
                )
                messages.success(request, f'Farmer "{user.username}" has been {status}.')
        
        elif user.role == 'buyer':
            profile = BuyerProfile.objects.filter(user=user).first()
            if profile:
                profile.is_approved = not profile.is_approved
                profile.save()
                status = "approved" if profile.is_approved else "revoked"
                
                # Update UserApproval record
                approval, _ = UserApproval.objects.get_or_create(user=user)
                approval.status = 'approved' if profile.is_approved else 'rejected'
                approval.reviewed_by = request.user
                approval.reviewed_at = timezone.now()
                approval.save()
                
                # Notify user
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title=f'Account {status.title()}',
                    message=f'Your buyer account has been {status} by admin.'
                )
                messages.success(request, f'Buyer "{user.username}" has been {status}.')
        else:
            messages.info(request, 'Admin accounts do not require approval.')
    
    return redirect('user_management')
