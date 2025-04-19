from django.db.models.signals import post_save, post_delete, pre_delete, pre_save
from django.dispatch import receiver
from .models import MovimientoInventario, DetalleVenta, CustomUser, Permission


@receiver(post_delete, sender=MovimientoInventario)
def actualizar_stock_al_eliminar(sender, instance, **kwargs):
    """
    Actualiza el stock cuando se elimina un movimiento
    """
    if instance.tipo == 'ENTRADA':
        instance.articulo.stock_actual -= instance.cantidad
    else:
        instance.articulo.stock_actual += instance.cantidad
    instance.articulo.save()

@receiver(pre_delete, sender=DetalleVenta)
def devolver_stock_al_eliminar(sender, instance, **kwargs):
    if instance.venta.estado == 'COMPLETADA':
        instance.articulo.stock_actual += instance.cantidad
        instance.articulo.save()

@receiver(pre_save, sender=CustomUser)
def eliminar_foto_anterior(sender, instance, **kwargs):
    if not instance.pk:
        return
    
    try:
        original = sender.objects.get(pk=instance.pk)
        if original.foto_perfil and original.foto_perfil != instance.foto_perfil:
            original.foto_perfil.delete(save=False)
    except sender.DoesNotExist:
        pass
