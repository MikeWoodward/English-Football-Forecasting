"""
URL configuration for the club_analysis app.
"""
from django.urls import path
from . import views

app_name = 'club_analysis'

urlpatterns = [
    path('', views.club_analysis, name='club_analysis'),
    path(
        'club-league-performance/',
        views.club_league_performance,
        name='club_league_performance',
    ),
    path(
        'club-league-season-analysis/',
        views.club_league_season_analysis,
        name='club_league_season_analysis',
    ),
    path(
        'get-club-season-analysis/',
        views.get_club_season_analysis,
        name='get_club_season_analysis',
    ),
]

