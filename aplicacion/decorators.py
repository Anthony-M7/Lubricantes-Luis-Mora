from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def nivel_requerido(*roles_requeridos):
    """Decorador que verifica que el usuario tenga el rol requerido"""
    def check_rol(user):
        # Admins pueden acceder a todo
        if user.admin:
            return True
        # Verificar si el usuario tiene alguno de los roles requeridos
        if user.rol in roles_requeridos:
            return True
        return False
    
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if check_rol(request.user):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para acceder a esta página")
            return redirect('inicio')
        return wrapper
    return decorator