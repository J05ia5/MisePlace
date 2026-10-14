from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.menu_pos, name='pos'),
    path('procesar/', views.procesar_venta_view, name='procesar_venta'),
    path('comprobante/<int:venta_id>/', views.comprobante_venta, name='comprobante'),
]
