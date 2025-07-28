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
from django.urls import path, include
from aplicacion.views import * 
from aplicacion.view.views_api import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('ProductosVentas.urls')),
    path('', include('ProductosCompras.urls')),

    # path('', home, name='home'),
    path('admin/', admin.site.urls, name="panel_admin"),
    path('login/', login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('panel_administrador/', panel_admin, name='panel_administrador'),
    path('personal/', panel_personal, name='panel_personal'),
    path('usuario/', panel_usuario, name='panel_usuario'),
    # path('', inicio, name='inicio'),

    # Blog
    path('', blog_informativo, name='inicio'),
    path('categoria/<slug:slug>/', posts_por_categoria, name='posts_categoria'),
    path('blog/<int:post_id>/', detalle_post, name='detalle_post'),

    # vistas
    path('dashboard/', dashboard, name='dashboard'),
    path('inventario/', inventario_view, name='inventario'),

    path('nomina/', gestion_personal, name='nomina_personal'),
    path('crear_personal/', crear_editar_personal, name='crear_personal'),
    path('editar_personal/', crear_editar_personal, name='editar_personal'),
    path('eliminar_personal/<int:id>/', eliminar_personal, name='eliminar_personal'),
    path('get_personal_data/<int:id>/', get_personal_data, name='get_personal_data'),

    path('perfil/', profile, name='perfil'),
    path('actualizar_perfil/', profile, name='actualizar_perfil'),

    path('reportes/', ReportesFinancierosView.as_view(), name='reportes'),

    # Formularios
    path('articulos/nuevo/', crear_articulo, name='crear_articulo'),

    # APIs
    path('api/productos/<int:pk>/', producto_detalle_api, name='producto-detalle-api'),
    path('api/articulos/', api_articulos, name='api_articulos'),

    path('articulos/editar/<int:producto_id>/', editar_producto, name='editar_articulo'),
    path('articulos/<int:producto_id>/eliminar/', eliminar_producto, name='eliminar_producto'),

    path('catalogo/pdf/', generar_catalogo_pdf, name='catalogo_pdf'),
    path('talonario-pagos/', GenerarTalonarioPagoExcel.as_view(), name='talonario_pagos'),
    
    # Clientes
    path('clientes/', listar_clientes, name='clientes'),
    path('nuevo-cliente/', crear_cliente, name='nuevo_cliente'),
    path('detalles-cliente/<int:pk>/', detalle_cliente, name='detalles_cliente'),
    path('detalles-cliente/<int:pk>/editar/', editar_cliente, name='editar_cliente'),
    path('detalles-cliente/<int:pk>/eliminar/', eliminar_cliente, name='eliminar_cliente'),

    # PERMISOS
    path('gestion-permisos/usuario/<int:user_id>/', gestion_permisos, name='gestion_permisos_user'),
    path('gestion-permisos/grupo/<int:group_id>/', gestion_permisos, name='gestion_permisos_group'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
