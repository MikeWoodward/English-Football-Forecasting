"""
Views for the about app.
"""
from django.shortcuts import render


def about_page(request):
    """
    Display the main about page with application description.

    Shows explanatory text about the whole app and provides links
    to login as a user or as an admin.
    """
    # Refresh user from database to ensure is_admin is current
    if request.user.is_authenticated:
        try:
            request.user.refresh_from_db()
        except Exception:
            pass
    
    context = {
        'title': 'About English Football League Analysis',
    }
    return render(request, 'about/about.html', context)
