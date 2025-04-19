from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "Permiso de sistema")

@register.filter
def modelo_verbose_name(permiso):
    return permiso.content_type.model_class()._meta.verbose_name if permiso.content_type.model_class() else permiso.content_type.model