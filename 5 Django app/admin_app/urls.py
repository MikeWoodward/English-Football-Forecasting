"""
URL configuration for the admin app.
"""
from django.urls import path
from . import views

app_name = 'admin_app'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]

