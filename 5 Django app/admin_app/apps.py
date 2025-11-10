"""
Admin app configuration.
"""
from django.apps import AppConfig


class AdminAppConfig(AppConfig):
    """Configuration for the admin app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_app'

