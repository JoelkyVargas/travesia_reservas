from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_superuser:
            messages.error(request, "Solo el dueño puede acceder a esta sección.")
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)
    return wrapper
