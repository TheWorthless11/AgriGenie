from django.shortcuts import redirect


class AdminIndexRedirectMiddleware:
    """Redirect authenticated admin users from Django admin index to custom super admin dashboard."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/admin/' and request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_dashboard')
        return self.get_response(request)
