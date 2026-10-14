from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from usuarios.decorators import roles_requeridos
from .models import Insumo, Proveedor, Compra, DetalleCompra, Perdida
from .services import registrar_ingreso_compra, registrar_perdida_merma


@roles_requeridos(['administrador', 'empleado'])
def lista_inventario(request):
    """
    Vista principal de inventario: formulario de ingresos, tabla de stock disponible,
    modales de mermas e historial interactivo.
    """
    insumos = Insumo.objects.all().order_by('nombre')
    proveedores = Proveedor.objects.all().order_by('nombre')

    # Historial combinado de compras (ingresos) y pérdidas (egresos)
    historial = []
    detalles_compras = DetalleCompra.objects.select_related('compra', 'insumo', 'compra__proveedor').order_by('-compra__fecha_ingreso', '-id')
    for dc in detalles_compras:
        historial.append({
            'tipo': 'ingreso',
            'fecha': dc.compra.fecha_ingreso,
            'insumo': dc.insumo.nombre,
            'unidad_medida': dc.insumo.unidad_medida,
            'cantidad': dc.cantidad,
            'proveedor_obs': dc.compra.proveedor.nombre,
            'precio_unidad': dc.precio_unidad,
            'total_pagado': dc.total_pagado,
            'timestamp': dc.compra.fecha_registro.timestamp() if dc.compra.fecha_registro else 0,
        })

    perdidas = Perdida.objects.select_related('insumo').order_by('-fecha', '-id')
    for pe in perdidas:
        historial.append({
            'tipo': 'egreso',
            'fecha': pe.fecha,
            'insumo': pe.insumo.nombre,
            'unidad_medida': pe.insumo.unidad_medida,
            'cantidad': pe.cantidad,
            'proveedor_obs': pe.observacion or 'Merma / Pérdida',
            'precio_unidad': None,
            'total_pagado': None,
            'timestamp': pe.fecha_registro.timestamp() if pe.fecha_registro else 0,
        })

    historial.sort(key=lambda x: (x['fecha'], x['timestamp']), reverse=True)

    context = {
        'insumos': insumos,
        'proveedores': proveedores,
        'historial': historial,
        'fecha_hoy': timezone.localdate(),
    }
    return render(request, 'inventario/ingreso_inventario.html', context)


@require_POST
@roles_requeridos(['administrador', 'empleado'])
def procesar_ingreso(request):
    nombre_insumo = request.POST.get('nombre_insumo', '').strip()
    unidad_medida = request.POST.get('unidadmedida', '').strip()
    proveedor_id = request.POST.get('id_proveedor')
    fecha_ingreso = request.POST.get('fecha_ingreso') or timezone.localdate()
    observaciones = request.POST.get('observaciones', '').strip()

    try:
        cantidad = Decimal(request.POST.get('cantidad', '0'))
        precio_total = Decimal(request.POST.get('precio_compra_total', '0'))
        precio_unidad_raw = request.POST.get('precio_unidad')
        precio_unidad = Decimal(precio_unidad_raw) if precio_unidad_raw else (precio_total / cantidad)

        if not proveedor_id:
            raise ValueError("Debes seleccionar un proveedor.")

        registrar_ingreso_compra(
            nombre_insumo=nombre_insumo,
            unidad_medida=unidad_medida,
            cantidad=cantidad,
            proveedor_id=int(proveedor_id),
            fecha_ingreso=fecha_ingreso,
            precio_compra_total=precio_total,
            precio_unidad=precio_unidad,
            observaciones=observaciones,
            usuario=request.user
        )
        messages.success(request, f"Ingreso de '{nombre_insumo}' registrado correctamente. Stock actualizado.")
    except Exception as e:
        messages.error(request, f"Error al registrar ingreso: {str(e)}")

    return redirect('inventario:lista')


@require_POST
@roles_requeridos(['administrador', 'empleado'])
def procesar_perdida(request):
    insumo_id = request.POST.get('id_insumo')
    fecha = request.POST.get('fecha') or timezone.localdate()
    observacion = request.POST.get('observacion', '').strip()

    try:
        cantidad = Decimal(request.POST.get('cantidad', '0'))
        if not insumo_id:
            raise ValueError("Debes seleccionar un insumo.")

        perdida = registrar_perdida_merma(
            insumo_id=int(insumo_id),
            cantidad=cantidad,
            fecha=fecha,
            observacion=observacion,
            usuario=request.user
        )
        messages.success(request, f"Pérdida registrada: -{cantidad} {perdida.insumo.unidad_medida} de {perdida.insumo.nombre}.")
    except Exception as e:
        messages.error(request, f"Error al registrar merma: {str(e)}")

    return redirect('inventario:lista')


@roles_requeridos(['administrador', 'empleado'])
def alertas_stock(request):
    """
    Vista dedicada de alertas tempranas y widgets de inventario.
    """
    insumos = Insumo.objects.all().order_by('nombre')
    criticos = sum(1 for i in insumos if i.estado == 'critico')
    bajos = sum(1 for i in insumos if i.estado == 'bajo')
    buenos = sum(1 for i in insumos if i.estado == 'bueno')

    context = {
        'insumos': insumos,
        'criticos': criticos,
        'bajos': bajos,
        'buenos': buenos,
        'total_alertas': criticos + bajos,
    }
    return render(request, 'inventario/alertas_stock.html', context)


@roles_requeridos(['administrador', 'empleado'])
def lista_compras(request):
    """
    Vista de compras sugeridas calculadas a partir del nivel objetivo (meta de stock).
    """
    insumos_alerta = [i for i in Insumo.objects.all().order_by('stock_actual', 'nombre') if i.estado in ('critico', 'bajo')]

    context = {
        'insumos_sugeridos': insumos_alerta,
        'total_alertas': len(insumos_alerta),
    }
    return render(request, 'inventario/lista_compras.html', context)
