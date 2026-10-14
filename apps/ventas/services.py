from collections import defaultdict
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from inventario.models import Insumo
from recetas.models import Plato
from .models import Venta, DetalleVenta


def procesar_venta_atomic(items: list, metodo_pago: str, usuario=None) -> Venta:
    """
    Procesa de manera atómica una venta desde el Menú POS:
    1. Valida cantidades y platos existentes.
    2. Calcula insumos requeridos según las recetas de cada plato.
    3. Bloquea con `select_for_update` los insumos para evitar condiciones de carrera.
    4. Valida disponibilidad de stock; si falta alguno, rechaza con detalle exacto.
    5. Descuenta el stock y registra la venta y sus detalles.
    """
    if not items:
        raise ValidationError("El pedido está vacío.")

    if metodo_pago not in ['Efectivo', 'QR', 'Tarjeta']:
        raise ValidationError("Método de pago no reconocido.")

    with transaction.atomic():
        # Validar y cargar platos
        platos_ids = [int(it['id']) for it in items]
        platos_map = Plato.objects.in_bulk(platos_ids)

        if len(platos_map) != len(set(platos_ids)):
            raise ValidationError("Uno o más platos del pedido no existen.")

        total_venta = Decimal('0.00')
        consumo_insumos = defaultdict(lambda: {
            'nombre': '',
            'unidad': '',
            'cantidad_requerida': Decimal('0.00'),
        })

        # Recorrer platos del pedido y acumular insumos necesarios
        for it in items:
            plato_id = int(it['id'])
            cantidad = int(it['cantidad'])
            if cantidad < 1:
                raise ValidationError("La cantidad de cada plato debe ser al menos 1.")

            plato = platos_map[plato_id]
            subtotal = plato.precio_venta * cantidad
            total_venta += subtotal

            # Cargar recetas asociadas
            for receta in plato.ingredientes.select_related('insumo').all():
                insumo_id = receta.insumo_id
                consumo_insumos[insumo_id]['nombre'] = receta.insumo.nombre
                consumo_insumos[insumo_id]['unidad'] = receta.insumo.unidad_medida
                consumo_insumos[insumo_id]['cantidad_requerida'] += (receta.cantidad_necesaria * cantidad)

        # Si hay insumos requeridos, bloquearlos y validar stock
        if consumo_insumos:
            insumos_ids = list(consumo_insumos.keys())
            # Bloqueo a nivel de base de datos
            insumos_db = Insumo.objects.select_for_update().in_bulk(insumos_ids)

            for insumo_id, datos in consumo_insumos.items():
                insumo = insumos_db.get(insumo_id)
                if not insumo:
                    raise ValidationError(f"El insumo '{datos['nombre']}' no existe en el inventario.")

                if insumo.stock_actual < datos['cantidad_requerida']:
                    raise ValidationError(
                        f"Stock insuficiente de '{insumo.nombre}'. "
                        f"Disponible: {insumo.stock_actual:.2f} {insumo.unidad_medida}, "
                        f"requerido para este pedido: {datos['cantidad_requerida']:.2f} {insumo.unidad_medida}."
                    )

            # Descontar stock
            for insumo_id, datos in consumo_insumos.items():
                insumo = insumos_db[insumo_id]
                insumo.stock_actual -= datos['cantidad_requerida']
                insumo.save()

        # Crear cabecera de Venta
        ahora = timezone.now()
        venta = Venta.objects.create(
            fecha_venta=timezone.localdate(ahora),
            fecha_hora=ahora,
            total_venta=total_venta,
            metodo_pago=metodo_pago,
            usuario=usuario
        )

        # Crear líneas de DetalleVenta
        for it in items:
            plato = platos_map[int(it['id'])]
            cantidad = int(it['cantidad'])
            subtotal = plato.precio_venta * cantidad
            observacion = it.get('observacion', '').strip() or None

            DetalleVenta.objects.create(
                venta=venta,
                plato=plato,
                cantidad=cantidad,
                precio_unitario=plato.precio_venta,
                subtotal=subtotal,
                observacion=observacion
            )

        return venta
