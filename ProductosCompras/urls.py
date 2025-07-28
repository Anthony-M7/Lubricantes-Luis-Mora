from django.urls import path
from .views import *

urlpatterns = [
    path('compras/', compras_view, name='compras'),
    path('compras/nueva/', registrar_compras, name='nueva_compra'),

    path('compras/editar/<int:pk>/', editar_compra, name='editar_compra'),
    path('compras/<int:pk>/eliminar/', eliminar_compra, name='eliminar_compra'),
    path('compras/detalle/<int:pk>/', detalle_compra, name='detalle_compra'),
]