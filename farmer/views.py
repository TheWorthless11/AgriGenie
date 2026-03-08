from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.http import JsonResponse
from farmer.models import Crop, Order, CropDisease, WeatherAlert, Message, FarmerRating
from farmer.forms import CropForm, OrderForm, MessageForm, WeatherAlertForm, CropDiseaseForm
from users.models import Notification, CustomUser, FarmerProfile
from admin_panel.models import MasterCrop
from marketplace.models import CropListing
from buyer.models import PurchaseRequest
from ai_models import analyze_disease_image, WeatherService, get_coordinates_from_location
import numpy as np
from sklearn.linear_model import LinearRegression
import json


def is_farmer_approved(user):
    """Check if a farmer is approved by admin"""
    profile = FarmerProfile.objects.filter(user=user).first()
    return profile and profile.is_approved


@login_required(login_url='login')
def farmer_dashboard(request):
    """Farmer dashboard"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    crops = Crop.objects.filter(farmer=request.user)
    orders = Order.objects.filter(farmer=request.user)
    pending_orders = orders.filter(status='pending')
    recent_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    unread_messages = recent_messages.filter(is_read=False).count()
    farmer_profile = FarmerProfile.objects.filter(user=request.user).first()
    
    context = {
        'crops': crops,
        'orders': orders,
        'recent_orders': orders.order_by('-order_date')[:5],
        'recent_crops': crops.order_by('-created_at')[:5],
        'pending_orders': pending_orders,
        'recent_messages': recent_messages,
        'unread_messages': unread_messages,
        'crops_count': crops.count(),
        'orders_count': orders.count(),
        'pending_orders_count': pending_orders.count(),
        'total_revenue': sum([order.total_price for order in orders.filter(status='delivered')]),
        'is_approved': is_farmer_approved(request.user),
        'farmer_profile': farmer_profile,
    }
    return render(request, 'farmer/dashboard.html', context)


@login_required(login_url='login')
def add_crop(request):
    """Add a new crop"""
    if request.user.role != 'farmer':
        messages.error(request, 'Only farmers can add crops!')
        return redirect('dashboard')
    
    if not is_farmer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot add crops until approved.')
        return redirect('farmer_crops')
    
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.farmer = request.user
            crop.save()
            
            # Create crop listing
            CropListing.objects.create(crop=crop)
            
            messages.success(request, 'Crop added successfully!')
            return redirect('farmer_crops')
    else:
        # Prefill location from user's profile if available (user.location or farmer_profile.farm_location)
        default_loc = ''
        if getattr(request.user, 'location', None):
            default_loc = request.user.location
        else:
            try:
                farmer_profile = getattr(request.user, 'farmer_profile', None)
                if farmer_profile and getattr(farmer_profile, 'farm_location', None):
                    default_loc = farmer_profile.farm_location
            except Exception:
                default_loc = ''

        form = CropForm(initial={'location': default_loc})
    
    context = {'form': form, 'title': 'Add Crop'}
    return render(request, 'farmer/add_crop.html', context)


@login_required(login_url='login')
def edit_crop(request, crop_id):
    """Edit crop"""
    if not is_farmer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot edit crops until approved.')
        return redirect('farmer_crops')
    
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)
    
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Crop updated successfully!')
            return redirect('farmer_crops')
    else:
        form = CropForm(instance=crop)
    
    context = {'form': form, 'crop': crop, 'title': 'Edit Crop'}
    return render(request, 'farmer/edit_crop.html', context)


@login_required(login_url='login')
def delete_crop(request, crop_id):
    """Delete crop"""
    if not is_farmer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot delete crops until approved.')
        return redirect('farmer_crops')
    
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)
    crop.delete()
    messages.success(request, 'Crop deleted successfully!')
    return redirect('farmer_crops')


@login_required(login_url='login')
def farmer_crops(request):
    """View all farmer crops"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    crops = Crop.objects.filter(farmer=request.user).order_by('-created_at')
    
    context = {'crops': crops, 'title': 'My Crops'}
    return render(request, 'farmer/crops_list.html', context)


@login_required(login_url='login')
def farmer_orders(request):
    """View all orders for farmer's crops"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    orders = Order.objects.filter(farmer=request.user).order_by('-order_date')
    status_filter = request.GET.get('status')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'title': 'Orders Received',
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'farmer/orders_list.html', context)


@login_required(login_url='login')
def order_detail(request, order_id):
    """View order detail"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.user not in [order.farmer, order.buyer]:
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    if request.method == 'POST' and request.user == order.farmer:
        new_status = request.POST.get('status')
        old_status = order.status
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            crop = order.crop
            
            # Deduct quantity when order is accepted
            if new_status == 'accepted' and old_status == 'pending':
                crop.deduct_quantity(order.quantity)
                if crop.quantity <= 0:
                    messages.info(request, f'{crop.crop_name} is now out of stock. It will be removed from marketplace in 24 hours if not restocked.')
            
            # Restore quantity if order is rejected or cancelled by farmer
            if new_status in ('rejected', 'cancelled') and old_status == 'accepted':
                crop.restore_quantity(order.quantity)
            
            # Send notification to buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='order',
                title=f'Order Update: {order.crop.crop_name}',
                message=f'Your order status has been updated to {new_status}'
            )
            messages.success(request, 'Order status updated!')
            return redirect('order_detail', order_id=order.id)
    
    context = {'order': order, 'title': 'Order Detail'}
    return render(request, 'farmer/order_detail.html', context)


@login_required(login_url='login')
def disease_result(request, disease_id):
    """Display disease detection result"""
    disease = get_object_or_404(CropDisease, id=disease_id)
    
    # Ensure user can only view their own results
    if disease.farmer != request.user and (disease.crop and disease.crop.farmer != request.user):
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('disease_detection')
    
    # Determine crop name
    if disease.crop and disease.crop.master_crop:
        crop_name = disease.crop.master_crop.crop_name
    elif disease.master_crop:
        crop_name = disease.master_crop.crop_name
    else:
        crop_name = 'Unknown Crop'
    
    context = {
        'disease': disease,
        'crop': disease.crop,
        'master_crop': disease.master_crop,
        'crop_name': crop_name,
        'title': 'Disease Detection Result'
    }
    return render(request, 'farmer/disease_result.html', context)


@login_required(login_url='login')
def disease_detection(request, crop_id=None):
    """AI Crop Disease Detection"""
    if request.user.role != 'farmer':
        messages.error(request, 'Only farmers can use disease detection!')
        return redirect('dashboard')
    
    # Only show crops that have master_crop assigned
    farmer_crops = Crop.objects.filter(farmer=request.user, master_crop__isnull=False).select_related('master_crop')
    # Master crops that admin allows farmers to analyze
    master_crops = MasterCrop.objects.filter(is_active=True, allow_detection=True)
    selected_crop = None
    selected_master_crop = None
    
    if request.method == 'POST':
        form = CropDiseaseForm(request.POST, request.FILES)
        selected_crop_id = request.POST.get('crop')
        selected_master_crop_id = request.POST.get('master_crop')

        # Prefer a farmer crop if provided, otherwise allow selecting a master crop type
        if selected_crop_id:
            selected_crop = get_object_or_404(Crop, id=selected_crop_id, farmer=request.user)
        elif selected_master_crop_id:
            selected_master_crop = get_object_or_404(MasterCrop, id=selected_master_crop_id, is_active=True, allow_detection=True)
        else:
            messages.error(request, 'Please select either one of your crops or an allowed crop type!')

        # If a crop/master_crop was chosen, proceed to analyze
        if selected_crop or selected_master_crop:
            image_file = request.FILES.get('disease_image')
            if image_file:
                try:
                    disease_info = analyze_disease_image(image_file)

                    # Create disease record; attach crop if a farmer listing was chosen,
                    # otherwise attach master_crop and record the farmer who requested the detection.
                    disease = CropDisease.objects.create(
                        crop=selected_crop if selected_crop else None,
                        master_crop=selected_master_crop if selected_master_crop else None,
                        farmer=request.user,
                        disease_name=disease_info.get('name', 'Unknown Disease'),
                        disease_type=disease_info.get('type', 'unknown'),
                        confidence_score=disease_info.get('confidence', 0),
                        disease_image=image_file,
                        treatment_recommendation=disease_info.get('treatment', ''),
                        ai_model_used=disease_info.get('model_used', 'plant_disease_model')
                    )

                    # Send notification
                    crop_name = selected_crop.master_crop.crop_name if selected_crop and selected_crop.master_crop else (selected_master_crop.crop_name if selected_master_crop else 'Unknown Crop')
                    Notification.objects.create(
                        user=request.user,
                        notification_type='disease',
                        title=f'Disease Detected: {disease.disease_name}',
                        message=f'Disease detected on {crop_name} with {disease.confidence_score:.1f}% confidence.'
                    )

                    messages.success(request, 'Disease analysis complete!')
                    # Redirect to result page
                    return redirect('disease_result', disease_id=disease.id)
                except Exception as e:
                    messages.error(request, f'Error analyzing image: {str(e)}')
                    detection_result = {'success': False, 'error': str(e)}
            else:
                messages.error(request, 'Please upload an image!')
    else:
        form = CropDiseaseForm()
    
    context = {
        'form': form,
        'crops': farmer_crops,
        'master_crops': master_crops,
        'selected_crop_id': crop_id,
        'title': 'AI Disease Detection'
    }
    return render(request, 'farmer/disease_detection.html', context)


@login_required(login_url='login')
def disease_history(request, crop_id):
    """View disease detection history"""
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)
    diseases = crop.diseases.all().order_by('-detected_date')
    
    context = {
        'crop': crop,
        'diseases': diseases,
        'title': f'{crop.crop_name} - Disease History'
    }
    return render(request, 'farmer/disease_history.html', context)


@login_required(login_url='login')
def weather_alerts(request):
    """View real-time weather and disaster alerts"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    alerts = WeatherAlert.objects.filter(farmer=request.user, is_active=True).order_by('-created_at')
    
    # Get live weather data for farmer's location
    weather_summary = None
    try:
        farmer_location = request.user.farmer_profile.farm_location or request.user.location
        if farmer_location:
            coords = get_coordinates_from_location(farmer_location)
            if coords:
                weather_summary = WeatherService.get_weather_summary(
                    coords['latitude'],
                    coords['longitude']
                )
    except Exception as e:
        print(f"Error fetching weather: {str(e)}")
    
    # Map weather description to Font Awesome icon
    weather_icon = 'cloud-sun'
    if weather_summary and weather_summary.get('description'):
        desc = weather_summary['description'].lower()
        if 'sunny' in desc or 'clear' in desc:
            weather_icon = 'sun'
        elif 'rain' in desc or 'drizzle' in desc or 'shower' in desc:
            weather_icon = 'cloud-rain'
        elif 'thunder' in desc or 'storm' in desc:
            weather_icon = 'bolt'
        elif 'snow' in desc or 'sleet' in desc:
            weather_icon = 'snowflake'
        elif 'fog' in desc or 'mist' in desc or 'haze' in desc:
            weather_icon = 'smog'
        elif 'cloud' in desc or 'overcast' in desc:
            weather_icon = 'cloud'
        elif 'wind' in desc:
            weather_icon = 'wind'

    context = {
        'alerts': alerts,
        'weather_summary': weather_summary,
        'weather_icon': weather_icon,
        'title': 'Weather & Disaster Alerts'
    }
    return render(request, 'farmer/weather_alerts.html', context)


@login_required(login_url='login')
def crop_price_prediction(request):
    """Render crop price prediction page with dropdown options."""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')

    from ai_models.price_prediction.predictor import get_dropdown_options
    options = get_dropdown_options()

    context = {
        'title': 'Crop Price Prediction',
        'commodities': options['commodities'],
        'varieties_json': json.dumps(options['varieties']),
        'markets': options['markets'],
    }
    return render(request, 'farmer/crop_price_prediction.html', context)


@login_required(login_url='login')
def price_predict_api(request):
    """AJAX endpoint: predict crop price for given inputs."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    commodity = data.get('commodity', '').strip()
    variety = data.get('variety', '').strip()
    market = data.get('market', '').strip()
    month = data.get('month')

    if not all([commodity, variety, market, month]):
        return JsonResponse({'error': 'All fields are required'}, status=400)

    try:
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Month must be 1-12'}, status=400)

    import os
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    from ai_models.price_prediction.predictor import predict_price
    try:
        result = predict_price(commodity, variety, market, month)
    except FileNotFoundError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Prediction failed: {str(e)}'}, status=500)

    return JsonResponse(result)


@login_required(login_url='login')
def price_history_api(request):
    """AJAX endpoint: return historical price data for chart."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    commodity = request.GET.get('commodity', '').strip()
    variety = request.GET.get('variety', '').strip()
    market = request.GET.get('market', '').strip()

    if not all([commodity, variety, market]):
        return JsonResponse({'error': 'commodity, variety, market required'}, status=400)

    from ai_models.price_prediction.predictor import get_price_history
    history = get_price_history(commodity, variety, market)
    return JsonResponse({'history': history})


@login_required(login_url='login')
def messages_view(request):
    """View messages"""
    messages_list = Message.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user)
    ).order_by('-created_at')
    
    # Mark as read
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_read':
            message_id = request.POST.get('message_id')
            msg = get_object_or_404(Message, id=message_id)
            if msg.recipient == request.user:
                msg.is_read = True
                msg.save()
    
    context = {
        'messages': messages_list,
        'unread_count': messages_list.filter(recipient=request.user, is_read=False).count(),
        'title': 'Messages'
    }
    return render(request, 'farmer/messages.html', context)


@login_required(login_url='login')
def send_message(request, recipient_id):
    """Send message to a user"""
    if not is_farmer_approved(request.user):
        messages.warning(request, 'Your account is pending admin approval. You cannot send messages until approved.')
        return redirect('messages')
    
    recipient = get_object_or_404(CustomUser, id=recipient_id)
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            
            # Create notification
            Notification.objects.create(
                user=recipient,
                notification_type='message',
                title=f'New message from {request.user.username}',
                message=form.cleaned_data.get('subject')
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('messages')
    else:
        form = MessageForm()
    
    context = {
        'form': form,
        'recipient': recipient,
        'title': f'Send Message to {recipient.username}'
    }
    return render(request, 'farmer/send_message.html', context)


@login_required(login_url='login')
def ratings_view(request):
    """View ratings received"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    ratings = FarmerRating.objects.filter(farmer=request.user).order_by('-created_at')
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'ratings': ratings,
        'avg_rating': avg_rating,
        'total_ratings': ratings.count(),
        'title': 'My Ratings'
    }
    return render(request, 'farmer/ratings.html', context)
