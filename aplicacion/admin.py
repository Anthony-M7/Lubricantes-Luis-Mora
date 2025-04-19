from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,Categoria, Proveedor, Articulo, MovimientoInventario, HistorialStock, Venta, Cliente, DetalleVenta
from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'admin')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'admin')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'telefono', 'direccion', 'foto_perfil', "rol")}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'admin'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'telefono', 'admin', "rol"),
        }),
    )

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'

    def ready(self):
        # Importa las señales
        import aplicacion.signals



class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    readonly_fields = ('valor_total', 'necesita_reabastecimiento', 'margen_ganancia')
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'codigo_barras', 'nombre', 'descripcion', 'categoria', "marca", "modelo", 'imagen')
        }),
        ('Inventario', {
            'fields': ('stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida')
        }),
        ('Información Financiera', {
            'fields': ('costo_promedio', 'precio_venta', 'tasa_impuesto', 'valor_total', 'margen_ganancia')
        }),
        ('Proveedores', {
            'fields': ('proveedor_principal', 'lead_time')
        }),
        ('Estado', {
            'fields': ('activo', 'necesita_reabastecimiento', "creado_por")
        }),
    )

admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(Articulo, ArticuloAdmin)
admin.site.register(MovimientoInventario)
admin.site.register(HistorialStock)
admin.site.register(Venta)
admin.site.register(Cliente)
admin.site.register(DetalleVenta)

admin.site.register(CustomUser, CustomUserAdmin)