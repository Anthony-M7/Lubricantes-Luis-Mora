import io
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .decorators import nivel_requerido
from django.contrib.auth import logout
from django.db.models import Q, Sum, Count, F, CharField, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncDay
from django.views.generic import TemplateView
from django.db.models.functions import Length
from django.utils import timezone
from datetime import timedelta, datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from openpyxl import Workbook

from django.core.paginator import Paginator
from django.core import serializers

from django.http import JsonResponse
import json

from .models import *
from .forms import ArticuloForm, CompraInventarioForm, PersonalForm, UserUpdateForm, ClienteForm, ClienteSearchForm
import os

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import lubricantesLuisMora.settings as settings


def inicio(request):
    """Vista para la página principal"""
    context = {
        'titulo': 'Bienvenido a Lubricantes Luis Mora'
    }
    return render(request, 'base.html', context)

def login_view(request):

    if request.user.is_authenticated:
        return redirect(get_redirect_url(request.user))
    
    if request.method == 'POST':
        username = request.POST.get('usuario')
        password = request.POST.get('password')
        
        # Validar que se ingresaron ambos campos
        if not username or not password:
            messages.error(request, "Debe ingresar usuario y contraseña")
            return render(request, 'login.html')
        
        # Autenticar al usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect(get_redirect_url(user))
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return render(request, 'login.html')
    
    return render(request, 'login.html')

def get_redirect_url(user):
    """Determina la URL de redirección según el rol del usuario"""
    if user.admin or user.rol == 'admin':
        return reverse('dashboard')  # Panel de administración
    elif user.rol == 'personal':
        return reverse('panel_personal')  # Panel de personal
    elif user.rol == 'usuario_regular':
        return reverse('panel_usuario')  # Panel de usuario regular
    else:
        return reverse('inicio')  # Página principal para clientes

@login_required
def panel_admin(request):
    if not request.user.admin and not request.user.rol == 'admin':
        messages.error(request, "No tienes permiso para acceder a esta área")
        return redirect('inicio')
    return render(request, 'paneles/admin.html')

@login_required
def panel_personal(request):
    if not request.user.rol == 'personal' and not request.user.admin:
        messages.error(request, "No tienes permiso para acceder a esta área")
        return redirect('inicio')
    return render(request, 'paneles/personal.html')

@login_required
def panel_usuario(request):
    if not request.user.rol == 'usuario_regular' and not request.user.admin:
        messages.error(request, "No tienes permiso para acceder a esta área")
        return redirect('inicio')
    return render(request, 'paneles/usuario.html')

def custom_logout(request):
    logout(request)
    return redirect('inicio')  # Redirige a la página principal

def dashboard(request):
    """
    Vista principal del dashboard administrativo que muestra métricas clave del negocio.
    Incluye estadísticas diarias, análisis de inventario, ventas y notificaciones.
    """
    
    # 1. OBTENER FECHAS DE REFERENCIA
    # -------------------------------
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    mes_pasado = inicio_mes - timedelta(days=1)
    inicio_mes_pasado = mes_pasado.replace(day=1)
    fecha_limite_inactivos = hoy - timedelta(days=90)
    inicio_trimestre = hoy - timedelta(days=90)
    inicio_semestre = hoy - timedelta(days=180)
    
    # 2. ESTADÍSTICAS DIARIAS
    # -----------------------
    # Clientes registrados hoy
    Usuarios_Hoy = CustomUser.objects.filter(date_joined__date=hoy).count()
    clientes_hoy = Cliente.objects.filter(fecha_creacion__date=hoy).count()
    
    # Ventas del día actual
    ventas_hoy = Venta.objects.filter(
        fecha__date=hoy,
        estado='COMPLETADA'
    ).aggregate(
        total=Sum('total'),
        count=Count('id'),
        articulos_vendidos=Sum('detalles__cantidad')
    )
    
    # 3. ESTADÍSTICAS GENERALES
    # -------------------------
    total_clientes = Cliente.objects.count()
    total_usuarios = CustomUser.objects.count()
    total_productos = Articulo.objects.filter(activo=True).count()
    total_articulos = Articulo.objects.filter(activo=True).count()
    
    # 4. INVENTARIO Y VALORACIÓN
    # --------------------------
    # Valor total del inventario
    valor_inventario = Articulo.objects.filter(activo=True).aggregate(
        total=Sum(F('stock_actual') * F('costo_promedio'))
    )['total'] or 0
    
    # Variación de artículos (mes actual vs mes anterior)
    articulos_mes_actual = Articulo.objects.filter(
        activo=True,
        fecha_creacion__gte=inicio_mes
    ).count()
    
    articulos_mes_pasado = Articulo.objects.filter(
        activo=True,
        fecha_creacion__gte=inicio_mes_pasado,
        fecha_creacion__lt=inicio_mes
    ).count()
    
    variacion_articulos = calcular_variacion(articulos_mes_actual, articulos_mes_pasado)
    
    # Variación de valor de inventario
    valor_mes_actual = valor_inventario
    valor_mes_pasado = Articulo.objects.filter(
        activo=True,
        fecha_actualizacion__gte=inicio_mes_pasado,
        fecha_actualizacion__lt=inicio_mes
    ).aggregate(
        total=Sum(F('stock_actual') * F('costo_promedio'))
    )['total'] or 0
    
    variacion_valor = calcular_variacion(valor_mes_actual, valor_mes_pasado)
    
    # 5. ANÁLISIS DE INVENTARIO
    # -------------------------
    # Artículos con stock bajo
    stock_bajo = Articulo.objects.filter(
        activo=True,
        stock_actual__lt=F('stock_minimo')
    ).order_by('stock_actual')[:5]
    
    # Artículos inactivos (sin movimiento en 90 días)
    articulos_inactivos = MovimientoInventario.objects.filter(
        fecha__lt=fecha_limite_inactivos
    ).values('articulo').distinct().count()
    
    # Articulos por Categoria
    productos_por_categoria = Articulo.objects.filter(activo=True).values(
        'categoria__nombre'
    ).annotate(
        total=Count('id'),
        valor_total=Sum(F('stock_actual') * F('costo_promedio'))
    ).order_by('-total')
    
    # Calcular el total general
    total_general = Articulo.objects.filter(activo=True).aggregate(
        total=Sum(F('stock_actual') * F('costo_promedio'))
    )['total'] or 0


    # 6. MÁRGENES DE GANANCIA
    # -----------------------
    margenes = Articulo.objects.filter(activo=True).annotate(
        margen=F('precio_venta') - F('costo_promedio'),
        margen_porcentaje=(F('precio_venta') - F('costo_promedio')) / F('costo_promedio') * 100
    ).order_by('-margen')
    
    articulo_mejor_margen = margenes.first()
    articulo_peor_margen = margenes.last()
    
    # 7. TOP PERFORMERS
    # -----------------
    # Cliente con más ventas
    cliente_top = Venta.objects.filter(estado='COMPLETADA').values(
        'cliente__nombre'
    ).annotate(
        total_ventas=Count('id'),
        monto_total=Sum('total')
    ).order_by('-monto_total').first()
    
    # Artículo más vendido
    articulo_top = DetalleVenta.objects.values(
        'articulo__nombre'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        total_ventas=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-cantidad_vendida').first()
    
    # Usuario con más ventas
    usuario_top = Venta.objects.filter(estado='COMPLETADA').values(
        'creado_por__first_name'
    ).annotate(
        total_ventas=Count('id')
    ).order_by('-total_ventas').first()
    
    # 8. VENTAS POR PERÍODO
    # ---------------------
    ventas_mes = Venta.objects.filter(
        fecha__date__gte=inicio_mes,
        estado='COMPLETADA'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    ventas_trimestre = Venta.objects.filter(
        fecha__date__gte=inicio_trimestre,
        estado='COMPLETADA'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    ventas_semestre = Venta.objects.filter(
        fecha__date__gte=inicio_semestre,
        estado='COMPLETADA'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # 9. NOTIFICACIONES DEL SISTEMA
    # -----------------------------
    notificaciones = generar_notificaciones(
        hoy, 
        stock_bajo, 
        articulos_inactivos, 
        ventas_hoy, 
        clientes_hoy
    )
    
    # 10. ÚLTIMOS MOVIMIENTOS
    # -----------------------
    ultimos_movimientos = MovimientoInventario.objects.select_related(
        'articulo', 'usuario'
    ).order_by('-fecha')[:10]

    
    # 11. PREPARAR CONTEXTO
    # ---------------------
    context = {
        # Estadísticas diarias
        'clientes_hoy': clientes_hoy,
        'ventas_hoy': ventas_hoy,
        
        # Totales generales
        'total_usuarios': total_usuarios,
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'total_articulos': total_articulos,
        
        # Inventario
        'valor_inventario': valor_inventario,
        'variacion_articulos': variacion_articulos,
        'variacion_valor': variacion_valor,
        'stock_bajo': stock_bajo,
        'articulos_inactivos': articulos_inactivos,

        # Articulos por Categoria
        'productos_por_categoria': productos_por_categoria,
        'total_general': total_general,

        # Margenes
        'articulo_mejor_margen': articulo_mejor_margen,
        'articulo_peor_margen': articulo_peor_margen,
        
        # Top performers
        'cliente_top': cliente_top,
        'articulo_top': articulo_top,
        'usuario_top': usuario_top,
        
        # Ventas por período
        'ventas_mes': ventas_mes,
        'ventas_trimestre': ventas_trimestre,
        'ventas_semestre': ventas_semestre,
        
        # Notificaciones
        'notificaciones': notificaciones,
        
        # Últimos movimientos
        'ultimos_movimientos': ultimos_movimientos,
    }
    
    return render(request, 'vistas/dashboard.html', context)

def calcular_variacion(actual, anterior):
    """Calcula el porcentaje de variación entre dos valores"""
    if anterior > 0:
        return round(((actual - anterior) / anterior) * 100, 2)
    return 0

def generar_notificaciones(hoy, stock_bajo, articulos_inactivos, ventas_hoy, clientes_hoy):
    """Genera las notificaciones del sistema basadas en diferentes condiciones"""
    notificaciones = []
    
    # Notificación de stock bajo
    if stock_bajo.exists():
        notificaciones.append({
            'tipo': 'warning',
            'mensaje': f'Tienes {stock_bajo.count()} artículos con stock bajo'
        })
    
    # Notificación de artículos inactivos
    if articulos_inactivos > 0:
        notificaciones.append({
            'tipo': 'info',
            'mensaje': f'{articulos_inactivos} artículos inactivos (90+ días sin movimiento)'
        })
    
    # Notificación de ventas recientes
    if ventas_hoy.get('count', 0) > 0:
        notificaciones.append({
            'tipo': 'success',
            'mensaje': f"{ventas_hoy['count']} ventas realizadas hoy (COP {ventas_hoy['total']:,.2f})"
        })
    
    # Notificación de nuevos clientes
    if clientes_hoy > 0:
        notificaciones.append({
            'tipo': 'primary',
            'mensaje': f'{clientes_hoy} nuevos clientes añadidos hoy'
        })
    
    # Notificación de compras recientes
    compras_recientes = MovimientoInventario.objects.filter(
        tipo='ENTRADA',
        fecha__date=hoy
    ).count()
    if compras_recientes > 0:
        notificaciones.append({
            'tipo': 'success',
            'mensaje': f'{compras_recientes} compras registradas hoy'
        })
    
    # Notificación de devoluciones
    devoluciones_recientes = Venta.objects.filter(
        estado='CANCELADO',
        fecha__date=hoy
    ).count()
    if devoluciones_recientes > 0:
        notificaciones.append({
            'tipo': 'danger',
            'mensaje': f'{devoluciones_recientes} devoluciones procesadas hoy'
        })
    
    # Notificación de artículos sin precio
    articulos_sin_precio = Articulo.objects.filter(
        precio_venta__isnull=True
    ).count()
    if articulos_sin_precio > 0:
        notificaciones.append({
            'tipo': 'warning',
            'mensaje': f'{articulos_sin_precio} artículos sin precio asignado'
        })
    
    return notificaciones

@login_required
def inventario_view(request):
    categorias = Categoria.objects.all()
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')

    productos = Articulo.objects.filter(activo=True)
    productos_json = serializers.serialize('json', productos)

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(codigo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(palabras_clave__icontains=query)
        )

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    if estado == 'activo':
        productos = productos.filter(activo=True)
    elif estado == 'inactivo':
        productos = productos.filter(activo=False)

    # Estadísticas
    total_productos = productos.count()
    productos_bajo_stock = [p for p in productos if p.necesita_reabastecimiento]
    cantidad_bajo_stock = len(productos_bajo_stock)
    productos_agotados = productos.filter(stock_actual=0).count()
    
    # Paginación
    paginator = Paginator(productos, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)
    
    context = {
        'productos': productos_paginados,
        'categoria_id': categoria_id,
        'total_productos': total_productos,
        'productos_json': productos_json,
        'productos_bajo_stock': productos_bajo_stock,
        'cantidad_bajo_stock': cantidad_bajo_stock,
        'productos_agotados': productos_agotados,
        'query': query,
        'estado': estado,
        "categorias": categorias,
    }
    return render(request, 'vistas/inventario.html', context)

@login_required
def crear_articulo(request):
    if request.method == 'POST':
        form = ArticuloForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            articulo = form.save()
            return redirect('/inventario/')
    else:
        form = ArticuloForm(user=request.user)
    
    return render(request, 'Forms/crear_articulos.html', {'form': form})

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


# ==========================================================================

@login_required
def gestion_personal(request):
    # Obtener parámetros de filtrado
    rol_filter = request.GET.get('rol', '')
    search_query = request.GET.get('search', '')
    
    # Construir el queryset base
    empleados = CustomUser.objects.filter(rol__in=['admin', 'personal']).exclude(username="Admin")
    
    # Aplicar filtros
    if rol_filter:
        empleados = empleados.filter(rol=rol_filter)
    
    if search_query:
        empleados = empleados.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Ordenar
    empleados = empleados.order_by('last_name', 'first_name')
    
    # Paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(empleados, 10)  # 10 items por página
    
    try:
        empleados_paginados = paginator.page(page)
    except PageNotAnInteger:
        empleados_paginados = paginator.page(1)
    except EmptyPage:
        empleados_paginados = paginator.page(paginator.num_pages)
    
    context = {
        'empleados': empleados_paginados,
        'mes_actual': timezone.now().strftime("%B %Y"),
        'roles': dict(CustomUser.ROLES),
        'selected_rol': rol_filter,
        'search_query': search_query,
    }
    return render(request, 'vistas/nomina.html', context)

@login_required
def crear_editar_personal(request):
    try:
        personal_id = request.POST.get('id')
        
        if personal_id:
            personal = get_object_or_404(CustomUser, id=personal_id)
            # Guardar referencia a la foto anterior
            foto_anterior = personal.foto_perfil.path if personal.foto_perfil else None
            form = PersonalForm(request.POST, request.FILES, instance=personal)
        else:
            form = PersonalForm(request.POST, request.FILES)
            foto_anterior = None
        
        if form.is_valid():
            personal = form.save(commit=False)
            
            # Asignar contraseña para nuevos usuarios
            if not personal_id:
                password = request.POST.get('password1', 'defaultpassword123')
                personal.set_password(password)
            
            # Manejo de la foto de perfil (eliminar anterior si existe)
            if 'foto_perfil' in request.FILES and foto_anterior and os.path.exists(foto_anterior):
                try:
                    os.remove(foto_anterior)
                except Exception as e:
                    print(f"Error eliminando foto anterior: {e}")
                    # No es crítico, puede continuar
            
            # Los campos is_staff y admin se manejan automáticamente en el save() del modelo
            personal.save()
            
            # Construir URL de la foto
            foto_url = personal.foto_perfil.url 
            
            return JsonResponse({
                'success': True, 
                'personal': {
                    'id': personal.id,
                    'nombre_completo': personal.get_full_name(),
                    'username': personal.username,
                    'email': personal.email,
                    'rol': personal.get_rol_display(),
                    'telefono': personal.telefono or '-',
                    'foto': foto_url,
                    'is_staff': personal.is_staff,
                    'is_admin': personal.admin
                }
            })
        
        # Manejo de errores del formulario
        errors = {field: [str(error) for error in error_list] for field, error_list in form.errors.items()}
        return JsonResponse({'success': False, 'errors': errors}, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
def eliminar_personal(request, id):
    personal = get_object_or_404(CustomUser, id=id)
    if personal == request.user:
        return JsonResponse({'success': False, 'error': 'No puedes eliminarte a ti mismo'}, status=400)
    personal.delete()
    return JsonResponse({'success': True})

@login_required
def get_personal_data(request, id):
    personal = get_object_or_404(CustomUser, id=id)
    data = {
        "id": personal.id,
        'username': personal.username,
        'first_name': personal.first_name,
        'last_name': personal.last_name,
        'email': personal.email,
        'rol': personal.rol,
        'telefono': personal.telefono,
        'direccion': personal.direccion,
    }
    return JsonResponse(data)

# =========================================================================

@login_required
def gestion_permisos(request, user_id=None, group_id=None):
    # Obtener el usuario o grupo objetivo
    target = None
    if user_id:
        target = get_object_or_404(CustomUser, pk=user_id)
        current_perms = target.user_permissions.all()
    elif group_id:
        target = get_object_or_404(Group, pk=group_id)
        current_perms = target.permissions.all()
    else:
        return redirect('lista_usuarios')
    
    # Organizar permisos por modelo/app
    content_types = ContentType.objects.all().order_by('app_label', 'model')
    permisos_organizados = []
    
    # Descripciones detalladas (ampliadas)
    DESCRIPCIONES = {
        # Descripciones generales por tipo de acción
        'add': 'Permite crear nuevos registros de este tipo (acceso a formularios de creación)',
        'change': 'Permite modificar registros existentes (edición de campos y propiedades)',
        'delete': 'Permite eliminar registros permanentemente (acción irreversible)',
        'view': 'Permite visualizar registros en listados y páginas de detalle',
        
        # Descripciones específicas por modelo
        'customuser': {
            'add': 'Registrar nuevos usuarios en el sistema (incluye configuración inicial de permisos)',
            'change': 'Editar información de usuarios (datos personales, credenciales y permisos)',
            'delete': 'Eliminar cuentas de usuario (se recomienda desactivar en lugar de eliminar)',
            'view': 'Ver listado de usuarios y sus perfiles completos'
        },
        'articulo': {
            'add': 'Agregar nuevos productos al catálogo (definir precios, categorías, existencias)',
            'change': 'Modificar información de productos (actualizar precios, descripciones, imágenes)',
            'delete': 'Eliminar productos del sistema (verificar que no tenga movimientos asociados)',
            'view': 'Consultar el inventario completo de productos'
        },
        'categoria': {
        'add': 'Crear nuevas categorías para clasificación de productos.',
        'change': 'Reorganizar la estructura de categorías y subcategorías.',
        'delete': 'Eliminar categorías (solo si no tienen productos asociados).',
        'view': 'Navegar por la estructura de categorías existente.'
    },
    'cliente': {
        'add': 'Registrar nuevos clientes en el sistema.',
        'change': 'Actualizar información de clientes (datos de contacto, historial).',
        'delete': 'Eliminar registros de clientes (cumplimiento RGPD).',
        'view': 'Consultar la base de datos de clientes.'
    },
    'venta': {
        'add': 'Crear nuevas transacciones de venta/compras.',
        'change': 'Modificar ventas existentes (antes de ser finalizadas).',
        'delete': 'Anular ventas/compras registradas.',
        'view': 'Consultar el historial de transacciones completadas.'
    },
    'movimientoinventario': {
        'add': 'Registrar entradas/salidas de inventario.',
        'change': 'Modificar movimientos de inventario no consolidados.',
        'delete': 'Eliminar registros de movimientos de almacén.',
        'view': 'Consultar el histórico de movimientos de stock.'
        },
    'historialstock': {
        'view': 'Acceder a reportes históricos de inventario.'
        }
    }

    for ct in content_types:
        permisos = Permission.objects.filter(content_type=ct).order_by('codename')
        if permisos.exists():
            permisos_con_desc = []
            for permiso in permisos:
                # Obtener la acción (add, change, delete, view)
                accion = permiso.codename.split('_')[0]
                modelo = ct.model
                
                # Buscar descripción específica o usar la general
                descripcion = DESCRIPCIONES.get(modelo, {}).get(
                    accion, 
                    DESCRIPCIONES.get(accion, "Permiso de sistema")
                )
                
                permisos_con_desc.append({
                    'obj': permiso,
                    'descripcion': descripcion
                })
            
            permisos_organizados.append({
                'app': ct.app_label,
                'model': ct.model,
                'verbose_name': ct.model_class()._meta.verbose_name if ct.model_class() else ct.model,
                'permisos': permisos_con_desc
            })
    
    if request.method == 'POST':
        selected_perms = request.POST.getlist('permisos')
        
        if user_id:
            target.user_permissions.set(selected_perms)
        elif group_id:
            target.permissions.set(selected_perms)
        
        return JsonResponse({'success': True})
    
    return render(request, 'vistas/permisos.html', {
        'target': target,
        'permisos_organizados': permisos_organizados,
        'current_perms': [p.id for p in current_perms],  # Solo pasamos IDs para comparación
        'descripciones': DESCRIPCIONES,
        'is_user': user_id is not None
    })



# =========================================================================


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            # 🔒 Obtenemos la versión guardada en BD (antes de actualizar)
            usuario_original = CustomUser.objects.get(pk=request.user.pk)
            foto_anterior_field = usuario_original.foto_perfil
            foto_anterior = os.path.join(
                settings.MEDIA_ROOT,
                'perfiles',
                os.path.basename(str(foto_anterior_field))
            )

            # 💾 Guardamos los nuevos datos (incluye la nueva foto si viene)
            form.save()

            # 🧹 Si se subió una nueva imagen y había una anterior → la eliminamos
            if 'foto_perfil' in request.FILES and foto_anterior and os.path.isfile(foto_anterior):
                try:
                    os.remove(foto_anterior)
                except Exception as e:
                    pass
            else:
                pass

            messages.success(request, 'Tu perfil ha sido actualizado correctamente!')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserUpdateForm(instance=request.user)

    context = {
        'form': form,
        'user': request.user
    }

    return render(request, 'vistas/perfil.html', context)



# =============================================================================

@login_required
def listar_clientes(request):
    clientes = Cliente.objects.filter(activo=True).order_by('-fecha_creacion')
    
    # Filtros
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    search_query = request.GET.get('search')
    
    if tipo:
        clientes = clientes.filter(tipo=tipo)
    if estado:
        clientes = clientes.filter(activo=estado == 'activo')
    if search_query:
        clientes = clientes.filter(
            models.Q(nombre__icontains=search_query) |
            models.Q(identificacion__icontains=search_query) |
            models.Q(telefono__icontains=search_query)
        )
    
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    search_form = ClienteSearchForm(request.GET or None)
    
    return render(request, 'vistas/clientes.html', {
        'clientes': page_obj,
        'page_obj': page_obj,
        'search_form': search_form
    })

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/cliente_form.html', {
        'form': form,
        'titulo': 'Crear Nuevo Cliente'
    })

@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/cliente_form.html', {
        'form': form,
        'object': cliente,
        'titulo': 'Editar Cliente'
    })

@login_required
def detalle_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/detalles_cliente.html', {
        'cliente': cliente
    })

@login_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        cliente.activo = False
        cliente.save()
        return redirect('clientes')
    
    return render(request, 'clientes/cliente_confirm_delete.html', {
        'object': cliente
    })


# ===============================================================================

def blog_informativo(request):
    # Obtener artículos destacados
    productos_destacados = Articulo.objects.filter(
        activo=True,
        stock_actual__gt=0
    ).order_by('-fecha_creacion')[:4]
    
    # Obtener categorías principales
    categorias_principales = Categoria.objects.filter(padre__isnull=True).prefetch_related('subcategorias')
    
    # Obtener marcas destacadas
    marcas_destacadas = Proveedor.objects.filter(activo=True)[:6]
    
    # Obtener artículos para el blog (versión más flexible)
    posts_blog = Articulo.objects.filter(
        activo=True
    ).exclude(descripcion__isnull=True).exclude(descripcion__exact='').order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(posts_blog, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'productos_destacados': productos_destacados,
        'categorias_principales': categorias_principales,
        'marcas_destacadas': marcas_destacadas,
        'page_obj': page_obj,
    }
    
    return render(request, 'vistas/blog.html', context)


def posts_por_categoria(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    
    # Obtener todos los artículos de esta categoría y subcategorías - solución corregida
    subcategorias = categoria.subcategorias.all()
    posts = Articulo.objects.filter(activo=True).annotate(
        desc_len=Length('descripcion')
    ).filter(
        Q(categoria=categoria) | Q(categoria__in=subcategorias)
    ).order_by('-fecha_creacion')
    
    print(posts)

    # Paginación
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categoria': categoria,
        'page_obj': page_obj,
    }
    
    return render(request, 'vistas/posts_por_categoria.html', context)

# La función detalle_post no necesita cambios
def detalle_post(request, categoria_slug=None, post_id=None):
    post = get_object_or_404(Articulo, id=post_id, activo=True)
    
    # Productos relacionados (misma categoría)
    productos_relacionados = Articulo.objects.filter(
        categoria=post.categoria,
        activo=True
    ).exclude(id=post.id)[:4]
    
    # Obtener especificaciones técnicas si existen
    especificaciones = []
    if post.descripcion:
        # Parsear descripción para extraer especificaciones
        import re
        especificaciones = re.findall(r'•\s*(.*?)\s*\n', post.descripcion)
    
    # Obtener otros productos de la misma marca
    productos_misma_marca = []
    if post.marca:
        productos_misma_marca = Articulo.objects.filter(
            marca=post.marca,
            activo=True
        ).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'productos_relacionados': productos_relacionados,
        'especificaciones': especificaciones,
        'productos_misma_marca': productos_misma_marca,
        'meta_description': f"Información detallada sobre {post.nombre}. {post.descripcion[:160]}" if post.descripcion else "",
    }
    
    return render(request, 'vistas/blog_details.html', context)



# ================================================================================

class ReportesFinancierosView(TemplateView):
    template_name = 'finanzas/finanzas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros del request con manejo robusto
        fecha_inicio_str = self.request.GET.get('fecha_inicio')
        fecha_fin_str = self.request.GET.get('fecha_fin')

        # Valores por defecto (últimos 30 días)
        fecha_actual = timezone.now().date()
        fecha_30_dias_atras = fecha_actual - timedelta(days=30)

        articulo_id = self.request.GET.get('articulo')
        tipo_reporte = self.request.GET.get('tipo_reporte', 'ventas')
        
        # Convertir fechas con manejo de errores mejorado
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else fecha_30_dias_atras
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else fecha_actual
        except (ValueError, TypeError):
            fecha_inicio = fecha_30_dias_atras
            fecha_fin = fecha_actual

         # Validar que fecha_inicio <= fecha_fin
        if fecha_inicio > fecha_fin:
            # Si las fechas están invertidas, las intercambiamos
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
        
         # Base queryset con filtrado mejorado
        ventas = Venta.objects.filter(
            fecha__date__range=(fecha_inicio, fecha_fin),  # Usamos __range para mayor claridad
            estado='COMPLETADA'
        ).order_by('fecha')

        # Resto del código permanece igual...
        articulo_id = self.request.GET.get('articulo')
        tipo_reporte = self.request.GET.get('tipo_reporte', 'ventas')
        
        # Reporte de Ventas
        if tipo_reporte == 'ventas':
            agrupacion = self.request.GET.get('agrupacion', 'mes')
            
            # Por esta versión corregida:
            ventas_report = DetalleVenta.objects.filter(
                venta__in=ventas
            ).annotate(
                periodo=TruncMonth('venta__fecha') if agrupacion == 'mes' else TruncDay('venta__fecha'),
                costo_linea=F('cantidad') * F('articulo__costo_promedio'),
                ganancia_linea=F('cantidad') * (F('precio_unitario') - F('articulo__costo_promedio'))
            ).values('periodo').annotate(
                total_ventas=Count('venta', distinct=True),
                monto_total=Sum('venta__total'),
                costo_total=Sum('costo_linea'),
                ganancia_total=Sum('ganancia_linea')
            ).order_by('periodo')
            
            # Calcular totales generales
            total_general = ventas.aggregate(
                total_monto=Sum('total'),
                total_ventas=Count('id')
            )
            
            # Calcular costos y ganancias si existen detalles
            try:
                detalles_totales = DetalleVenta.objects.filter(venta__in=ventas).aggregate(
                    total_costo=Sum(F('cantidad') * F('articulo__costo_promedio')),
                    total_ganancia=Sum(F('cantidad') * (F('precio_unitario') - F('articulo__costo_promedio'))),
                )
            except:
                detalles_totales = {'total_costo': 0, 'total_ganancia': 0}
            
            # Datos para la gráfica de ventas mensuales
            ventas_mensuales = ventas.annotate(
                mes=TruncMonth('fecha')
            ).values('mes').annotate(
                total_ventas=Count('id')
            ).order_by('mes')
            
            # Preparar datos para Chart.js
            meses = [v['mes'].strftime("%Y-%m") for v in ventas_mensuales]
            cantidades = [v['total_ventas'] for v in ventas_mensuales]

            context.update({
                'ventas_report': ventas_report,
                'monto_total': total_general['total_monto'] or 0,
                'costo_total': detalles_totales['total_costo'] or 0,
                'ganancia_total': detalles_totales['total_ganancia'] or 0,
                'total_ventas': total_general['total_ventas'] or 0,
                
                'grafica_meses': meses,
                'grafica_ventas': cantidades,
            })
        
        # Reporte de Artículos
        elif tipo_reporte == 'articulos':
            articulos_report = DetalleVenta.objects.filter(
                venta__in=ventas
            ).annotate(
                costo_linea=F('cantidad') * F('articulo__costo_promedio'),
                ganancia_linea=F('cantidad') * (F('precio_unitario') - F('articulo__costo_promedio'))
            ).values(
                'articulo__codigo', 
                'articulo__nombre',
                'articulo__categoria__nombre'
            ).annotate(
                cantidad_vendida=Sum('cantidad'),
                monto_total=Sum(F('cantidad') * F('precio_unitario')),
                ganancia_total=Sum('ganancia_linea')
            ).order_by('-monto_total')[:20]
            
            context['articulos_report'] = articulos_report
        
        # Detalle por Artículo
        elif tipo_reporte == 'articulo_detalle' and articulo_id:
            try:
                articulo = Articulo.objects.get(id=articulo_id)
                articulo_detalle = DetalleVenta.objects.filter(
                    venta__in=ventas,
                    articulo=articulo
                ).annotate(
                    dia=TruncDay('venta__fecha'),
                    # Precalculamos los valores por línea primero
                    monto_linea=F('cantidad') * F('precio_unitario'),
                    ganancia_linea=F('cantidad') * (F('precio_unitario') - F('articulo__costo_promedio'))
                ).values(
                    'dia',
                    'venta__codigo'
                ).annotate(
                    cantidad=Sum('cantidad'),
                    # Sumamos los valores precalculados
                    monto=Sum('monto_linea'),
                    ganancia=Sum('ganancia_linea')
                ).order_by('dia')
                
                context.update({
                    'articulo_detalle': articulo_detalle,
                    'articulo': articulo,
                    'total_cantidad': articulo_detalle.aggregate(total=Sum('cantidad'))['total'] or 0,
                    'total_monto': articulo_detalle.aggregate(total=Sum('monto'))['total'] or 0,
                    'total_ganancia': articulo_detalle.aggregate(total=Sum('ganancia'))['total'] or 0,
                })
            except Articulo.DoesNotExist:
                pass
        
        # Contexto común
        context.update({
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            'tipo_reporte': tipo_reporte,
            'articulo_id': articulo_id,
            'articulos': Articulo.objects.filter(activo=True).order_by('nombre'),
        })
        
        return context

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('export')
        
        if export_format in ['pdf', 'excel']:
            context = self.get_context_data(**kwargs)
            
            if export_format == 'pdf':
                return self.generate_pdf(context)
            elif export_format == 'excel':
                return self.generate_excel(context)
        
        return super().get(request, *args, **kwargs)
    
    def generate_pdf(self, context):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_financiero.pdf"'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Título del reporte
        title = f"Reporte Financiero - {context.get('tipo_reporte', 'general').title()}"
        
        # Datos según el tipo de reporte
        if context['tipo_reporte'] == 'ventas':
            data = [['Periodo', 'Ventas', 'Monto', 'Costo', 'Ganancia', 'Margen']]
            for venta in context['ventas_report']:
                margen = (venta['ganancia_total'] / venta['monto_total'] * 100) if venta['monto_total'] else 0
                data.append([
                    venta['periodo'].strftime('%B %Y') if 'month' in str(venta['periodo']) else venta['periodo'].strftime('%d/%m/%Y'),
                    venta['total_ventas'],
                    f"${venta['monto_total']:,.2f}",
                    f"${venta['costo_total']:,.2f}",
                    f"${venta['ganancia_total']:,.2f}",
                    f"{margen:.2f}%"
                ])
        
        elif context['tipo_reporte'] == 'articulos':
            data = [['Código', 'Artículo', 'Categoría', 'Cantidad', 'Monto', 'Ganancia']]
            for art in context['articulos_report']:
                data.append([
                    art['articulo__codigo'],
                    art['articulo__nombre'],
                    art['articulo__categoria__nombre'],
                    art['cantidad_vendida'],
                    f"${art['monto_total']:,.2f}",
                    f"${art['ganancia_total']:,.2f}"
                ])
        
        elif context['tipo_reporte'] == 'articulo_detalle' and 'articulo_detalle' in context:
            data = [['Fecha', 'Venta', 'Cantidad', 'P. Unitario', 'Monto', 'Ganancia']]
            for detalle in context['articulo_detalle']:
                precio_unitario = detalle['monto'] / detalle['cantidad'] if detalle['cantidad'] else 0
                data.append([
                    detalle['dia'].strftime('%d/%m/%Y'),
                    detalle['venta__codigo'],
                    detalle['cantidad'],
                    f"${precio_unitario:,.2f}",
                    f"${detalle['monto']:,.2f}",
                    f"${detalle['ganancia']:,.2f}"
                ])
        
        # Crear tabla
        if len(data) > 1:
            table = Table(data)
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            table.setStyle(style)
            elements.append(table)
        
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
    
    def generate_excel(self, context):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_financiero.xlsx"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"
        
        # Datos según el tipo de reporte
        if context['tipo_reporte'] == 'ventas':
            ws.append(['Periodo', 'Ventas', 'Monto', 'Costo', 'Ganancia', 'Margen'])
            for venta in context['ventas_report']:
                margen = (venta['ganancia_total'] / venta['monto_total'] * 100) if venta['monto_total'] else 0
                ws.append([
                    venta['periodo'].strftime('%B %Y') if 'month' in str(venta['periodo']) else venta['periodo'].strftime('%d/%m/%Y'),
                    venta['total_ventas'],
                    venta['monto_total'],
                    venta['costo_total'],
                    venta['ganancia_total'],
                    margen
                ])
        
        elif context['tipo_reporte'] == 'articulos':
            ws.append(['Código', 'Artículo', 'Categoría', 'Cantidad', 'Monto', 'Ganancia'])
            for art in context['articulos_report']:
                ws.append([
                    art['articulo__codigo'],
                    art['articulo__nombre'],
                    art['articulo__categoria__nombre'],
                    art['cantidad_vendida'],
                    art['monto_total'],
                    art['ganancia_total']
                ])
        
        elif context['tipo_reporte'] == 'articulo_detalle' and 'articulo_detalle' in context:
            ws.append(['Fecha', 'Venta', 'Cantidad', 'P. Unitario', 'Monto', 'Ganancia'])
            for detalle in context['articulo_detalle']:
                precio_unitario = detalle['monto'] / detalle['cantidad'] if detalle['cantidad'] else 0
                ws.append([
                    detalle['dia'].strftime('%d/%m/%Y'),
                    detalle['venta__codigo'],
                    detalle['cantidad'],
                    precio_unitario,
                    detalle['monto'],
                    detalle['ganancia']
                ])
        
        wb.save(response)
        return response


# ================================================================================


@nivel_requerido('admin')
def vista_solo_admin(request):
    # Solo accesible para admins
    pass

@nivel_requerido('personal', 'admin')
def vista_personal_y_admin(request):
    # Accesible para personal y admins
    pass

@nivel_requerido('personal', 'admin')
def vista_personal_y_admin(request):
    # Accesible para personal y admins
    pass