import ctypes
import os

from modulos.utils.utils import resource_path


FONT_FILES = (
    'media/fonts/poppinsregular.ttf',
    'media/fonts/poppinsmedium.ttf',
    'media/fonts/Poppins-Light.ttf',
    'media/fonts/Poppins-SemiBold.ttf',
    'media/fonts/montserratregular.ttf',
    'media/fonts/Montserrat-Medium.ttf',
    'media/fonts/Montserrat-Light.ttf',
    'media/fonts/AndimantePersonalUse-Regular.otf',
)


def registrar_fuentes():
    if os.name != 'nt':
        return
    try:
        add_font = ctypes.windll.gdi32.AddFontResourceExW
    except Exception:
        return
    for rel_path in FONT_FILES:
        try:
            font_path = resource_path(rel_path)
            if os.path.exists(font_path):
                add_font(font_path, 0x10, 0)
        except Exception:
            continue
