"""
URL configuration for the trends app.
"""
from django.urls import path
from . import views

app_name = 'trends'

urlpatterns = [
    path('', views.trends_dashboard, name='dashboard'),
    path('goals-over-time/', views.goals_over_time, name='goals_over_time'),
    path('home-advantage-over-time/', views.home_advantage_over_time,
         name='home_advantage_over_time'),
    path('draw-fraction-over-time/', views.draw_fraction_over_time,
         name='draw_fraction_over_time'),
    path(
        'inequality-win-fraction-sd-over-time/',
        views.inequality_win_fraction_sd_over_time,
        name='inequality_win_fraction_sd_over_time',
    ),
    path(
        'discipline-over-time/',
        views.discipline_over_time,
        name='discipline_over_time',
    ),
    path(
        'attendance-over-time/',
        views.attendance_over_time,
        name='attendance_over_time',
    ),
    path(
        'attendance-violin-json/',
        views.attendance_violin_json,
        name='attendance_violin_json',
    ),
]
