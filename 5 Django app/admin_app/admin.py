"""
Admin configuration for the admin app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser model."""
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_admin', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_admin', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Admin Status', {'fields': ('is_admin',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Admin Status', {'fields': ('is_admin',)}),
    )
