from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse


def roles_requeridos(roles_permitidos, formato='html'):
    """
    Decorador que restringe el acceso a vistas según los roles del usuario.
    roles_permitidos: lista o tupla de strings ('administrador', 'cajero', 'empleado')
    formato: 'html' o 'json'
    """
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if formato == 'json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Debes iniciar sesión.'}, status=401)
                return redirect(f"{reverse('usuarios:login')}?next={request.path}")

            # Superusers always have full access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            rol_usuario = getattr(request.user, 'rol', None)
            if rol_usuario not in roles_permitidos:
                if formato == 'json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'No tienes permisos para realizar esta operación.'}, status=403)
                
                # Redirect to appropriate home page for their role with an error or forbidden response
                if request.user.es_empleado:
                    return redirect('inventario:lista')
                elif request.user.es_cajero:
                    return redirect('ventas:pos')
                else:
                    return HttpResponseForbidden("Acceso denegado. Tu rol no tiene permisos para esta funcionalidad.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorador
