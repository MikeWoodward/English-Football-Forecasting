"""
Club analysis app configuration.
"""
from django.apps import AppConfig


class ClubAnalysisConfig(AppConfig):
    """
    Configuration for the club analysis app.
    
    This app provides functionality for analyzing individual club
    performance, history, and statistics across different leagues and seasons.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'club_analysis'
