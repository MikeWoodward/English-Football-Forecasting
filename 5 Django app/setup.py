#!/usr/bin/env python
"""
Setup script for English Football League Analysis Django application.
"""
import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("Setting up English Football League Analysis Django Application")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not Path("venv").exists():
        print("Creating virtual environment...")
        if not run_command("python -m venv venv", "Virtual environment creation"):
            sys.exit(1)
    
    # Install requirements
    print("\nInstalling requirements...")
    if not run_command("pip install -r requirements.txt", "Requirements installation"):
        print("Warning: Requirements installation failed. Please install manually.")
    
    # Check for .env file
    if not Path(".env").exists():
        print("\nCreating .env file from template...")
        if Path("env.example").exists():
            run_command("cp env.example .env", "Environment file creation")
            print("Please edit .env file with your database credentials.")
        else:
            print("Warning: env.example not found. Please create .env manually.")
    
    # Run migrations
    print("\nRunning database migrations...")
    if not run_command("python manage.py makemigrations", "Migration creation"):
        print("Warning: Migration creation failed.")
    
    if not run_command("python manage.py migrate", "Database migration"):
        print("Warning: Database migration failed.")
    
    # Create initial users
    print("\nCreating initial users...")
    if not run_command("python manage.py create_users", "User creation"):
        print("Warning: User creation failed.")
    
    print("\n" + "=" * 60)
    print("Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Run: python manage.py runserver")
    print("3. Visit: http://localhost:8000")
    print("\nDefault users:")
    print("- Admin: Falcon1234 / birdbrain")
    print("- User: Footsmall / roundball")


if __name__ == "__main__":
    main()
