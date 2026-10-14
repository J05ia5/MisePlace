from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Insumo, Proveedor, Compra, DetalleCompra, Perdida


def registrar_ingreso_compra(nombre_insumo: str, unidad_medida: str, cantidad: Decimal,
                             proveedor_id: int, fecha_ingreso, precio_compra_total: Decimal,
                             precio_unidad: Decimal = None, observaciones: str = '', usuario=None) -> Compra:
    """
    Registra atómicamente la compra de un insumo, sumando la cantidad al stock del inventario.
    """
    nombre_insumo = nombre_insumo.strip()
    if not nombre_insumo:
        raise ValidationError("El nombre del insumo es obligatorio.")

    if cantidad <= Decimal('0.00'):
        raise ValidationError("La cantidad a ingresar debe ser mayor a cero.")

    if precio_compra_total <= Decimal('0.00'):
        raise ValidationError("El precio de compra total debe ser mayor a cero.")

    if not precio_unidad or precio_unidad <= Decimal('0.00'):
        precio_unidad = precio_compra_total / cantidad

    # Determinar tipo de medición según unidad
    if unidad_medida == 'litros':
        tipo_medicion = 'volumen'
    elif unidad_medida == 'kg':
        tipo_medicion = 'peso'
    else:
        tipo_medicion = 'unidad'

    with transaction.atomic():
        proveedor = Proveedor.objects.get(id=proveedor_id)

        # Buscar o crear insumo
        insumo = Insumo.objects.select_for_update().filter(nombre__iexact=nombre_insumo).first()
        if insumo:
            insumo.unidad_medida = unidad_medida
            insumo.tipo_medicion = tipo_medicion
            insumo.stock_actual += cantidad
            insumo.save()
        else:
            insumo = Insumo.objects.create(
                nombre=nombre_insumo,
                tipo_medicion=tipo_medicion,
                unidad_medida=unidad_medida,
                stock_actual=cantidad
            )

        # Crear Compra
        compra = Compra.objects.create(
            proveedor=proveedor,
            fecha_ingreso=fecha_ingreso,
            precio_compra_total=precio_compra_total,
            observaciones=observaciones or None,
            creado_por=usuario
        )

        # Crear DetalleCompra
        DetalleCompra.objects.create(
            compra=compra,
            insumo=insumo,
            cantidad=cantidad,
            precio_unidad=precio_unidad
        )

        return compra


def registrar_perdida_merma(insumo_id: int, cantidad: Decimal, fecha, observacion: str = '', usuario=None) -> Perdida:
    """
    Registra una pérdida o merma de inventario de forma atómica, validando que no exceda el stock actual.
    """
    if cantidad <= Decimal('0.00'):
        raise ValidationError("La cantidad de merma debe ser positiva.")

    with transaction.atomic():
        try:
            insumo = Insumo.objects.select_for_update().get(id=insumo_id)
        except Insumo.DoesNotExist:
            raise ValidationError("El insumo seleccionado no existe.")

        if cantidad > insumo.stock_actual:
            raise ValidationError(
                f"La pérdida ({cantidad} {insumo.unidad_medida}) supera el stock disponible de "
                f"{insumo.nombre} ({insumo.stock_actual} {insumo.unidad_medida})."
            )

        insumo.stock_actual -= cantidad
        insumo.save()

        perdida = Perdida.objects.create(
            insumo=insumo,
            cantidad=cantidad,
            fecha=fecha,
            observacion=observacion or None,
            registrado_por=usuario
        )

        return perdida
