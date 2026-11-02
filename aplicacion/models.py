from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils.text import slugify
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('personal', 'Personal'),
        ("invitado", "Invitado"),
    )

    # Campos adicionales
    rol = models.CharField(max_length=20, choices=ROLES, default='personal')
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
                    'view_user', 'change_user',
                    'view_group', 'view_permission'
                ]
            )
            self.user_permissions.add(*basic_perms)
            
            self.is_staff = True
            super().save(*args, **kwargs)


class Categoria(models.Model):
    """
    Modelo para categorizar los artículos
    """
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def clean(self):
        if self.padre and self.padre.id == self.id:
            raise ValidationError('Una categoría no puede ser padre de sí misma')
        
        if Categoria.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            raise ValidationError('Ya existe una categoría con este slug')


class Articulo(models.Model):
    # 1. Información básica
    codigo = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Código")
    codigo_barras = models.CharField(max_length=100, blank=True, unique=True, null=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    imagen = models.ImageField(upload_to='articulos/', null=True, blank=True)
    
    # 2. Gestión de inventario
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=3)
    stock_maximo = models.DecimalField(max_digits=12, decimal_places=2, default=12, null=True, blank=True)
    
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
    proveedor_principal = models.ForeignKey("ProductosCompras.Proveedor", on_delete=models.SET_NULL, null=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Articulo.objects.order_by('-id').first()
            siguiente_id = (ultimo.id + 1) if ultimo else 1
            self.codigo = f"ART-{siguiente_id:04d}"
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}
        
        if self.stock_minimo < 0:
            errors['stock_minimo'] = 'El stock mínimo no puede ser negativo'
        
        if self.stock_maximo and self.stock_minimo > self.stock_maximo:
            errors['stock_minimo'] = 'No puede ser mayor al stock máximo'
        
        if self.precio_venta < self.costo_promedio:
            errors['precio_venta'] = 'El precio de venta no puede ser menor al costo promedio'
        
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


# Señales para limpieza de archivos de imagen obsoletos
@receiver(post_delete, sender=Articulo)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Elimina el archivo de imagen del almacenamiento local al borrar el artículo."""
    if instance.imagen and instance.imagen.storage.exists(instance.imagen.name):
        instance.imagen.delete(save=False)


@receiver(pre_save, sender=Articulo)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """Elimina la imagen antigua del almacenamiento cuando se actualiza la foto del artículo."""
    if not instance.pk:
        return False
    try:
        old_file = Articulo.objects.get(pk=instance.pk).imagen
    except Articulo.DoesNotExist:
        return False

    new_file = instance.imagen
    if old_file and old_file != new_file:
        if old_file.storage.exists(old_file.name):
            old_file.delete(save=False)


@receiver(post_save, sender=Articulo)
def auto_enhance_image_in_background(sender, instance, created, **kwargs):
    """
    Tarea en segundo plano: embellece la fotografía del producto 
    (ajuste de contraste, color, nitidez y fondo) sin ralentizar al usuario.
    """
    if instance.imagen:
        from aplicacion.services.image_processor import procesar_imagen_en_segundo_plano
        procesar_imagen_en_segundo_plano(instance.id)

class NotificacionAsincrona(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notificaciones_asincronas')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.titulo}"
