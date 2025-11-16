"""
URL configuration for the club_analysis app.
"""
from django.urls import path
from . import views

app_name = 'club_analysis'

urlpatterns = [
    path('', views.club_analysis, name='club_analysis'),
]

