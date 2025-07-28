from django import forms
from aplicacion.models import *
from ProductosCompras.models import *
from ProductosVentas.models import *
from django.db import transaction


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