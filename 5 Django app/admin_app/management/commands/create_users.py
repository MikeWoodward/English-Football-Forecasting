"""
Management command to create initial users.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Create initial admin and regular users."""

    help = 'Create initial admin and regular users for the application'

    def handle(self, *args, **options):
        """Create the initial users."""
        try:
            # Create admin user
            admin_user, created = User.objects.get_or_create(
                username='Falcon1234',
                defaults={
                    'email': 'admin@footballanalysis.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_admin': True,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True
                }
            )

            if created:
                admin_user.set_password('birdbrain')
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Admin user "Falcon1234" created successfully')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Admin user "Falcon1234" already exists')
                )

            # Create regular user
            regular_user, created = User.objects.get_or_create(
                username='Footsmall',
                defaults={
                    'email': 'user@footballanalysis.com',
                    'first_name': 'Regular',
                    'last_name': 'User',
                    'is_admin': False,
                    'is_staff': False,
                    'is_superuser': False,
                    'is_active': True
                }
            )

            # Always ensure password is set correctly
            regular_user.set_password('roundball')
            regular_user.save()

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        'Regular user "Footsmall" created successfully')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        'Regular user "Footsmall" already exists, password updated'
                    )
                )

        except Exception as e:
            logger.error(
                f"Error creating users at line {e.__traceback__.tb_lineno}: {e}")
            self.stdout.write(
                self.style.ERROR(f'Error creating users: {e}')
            )
