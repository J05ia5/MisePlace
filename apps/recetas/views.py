from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.utils import timezone
from usuarios.decorators import roles_requeridos
from inventario.models import Insumo
from .models import Plato, RecetaIngrediente


@roles_requeridos(['administrador'])
def gestion_recetas(request):
    """
    Vista de gestión completa de recetas (creación, edición, listado de ingredientes).
    """
    platos = Plato.objects.prefetch_related('ingredientes__insumo').all().order_by('nombre')
    insumos = Insumo.objects.all().order_by('nombre')
    context = {
        'platos': platos,
        'insumos': insumos,
        'fecha_hoy': timezone.localdate(),
    }
    return render(request, 'recetas/gestion_recetas.html', context)


@require_GET
@roles_requeridos(['administrador'], formato='json')
def api_insumos_list(request):
    """Retorna la lista de insumos disponibles en formato JSON."""
    insumos = Insumo.objects.all().order_by('nombre').values('id', 'nombre', 'unidad_medida')
    return JsonResponse(list(insumos), safe=False)


@require_GET
@roles_requeridos(['administrador', 'cajero'], formato='json')
def api_obtener_receta(request, plato_id):
    """Obtiene los detalles e ingredientes de un plato en JSON."""
    try:
        plato = Plato.objects.prefetch_related('ingredientes__insumo').get(id=plato_id)
    except Plato.DoesNotExist:
        return JsonResponse({'error': 'Receta no encontrada'}, status=404)

    ingredientes = []
    for ing in plato.ingredientes.all():
        ingredientes.append({
            'id_insumo': ing.insumo.id,
            'nombre': ing.insumo.nombre,
            'cantidad_necesaria': str(ing.cantidad_necesaria),
            'unidad_medida': ing.insumo.unidad_medida,
        })

    return JsonResponse({
        'id': plato.id,
        'nombre': plato.nombre,
        'precio_venta': str(plato.precio_venta),
        'imagen_url': plato.imagen.url if plato.imagen else '',
        'ingredientes': ingredientes,
    })


@require_POST
@roles_requeridos(['administrador'], formato='json')
def api_guardar_receta(request):
    """Crea o actualiza una receta de forma atómica."""
    nombre = request.POST.get('nombreplato', '').strip()
    precio_str = request.POST.get('precioventa', '').strip()
    id_plato = request.POST.get('id_plato')
    imagen = request.FILES.get('imagen')

    insumos_ids = request.POST.getlist('insumo[]')
    cantidades = request.POST.getlist('cantidad[]')

    if not nombre:
        return JsonResponse({'ok': False, 'mensaje': 'El nombre del plato es obligatorio.'}, status=400)

    try:
        precio = Decimal(precio_str)
        if precio <= Decimal('0'):
            return JsonResponse({'ok': False, 'mensaje': 'El precio de venta debe ser mayor a cero.'}, status=400)
    except Exception:
        return JsonResponse({'ok': False, 'mensaje': 'Precio de venta inválido.'}, status=400)

    # Validar ingredientes
    ingredientes_a_guardar = []
    insumos_usados = set()

    for idx, insumo_id in enumerate(insumos_ids):
        if not insumo_id:
            continue
        try:
            cant_str = cantidades[idx] if idx < len(cantidades) else '0'
            cantidad = Decimal(cant_str)
            if cantidad <= Decimal('0'):
                return JsonResponse({'ok': False, 'mensaje': 'Las cantidades de ingredientes deben ser positivas.'}, status=400)
        except Exception:
            return JsonResponse({'ok': False, 'mensaje': 'Cantidad de insumo inválida.'}, status=400)

        insumo_id = int(insumo_id)
        if insumo_id in insumos_usados:
            return JsonResponse({'ok': False, 'mensaje': 'No puedes repetir el mismo insumo en una receta.'}, status=400)
        insumos_usados.add(insumo_id)
        ingredientes_a_guardar.append((insumo_id, cantidad))

    if not ingredientes_a_guardar:
        return JsonResponse({'ok': False, 'mensaje': 'Debes agregar al menos un insumo a la receta.'}, status=400)

    try:
        with transaction.atomic():
            es_edicion = bool(id_plato)
            if es_edicion:
                plato = Plato.objects.get(id=int(id_plato))
                plato.nombre = nombre
                plato.precio_venta = precio
                if imagen:
                    plato.imagen = imagen
                plato.save()
                # Borrar ingredientes anteriores
                plato.ingredientes.all().delete()
            else:
                plato = Plato.objects.create(
                    nombre=nombre,
                    precio_venta=precio,
                    imagen=imagen
                )

            # Insertar nuevos ingredientes
            for insumo_id, cantidad in ingredientes_a_guardar:
                insumo = Insumo.objects.get(id=insumo_id)
                RecetaIngrediente.objects.create(
                    plato=plato,
                    insumo=insumo,
                    cantidad_necesaria=cantidad
                )

        mensaje = f"Receta '{plato.nombre}' {'actualizada' if es_edicion else 'registrada'} con éxito."
        return JsonResponse({'ok': True, 'mensaje': mensaje, 'id_plato': plato.id})

    except Exception as e:
        return JsonResponse({'ok': False, 'mensaje': f"Error al guardar la receta: {str(e)}"}, status=500)


@require_POST
@roles_requeridos(['administrador'], formato='json')
def api_eliminar_receta(request, plato_id):
    """Elimina una receta si no tiene ventas registradas."""
    try:
        plato = Plato.objects.get(id=plato_id)
    except Plato.DoesNotExist:
        return JsonResponse({'ok': False, 'mensaje': 'El plato a eliminar no existe.'}, status=404)

    # Verificar si tiene ventas registradas
    if plato.ventas_detalle.exists():
        return JsonResponse({
            'ok': False,
            'mensaje': 'No se puede eliminar esta receta porque ya tiene ventas registradas en el historial.'
        }, status=400)

    try:
        nombre = plato.nombre
        if plato.imagen:
            plato.imagen.delete(save=False)
        plato.delete()
        return JsonResponse({'ok': True, 'mensaje': f"Receta '{nombre}' eliminada con éxito."})
    except Exception as e:
        return JsonResponse({'ok': False, 'mensaje': f"Error al eliminar la receta: {str(e)}"}, status=500)
