"""
Admin configuration for the admin app.
"""
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse
from .models import CustomUser


class AdminOnlyAdminSite(AdminSite):
    """
    Custom admin site that restricts access to admin users only.
    
    Only users with is_admin=True can access this admin site.
    """
    site_header = 'English Football League Analysis Admin'
    site_title = 'EFL Admin'
    index_title = 'Administration'

    def has_permission(self, request):
        """
        Check if user has permission to access the admin site.
        
        Returns True only if user is authenticated and is_admin=True.
        """
        if not request.user.is_authenticated:
            return False
        if not request.user.is_active:
            return False
        # Check if user has is_admin attribute and it's True
        return (
            hasattr(request.user, 'is_admin') and
            request.user.is_admin
        )

    def login(self, request, extra_context=None):
        """
        Override login to redirect to custom admin login page.
        """
        if request.method == 'GET' and self.has_permission(request):
            # Already logged in and is admin, redirect to home page
            return redirect('/')
        # Redirect to custom admin login page
        from django.urls import reverse as url_reverse
        try:
            admin_login_url = url_reverse('admin_login')
            return redirect(admin_login_url)
        except Exception:
            # Fallback to default admin login if custom URL doesn't exist
            return super().login(request, extra_context)


# Create custom admin site instance
admin_site = AdminOnlyAdminSite(name='admin')


class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser model."""
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_admin',
        'is_staff',
        'is_active',
        'date_joined'
    )
    list_filter = (
        'is_admin',
        'is_staff',
        'is_active',
        'date_joined'
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Admin Status', {'fields': ('is_admin',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Admin Status', {'fields': ('is_admin',)}),
    )


# Register the model after the class is defined
admin_site.register(CustomUser, CustomUserAdmin)
