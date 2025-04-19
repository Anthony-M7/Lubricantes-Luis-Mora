from django.contrib.auth.models import AbstractUser, Permission, ContentType, Group
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum
    
class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('personal', 'Personal'),
        ("invitado", "Invitado"),
    )

    # Campos adicionales
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True, verbose_name="Foto de perfil")
    admin = models.BooleanField(default=False, verbose_name="¿Administrador?")
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Permisos de vista básicos + permisos de autenticación
            basic_perms = Permission.objects.filter(
                codename__in=[
                    'view_articulo', 'view_categoria', 'view_cliente',
                    'view_user', 'change_user',  # Para su perfil
                    'view_group', 'view_permission'  # Autenticación básica
                ]
            )
            self.user_permissions.add(*basic_perms)
            
            # Opcional: acceso al admin (sin permisos peligrosos)
            self.is_staff = True
            super().save(*args, **kwargs)


 
class Categoria(models.Model):
    """
    Modelo para categorizar los artículos
    """
    nombre = models.CharField(max_length=100, unique=True)
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='subcategorias')
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.padre and self.padre.id == self.id:
            raise ValidationError(('Una categoría no puede ser padre de sí misma'))


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


class Articulo(models.Model):
    """
    Modelo principal para gestión de artículos de inventario
    """
    # 1. Información básica
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    codigo_barras = models.CharField(max_length=100, blank=True, unique=True, null=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    imagen = models.ImageField(upload_to='articulos/', null=True, blank=True)
    
    # 2. Gestión de inventario
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_maximo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    UNIDADES_MEDIDA = (
        ('UN', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('LT', 'Litro'),
        ('MT', 'Metro'),
        ('PAR', 'Par'),
        ('JUEGO', 'Juego'),
        ('CAJA', 'Caja'),
    )
    unidad_medida = models.CharField(max_length=10, choices=UNIDADES_MEDIDA, default='UN')
    
    # 3. Información financiera
    costo_promedio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    TIPO_IMPUESTO = (
        (Decimal('0.00'), 'Exento'),
        (Decimal('0.16'), 'IVA 16%'),
        (Decimal('0.08'), 'IVA 8%'),
    )

    tasa_impuesto = models.DecimalField(max_digits=4, decimal_places=2, choices=TIPO_IMPUESTO, default=Decimal('0.16'))
    
    # 4. Ubicación y logística
    # ubicacion = models.CharField(max_length=100, blank=True, verbose_name="Ubicación en almacén")
    proveedor_principal = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    lead_time = models.PositiveIntegerField(default=0, help_text="Tiempo de reposición en días")
    
    # 5. Estado y auditoría
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='articulos_creados')

    palabras_clave = models.TextField(
        blank=True,
        help_text="Ingrese palabras clave separadas por comas. Ej: Toyota, Carro, Automático"
    )

    def lista_palabras_clave(self):
        return [palabra.strip().lower() for palabra in self.palabras_clave.split(',') if palabra.strip()]

    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nombre']),
            models.Index(fields=['categoria']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def clean(self):
        errors = {}
        
        if self.stock_minimo < 0:
            errors['stock_minimo'] = ('El stock mínimo no puede ser negativo')
        
        if self.stock_maximo and self.stock_minimo > self.stock_maximo:
            errors['stock_minimo'] = ('No puede ser mayor al stock máximo')
        
        if self.precio_venta < self.costo_promedio:
            errors['precio_venta'] = ('El precio de venta no puede ser menor al costo promedio')
        
        if errors:
            raise ValidationError(errors)

    @property
    def valor_total(self):
        """Calcula el valor total del inventario para este artículo"""
        return self.stock_actual * self.costo_promedio

    @property
    def necesita_reabastecimiento(self):
        """Determina si el artículo necesita reabastecerse"""
        return self.stock_actual < self.stock_minimo

    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia porcentual"""
        if self.costo_promedio == 0:
            return 0
        return ((self.precio_venta - self.costo_promedio) / self.costo_promedio) * 100


class MovimientoInventario(models.Model):
    """
    Registro de movimientos de inventario (entradas/salidas)
    """
    TIPO_MOVIMIENTO = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
    )
    
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
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

    usuario = models.ForeignKey(CustomUser, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-fecha']






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
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
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
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
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


class Cliente(models.Model):
    TIPO_CHOICES = (
        ('NATURAL', 'Persona Natural'),
        ('JURIDICO', 'Persona Jurídica'),
    )
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='NATURAL')
    identificacion = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre} ({self.identificacion})"
