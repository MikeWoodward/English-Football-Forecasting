"""
Custom authentication views for separate admin and user login pages.
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class AdminLoginView(auth_views.LoginView):
    """
    Custom login view for admin users.
    
    Shows "Admin user login" header and redirects to admin panel
    after successful login.
    """
    template_name = 'registration/admin_login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Redirect admin users to home page after login.
        """
        return '/'

    def form_valid(self, form):
        """
        Override form_valid to ensure user object is refreshed after login.
        """
        # Get the user before login
        user = form.get_user()
        # Call parent to perform login (this sets request.user)
        response = super().form_valid(form)
        # Ensure user object is fresh from database
        # This is important for custom user attributes like is_admin
        try:
            # Refresh user from database to get latest is_admin value
            user.refresh_from_db()
            # Re-authenticate to update session with fresh user data
            from django.contrib.auth import login
            login(self.request, user)
        except Exception:
            # If refresh fails, the user is still logged in
            # The template should still work with request.user
            pass
        return response

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect already authenticated admin users.
        """
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


class UserLoginView(auth_views.LoginView):
    """
    Custom login view for regular users.
    
    Shows "User login" header and redirects to home page
    after successful login.
    """
    template_name = 'registration/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Redirect users to home page after login.
        """
        return '/'

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect already authenticated users.
        """
        if request.user.is_authenticated:
            return redirect('about:about')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(auth_views.LogoutView):
    """
    Custom logout view that redirects to home page.
    
    Works for both admin and regular users.
    Accepts both GET and POST requests to handle admin panel logout.
    CSRF is exempted to allow GET requests from admin panel.
    """
    next_page = '/'
    http_method_names = ['get', 'post', 'options']

    def dispatch(self, request, *args, **kwargs):
        """
        Handle both GET and POST requests for logout.
        """
        # For GET requests, logout immediately
        if request.method == 'GET':
            logout(request)
            return redirect(self.next_page)
        # For POST requests, use the parent class behavior
        return super().dispatch(request, *args, **kwargs)

