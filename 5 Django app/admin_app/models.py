"""
Models for the admin app.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    This model stores user and admin data in the PostgreSQL database.
    """
    is_admin = models.BooleanField(
        default=False,
        help_text="Designates whether this user is an admin."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        """Return string representation of the user."""
        return f"{self.username} ({'Admin' if self.is_admin else 'User'})"
