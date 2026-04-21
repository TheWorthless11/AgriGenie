from django.urls import path
from admin_panel import views

app_name = 'admin_panel'

urlpatterns = [
    # Admin Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/approvals/', views.user_approvals, name='user_approvals'),
    path('users/approvals/<int:approval_id>/approve/', views.approve_user, name='approve_user'),
    
    # Add more admin URLs here as needed
]
