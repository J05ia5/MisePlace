from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('usuarios:inicio_por_rol')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('usuarios:inicio_por_rol')
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


@login_required
def inicio_por_rol(request):
    """Redirige al usuario a su vista principal según su rol asignado."""
    user = request.user
    if user.es_empleado:
        return redirect('inventario:lista')
    # Tanto administrador como cajero van al menú POS
    return redirect('ventas:pos')
