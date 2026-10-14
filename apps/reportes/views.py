import hashlib
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Max, F
from usuarios.decorators import roles_requeridos
from inventario.models import Insumo, Compra, Perdida
from recetas.models import Plato
from ventas.models import Venta, DetalleVenta


@roles_requeridos(['administrador', 'empleado'])
def dashboard_reportes(request):
    """
    Dashboard de reportes:
    - Para Administrador: Inventario + Ranking de ventas + Gráfica semanal + Historiales.
    - Para Empleado: Enfoque operativo en inventario, alertas y reposiciones.
    """
    es_admin = request.user.es_admin

    # Inventario completo ordenado de menor a mayor stock
    inventario = list(Insumo.objects.all().order_by('stock_actual', 'nombre'))
    stock_bajo_total = sum(1 for i in inventario if i.estado in ('critico', 'bajo'))
    inventario_visible = inventario[:5]

    ventas_por_producto = []
    ventas_visibles = []
    max_unidades = 0
    historial_ventas = []
    datos_semana = []
    ingreso_semana = Decimal('0.00')
    unidades_semana = 0
    inicio_semana = None
    fin_semana = None

    if es_admin:
        # Ranking de productos por unidades e ingresos
        platos_agrupados = DetalleVenta.objects.values(
            'plato__id', 'plato__nombre', 'plato__precio_venta'
        ).annotate(
            total_unidades=Sum('cantidad'),
            total_ingresos=Sum('subtotal')
        ).order_by('-total_unidades', '-total_ingresos', 'plato__nombre')

        for p in platos_agrupados:
            ventas_por_producto.append({
                'id_plato': p['plato__id'],
                'plato': p['plato__nombre'],
                'precio_venta': p['plato__precio_venta'],
                'total_unidades': p['total_unidades'] or 0,
                'total_ingresos': p['total_ingresos'] or Decimal('0.00'),
            })

        ventas_visibles = ventas_por_producto[:5]
        if ventas_visibles:
            max_unidades = max(v['total_unidades'] for v in ventas_visibles)

        # Historial de ventas cronológico
        historial_ventas = DetalleVenta.objects.select_related('venta', 'plato').order_by('-venta__fecha_venta', '-venta__id', '-id')

        # Gráfica semanal: semana de la última venta o actual
        ultima_venta = Venta.objects.aggregate(max_fecha=Max('fecha_venta'))['max_fecha']
        fecha_ancla = ultima_venta or timezone.localdate()

        # Inicio de semana (Lunes = 0)
        inicio_semana = fecha_ancla - timedelta(days=fecha_ancla.weekday())
        fin_semana = inicio_semana + timedelta(days=6)

        # Totales agrupados por fecha dentro de la semana
        ventas_semana_db = Venta.objects.filter(
            fecha_venta__range=[inicio_semana, fin_semana]
        ).values('fecha_venta').annotate(
            ingresos=Sum('total_venta'),
            unidades=Sum('detalles__cantidad')
        )

        mapa_fechas = {v['fecha_venta']: v for v in ventas_semana_db}
        nombres_dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

        for i in range(7):
            dia_fecha = inicio_semana + timedelta(days=i)
            datos_dia = mapa_fechas.get(dia_fecha, {'ingresos': Decimal('0.00'), 'unidades': 0})
            ing = datos_dia['ingresos'] or Decimal('0.00')
            uni = datos_dia['unidades'] or 0
            ingreso_semana += ing
            unidades_semana += uni

            datos_semana.append({
                'dia': nombres_dias[i],
                'fecha': dia_fecha.strftime('%d/%m'),
                'ingresos': float(ing),
                'unidades': int(uni)
            })

    # Insumos sugeridos para modal de compras
    insumos_sugeridos = [i for i in inventario if i.estado in ('critico', 'bajo')]

    context = {
        'es_admin': es_admin,
        'inventario': inventario,
        'inventario_visible': inventario_visible,
        'stock_bajo_total': stock_bajo_total,
        'insumos_sugeridos': insumos_sugeridos,
        'ventas_por_producto': ventas_por_producto,
        'ventas_visibles': ventas_visibles,
        'max_unidades': max_unidades,
        'historial_ventas': historial_ventas,
        'datos_semana': datos_semana,
        'ingreso_semana': ingreso_semana,
        'unidades_semana': unidades_semana,
        'inicio_semana': inicio_semana,
        'fin_semana': fin_semana,
    }
    return render(request, 'reportes/dashboard.html', context)


def api_estado_sistema(request):
    """
    Endpoint que devuelve un hash SHA-256 del estado actual del sistema
    (inventario, ventas, compras, pérdidas y platos).
    Permite a los clientes sincronizar y detectar actualizaciones de otros usuarios en tiempo real.
    """
    partes = []

    # Insumos
    insumo_hash = Insumo.objects.aggregate(
        total=Count('id'),
        stock_sum=Sum('stock_actual'),
        max_id=Max('id')
    )
    partes.append(f"insumos:{insumo_hash['total']}:{insumo_hash['stock_sum']}:{insumo_hash['max_id']}")

    # Ventas
    venta_hash = Venta.objects.aggregate(
        total=Count('id'),
        total_sum=Sum('total_venta'),
        max_id=Max('id')
    )
    partes.append(f"ventas:{venta_hash['total']}:{venta_hash['total_sum']}:{venta_hash['max_id']}")

    # Compras
    compra_hash = Compra.objects.aggregate(
        total=Count('id'),
        total_sum=Sum('precio_compra_total'),
        max_id=Max('id')
    )
    partes.append(f"compras:{compra_hash['total']}:{compra_hash['total_sum']}:{compra_hash['max_id']}")

    # Pérdidas
    perdida_hash = Perdida.objects.aggregate(
        total=Count('id'),
        total_sum=Sum('cantidad'),
        max_id=Max('id')
    )
    partes.append(f"perdidas:{perdida_hash['total']}:{perdida_hash['total_sum']}:{perdida_hash['max_id']}")

    # Platos
    plato_hash = Plato.objects.aggregate(
        total=Count('id'),
        precio_sum=Sum('precio_venta'),
        max_id=Max('id')
    )
    partes.append(f"platos:{plato_hash['total']}:{plato_hash['precio_sum']}:{plato_hash['max_id']}")

    cadena = "||".join(partes)
    version = hashlib.sha256(cadena.encode('utf-8')).hexdigest()

    response = JsonResponse({'version': version})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
