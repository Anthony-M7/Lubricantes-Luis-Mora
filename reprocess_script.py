import os
import sys
import django

# Asegurar que el path del proyecto este configurado
sys.path.append('c:\\Proyectos\\Lubricantes-Luis-Mora')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lubricantesLuisMora.settings")
django.setup()

from aplicacion.models import Articulo
from aplicacion.services.image_processor import embellecer_foto_producto

articulos = Articulo.objects.all()
for articulo in articulos:
    if articulo.imagen and hasattr(articulo.imagen, 'path'):
        try:
            print(f"Procesando imagen de: {articulo.nombre}")
            embellecer_foto_producto(articulo.imagen.path)
        except Exception as e:
            print(f"Error procesando {articulo.nombre}: {e}")

print("Procesamiento terminado.")
