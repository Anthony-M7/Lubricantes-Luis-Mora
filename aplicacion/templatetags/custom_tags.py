from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "Permiso de sistema")

@register.filter
def modelo_verbose_name(permiso):
    return permiso.content_type.model_class()._meta.verbose_name if permiso.content_type.model_class() else permiso.content_type.model

@register.filter
def normalize_decimal(value):
    try:
        from decimal import Decimal
        val = Decimal(str(value)).normalize()
        # Si no tiene decimales, se devuelve como entero (para que no salga 1.0)
        # normalize() en python 3 hace que Decimal('1.0') se convierta en Decimal('1') 
        # pero si es 1.000 se vuelve 1. Si es 1.500 se vuelve 1.5
        # Sin embargo, normalize() convierte a notacion cientifica valores como 0, 
        # para evitarlo:
        if val == val.to_integral():
            return val.quantize(Decimal(1))
        return val
    except Exception:
        return value