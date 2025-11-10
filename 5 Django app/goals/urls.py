"""
URL configuration for the goals app.
"""
from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goals_dashboard, name='dashboard'),
    path('goal-timing/', views.goal_timing, name='goal_timing'),
    path('player-impact/', views.player_impact, name='player_impact'),
]
