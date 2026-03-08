from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.shortcuts import redirect
import re


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        """
        After any login, check if user still has role='pending'.
        If so, send them to role selection. Otherwise, dashboard.
        """
        user = request.user
        if user.is_authenticated and getattr(user, 'role', '') == 'pending':
            return '/google-role-select/'
        return '/dashboard/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Called after OAuth callback but before login/connect.
        If a user with this email already exists, connect the social account.
        """
        from users.models import CustomUser

        if not sociallogin.is_existing:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if email:
                try:
                    existing_user = CustomUser.objects.get(email=email)
                    sociallogin.connect(request, existing_user)
                except CustomUser.DoesNotExist:
                    pass  # New user — will be created in save_user

    def save_user(self, request, sociallogin, form=None):
        """
        Called only for NEW users. Sets role='pending' so the dashboard
        redirects them to the role selection page.
        """
        user = super().save_user(request, sociallogin, form)

        extra_data = sociallogin.account.extra_data
        if not user.first_name:
            user.first_name = extra_data.get('given_name', '')
        if not user.last_name:
            user.last_name = extra_data.get('family_name', '')

        user.auth_type = 'password'
        user.role = 'pending'  # Will be set on role selection page
        user.is_verified = True

        # Clean username from email
        if not user.username or user.username.startswith('user_'):
            email = user.email or ''
            base = re.sub(r'[^a-zA-Z0-9]', '', email.split('@')[0])[:20] or 'user'
            username = base
            counter = 1
            from users.models import CustomUser
            while CustomUser.objects.filter(username=username).exclude(pk=user.pk).exists():
                username = f"{base}{counter}"
                counter += 1
            user.username = username

        user.save()
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        return '/dashboard/'

    def is_open_for_signup(self, request, sociallogin):
        return True
