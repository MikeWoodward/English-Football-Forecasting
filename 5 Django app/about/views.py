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
    context = {
        'title': 'About English Football League Analysis',
    }
    return render(request, 'about/about.html', context)
