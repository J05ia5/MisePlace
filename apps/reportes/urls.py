from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard_reportes, name='dashboard'),
    path('api/estado-sistema/', views.api_estado_sistema, name='api_estado_sistema'),
]
