"""
URL configuration for EnglishFootballLeagueAnalysis project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import admin_site with error handling to prevent startup failures
try:
    from admin_app.admin import admin_site
except ImportError as e:
    import sys
    print(f"Error importing admin_site: {e}", file=sys.stderr)
    # Fallback to default admin if custom admin fails to import
    from django.contrib import admin
    admin_site = admin.site

# Import custom login and logout views
try:
    from registration.views import (
        AdminLoginView,
        UserLoginView,
        LogoutView
    )
except ImportError:
    # Fallback if registration app doesn't exist
    from django.contrib.auth import views as auth_views
    AdminLoginView = auth_views.LoginView
    UserLoginView = auth_views.LoginView
    LogoutView = auth_views.LogoutView

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('about.urls')),
    path('trends/', include('trends.urls')),
    path('goals/', include('goals.urls')),
    path('admin_app/', include('admin_app.urls')),
    path('club_analysis/', include('club_analysis.urls')),
    # Custom login and logout views - must come before
    # django.contrib.auth.urls
    path(
        'accounts/admin-login/',
        AdminLoginView.as_view(),
        name='admin_login'
    ),
    path(
        'accounts/login/',
        UserLoginView.as_view(),
        name='login'
    ),
    path(
        'accounts/logout/',
        LogoutView.as_view(),
        name='logout'
    ),
    # Other auth URLs (password change, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
