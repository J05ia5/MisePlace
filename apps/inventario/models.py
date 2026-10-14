from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings


class Insumo(models.Model):
    TIPO_MEDICION_CHOICES = [
        ('peso', 'Peso'),
        ('volumen', 'Volumen'),
        ('unidad', 'Unidad'),
    ]

    UNIDAD_MEDIDA_CHOICES = [
        ('kg', 'Kilogramos (kg)'),
        ('litros', 'Litros'),
        ('und', 'Unidades (und)'),
        ('paquete', 'Paquete'),
    ]

    nombre = models.CharField('Nombre del insumo', max_length=100, unique=True)
    tipo_medicion = models.CharField('Tipo de medición', max_length=20, choices=TIPO_MEDICION_CHOICES, default='peso')
    unidad_medida = models.CharField('Unidad de medida', max_length=20, choices=UNIDAD_MEDIDA_CHOICES, default='kg')
    stock_actual = models.DecimalField('Stock actual', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    stock_minimo = models.DecimalField('Umbral mínimo de alerta', max_digits=12, decimal_places=2, default=Decimal('5.00'))
    stock_objetivo = models.DecimalField('Stock objetivo sugerido', max_digits=12, decimal_places=2, default=Decimal('10.00'))

    class Meta:
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad_medida})"

    @property
    def estado(self) -> str:
        if self.stock_actual <= 0:
            return 'critico'
        elif self.stock_actual <= self.stock_minimo:
            return 'bajo'
        return 'bueno'

    @property
    def estado_texto(self) -> str:
        if self.stock_actual <= 0:
            return 'Agotado'
        elif self.stock_actual <= self.stock_minimo:
            return 'Bajo Mínimo'
        return 'OK'

    @property
    def compra_sugerida(self) -> Decimal:
        if self.stock_actual < self.stock_objetivo:
            return max(Decimal('0.00'), self.stock_objetivo - self.stock_actual)
        return Decimal('0.00')

    @property
    def ultima_fecha_ingreso(self):
        ultimo_detalle = self.compras_detalle.select_related('compra').order_by('-compra__fecha_ingreso').first()
        if ultimo_detalle:
            return ultimo_detalle.compra.fecha_ingreso
        return None


class Proveedor(models.Model):
    nombre = models.CharField('Nombre o Razón Social', max_length=100, unique=True)
    telefono = models.CharField('Teléfono / Celular', max_length=30, blank=True, null=True)
    direccion = models.CharField('Dirección', max_length=150, blank=True, null=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    fecha_ingreso = models.DateField('Fecha de ingreso', default=timezone.localdate)
    precio_compra_total = models.DecimalField('Precio de compra total (Bs.)', max_digits=12, decimal_places=2)
    observaciones = models.TextField('Observaciones', blank=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compras_registradas'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha_ingreso', '-id']

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor.nombre} ({self.fecha_ingreso})"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT, related_name='compras_detalle')
    cantidad = models.DecimalField('Cantidad', max_digits=12, decimal_places=2)
    precio_unidad = models.DecimalField('Precio unitario (Bs.)', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de compra'
        verbose_name_plural = 'Detalles de compra'

    def __str__(self):
        return f"{self.insumo.nombre} x {self.cantidad} ({self.compra})"

    @property
    def total_pagado(self) -> Decimal:
        return self.cantidad * self.precio_unidad


class Perdida(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='perdidas')
    cantidad = models.DecimalField('Cantidad perdida/merma', max_digits=12, decimal_places=2)
    fecha = models.DateField('Fecha de pérdida', default=timezone.localdate)
    observacion = models.TextField('Observación o motivo', blank=True, null=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perdidas_registradas'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pérdida / Merma'
        verbose_name_plural = 'Pérdidas y Mermas'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"Pérdida #{self.id}: {self.insumo.nombre} (-{self.cantidad})"
