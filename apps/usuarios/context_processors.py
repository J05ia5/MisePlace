def usuario_contexto(request):
    if not request.user.is_authenticated:
        return {'total_alertas_stock': 0}

    # Low stock count for alert badge
    try:
        from inventario.models import Insumo
        from django.db.models import F
        total_alertas = Insumo.objects.filter(stock_actual__lte=F('stock_minimo')).count()
    except Exception:
        total_alertas = 0

    return {
        'total_alertas_stock': total_alertas,
        'usuario_actual': request.user,
    }
