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

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('about.urls')),
    path('trends/', include('trends.urls')),
    path('goals/', include('goals.urls')),
    path('admin_app/', include('admin_app.urls')),
    path('club_analysis/', include('club_analysis.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
