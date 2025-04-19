from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Articulo, Categoria, Proveedor, MovimientoInventario, HistorialStock, Venta, DetalleVenta, Cliente, CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import transaction
from django.core.exceptions import ValidationError

User = get_user_model()

class ArticuloForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.editing = kwargs.pop('editing', False)  # Nuevo parámetro para saber si estamos editando
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['categoria'].queryset = Categoria.objects.all()
        self.fields['proveedor_principal'].queryset = Proveedor.objects.filter(activo=True)
        self.fields['creado_por'].initial = user
        self.fields['creado_por'].widget = forms.HiddenInput()
        
        # Campos que deben ser de solo lectura al editar
        if self.editing:
            readonly_fields = ['codigo', 'codigo_barras', 'creado_por', 'fecha_creacion']
            for field_name in readonly_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True
                    self.fields[field_name].widget.attrs['class'] = 'form-control-plaintext'
                    self.fields[field_name].required = False

    class Meta:
        model = Articulo
        fields = '__all__'
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: LUB-001'
            }),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Codigo de Barras del Producto'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del artículo'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la Marca del Articulo'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del Modelo del Articulo'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada'
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'stock_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'costo_promedio': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'tasa_impuesto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'proveedor_principal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'lead_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'palabras_clave': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Toyota, Carro, Automático',
                'rows': 3,
            }),
            'fecha_creacion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
        labels = {
            'codigo': 'Código del artículo',
            'codigo_barras': 'Código de Barras del Articulo',
            'descripcion': 'Descripción',
            'stock_actual': 'Stock actual',
            'stock_minimo': 'Stock mínimo',
            'stock_maximo': 'Stock máximo (opcional)',
            'costo_promedio': 'Costo promedio',
            'precio_venta': 'Precio de venta',
            'tasa_impuesto': 'Impuesto aplicable',
            'unidad_medida': 'Unidad de medida',
            'proveedor_principal': 'Proveedor principal',
            'lead_time': 'Tiempo de reposición (días)',
            'activo': '¿Artículo activo?',
            'imagen': 'Imagen del artículo',
            'palabras_clave': 'Palabras clave (etiquetas)',
            'fecha_creacion': 'Fecha de creación'
        }
        
    def clean(self):
        cleaned_data = super().clean()
        precio_venta = cleaned_data.get('precio_venta')
        costo_promedio = cleaned_data.get('costo_promedio')
        
        if precio_venta and costo_promedio and precio_venta < costo_promedio:
            self.add_error('precio_venta', 'El precio de venta no puede ser menor al costo promedio')
        
        stock_minimo = cleaned_data.get('stock_minimo')
        stock_maximo = cleaned_data.get('stock_maximo')
        
        if stock_maximo and stock_minimo > stock_maximo:
            self.add_error('stock_minimo', 'El stock mínimo no puede ser mayor al stock máximo')
        
        return cleaned_data
    
    def clean_palabras_clave(self):
        raw = self.cleaned_data.get('palabras_clave', '')
        palabras = [p.strip() for p in raw.split(',') if p.strip()]
        return ', '.join(palabras)


class CompraInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['articulo', 'proveedor', 'cantidad', 'costo_unitario', 'referencia', 'observaciones']
        widgets = {
            'articulo': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un artículo'
            }),
            'proveedor': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione proveedor'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1'
            }),
            'costo_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1'
            }),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° factura, remisión, etc.'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles adicionales de la compra'
            }),
        }
        labels = {
            'costo_unitario': 'Precio de compra unitario',
            'referencia': 'Documento de referencia'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['articulo'].queryset = Articulo.objects.filter(activo=True)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
        
        # Campos requeridos
        self.fields['costo_unitario'].required = True
        self.fields['proveedor'].required = False  # Opcional según tu modelo
        
        # Agregar clases adicionales
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = 'ENTRADA'
        instance.usuario = self.user  # Asegúrate que `self.user` esté definido en el form

        if not commit:
            return instance

        with transaction.atomic():
            articulo = instance.articulo
            es_nuevo = instance.pk is None

            # Valores actuales del artículo
            stock_antes = articulo.stock_actual
            costo_promedio_antes = articulo.costo_promedio or 0

            if not es_nuevo:
                # Obtener movimiento original para revertirlo
                original = MovimientoInventario.objects.get(pk=instance.pk)
                stock_revertido = stock_antes - (instance.cantidad - original.cantidad)

                if stock_revertido < 0:
                    raise ValidationError("No hay suficiente stock para editar este movimiento.")

                total_original = original.costo_unitario * original.cantidad
                total_resto = (costo_promedio_antes * stock_antes) - total_original

                # Nuevo total con el nuevo movimiento
                total_nuevo = instance.costo_unitario * instance.cantidad
                nuevo_stock = stock_antes - original.cantidad + instance.cantidad

                nuevo_promedio = (total_resto + total_nuevo) / nuevo_stock if nuevo_stock else 0
                nuevo_promedio = round(nuevo_promedio, 2)

                # Guardar cambios
                instance.save()
                articulo.stock_actual = nuevo_stock
                articulo.costo_promedio = nuevo_promedio
                articulo.save()

                # Obtener historial original
                historial_original = HistorialStock.objects.filter(movimiento=instance).first()

                if historial_original:
                    historial_original.stock_despues = nuevo_stock
                    historial_original.costo_promedio_despues = nuevo_promedio
                    historial_original.costo_unitario_compra = instance.costo_unitario
                    historial_original.usuario = self.user
                    historial_original.save()
                else:
                    # Si por alguna razón no hay historial, lo creamos con los valores actuales
                    HistorialStock.objects.create(
                        movimiento=instance,
                        stock_antes=stock_antes,
                        stock_despues=nuevo_stock,
                        costo_promedio_antes=costo_promedio_antes,
                        costo_promedio_despues=nuevo_promedio,
                        costo_unitario_compra=instance.costo_unitario,
                        costo_unitario_anterior=original.costo_unitario,
                        usuario=self.user
                    )

            else:
                # NUEVA COMPRA
                total_actual = costo_promedio_antes * stock_antes
                total_nuevo = instance.costo_unitario * instance.cantidad
                nuevo_stock = stock_antes + instance.cantidad
                nuevo_promedio = (total_actual + total_nuevo) / nuevo_stock if nuevo_stock else 0
                nuevo_promedio = round(nuevo_promedio, 2)

                instance.save()
                articulo.stock_actual = nuevo_stock
                articulo.costo_promedio = nuevo_promedio
                articulo.save()

                # Obtener la última compra (anterior a esta)
                ultima_compra = MovimientoInventario.objects.filter(
                    articulo=articulo,
                    tipo='ENTRADA'
                ).exclude(pk=instance.pk).order_by('-fecha').first()

                costo_unitario_anterior = ultima_compra.costo_unitario if ultima_compra else 0

                HistorialStock.objects.create(
                    movimiento=instance,
                    stock_antes=stock_antes,
                    stock_despues=nuevo_stock,
                    costo_promedio_antes=costo_promedio_antes,
                    costo_promedio_despues=nuevo_promedio,
                    costo_unitario_compra=instance.costo_unitario,
                    costo_unitario_anterior=costo_unitario_anterior,
                    usuario=self.user
                )

        return instance


    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        costo_unitario = cleaned_data.get('costo_unitario')
        
        if cantidad and cantidad <= 0:
            self.add_error('cantidad', 'La cantidad debe ser mayor a cero')
            
        if costo_unitario and costo_unitario <= 0:
            self.add_error('costo_unitario', 'El precio de compra debe ser mayor a cero')
            
        return cleaned_data


class PersonalForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'direccion', 'foto_perfil']
        widgets = {
            'password': forms.PasswordInput(),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        if self.instance.pk:
            self.fields['username'].disabled = True
            self.fields.pop('username', None)  # Eliminar el campo username



class UserUpdateForm(UserChangeForm):
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    direccion = forms.CharField(label="Dirección", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(label="Rol", choices=CustomUser.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'direccion',
            'foto_perfil',
            'rol',
            'admin',
            'is_active',
            'is_staff',
            'is_superuser'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalización adicional si es necesaria
        self.fields['foto_perfil'].widget.attrs.update({'class': 'form-control'})
        
        # Si no quieres incluir el campo de contraseña (ya que UserChangeForm lo incluye por defecto)
        if 'password' in self.fields:
            del self.fields['password']



class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'metodo_pago', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un cliente...'
            }),
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones adicionales...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        self.fields['cliente'].required = False

class DetalleVentaForm(forms.ModelForm):
    articulo_id = forms.IntegerField(widget=forms.HiddenInput())
    codigo = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Código o nombre del artículo'
    }))
    
    class Meta:
        model = DetalleVenta
        fields = ['articulo_id', 'cantidad', 'descuento']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.001',
                'step': '0.001'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.venta = kwargs.pop('venta', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        articulo_id = cleaned_data.get('articulo_id')
        cantidad = cleaned_data.get('cantidad')
        
        if articulo_id and cantidad:
            try:
                articulo = Articulo.objects.get(id=articulo_id)
                if articulo.stock_actual < Decimal(str(cantidad)):
                    raise forms.ValidationError(
                        f'Stock insuficiente. Disponible: {articulo.stock_actual}'
                    )
                cleaned_data['articulo'] = articulo
                cleaned_data['precio_unitario'] = articulo.precio_venta
            except Articulo.DoesNotExist:
                raise forms.ValidationError('Artículo no encontrado')
        
        return cleaned_data
    
    def save(self, commit=True):
        detalle = super().save(commit=False)
        detalle.venta = self.venta
        detalle.articulo = self.cleaned_data['articulo']
        detalle.precio_unitario = self.cleaned_data['precio_unitario']
        if commit:
            detalle.save()
        return detalle

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['tipo', 'identificacion', 'nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'identificacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cédula/RUC'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Dirección completa...'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
        }