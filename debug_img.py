import os
import sys
import django
from PIL import Image
import rembg

sys.path.append('c:\\Proyectos\\Lubricantes-Luis-Mora')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lubricantesLuisMora.settings")
django.setup()

from aplicacion.models import Articulo
articulo = Articulo.objects.first()

if articulo and articulo.imagen:
    path = articulo.imagen.path
    print(f"Path: {path}")
    with Image.open(path) as img:
        img = img.convert('RGBA')
        print(f"Original size: {img.size}")
        
        output = rembg.remove(img)
        print(f"After rembg size: {output.size}")
        
        bbox = output.getbbox()
        print(f"Bbox: {bbox}")
        
        if bbox:
            output = output.crop(bbox)
        print(f"After crop size: {output.size}")
        
        bg_w, bg_h = (1080, 1080) # Assuming template is 1080x1080
        out_w, out_h = output.size
        
        ratio = min((bg_w * 0.9) / out_w, (bg_h * 0.9) / out_h)
        print(f"Ratio: {ratio}")
        new_size = (int(out_w * ratio), int(out_h * ratio))
        print(f"New size: {new_size}")
