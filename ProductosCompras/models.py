from django.db import models
from aplicacion.models import *

# Create your models here.


class Proveedor(models.Model):
    """
    Modelo para gestionar proveedores
    """
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=20, blank=True, verbose_name="RFC")
    contacto = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MovimientoInventario(models.Model):
    """
    Registro de movimientos de inventario (entradas/salidas)
    """
    TIPO_MOVIMIENTO = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
    )
    
    articulo = models.ForeignKey("aplicacion.Articulo", on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey("aplicacion.CustomUser", on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100, blank=True)
    proveedor = models.ForeignKey("Proveedor", on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()} de {self.articulo.nombre}"

    @property
    def total(self):
        if self.costo_unitario and self.cantidad:
            return self.costo_unitario * self.cantidad
        return 0
    
    def delete(self, *args, **kwargs):
        articulo = self.articulo
        
        if self.tipo == 'ENTRADA' and self.costo_unitario:
            # Eliminar primero el registro histórico asociado
            HistorialStock.objects.filter(movimiento=self).delete()
            
            # Luego revertir los cambios en el artículo
            articulo.stock_actual -= self.cantidad
            
            if articulo.stock_actual > 0:
                total_costo_actual = articulo.costo_promedio * (articulo.stock_actual + self.cantidad)
                total_costo_revertir = self.costo_unitario * self.cantidad
                nuevo_costo = (total_costo_actual - total_costo_revertir) / articulo.stock_actual
                articulo.costo_promedio = round(nuevo_costo / 100) * 100
            else:
                articulo.costo_promedio = 0
            
            articulo.save()
        
        """Eliminación personalizada para revertir efectos"""
        if self.tipo == 'SALIDA':
            # Revertir stock para movimientos de salida (ventas)
            self.articulo.stock_actual += self.cantidad
            self.articulo.save()
        
            # Eliminar primero el historial asociado
            HistorialStock.objects.filter(movimiento=self).delete()
        
        # Luego eliminar el movimiento
        super().delete(*args, **kwargs)


class HistorialStock(models.Model):
    movimiento = models.ForeignKey(MovimientoInventario, on_delete=models.CASCADE, related_name='historial')
    fecha = models.DateTimeField(auto_now_add=True)
    stock_antes = models.DecimalField(max_digits=12, decimal_places=2)
    stock_despues = models.DecimalField(max_digits=12, decimal_places=2)

    costo_promedio_antes = models.DecimalField(max_digits=12, decimal_places=2)
    costo_promedio_despues = models.DecimalField(max_digits=12, decimal_places=2)

    # Nuevos campos para costos unitarios
    costo_unitario_compra = models.DecimalField(max_digits=10, decimal_places=2)  # Precio de esta compra
    costo_unitario_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Precio compra anterior

    usuario = models.ForeignKey("aplicacion.CustomUser", on_delete=models.PROTECT)

    class Meta:
        ordering = ['-fecha']

