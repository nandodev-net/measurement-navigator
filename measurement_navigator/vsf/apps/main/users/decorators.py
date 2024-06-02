from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


def superuser_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/"
):
    """
    Decorator for views that checks that the logged in user is a superuser,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/"
):
    """
    Decorator for views that checks that the logged in user is an admin user,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_admin,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def analist_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/"
):
    """
    Decorator for views that checks that the logged in user is an analist user,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_analist,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def editor_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/"
):
    """
    Decorator for views that checks that the logged in user is an editor user,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_editor,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def guest_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url="/"
):
    """
    Decorator for views that checks that the logged in user is an guest user,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_guest,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
