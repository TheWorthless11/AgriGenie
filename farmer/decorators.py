"""
Decorators for farmer feature access control based on approval status
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def farmer_approval_required(redirect_url='marketplace'):
    """
    Decorator to check if farmer is approved before accessing restricted features.
    
    Unapproved farmers can only access:
    - marketplace (browse crops)
    - dashboard (read-only with warning)
    
    Restricted features requiring approval:
    - Create/Edit/Delete crops
    - View orders
    - Send messages/chat
    - Disease detection
    - Weather alerts
    - Price prediction
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Only apply to farmers
            if request.user.role != 'farmer':
                return view_func(request, *args, **kwargs)
            
            # Check if farmer has FarmerProfile
            try:
                farmer_profile = request.user.farmer_profile
            except:
                messages.warning(
                    request,
                    'Please complete your farmer profile setup.'
                )
                return redirect(redirect_url)
            
            # Check approval status
            if farmer_profile.approval_status != 'approved':
                if farmer_profile.approval_status == 'pending':
                    message = (
                        "⏳ Your farmer account is pending super admin approval. "
                        "Please wait or check your email for updates."
                    )
                elif farmer_profile.approval_status == 'rejected':
                    message = (
                        "❌ Your farmer application was rejected. "
                        "Please contact support for more details."
                    )
                elif farmer_profile.approval_status == 'not_submitted':
                    message = (
                        "📋 Please complete your NID verification to access this feature."
                    )
                else:
                    message = "This feature is only available for approved farmers."
                
                messages.warning(request, message)
                return redirect(redirect_url)
            
            # Farmer is approved, proceed
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
