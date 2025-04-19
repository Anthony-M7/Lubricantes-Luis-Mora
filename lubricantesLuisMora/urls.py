"""
URL configuration for lubricantesLuisMora project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from aplicacion.views import * 
from aplicacion.view.views_api import * 
from aplicacion.view.view_ventas import * 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls, name="panel_admin"),

    # path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('panel_administrador/', panel_admin, name='panel_administrador'),
    path('personal/', panel_personal, name='panel_personal'),
    path('usuario/', panel_usuario, name='panel_usuario'),
    path('', inicio, name='inicio'),

    # vistas
    path('dashboard/', dashboard, name='dashboard'),
    path('inventario/', inventario_view, name='inventario'),
    path('compras/', compras_view, name='compras'),

    path('nomina/', gestion_personal, name='nomina_personal'),
    path('crear_personal/', crear_editar_personal, name='crear_personal'),
    path('editar_personal/', crear_editar_personal, name='editar_personal'),
    path('eliminar_personal/<int:id>/', eliminar_personal, name='eliminar_personal'),
    path('get_personal_data/<int:id>/', get_personal_data, name='get_personal_data'),

    path('perfil/', profile, name='perfil'),
    path('actualizar_perfil/', profile, name='actualizar_perfil'),

    # Formularios
    path('articulos/nuevo/', crear_articulo, name='crear_articulo'),
    path('compras/nueva/', registrar_compras, name='nueva_compra'),

    # APIs
    path('api/productos/<int:pk>/', producto_detalle_api, name='producto-detalle-api'),
    path('api/articulos/', api_articulos, name='api_articulos'),

    path('compras/editar/<int:pk>/', editar_compra, name='editar_compra'),
    path('compras/<int:pk>/eliminar/', eliminar_compra, name='eliminar_compra'),
    path('compras/detalle/<int:pk>/', detalle_compra, name='detalle_compra'),

    path('articulos/editar/<int:producto_id>/', editar_producto, name='editar_articulo'),
    path('articulos/<int:producto_id>/eliminar/', eliminar_producto, name='eliminar_producto'),


    # Ventas
    path('ventas/', lista_ventas, name='lista_ventas'),
    path('ventas/crear/', crear_venta, name='crear_venta'),
    path('ventas/editar/<int:pk>/', editar_venta, name='editar_venta'),
    path('ventas/<int:venta_id>/eliminar/', eliminar_venta, name='eliminar_venta'),
    path('ventas/<int:venta_id>/detalle/', detalle_venta, name='detalle_venta'),
    
    # Detalles de venta
    path('ventas/cambiar-estado/', cambiar_estado_venta, name='cambiar_estado_venta'),
    path('ventas/<int:venta_id>/agregar-detalle/', agregar_detalle, name='agregar_detalle'),
    path('ventas/detalles/<int:detalle_id>/', eliminar_detalle, name='eliminar_detalle'),
    path('venta/<int:venta_id>/descargar_recibo/', descargar_recibo, name='descargar_recibo'),
    
    # Búsquedas
    path('ventas/buscar-articulos/', buscar_articulos, name='buscar_articulos'),
    path('api/articulos/<int:pk>/', obtener_articulo_api, name='obtener_articulo_api'),
    path('ventas/crear-cliente-rapido/', crear_cliente_rapido, name='crear_cliente_rapido'),
    path('api/clientes/buscar/', buscar_clientes_api, name='buscar_clientes_api'),

    # PERMISOS
    path('gestion-permisos/usuario/<int:user_id>/', gestion_permisos, name='gestion_permisos_user'),
    path('gestion-permisos/grupo/<int:group_id>/', gestion_permisos, name='gestion_permisos_group'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
