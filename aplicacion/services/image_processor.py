import os
import threading
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import rembg
from django.conf import settings

def embellecer_foto_producto(file_path):
    """
    Procesa y embellece la fotografía del producto en segundo plano:
    1. Remueve el fondo automáticamente con IA (rembg).
    2. Ajusta brillo, contraste y nitidez para resaltar el producto.
    3. Compone el producto sobre la plantilla de red social.
    """
    if not os.path.exists(file_path):
        return

    try:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)  # Corregir orientación de cámara celular
            img = img.convert('RGBA')

            # 1. Remover el fondo
            output = rembg.remove(img)
            
            # Recortar bordes transparentes para obtener el tamaño real del producto
            bbox = output.getbbox()
            if bbox:
                output = output.crop(bbox)

            # 2. Ajustes al producto sin fondo
            # Mejora de Nitidez (Sharpness)
            enhancer = ImageEnhance.Sharpness(output)
            output = enhancer.enhance(1.2)
            # Mejora de Contraste (Contrast)
            enhancer = ImageEnhance.Contrast(output)
            output = enhancer.enhance(1.1)
            # Mejora de Color / Saturación
            enhancer = ImageEnhance.Color(output)
            output = enhancer.enhance(1.15)
            # Ajuste ligero de Brillo
            enhancer = ImageEnhance.Brightness(output)
            output = enhancer.enhance(1.04)

            # 3. Cargar la plantilla de fondo "red social"
            # Asumimos que media root esta configurado y que copiamos la imagen ahi
            bg_path = os.path.join(settings.MEDIA_ROOT, 'articulos', 'bg_social_template.png')
            
            if os.path.exists(bg_path):
                bg = Image.open(bg_path).convert('RGBA')
            else:
                # Fallback si no existe la plantilla
                bg = Image.new('RGBA', output.size, (255, 255, 255, 255))
            
            bg_w, bg_h = bg.size
            out_w, out_h = output.size
            
            # Ajustar el tamaño del producto (aprox 58% de la altura para no tapar toda la sala)
            ratio = min((bg_w * 0.58) / out_w, (bg_h * 0.58) / out_h)
            new_size = (int(out_w * ratio), int(out_h * ratio))
            output = output.resize(new_size, Image.Resampling.LANCZOS)
            
            # La base iluminada de la plantilla está al 65% de la altura de la imagen
            # Centramos horizontalmente y sentamos la base del producto justo encima
            x = (bg_w - new_size[0]) // 2
            pedestal_y = int(bg_h * 0.65)
            y = pedestal_y - new_size[1]
            
            # Componer final
            final_img = Image.new('RGBA', bg.size)
            final_img.paste(bg, (0, 0))
            final_img.paste(output, (x, y), output)

            # Guardar la imagen embellecida con máxima calidad
            final_img = final_img.convert('RGB')
            final_img.save(file_path, format='JPEG', quality=92, optimize=True)

    except Exception as e:
        print(f"Error procesando imagen: {e}")


def procesar_imagen_en_segundo_plano(articulo_id):
    """
    Lanza una tarea asíncrona en segundo plano (Thread) para procesar la foto
    sin bloquear la experiencia ni el guardado del usuario en la web.
    """
    from aplicacion.models import Articulo, NotificacionAsincrona

    def worker():
        try:
            articulo = Articulo.objects.get(pk=articulo_id)
            if articulo.imagen and hasattr(articulo.imagen, 'path'):
                file_path = articulo.imagen.path
                embellecer_foto_producto(file_path)
                
                # Crear notificación
                if articulo.creado_por:
                    NotificacionAsincrona.objects.create(
                        usuario=articulo.creado_por,
                        titulo="Imagen Procesada",
                        mensaje=f"La imagen del producto {articulo.nombre} ha sido mejorada con IA exitosamente."
                    )
        except Exception as e:
            try:
                if 'articulo' in locals() and articulo.creado_por:
                    NotificacionAsincrona.objects.create(
                        usuario=articulo.creado_por,
                        titulo="Error al procesar imagen",
                        mensaje=f"No se pudo mejorar la imagen del producto {articulo.nombre}."
                    )
            except:
                pass

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

