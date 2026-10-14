from django.contrib import admin
from .models import Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora', 'total_venta', 'metodo_pago', 'usuario', 'unidades_totales')
    list_filter = ('fecha_venta', 'metodo_pago', 'usuario')
    inlines = [DetalleVentaInline]
