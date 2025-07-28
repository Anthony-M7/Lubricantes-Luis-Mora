from django import forms
from .models import Articulo, Categoria, Cliente, CustomUser
from ProductosCompras.models import *
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

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
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClienteSearchForm(forms.Form):
    TIPO_CHOICES = [
        ('', 'Todos los tipos'),
        ('NATURAL', 'Persona Natural'),
        ('JURIDICO', 'Persona Jurídica'),
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre, ID o teléfono',
            'class': 'form-control'
        })
    )
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

