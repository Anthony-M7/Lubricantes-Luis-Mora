 # Ventas
from django.urls import path
from .views import *

urlpatterns = [
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
]