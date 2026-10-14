from django.urls import path
from . import views

app_name = 'recetas'

urlpatterns = [
    path('', views.gestion_recetas, name='lista'),
    path('api/insumos/', views.api_insumos_list, name='api_insumos'),
    path('api/<int:plato_id>/', views.api_obtener_receta, name='api_obtener_receta'),
    path('api/guardar/', views.api_guardar_receta, name='api_guardar_receta'),
    path('api/eliminar/<int:plato_id>/', views.api_eliminar_receta, name='api_eliminar_receta'),
]
