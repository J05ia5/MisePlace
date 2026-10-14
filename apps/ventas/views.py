import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Sum
from usuarios.decorators import roles_requeridos
from recetas.models import Plato
from .models import Venta, DetalleVenta
from .services import procesar_venta_atomic


@roles_requeridos(['administrador', 'cajero'])
def menu_pos(request):
    """
    Menú Virtual / POS para cajeros y administradores:
    - Catálogo de platos interactivo con imágenes y precios.
    - Panel lateral de pedido (agregar, editar cantidades/notas, eliminar).
    - Modal de ingredientes a descontar.
    - Confirmación de pago (Efectivo / QR).
    - Comprobante imprimible y consulta del historial diario.
    """
    platos = Plato.objects.filter(activo=True).prefetch_related('ingredientes__insumo').order_by('nombre')

    # Diccionario de recetas en formato JSON para la inspección rápida en el navegador
    recetas_data = {}
    for p in platos:
        recetas_data[str(p.id)] = [
            {
                'insumo': ing.insumo.nombre,
                'cantidad_necesaria': str(ing.cantidad_necesaria),
                'unidad_medida': ing.insumo.unidad_medida,
            }
            for ing in p.ingredientes.all()
        ]

    # Filtro de fecha para historial del día
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_consulta = timezone.datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_consulta = timezone.localdate()
    else:
        fecha_consulta = timezone.localdate()

    ventas_dia = Venta.objects.filter(fecha_venta=fecha_consulta).prefetch_related('detalles__plato').order_by('-fecha_hora')

    # Si se solicitó ver un comprobante específico
    id_venta_recibo = request.GET.get('venta')
    venta_recibo = None
    if id_venta_recibo:
        venta_recibo = Venta.objects.filter(id=id_venta_recibo).prefetch_related('detalles__plato', 'usuario').first()

    context = {
        'platos': platos,
        'recetas_json': json.dumps(recetas_data),
        'ventas_dia': ventas_dia,
        'fecha_historial': fecha_consulta.strftime('%Y-%m-%d'),
        'venta_recibo': venta_recibo,
    }
    return render(request, 'ventas/pos.html', context)


@require_POST
@roles_requeridos(['administrador', 'cajero'])
def procesar_venta_view(request):
    """Recibe la confirmación del pedido y ejecuta la venta de forma atómica."""
    items_raw = request.POST.get('items', '')
    metodo_pago = request.POST.get('metodo_pago', 'Efectivo')

    if not items_raw:
        messages.error(request, "El pedido está vacío.")
        return redirect('ventas:pos')

    try:
        items = json.loads(items_raw)
        if not isinstance(items, list) or len(items) == 0:
            raise ValueError("Formato de pedido inválido.")

        venta = procesar_venta_atomic(
            items=items,
            metodo_pago=metodo_pago,
            usuario=request.user
        )
        return redirect(f"{redirect('ventas:pos').url}?venta={venta.id}")

    except Exception as e:
        messages.error(request, f"No se pudo completar la venta: {str(e)}")
        return redirect('ventas:pos')


@require_GET
@roles_requeridos(['administrador', 'cajero'])
def comprobante_venta(request, venta_id):
    """Comprobante de venta en vista limpia imprimible."""
    venta = get_object_or_404(Venta.objects.prefetch_related('detalles__plato', 'usuario'), id=venta_id)
    return render(request, 'ventas/comprobante.html', {'venta': venta})
