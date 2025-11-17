"""
URL configuration for EnglishFootballLeagueAnalysis project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from admin_app.admin import admin_site

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
