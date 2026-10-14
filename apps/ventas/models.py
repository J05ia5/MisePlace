from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings


class Venta(models.Model):
    METODOS_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('QR', 'QR'),
        ('Tarjeta', 'Tarjeta'),
    ]

    fecha_venta = models.DateField('Fecha de venta', default=timezone.localdate)
    fecha_hora = models.DateTimeField('Fecha y hora', default=timezone.now)
    total_venta = models.DecimalField('Total venta (Bs.)', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    metodo_pago = models.CharField('Método de pago', max_length=20, choices=METODOS_PAGO, default='Efectivo')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas'
    )

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_hora', '-id']

    def __str__(self):
        return f"Venta #{self.id} - Bs. {self.total_venta} ({self.metodo_pago})"

    @property
    def unidades_totales(self) -> int:
        return sum(d.cantidad for d in self.detalles.all())


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    plato = models.ForeignKey('recetas.Plato', on_delete=models.PROTECT, related_name='ventas_detalle')
    cantidad = models.PositiveIntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Precio unitario (Bs.)', max_digits=10, decimal_places=2)
    subtotal = models.DecimalField('Subtotal (Bs.)', max_digits=12, decimal_places=2)
    observacion = models.TextField('Observación / Instrucción', blank=True, null=True)

    class Meta:
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'
        ordering = ['id']

    def __str__(self):
        return f"{self.cantidad}x {self.plato.nombre} (Bs. {self.subtotal})"
