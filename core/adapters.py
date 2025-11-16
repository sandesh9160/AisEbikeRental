from django.urls import reverse
from django.contrib.auth.views import LoginView

class CustomAccountAdapter:
    def get_login_redirect_url(self, request):
        """Override the login redirect URL"""
        return reverse('home')
