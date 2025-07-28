from django.db import migrations, models, transaction
from django.utils.text import slugify

def generar_slugs(apps, schema_editor):
    Categoria = apps.get_model('aplicacion', 'Categoria')
    
    # Bloque transaccional para evitar race conditions
    with transaction.atomic():
        for cat in Categoria.objects.all().select_for_update():  # Bloquea registros
            base_slug = slugify(cat.nombre)
            unique_slug = base_slug
            counter = 1
            
            # Verifica unicidad dentro de la transacción
            while Categoria.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
                
            cat.slug = unique_slug
            cat.save(update_fields=['slug'])

class Migration(migrations.Migration):
    dependencies = [
        ('aplicacion', '0003_alter_venta_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),  # Directamente único
        ),
        migrations.RunPython(
            generar_slugs,
            reverse_code=migrations.RunPython.noop  # No hay operación inversa
        ),
    ]