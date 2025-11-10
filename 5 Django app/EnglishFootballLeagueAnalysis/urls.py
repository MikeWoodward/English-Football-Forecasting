"""
URL configuration for EnglishFootballLeagueAnalysis project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('about.urls')),
    path('trends/', include('trends.urls')),
    path('goals/', include('goals.urls')),
    path('admin_app/', include('admin_app.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, 
                         document_root=settings.STATIC_ROOT)

