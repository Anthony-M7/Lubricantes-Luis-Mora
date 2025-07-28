from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import Sum
from aplicacion.models import CustomUser, Articulo, Cliente
from ProductosCompras.models import HistorialStock, MovimientoInventario
from decimal import Decimal
from django.core.exceptions import ValidationError

# Create your models here.

class Venta(models.Model):
    ESTADO_CHOICES = (
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE', 'Pendiente de pago'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    )
    
    METODO_PAGO_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CREDITO', 'Crédito'),
    )
    
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de venta")
    cliente = models.ForeignKey("aplicacion.Cliente", on_delete=models.SET_NULL, null=True, blank=True, default="0")
    fecha = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey("aplicacion.CustomUser", on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        return f"Venta #{self.codigo} - {self.estado} - {self.total}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código de venta automático (ej: VENT-0001)
            ultima_venta = Venta.objects.order_by('-id').first()
            ultimo_numero = int(ultima_venta.codigo.split('-')[1]) if ultima_venta else 0
            self.codigo = f"VENT-{ultimo_numero + 1:04d}"
        super().save(*args, **kwargs)

    def calcular_totales(self):
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.subtotal for detalle in detalles)
        self.impuesto = sum(detalle.impuesto for detalle in detalles)
        self.total = self.subtotal + self.impuesto
        self.save()

    def registrar_movimientos_inventario(self):
        """Registra los movimientos de inventario al completar una venta"""
        for detalle in self.detalles.all():
            movimiento = MovimientoInventario.objects.create(
                articulo=detalle.articulo,
                tipo='SALIDA',
                cantidad=detalle.cantidad,
                usuario=self.creado_por,
                referencia=f"Venta {self.codigo}",
                observaciones=f"Venta a {self.cliente.nombre if self.cliente else 'Cliente ocasional'}",
                costo_unitario=detalle.precio_unitario,  # Precio de venta
            )
            
            # Registrar en el historial de stock
            HistorialStock.objects.create(
                movimiento=movimiento,
                stock_antes=detalle.articulo.stock_actual,
                stock_despues=detalle.articulo.stock_actual - detalle.cantidad,
                costo_promedio_antes=detalle.articulo.costo_promedio,
                costo_promedio_despues=detalle.articulo.costo_promedio,
                costo_unitario_compra=detalle.precio_unitario,  # No aplica para ventas
                costo_unitario_anterior=detalle.articulo.precio_venta,  # No aplica para ventas
                usuario=self.creado_por
            )
            
            # Actualizar stock del artículo
            detalle.articulo.stock_actual -= detalle.cantidad
            detalle.articulo.save()

    def finalizar_venta(self):
        self.estado = 'COMPLETADO'
        self.fecha_finalizacion = timezone.now()
        self.save()
        
        # Actualizar stock para cada artículo
        for detalle in self.detalles.all():
            detalle.articulo.save()
            detalle.self.registrar_movimientos_inventario()
    
    def verificar_stock(self):
        """Verifica que haya suficiente stock para todos los artículos"""
        for detalle in self.detalles.all():
            if detalle.articulo.stock_actual < detalle.cantidad:
                raise ValidationError(
                    f'Stock insuficiente para {detalle.articulo.nombre}. '
                    f'Disponible: {detalle.articulo.stock_actual}, '
                    f'Solicitado: {detalle.cantidad}'
                )
        return True

    def revertir_movimientos_inventario(self):
            """Revierte los movimientos de inventario al eliminar una venta completada"""
            for detalle in self.detalles.all():
                try:
                    movimiento = MovimientoInventario.objects.get(
                        referencia=f"Venta {self.codigo}",
                        articulo=detalle.articulo
                    )
                    
                    # Revertir el stock
                    detalle.articulo.stock_actual += detalle.cantidad
                    detalle.articulo.save()
                    
                    # Eliminar el historial asociado
                    HistorialStock.objects.filter(movimiento=movimiento).delete()
                    
                    # Eliminar el movimiento
                    movimiento.delete()
                    
                except MovimientoInventario.DoesNotExist:
                    continue

    @property
    def articulos_vendidos(self):
        return self.detalleventa_set.aggregate(total=Sum('cantidad'))['total'] or 0


class DetalleVenta(models.Model):
    venta = models.ForeignKey("Venta", on_delete=models.CASCADE, related_name='detalles')
    articulo = models.ForeignKey("aplicacion.Articulo", on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"

    def save(self, *args, **kwargs):
        self.subtotal = (self.precio_unitario * self.cantidad) - self.descuento
        self.impuesto = self.subtotal * (self.articulo.tasa_impuesto / 100)
        super().save(*args, **kwargs)
        self.venta.calcular_totales()

