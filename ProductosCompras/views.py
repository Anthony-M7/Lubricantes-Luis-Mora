from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ProductosCompras.models import *
from django.utils import timezone

from datetime import timedelta
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import *

from django.contrib import messages

# Create your views here.
@login_required
def compras_view(request):
    # Obtener parámetros de la URL
    dias = int(request.GET.get('dias', 30))
    busqueda = request.GET.get('q', '')
    proveedor_id = request.GET.get('proveedor', '')
    page_number = request.GET.get('page', 1)
    
    # Obtener el queryset base
    compras = MovimientoInventario.objects.filter(
        tipo='ENTRADA'
    ).select_related('articulo', 'usuario', 'proveedor').order_by('-fecha')
    
    # Aplicar filtros
    fecha_inicio = timezone.now() - timedelta(days=dias)
    compras = compras.filter(fecha__gte=fecha_inicio)
    
    if busqueda:
        compras = compras.filter(
            Q(articulo__nombre__icontains=busqueda) |
            Q(articulo__codigo__icontains=busqueda) |
            Q(referencia__icontains=busqueda)
        )
    
    if proveedor_id:
        compras = compras.filter(proveedor_id=proveedor_id)
    
    # Paginación
    paginator = Paginator(compras, 20)  # 20 items por página
    page_obj = paginator.get_page(page_number)
    
    # Cálculos para estadísticas
    # Con esto:
    total_compras = sum(compra.cantidad * compra.costo_unitario for compra in page_obj.object_list if compra.costo_unitario)
    articulos_ids = set(c.articulo.id for c in page_obj.object_list)
    total_articulos = len(articulos_ids)
    promedio_compra = total_compras / len(page_obj.object_list) if page_obj else 0
    
    # Generar rango de páginas para la paginación (mostrar 5 páginas alrededor de la actual)
    page_range = []
    if paginator.num_pages <= 5:
        page_range = range(1, paginator.num_pages + 1)
    else:
        if page_obj.number <= 3:
            page_range = range(1, 6)
        elif page_obj.number >= paginator.num_pages - 2:
            page_range = range(paginator.num_pages - 4, paginator.num_pages + 1)
        else:
            page_range = range(page_obj.number - 2, page_obj.number + 3)
    
    # Preparar el contexto completo
    context = {
        'titulo': 'Últimas Compras Registradas',
        'compras': page_obj,
        'dias': dias,
        'q': busqueda,
        'proveedor_id': int(proveedor_id) if proveedor_id else '',
        'proveedores': Proveedor.objects.all(),
        'total_compras': total_compras,
        'total_articulos': total_articulos,
        'promedio_compra': promedio_compra,
        'page_obj': page_obj,
        'page_range': page_range,
    }
    
    return render(request, 'vistas/compras.html', context)

@login_required
def registrar_compras(request):
    if request.method == 'POST':
        form = CompraInventarioForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('compras')
    else:
        form = CompraInventarioForm(user=request.user)
    
    context = {
        'titulo': 'Registrar Nueva Compra',
        'boton_submit': 'Registrar Compra',
        'form': form
    }
    return render(request, 'Forms/crear_compras.html', context)


def eliminar_compra(request, pk):
    # Obtener el movimiento de compra
    movimiento = get_object_or_404(MovimientoInventario, pk=pk, tipo='ENTRADA')
    
    if request.method == 'POST':
        try:
            articulo = movimiento.articulo
            
            # 3. Eliminar el movimiento
            movimiento.delete()
            
            messages.success(request, 'Compra eliminada correctamente y stock revertido')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar la compra: {str(e)}')
            return redirect('compras')
    
    return redirect('compras')


def detalle_compra(request, pk):
    # Obtener datos principales
    compra = get_object_or_404(
        MovimientoInventario.objects.select_related('articulo', 'proveedor', 'usuario'),
        pk=pk,
        tipo='ENTRADA'
    )
    historico = get_object_or_404(HistorialStock, movimiento=compra)
    
    # Calcular valores necesarios
    total = compra.cantidad * compra.costo_unitario
    
    # Variación de cantidad (% aumento stock)
    aumento_stock_pct = (compra.cantidad / historico.stock_antes * 100) if historico.stock_antes > 0 else 0
    aumento_stock_text = f"+{compra.cantidad:.0f} ({aumento_stock_pct:.1f}%)"
    
    # Variación de precio (vs compra anterior)
    if historico.costo_unitario_anterior:
        variacion_precio = (
            (compra.costo_unitario - historico.costo_unitario_anterior) / 
            historico.costo_unitario_anterior * 100
        )
    else:
        variacion_precio = 0
    
    # Variación de costo promedio
    if historico.costo_promedio_antes > 0:
        variacion_promedio = (
            (historico.costo_promedio_despues - historico.costo_promedio_antes) / 
            historico.costo_promedio_antes * 100
        )
        variacion_promedio_text = f"{'↑' if variacion_promedio > 0 else '↓'} {abs(variacion_promedio):.1f}%"
    else:
        variacion_promedio = 0
        variacion_promedio_text = "0.0%"
    
    context = {
        'compra': compra,
        'historico': historico,
        'titulo': f'Detalle de Compra #{compra.id}',
        'total': total,
        'aumento_stock_text': aumento_stock_text,
        'variacion_precio': variacion_precio,
        'variacion_promedio_text': variacion_promedio_text,
    }
    
    return render(request, 'detalles/detalles_compra.html', context)


def editar_compra(request, pk):
    compra = get_object_or_404(MovimientoInventario, pk=pk, tipo='ENTRADA')
    
    if request.method == 'POST':
        form = CompraInventarioForm(request.POST, instance=compra, user=request.user)
        if form.is_valid():
            # El formulario se encarga de toda la lógica de actualización
            form.save()
            messages.success(request, 'Compra actualizada correctamente')
            return redirect('detalle_compra', pk=compra.pk)
    else:
        form = CompraInventarioForm(instance=compra, user=request.user)
    
    return render(request, 'Forms/editar_compra.html', {
        'form': form,
        'compra': compra,
        "titulo": f"Editar Compra #{compra.id}",
        "codigo": compra.articulo.codigo,
        "articulo": compra.articulo.nombre,
        "stock_actual": int(compra.articulo.stock_actual),
        "costo_promedio": compra.articulo.costo_promedio,
    })

