"""
Views for the admin app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import UserCreateForm, UserEditForm

User = get_user_model()


def is_admin_user(user):
    """Check if user is an admin or superuser."""
    if not user.is_authenticated:
        return False
    if not user.is_active:
        return False
    # Check if user is superuser (has all permissions)
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True
    # Check if user has is_admin attribute and it's True
    return (
        hasattr(user, 'is_admin') and
        user.is_admin
    )


@login_required(login_url='/accounts/admin-login/')
@user_passes_test(
    is_admin_user,
    login_url='/accounts/admin-login/'
)
def admin_dashboard(request):
    """
    Admin dashboard showing user management options.

    Only accessible to logged in admin users.
    """
    # Refresh user from database to ensure is_admin is current
    try:
        request.user.refresh_from_db()
    except Exception:
        pass
    
    # Double-check user is admin or superuser (defensive programming)
    is_admin = (
        (hasattr(request.user, 'is_admin') and request.user.is_admin) or
        (hasattr(request.user, 'is_superuser') and request.user.is_superuser)
    )
    if not is_admin:
        from django.contrib import messages
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        from django.shortcuts import redirect
        return redirect('/')
    
    context = {
        'title': 'Admin Dashboard',
        'total_users': User.objects.count(),
        'admin_users': User.objects.filter(is_admin=True).count(),
        'regular_users': User.objects.filter(is_admin=False).count(),
    }
    return render(request, 'admin_app/dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_list(request):
    """
    List all users with pagination and search.

    Only accessible to logged in admin users.
    """
    search_query = request.GET.get('search', '')
    users = User.objects.all()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'User Management',
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_app/user_list.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_create(request):
    """
    Create a new user.

    Only accessible to logged in admin users.
    """
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f'User "{user.username}" created successfully.')
            return redirect('admin_app:user_list')
    else:
        form = UserCreateForm()

    context = {
        'title': 'Create User',
        'form': form,
    }
    return render(request, 'admin_app/user_form.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_edit(request, user_id):
    """
    Edit an existing user.

    Only accessible to logged in admin users.
    """
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'User "{user.username}" updated successfully.')
            return redirect('admin_app:user_list')
    else:
        form = UserEditForm(instance=user)

    context = {
        'title': f'Edit User: {user.username}',
        'form': form,
        'user': user,
    }
    return render(request, 'admin_app/user_form.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_delete(request, user_id):
    """
    Delete a user.

    Only accessible to logged in admin users.
    """
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('admin_app:user_list')

    context = {
        'title': f'Delete User: {user.username}',
        'user': user,
    }
    return render(request, 'admin_app/user_confirm_delete.html', context)
