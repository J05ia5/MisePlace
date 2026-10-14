from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.lista_inventario, name='lista'),
    path('ingreso/', views.procesar_ingreso, name='procesar_ingreso'),
    path('perdida/', views.procesar_perdida, name='procesar_perdida'),
    path('alertas/', views.alertas_stock, name='alertas'),
    path('compras-sugeridas/', views.lista_compras, name='compras_sugeridas'),
]
