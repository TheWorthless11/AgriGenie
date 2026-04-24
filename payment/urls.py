from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Payment method selection
    path('choose/<int:order_id>/', views.choose_payment_method, name='choose_payment_method'),
    
    # SSLCommerz integration
    path('initiate/<int:order_id>/', views.initiate_sslcommerz_payment, name='initiate_sslcommerz_payment'),
    
    # Payment callbacks from SSLCommerz
    path('success/', views.payment_success, name='payment_success'),
    path('failed/', views.payment_failed, name='payment_failed'),
    path('cancelled/', views.payment_cancelled, name='payment_cancelled'),
    
    # Payment details
    path('details/<uuid:payment_id>/', views.payment_details, name='payment_details'),
    path('success-page/<int:order_id>/', views.order_payment_success, name='order_payment_success'),
    
    # COD verification
    path('verify/<int:order_id>/', views.verify_payment, name='verify_payment'),
]
