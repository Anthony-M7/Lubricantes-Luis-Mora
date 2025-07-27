from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from ..models import Venta, DetalleVenta, Cliente, Articulo, MovimientoInventario, HistorialStock
from ..forms import VentaForm, DetalleVentaForm, ClienteForm

from django.db import models
from django.forms import forms
from decimal import Decimal, InvalidOperation
import json

from django.db.models import Sum, F, Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST


from django.shortcuts import get_object_or_404
from django.utils import timezone

from django.forms.models import model_to_dict

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
from reportlab.lib.utils import ImageReader
from django.conf import settings



def lista_ventas(request):
    estado = request.GET.get('estado')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Cargar las ventas con detalles y artículos
    ventas = Venta.objects.select_related('cliente', 'creado_por')\
                          .prefetch_related('detalles__articulo')\
                          .annotate(num_articulos=Sum('detalles__cantidad'))\
                          .order_by('-fecha')
    
    if estado:
        ventas = ventas.filter(estado=estado)
    if fecha_inicio:
        ventas = ventas.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(fecha__lte=fecha_fin)
    
    total_ventas = ventas.count()
    
    ventas_completadas = ventas.filter(estado='COMPLETADA').aggregate(
        total=Sum('total'),
        count=Count('id')
    )
    ventas_pendientes = ventas.filter(estado='PENDIENTE').aggregate(
        total=Sum('total'),
        count=Count('id')
    )
    ventas_canceladas = ventas.filter(estado='CANCELADA').aggregate(
        total=Sum('total'),
        count=Count('id')
    )
    
    # Obtener los artículos vendidos para cada venta
    ventas_con_articulos = []
    for venta in ventas:
        articulos = [detalle.articulo.nombre for detalle in venta.detalles.all() if detalle.articulo]
        ventas_con_articulos.append({
            'venta': venta,
            'articulos': articulos
        })
    
    paginator = Paginator(ventas_con_articulos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estados': dict(Venta.ESTADO_CHOICES),
        'filtros': {
            'estado': estado,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        },
        'total_ventas': total_ventas,
        'ventas_completadas': {
            'total': ventas_completadas['total'] or 0,
            'count': ventas_completadas['count'] or 0
        },
        'ventas_pendientes': {
            'total': ventas_pendientes['total'] or 0,
            'count': ventas_pendientes['count'] or 0
        },
        'ventas_canceladas': {
            'total': ventas_canceladas['total'] or 0,
            'count': ventas_canceladas['count'] or 0
        },
        'ventas_con_articulos': ventas_con_articulos,
    }
    return render(request, 'vistas/lista_ventas.html', context)


# Funcion Para Obtener Los Detalles de La venta
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'creado_por'), 
                             id=venta_id)
    detalles = venta.detalles.select_related('articulo')
    
    # Obtener movimientos de inventario relacionados
    movimientos = MovimientoInventario.objects.filter(
        referencia=f"Venta {venta.codigo}"
    ).select_related('articulo', 'usuario')
    
    context = {
        'venta': venta,
        'detalles': detalles,
        'movimientos': movimientos
    }
    return render(request, 'detalles/detalles_ventas.html', context)


def descargar_recibo(request, venta_id):
    # Obtener la venta
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.select_related('articulo')
    
    # Crear un buffer para el PDF
    buffer = BytesIO()
    
    # Crear el PDF usando ReportLab
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Configuración de márgenes y área útil
    margin = 0.5 * inch
    usable_width = width - 2 * margin
    current_y = height - margin
    
    # Encabezado del recibo (centrado)
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, current_y, "RECIBO")
    current_y -= 30
    
    # Información de la empresa
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margin, current_y, "LUBRICANTES LUIS MORA")
    current_y -= 15
    p.setFont("Helvetica", 9)
    p.drawString(margin, current_y, "Calle Principal El Milagro")
    current_y -= 12
    p.drawString(margin, current_y, "Troncal 5 - Via El Llano")
    current_y -= 20
    
    # Línea divisoria
    p.line(margin, current_y, width - margin, current_y)
    current_y -= 20
    
    # Información del cliente
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margin, current_y, "A:")
    current_y -= 15
    p.setFont("Helvetica", 9)
    p.drawString(margin, current_y, venta.cliente.nombre)
    current_y -= 12
    p.drawString(margin, current_y, venta.cliente.direccion if hasattr(venta.cliente, 'direccion') else "Dirección no especificada")
    current_y -= 12
    
    # Línea divisoria
    p.line(margin, current_y, width - margin, current_y)
    current_y -= 20
    
    # Detalles del recibo
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margin, current_y, f"N° DE RECIBO: {venta.codigo}")
    p.drawString(width/2, current_y, f"FECHA: {venta.fecha_creacion.strftime('%d/%m/%Y')}")
    current_y -= 15
    current_y -= 15
    
    # Tabla de artículos
    data = [['CANT.', 'DESCRIPCIÓN', 'PRECIO UNITARIO', 'TASA DE IMPUESTOS', 'IMPORTE']]
    
    for detalle in detalles:
        data.append([
            str(int(detalle.cantidad)),
            detalle.articulo.nombre,
            f"{detalle.precio_unitario:,.2f} COP",
            f"{detalle.articulo.tasa_impuesto*100}%",
            f"{detalle.subtotal:,.2f} COP"
        ])
    
    table = Table(data, colWidths=[0.5*inch, 3.0*inch, 1.3*inch, 1.7*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    
    table.wrapOn(p, usable_width, height)
    table.drawOn(p, margin, current_y - (len(data) * 15))
    current_y -= (len(data) * 15) + 20
    
    # Totales
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(width - margin - 100, current_y, f"Subtotal:")
    p.drawRightString(width - margin, current_y, f"{venta.subtotal:,.2f} COP")
    current_y -= 15
    
    p.drawRightString(width - margin, current_y, f"{venta.impuesto:,.2f} COP")
    current_y -= 20
    
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - margin - 100, current_y, "TOTAL:")
    p.drawRightString(width - margin, current_y, f"{venta.total:,.2f} COP")
    current_y -= 30
    
    # Línea divisoria
    p.line(margin, current_y, width - margin, current_y)
    current_y -= 20
    
    # Información de pago
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margin, current_y, "CONDICIONES Y FORMA DE PAGO")
    current_y -= 15
    p.setFont("Helvetica", 9)
    p.drawString(margin, current_y, venta.estado or "El pago se realizará en un plazo de 15 días")
    current_y -= 15
    
    # Pie de página simple
    current_y -= 20
    p.setFont("Helvetica", 7)
    p.drawCentredString(width/2, current_y, "Documento generado automáticamente - No válido como factura")
    
    # Finalizar el PDF
    p.showPage()
    p.save()
    
    # Obtener el valor del buffer y crear la respuesta
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=recibo_venta_{venta.codigo}.pdf'
    response.write(pdf)
    
    return response


# Funcion Para Crear Nueva Venta
@transaction.atomic
def crear_venta(request):
    if request.method == 'POST':
        venta_form = VentaForm(request.POST, user=request.user)

        if venta_form.is_valid():
            venta = venta_form.save(commit=False)
            venta.creado_por = request.user
            
            # DEBUG: Imprimir el contenido de request.POST
            print("Datos POST recibidos:", request.POST)
            
            # Mejorar la detección del botón de finalizar
            finalizar = request.POST.get('finalizar_venta') == '1' or 'finalizar_venta' in request.POST
            venta.estado = 'COMPLETADA' if finalizar else 'BORRADOR'
            
            print(f"Estado de venta a guardar: {venta.estado}")  # Debug
            
            venta.save()
            
            # Procesar detalles de venta
            detalles_data = json.loads(request.POST.get('detalles', '[]'))
            for detalle_data in detalles_data:
                try:
                    # Aceptar tanto 'id' como 'articulo_id'
                    articulo_id = detalle_data.get('articulo_id', detalle_data.get('id'))
                    if not articulo_id:
                        continue
                        
                    articulo = Articulo.objects.get(id=articulo_id)
                    cantidad = Decimal(str(detalle_data.get('cantidad', 0)))
                    
                    if articulo.stock_actual < cantidad:
                        raise forms.ValidationError(
                            f'Stock insuficiente para {articulo.nombre}. Disponible: {articulo.stock_actual}'
                        )
                    
                    DetalleVenta.objects.create(
                        venta=venta,
                        articulo=articulo,
                        cantidad=cantidad,
                        precio_unitario=Decimal(str(detalle_data.get('precio', detalle_data.get('precio_unitario', 0)))),
                        descuento=Decimal(str(detalle_data.get('descuento', 0)))
                    )
                except Articulo.DoesNotExist:
                    continue
            
            if venta.estado == 'COMPLETADA':
                venta.registrar_movimientos_inventario()
                messages.success(request, 'Venta completada y stock actualizado')
            else:
                messages.success(request, 'Venta guardada como borrador')
            
            return redirect('lista_ventas')
    else:
        venta_form = VentaForm(user=request.user)
    
    return render(request, 'Forms/crear_venta.html', {
        'venta_form': venta_form,
        'modo_creacion': True
    })


# Funciona (Solo con uno)
@require_http_methods(["DELETE"])
@transaction.atomic
def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    
    if venta.estado != 'BORRADOR':
        return JsonResponse({
            'success': False,
            'error': 'Solo se pueden eliminar ventas en estado Borrador'
        }, status=400)
    
    try:
        if venta.estado == 'COMPLETADA':
            venta.revertir_movimientos_inventario()
        
        venta.delete()
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

# Funciona Buscar Articulo Para Agregarlo a la Venta
def buscar_articulos(request):
    term = request.GET.get('term', '')
    articulos = Articulo.objects.filter(
        models.Q(nombre__icontains=term) |
        models.Q(codigo__icontains=term) |
        models.Q(codigo_barras__icontains=term),
        activo=True,
        stock_actual__gt=0  # Solo artículos con stock disponible
    ).values(
        'id', 'codigo', 'nombre', 'precio_venta', 
        'stock_actual', 'tasa_impuesto'
    )[:10]
    
    # Agregamos el campo disponible igual al stock_actual
    articulos_list = list(articulos)
    for articulo in articulos_list:
        articulo['disponible'] = articulo['stock_actual']
    
    return JsonResponse(articulos_list, safe=False)


# Funciona (Solo con uno)
@require_http_methods(["POST"])
def agregar_detalle(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    form = DetalleVentaForm(request.POST, venta=venta)
    
    if form.is_valid():
        detalle = form.save()
        return JsonResponse({
            'success': True,
            'detalle': {
                'id': detalle.id,
                'articulo': detalle.articulo.nombre,
                'cantidad': str(detalle.cantidad),
                'precio_unitario': str(detalle.precio_unitario),
                'subtotal': str(detalle.subtotal),
                'impuesto': str(detalle.impuesto)
            }
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors.as_json()
    }, status=400)


# Eliminar Detalles de Venta
@require_http_methods(["DELETE"])
@transaction.atomic
def eliminar_detalle(request, detalle_id):
    detalle = get_object_or_404(DetalleVenta, id=detalle_id)
    
    if detalle.venta.estado != 'BORRADOR':
        return JsonResponse({
            'success': False,
            'error': 'Solo se pueden eliminar detalles de ventas en estado Borrador'
        }, status=400)
    
    try:
        articulo = detalle.articulo
        cantidad = detalle.cantidad
        
        # Si la venta estaba completada, revertir el movimiento
        if detalle.venta.estado == 'COMPLETADA':
            try:
                movimiento = MovimientoInventario.objects.get(
                    referencia=f"Venta {detalle.venta.codigo}",
                    articulo=articulo
                )
                
                # Revertir el stock
                articulo.stock_actual += cantidad
                articulo.save()
                
                # Eliminar el historial asociado
                HistorialStock.objects.filter(movimiento=movimiento).delete()
                movimiento.delete()
                
            except MovimientoInventario.DoesNotExist:
                pass
        
        detalle.delete()
        detalle.venta.calcular_totales()  # Recalcular totales
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

# Funcion Crear Cliente Rapido
def crear_cliente_rapido(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            return JsonResponse(model_to_dict(cliente))  # 👈 Solucionado

        return JsonResponse({
            'success': False,
            'errors': form.errors.as_json()
        }, status=400)

    return JsonResponse({'success': False}, status=405)


## FUNCIONES PARA EDITAR VENTA ##
def editar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    if request.method == 'POST':
        venta_form = VentaForm(request.POST, instance=venta, user=request.user)
        
        if venta_form.is_valid():
            venta = venta_form.save(commit=False)
            venta.creado_por = request.user
            venta.save()
            
            # Procesar detalles de venta
            detalles_data = json.loads(request.POST.get('detalles', '[]'))
            
            # IDs de detalles existentes para identificar qué eliminar
            detalles_existentes_ids = set(venta.detalles.values_list('id', flat=True))
            detalles_actualizados_ids = set()
            
            for detalle_data in detalles_data:
                detalle_form = DetalleVentaForm(detalle_data, venta=venta)
                
                if detalle_form.is_valid():
                    detalle = detalle_form.save()
                    detalles_actualizados_ids.add(detalle.id)
            
            # Eliminar detalles que ya no están en la venta
            detalles_a_eliminar = detalles_existentes_ids - detalles_actualizados_ids
            venta.detalles.filter(id__in=detalles_a_eliminar).delete()
            
            # Recalcular totales
            venta.calcular_totales()
            
            if 'finalizar_venta' in request.POST or request.POST.get('finalizar_venta_hidden') == '1':
                if venta.estado == 'BORRADOR':
                    venta.estado = 'COMPLETADA'
                    venta.fecha = timezone.now()
                    venta.save()
                    venta.registrar_movimientos_inventario()
                return redirect('detalle_venta', venta_id=venta.id)
            
            return redirect('lista_ventas')
    else:
        venta_form = VentaForm(instance=venta, user=request.user)
    
    detalles = venta.detalles.all().select_related('articulo')
    detalles_data = []
    
    for detalle in detalles:
        detalles_data.append({
            'articulo_id': detalle.articulo.id,
            'codigo': detalle.articulo.codigo,
            'descripcion': detalle.articulo.nombre,
            'cantidad': float(detalle.cantidad),
            'precio_unitario': float(detalle.precio_unitario),
            'descuento': float(detalle.descuento),
            'subtotal': float(detalle.subtotal),
            'impuesto': float(detalle.impuesto)
        })
    
    context = {
        'venta_form': venta_form,
        'venta': venta,
        'detalles_data': json.dumps(detalles_data),
        'subtotal': float(venta.subtotal),
        'impuesto': float(venta.impuesto),
        'total': float(venta.total),
    }
    
    return render(request, 'ventas/editar_venta.html', context)


@require_GET
def obtener_articulo_api(request, pk):
    try:
        articulo = Articulo.objects.get(pk=pk, activo=True)
        
        # Obtener parámetros adicionales si existen
        cantidad_solicitada = request.GET.get('cantidad', None)
        validar_stock = request.GET.get('validar_stock', 'false').lower() == 'true'
        
        response_data = {
            'id': articulo.id,
            'codigo': articulo.codigo,
            'nombre': articulo.nombre,
            'precio_venta': str(articulo.precio_venta),
            'stock_actual': str(articulo.stock_actual),
            'tasa_impuesto': str(articulo.tasa_impuesto),
            'unidad_medida': articulo.unidad_medida if articulo.unidad_medida else '',
        }
        
        # Validar stock si se solicita
        if validar_stock and cantidad_solicitada:
            try:
                cantidad = Decimal(cantidad_solicitada)
                if articulo.stock_actual < cantidad:
                    response_data['error_stock'] = f'Stock insuficiente. Disponible: {articulo.stock_actual}'
            except (ValueError, InvalidOperation):
                response_data['error_stock'] = 'Cantidad inválida'
        
        return JsonResponse(response_data)
        
    except Articulo.DoesNotExist:
        return JsonResponse(
            {'error': 'Artículo no encontrado o inactivo'},
            status=404
        )
    

def buscar_clientes_api(request):
    # Obtener término de búsqueda del parámetro GET 'q' o 'term'
    term = request.GET.get('term', '') or request.GET.get('q', '')
    term = term.strip()
    
    if not term:
        return JsonResponse([], safe=False)
    
    # Buscar clientes activos que coincidan con el término
    clientes = Cliente.objects.filter(
        Q(nombre__icontains=term) |
        Q(identificacion__icontains=term) |
        Q(telefono__icontains=term),
        activo=True
    ).order_by('nombre')[:10]  # Limitar a 10 resultados
    
    # Formatear resultados para Select2 (si lo usas)
    resultados = [
        {
            'id': cliente.id,
            'text': f"{cliente.nombre} - {cliente.identificacion}",
            'nombre': cliente.nombre,
            'identificacion': cliente.identificacion,
            'telefono': cliente.telefono or ''
        }
        for cliente in clientes
    ]
    
    return JsonResponse({'results': resultados})  # Formato compatible con Select2


@require_POST
def cambiar_estado_venta(request):
    venta_id = request.POST.get('venta_id')
    nuevo_estado = request.POST.get('nuevo_estado')
    observaciones = request.POST.get('observaciones', '')
    
    try:
        venta = Venta.objects.get(id=venta_id)
        
        # Validar que no esté completada
        if venta.estado == 'COMPLETADA':
            messages.error(request, 'No se puede modificar una venta completada')
            return redirect('lista_ventas')
            
        # Validar nuevo estado
        if nuevo_estado not in ['BORRADOR', 'PENDIENTE', 'CANCELADA']:
            messages.error(request, 'Estado no válido')
            return redirect('lista_ventas')
        
        # Actualizar venta
        venta.estado = nuevo_estado
        if observaciones:
            venta.observaciones = observaciones
        venta.save()
        
        messages.success(request, f'El estado de la venta {venta.codigo} ha sido actualizado a {venta.get_estado_display()}')
    except Venta.DoesNotExist:
        messages.error(request, 'No se pudo encontrar la venta')
    
    return redirect('lista_ventas')