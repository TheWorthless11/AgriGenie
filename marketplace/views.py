from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from marketplace.models import CropListing, Review, Search
from farmer.models import Crop, Order
from buyer.models import SavedCrop
from users.models import CustomUser, FarmerProfile


def marketplace_home(request):
    """Marketplace homepage"""
    featured_listings = CropListing.objects.filter(is_featured=True).select_related('crop').order_by('-created_at')[:6]
    latest_crops = Crop.objects.filter(is_available=True).select_related('farmer').order_by('-created_at')[:12]
    
    # Get top crops by orders
    top_crops = Crop.objects.filter(is_available=True).annotate(
        order_count=Count('orders')
    ).order_by('-order_count')[:6]
    
    context = {
        'featured_listings': featured_listings,
        'latest_crops': latest_crops,
        'top_crops': top_crops,
        'title': 'Marketplace'
    }
    return render(request, 'marketplace/index.html', context)


def search_crops(request):
    """Search crops"""
    query = request.GET.get('q', '')
    crops = Crop.objects.filter(is_available=True)
    
    if query:
        crops = crops.filter(
            Q(crop_name__icontains=query) |
            Q(crop_type__icontains=query) |
            Q(description__icontains=query) |
            Q(farmer__username__icontains=query) |
            Q(location__icontains=query)
        )
        
        # Log search
        if request.user.is_authenticated:
            Search.objects.create(
                user=request.user,
                query=query,
                results_count=crops.count()
            )
    
    # Apply filters
    crop_type = request.GET.get('crop_type')
    location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    quality_grade = request.GET.get('quality_grade')
    
    if crop_type:
        crops = crops.filter(crop_type=crop_type)
    
    if location:
        crops = crops.filter(location__icontains=location)
    
    if min_price:
        try:
            crops = crops.filter(price_per_unit__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            crops = crops.filter(price_per_unit__lte=float(max_price))
        except ValueError:
            pass
    
    if quality_grade:
        crops = crops.filter(quality_grade=quality_grade)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    crops = crops.order_by(sort_by)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(crops, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'crops': page_obj,
        'query': query,
        'title': f'Search Results for "{query}"'
    }
    return render(request, 'marketplace/search_results.html', context)


def crop_listing(request, crop_id):
    """View crop listing details"""
    crop = get_object_or_404(Crop, id=crop_id, is_available=True)
    
    # Update view count
    try:
        listing = CropListing.objects.get(crop=crop)
        listing.views_count += 1
        listing.save()
    except CropListing.DoesNotExist:
        CropListing.objects.create(crop=crop)
    
    # Get reviews
    reviews = Review.objects.filter(crop=crop).select_related('reviewer').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if in wishlist or saved
    is_in_wishlist = False
    is_saved = False
    if request.user.is_authenticated:
        is_in_wishlist = request.user.wishlist_items.filter(crop=crop).exists()
        is_saved = SavedCrop.objects.filter(buyer=request.user, crop=crop).exists()
    
    # Get similar crops
    similar_crops = Crop.objects.filter(
        crop_type=crop.crop_type,
        is_available=True
    ).exclude(id=crop.id)[:4]
    
    context = {
        'crop': crop,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'reviews_count': reviews.count(),
        'is_in_wishlist': is_in_wishlist,
        'is_saved': is_saved,
        'similar_crops': similar_crops,
        'farmer': crop.farmer,
        'title': crop.crop_name
    }
    return render(request, 'marketplace/crop_listing.html', context)


@login_required(login_url='login')
def add_to_wishlist(request, crop_id):
    """Add crop to wishlist"""
    from buyer.models import WishlistItem
    crop = get_object_or_404(Crop, id=crop_id)
    
    WishlistItem.objects.get_or_create(buyer=request.user, crop=crop)
    messages.success(request, f'{crop.crop_name} added to wishlist!')
    
    return redirect('crop_listing', crop_id=crop.id)


@login_required(login_url='login')
def remove_from_wishlist(request, crop_id):
    """Remove crop from wishlist"""
    from buyer.models import WishlistItem
    crop = get_object_or_404(Crop, id=crop_id)
    
    WishlistItem.objects.filter(buyer=request.user, crop=crop).delete()
    messages.success(request, f'{crop.crop_name} removed from wishlist!')
    
    return redirect('crop_listing', crop_id=crop.id)


@login_required(login_url='login')
def save_crop(request, crop_id):
    """Save/unsave crop for later (toggle)"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    saved, created = SavedCrop.objects.get_or_create(buyer=request.user, crop=crop)
    if not created:
        saved.delete()
        messages.success(request, f'{crop.crop_name} removed from saved!')
    else:
        messages.success(request, f'{crop.crop_name} saved for later!')
    
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'marketplace'
    return redirect(next_url)


@login_required(login_url='login')
def remove_saved_crop(request, crop_id):
    """Remove saved crop"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    SavedCrop.objects.filter(buyer=request.user, crop=crop).delete()
    messages.success(request, f'{crop.crop_name} unsaved!')
    
    return redirect('crop_listing', crop_id=crop.id)


@login_required(login_url='login')
def add_review(request, crop_id):
    """Add review to crop"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check if user has ordered this crop
    has_ordered = Order.objects.filter(
        buyer=request.user,
        crop=crop,
        status='delivered'
    ).exists()
    
    if not has_ordered and request.user != crop.farmer:
        messages.error(request, 'You can only review crops you have ordered and received!')
        return redirect('crop_listing', crop_id=crop.id)
    
    existing_review = Review.objects.filter(crop=crop, reviewer=request.user).first()
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        review_text = request.POST.get('review_text')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                messages.error(request, 'Rating must be between 1 and 5!')
                return redirect('crop_listing', crop_id=crop.id)
            
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
                    verified_purchase=has_ordered
                )
                messages.success(request, 'Review posted successfully!')
            
            return redirect('crop_listing', crop_id=crop.id)
        
        except ValueError:
            messages.error(request, 'Invalid rating value!')
    
    context = {
        'crop': crop,
        'existing_review': existing_review,
        'title': f'Review {crop.crop_name}'
    }
    return render(request, 'marketplace/add_review.html', context)


def trending_crops(request):
    """View trending crops"""
    # By orders
    trending = Crop.objects.filter(is_available=True).annotate(
        order_count=Count('orders')
    ).order_by('-order_count')[:20]
    
    context = {
        'crops': trending,
        'title': 'Trending Crops'
    }
    return render(request, 'marketplace/trending_crops.html', context)


def top_rated_crops(request):
    """View top rated crops"""
    top_rated = Crop.objects.filter(is_available=True).annotate(
        avg_rating=Avg('reviews__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:20]
    
    context = {
        'crops': top_rated,
        'title': 'Top Rated Crops'
    }
    return render(request, 'marketplace/top_rated_crops.html', context)


def farmer_storefront(request, farmer_id):
    """View farmer's storefront"""
    farmer = get_object_or_404(CustomUser, id=farmer_id, role='farmer')
    crops = Crop.objects.filter(farmer=farmer, is_available=True)
    
    farmer_profile = FarmerProfile.objects.filter(user=farmer).first()
    
    # Get farmer stats
    total_crops = crops.count()
    total_orders = Order.objects.filter(farmer=farmer).count()
    avg_rating = farmer_profile.rating if farmer_profile else 0
    
    context = {
        'farmer': farmer,
        'farmer_profile': farmer_profile,
        'crops': crops,
        'total_crops': total_crops,
        'total_orders': total_orders,
        'avg_rating': avg_rating,
        'title': f'{farmer.username} - Storefront'
    }
    return render(request, 'marketplace/farmer_storefront.html', context)
