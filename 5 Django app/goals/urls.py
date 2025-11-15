"""
URL configuration for the goals app.
"""
from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goals_dashboard, name='dashboard'),
    path('money-and-goals/', views.money_and_goals, name='money_and_goals'),
    path(
        'money-goals-json/<int:league_tier>/<int:season_start>/',
        views.money_goals_json,
        name='money_goals_json',
    ),
    path('tenure-and-goals/', views.tenure_and_goals, name='tenure_and_goals'),
    path(
        'tenure-goals-json/<int:league_tier>/<int:season_start>/',
        views.tenure_goals_json,
        name='tenure_goals_json',
    ),
    path('mean-age-and-goals/', views.mean_age_and_goals, name='mean_age_and_goals'),
    path(
        'mean-age-goals-json/<int:league_tier>/<int:season_start>/',
        views.mean_age_goals_json,
        name='mean_age_goals_json',
    ),
    path('foreigner-count-and-goals/', views.foreigner_count_and_goals, name='foreigner_count_and_goals'),
    path(
        'foreigner-count-goals-json/<int:league_tier>/<int:season_start>/',
        views.foreigner_count_goals_json,
        name='foreigner_count_goals_json',
    ),
    path('score-distribution/', views.score_distribution, name='score_distribution'),
]
