"""
URL configuration for the about app.
"""
from django.urls import path
from . import views

app_name = 'about'

urlpatterns = [
    path('', views.about_page, name='about'),
]
