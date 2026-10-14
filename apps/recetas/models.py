import math
from decimal import Decimal
from django.db import models


class Plato(models.Model):
    nombre = models.CharField('Nombre del plato o producto', max_length=100, unique=True)
    precio_venta = models.DecimalField('Precio de venta (Bs.)', max_digits=10, decimal_places=2)
    imagen = models.ImageField('Imagen del plato', upload_to='platos/', blank=True, null=True)
    activo = models.BooleanField('Activo en el menú', default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plato / Producto'
        verbose_name_plural = 'Platos y Productos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - Bs. {self.precio_venta}"

    @property
    def total_ingredientes(self) -> int:
        return self.ingredientes.count()

    def calcular_porciones_disponibles(self) -> int:
        """
        Calcula cuántas porciones pueden prepararse en base al stock actual de sus insumos.
        Si no tiene receta configurada, retorna 999.
        """
        ingredientes = self.ingredientes.select_related('insumo').all()
        if not ingredientes.exists():
            return 999

        porciones = []
        for ing in ingredientes:
            if ing.cantidad_necesaria <= Decimal('0'):
                continue
            disponible = ing.insumo.stock_actual / ing.cantidad_necesaria
            porciones.append(max(0, int(math.floor(float(disponible)))))

        return min(porciones) if porciones else 0


class RecetaIngrediente(models.Model):
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='ingredientes')
    insumo = models.ForeignKey('inventario.Insumo', on_delete=models.PROTECT, related_name='recetas')
    cantidad_necesaria = models.DecimalField('Cantidad requerida por plato', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ingrediente de receta'
        verbose_name_plural = 'Ingredientes de receta'
        unique_together = ('plato', 'insumo')
        ordering = ['insumo__nombre']

    def __str__(self):
        return f"{self.plato.nombre} -> {self.insumo.nombre}: {self.cantidad_necesaria} {self.insumo.unidad_medida}"
