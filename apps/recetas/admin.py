from django.contrib import admin
from .models import Plato, RecetaIngrediente


class RecetaIngredienteInline(admin.TabularInline):
    model = RecetaIngrediente
    extra = 1


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_venta', 'total_ingredientes', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    inlines = [RecetaIngredienteInline]
