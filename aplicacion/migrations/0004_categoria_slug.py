from django.db import migrations, models
from django.utils.text import slugify

def generar_slugs(apps, schema_editor):
    Categoria = apps.get_model('aplicacion', 'Categoria')
    for cat in Categoria.objects.all():
        base_slug = slugify(cat.nombre)
        unique_slug = base_slug
        counter = 1
        while Categoria.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        cat.slug = unique_slug
        cat.save()

class Migration(migrations.Migration):
    dependencies = [
        ('aplicacion', '0003_alter_venta_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='slug',
            field=models.SlugField(max_length=100, null=True),  # Primero permite nulos
        ),
        migrations.RunPython(generar_slugs),
        migrations.AlterField(
            model_name='categoria',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),  # Luego hace único
        ),
    ]