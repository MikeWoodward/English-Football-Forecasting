#!/usr/bin/env python
"""
Simple test script to verify the Django application is working.
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'EnglishFootballLeagueAnalysis.settings')
django.setup()


User = get_user_model()


def test_basic_functionality():
    """Test basic application functionality."""
    print("Testing English Football League Analysis Application")
    print("=" * 50)

    client = Client()

    # Test 1: Home page loads
    print("1. Testing home page...")
    try:
        response = client.get('/')
        if response.status_code == 200:
            print("   ✓ Home page loads successfully")
        else:
            print(f"   ✗ Home page failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Home page error: {e}")

    # Test 2: Login page loads
    print("2. Testing login page...")
    try:
        response = client.get('/accounts/login/')
        if response.status_code == 200:
            print("   ✓ Login page loads successfully")
        else:
            print(f"   ✗ Login page failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Login page error: {e}")

    # Test 3: User model works
    print("3. Testing user model...")
    try:
        user_count = User.objects.count()
        print(f"   ✓ User model works: {user_count} users found")
    except Exception as e:
        print(f"   ✗ User model error: {e}")

    # Test 4: Apps are registered
    print("4. Testing app registration...")
    try:
        from django.conf import settings
        apps = ['about', 'trends', 'goals', 'admin_app']
        for app in apps:
            if app in settings.INSTALLED_APPS:
                print(f"   ✓ {app} app is registered")
            else:
                print(f"   ✗ {app} app is not registered")
    except Exception as e:
        print(f"   ✗ App registration error: {e}")

    print("\n" + "=" * 50)
    print("Basic functionality test completed!")


if __name__ == "__main__":
    test_basic_functionality()
