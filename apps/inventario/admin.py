from django.contrib import admin
from .models import Insumo, Proveedor, Compra, DetalleCompra, Perdida


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock_actual', 'unidad_medida', 'tipo_medicion', 'stock_minimo', 'estado_texto')
    list_filter = ('tipo_medicion', 'unidad_medida')
    search_fields = ('nombre',)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion')
    search_fields = ('nombre', 'telefono')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'fecha_ingreso', 'precio_compra_total', 'creado_por')
    list_filter = ('fecha_ingreso', 'proveedor')
    inlines = [DetalleCompraInline]


@admin.register(Perdida)
class PerdidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'insumo', 'cantidad', 'fecha', 'observacion', 'registrado_por')
    list_filter = ('fecha', 'insumo')
    search_fields = ('insumo__nombre', 'observacion')
