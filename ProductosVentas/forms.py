from django import forms
from decimal import Decimal
from .models import DetalleVenta, Venta
from aplicacion.models import Articulo, Cliente


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

