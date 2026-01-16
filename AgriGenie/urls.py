"""
URL configuration for AgriGenie project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from farmer import views as farmer_views
from buyer import views as buyer_views
from marketplace import views as marketplace_views
from admin_panel import views as admin_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home and Authentication
    path('', user_views.home, name='home'),
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('dashboard/', user_views.dashboard, name='dashboard'),
    
    # User Profile
    path('profile/', user_views.profile_view, name='profile'),
    path('profile/<str:username>/', user_views.profile_view, name='profile_detail'),
    path('profile/edit/', user_views.profile_edit, name='profile_edit'),
    path('notifications/', user_views.notifications_view, name='notifications'),
    path('notification/<int:notification_id>/read/', user_views.mark_notification_read, name='mark_notification_read'),
    
    # Farmer URLs
    path('farmer/crops/', farmer_views.farmer_crops, name='farmer_crops'),
    path('farmer/orders/', farmer_views.farmer_orders, name='farmer_orders'),
    path('farmer/add-crop/', farmer_views.add_crop, name='add_crop'),
    path('farmer/edit-crop/<int:crop_id>/', farmer_views.edit_crop, name='edit_crop'),
    path('farmer/delete-crop/<int:crop_id>/', farmer_views.delete_crop, name='delete_crop'),
    path('farmer/disease-detection/', farmer_views.disease_detection, name='disease_detection'),
    path('farmer/disease-history/<int:crop_id>/', farmer_views.disease_history, name='disease_history'),
    path('farmer/price-prediction/', farmer_views.price_prediction, name='price_prediction'),
    path('farmer/weather-alerts/', farmer_views.weather_alerts, name='weather_alerts'),
    path('farmer/messages/', farmer_views.messages_view, name='messages'),
    path('farmer/send-message/<int:recipient_id>/', farmer_views.send_message, name='send_message'),
    path('farmer/ratings/', farmer_views.ratings_view, name='farmer_ratings'),
    path('farmer/order/<int:order_id>/', farmer_views.order_detail, name='order_detail'),
    
    # Buyer URLs
    path('buyer/marketplace/', buyer_views.marketplace, name='marketplace'),
    path('buyer/crop/<int:crop_id>/', buyer_views.crop_detail, name='crop_detail'),
    path('buyer/place-order/<int:crop_id>/', buyer_views.place_order, name='place_order'),
    path('buyer/orders/', buyer_views.buyer_orders, name='buyer_orders'),
    path('buyer/wishlist/', buyer_views.wishlist, name='wishlist'),
    path('buyer/saved-crops/', buyer_views.saved_crops, name='saved_crops'),
    path('buyer/contact-farmer/<int:farmer_id>/', buyer_views.contact_farmer, name='contact_farmer'),
    path('buyer/review/<int:crop_id>/', buyer_views.leave_review, name='leave_review'),
    path('buyer/confirm-receipt/<int:order_id>/', buyer_views.confirm_receipt, name='confirm_receipt'),
    path('buyer/purchase-history/', buyer_views.purchase_history, name='purchase_history'),
    
    # Marketplace URLs
    path('marketplace/', marketplace_views.marketplace_home, name='marketplace_home'),
    path('search/', marketplace_views.search_crops, name='search_crops'),
    path('crop/<int:crop_id>/', marketplace_views.crop_listing, name='crop_listing'),
    path('crop/<int:crop_id>/add-to-wishlist/', marketplace_views.add_to_wishlist, name='add_to_wishlist'),
    path('crop/<int:crop_id>/remove-from-wishlist/', marketplace_views.remove_from_wishlist, name='remove_from_wishlist'),
    path('crop/<int:crop_id>/save/', marketplace_views.save_crop, name='save_crop'),
    path('crop/<int:crop_id>/unsave/', marketplace_views.remove_saved_crop, name='remove_saved_crop'),
    path('crop/<int:crop_id>/review/', marketplace_views.add_review, name='add_review'),
    path('trending/', marketplace_views.trending_crops, name='trending_crops'),
    path('top-rated/', marketplace_views.top_rated_crops, name='top_rated_crops'),
    path('farmer/<int:farmer_id>/', marketplace_views.farmer_storefront, name='farmer_storefront'),
    
    # Admin URLs
    path('admin-panel/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/approvals/', admin_views.user_approvals, name='user_approvals'),
    path('admin-panel/approve/<int:approval_id>/', admin_views.approve_user, name='approve_user'),
    path('admin-panel/reject/<int:approval_id>/', admin_views.reject_user, name='reject_user'),
    path('admin-panel/crops/', admin_views.crop_management, name='crop_management'),
    path('admin-panel/crop/<int:crop_id>/', admin_views.admin_crop_detail, name='admin_crop_detail'),
    path('admin-panel/crop/<int:crop_id>/remove/', admin_views.admin_remove_crop, name='admin_remove_crop'),
    path('admin-panel/alerts/', admin_views.system_alerts_admin, name='system_alerts_admin'),
    path('admin-panel/reports/', admin_views.system_reports, name='admin_reports'),
    path('admin-panel/ai-monitoring/', admin_views.ai_monitoring, name='ai_monitoring'),
    path('admin-panel/activity-logs/', admin_views.activity_logs, name='activity_logs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
