from tkinter import *
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps, ImageTk
import sys
import os
import traceback
import unicodedata
import math
import threading

from modulos.inicio_dashboard import InicioDashboard as Inicio
from modulos.ventas.ventas_moderna import VentasModerna as Ventas
from modulos.inventario.inventario_simple import InventarioSimple as Inventario
from modulos.clientes_moderno import ClientesModerno as Clientes
from modulos.pedidos_moderno import PedidosModerno as Pedidos
from modulos.proveedores.proveedor_moderno import ProveedorModerno as Proveedor
from modulos.compras.compras_moderno import ComprasModerno as Compras
from modulos.rendimiento.rendimiento_moderno import RendimientoModerno as Rendimiento
from modulos.prestamos.prestamos_moderno import PrestamosModerno as Prestamos
from modulos.nominas.nominas_moderno import NominasModerno as Nominas
from modulos.abonos.abonos_moderno import AbonosModerno as Abonos
from modulos.informacion.informacion_moderna import InformacionModerna as Informacion
from modulos.empacadora import (
    EmpacadoraInicio,
    EmpacadoraVentas,
    EmpacadoraLotes,
    EmpacadoraClientes,
    EmpacadoraCobranza,
)
from modulos.utils.estilos_modernos import estilos
from modulos.utils.utils import resource_path
from modulos.auth.permisos import tiene_permiso, asegurar_tablas_permisos

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')


class _DibujoIconoHD:
    """Dibuja en una cuadrícula 32x32 sobre un lienzo HD con antialias real."""

    def __init__(self, image, scale=16):
        self._draw = ImageDraw.Draw(image)
        self._scale = scale

    def _coords(self, values):
        return tuple(round(value * self._scale) for value in values)

    def _width(self, value):
        return max(1, round(value * self._scale))

    def line(self, coords, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = self._width(kwargs['width'])
        self._draw.line(self._coords(coords), **kwargs)

    def rounded_rectangle(self, coords, **kwargs):
        if 'radius' in kwargs:
            kwargs['radius'] = self._width(kwargs['radius'])
        if 'width' in kwargs:
            kwargs['width'] = self._width(kwargs['width'])
        self._draw.rounded_rectangle(self._coords(coords), **kwargs)

    def rectangle(self, coords, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = self._width(kwargs['width'])
        self._draw.rectangle(self._coords(coords), **kwargs)

    def ellipse(self, coords, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = self._width(kwargs['width'])
        self._draw.ellipse(self._coords(coords), **kwargs)

    def arc(self, coords, start, end, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = self._width(kwargs['width'])
        self._draw.arc(self._coords(coords), start, end, **kwargs)


def _crear_lienzo_icono_hd():
    # Maestro 4x real: cuadrícula base 32x32 dibujada sobre 128x128.
    image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    return image, _DibujoIconoHD(image, scale=4)


def crear_logo_sidebar_hd(color=(226, 232, 239)):
    """Convierte el sello original en una marca blanca sin fondo cuadrado."""
    original = Image.open(
        resource_path('media/icons/logo_luevanos.png')
    ).convert('RGBA')
    gray = ImageOps.grayscale(original)
    inverted = ImageOps.autocontrast(ImageOps.invert(gray), cutoff=1)
    alpha = inverted.point(
        lambda value: 0 if value < 18 else min(255, int(value * 1.22))
    )
    bbox = alpha.getbbox()
    if bbox:
        alpha = alpha.crop(bbox)
    mark = Image.new('RGBA', alpha.size, (*color, 0))
    mark.putalpha(alpha)
    mark = ImageOps.contain(mark, (120, 120), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    canvas.paste(mark, ((128 - mark.width) // 2, (128 - mark.height) // 2), mark)
    return canvas


def crear_icono_sobre(color='#f2c14e'):
    # Compatibilidad: donde antes se usaba el sobre, ahora se muestra campana.
    return crear_icono_campana(color)


def crear_icono_hamburguesa(color='#d7b56d'):
    img, draw = _crear_lienzo_icono_hd()
    for y in (10, 16, 22):
        draw.rounded_rectangle((7, y, 25, y + 2), radius=1, fill=color)
    return img

def crear_icono_busqueda(color='#d7b56d'):
    img, draw = _crear_lienzo_icono_hd()
    draw.ellipse((7, 7, 20, 20), outline=color, width=3)
    draw.line((18, 18, 25, 25), fill=color, width=3)
    return img


def crear_icono_campana(color='#d7b56d'):
    """Campana vectorial HD, nitida al escalarse en la barra superior."""
    img, draw = _crear_lienzo_icono_hd()
    draw.arc((10, 8, 22, 22), 205, 335, fill=color, width=2.4)
    draw.line((10, 16, 10, 22), fill=color, width=2.4)
    draw.line((22, 16, 22, 22), fill=color, width=2.4)
    draw.rounded_rectangle((7, 21, 25, 24), radius=1.6, outline=color, width=2.2)
    draw.line((12, 24, 20, 24), fill=color, width=2.2)
    draw.ellipse((14, 25, 18, 29), fill=color)
    draw.rounded_rectangle((14.2, 5, 17.8, 8.2), radius=1.6, fill=color)
    draw.arc((7, 6, 25, 27), 213, 327, fill=color, width=.8)
    return img


def crear_icono_usuario_hd(color='#f7fbff'):
    """Usuario vectorial circular en alta resolucion para reemplazar iniciales."""
    img, draw = _crear_lienzo_icono_hd()
    draw.ellipse((10, 5.8, 22, 17.8), outline=color, width=2.2)
    draw.arc((6.5, 15.6, 25.5, 30.5), 202, 338, fill=color, width=2.4)
    draw.arc((9, 18.4, 23, 29.5), 198, 342, fill=color, width=1.1)
    return img


def crear_icono_tema(modo_oscuro=False, color='#20242c'):
    """Crea un sol o una luna para el selector de apariencia."""
    img, draw = _crear_lienzo_icono_hd()
    if modo_oscuro:
        draw.ellipse((8, 6, 24, 24), fill=color)
        draw.ellipse((14, 3, 27, 18), fill=(0, 0, 0, 0))
        draw.ellipse((22, 7, 25, 10), fill=color)
    else:
        draw.ellipse((11, 11, 21, 21), outline=color, width=2)
        for x1, y1, x2, y2 in (
            (16, 4, 16, 8), (16, 24, 16, 28), (4, 16, 8, 16), (24, 16, 28, 16),
            (7, 7, 10, 10), (22, 22, 25, 25), (25, 7, 22, 10), (10, 22, 7, 25),
        ):
            draw.line((x1, y1, x2, y2), fill=color, width=2)
    return img

def crear_icono_menu(simbolo, color='#d7b56d'):
    img, draw = _crear_lienzo_icono_hd()
    line = 3
    if simbolo in ('home', 'inicio'):
        draw.line((7, 16, 16, 8, 25, 16), fill=color, width=line)
        draw.line((10, 16, 10, 25, 22, 25, 22, 16), fill=color, width=line)
    elif simbolo in ('cart', 'ventas'):
        draw.line((7, 9, 10, 9, 13, 21, 24, 21), fill=color, width=line)
        draw.line((13, 12, 25, 12, 23, 18, 14, 18), fill=color, width=line)
        draw.ellipse((13, 23, 17, 27), fill=color)
        draw.ellipse((22, 23, 26, 27), fill=color)
    elif simbolo in ('bag', 'compras'):
        draw.rounded_rectangle((8, 13, 24, 25), radius=2, outline=color, width=line)
        draw.arc((12, 7, 20, 17), 180, 360, fill=color, width=line)
    elif simbolo in ('truck', 'pedidos'):
        draw.rounded_rectangle((6, 13, 18, 21), radius=1, outline=color, width=line)
        draw.line((18, 16, 23, 16, 26, 21, 18, 21), fill=color, width=line)
        draw.ellipse((9, 22, 14, 27), fill=color)
        draw.ellipse((20, 22, 25, 27), fill=color)
    elif simbolo in ('user', 'clientes', 'sesion'):
        draw.ellipse((12, 7, 20, 15), outline=color, width=line)
        draw.arc((8, 15, 24, 29), 205, 335, fill=color, width=line)
    elif simbolo in ('provider', 'proveedores'):
        draw.ellipse((8, 8, 14, 14), outline=color, width=line)
        draw.ellipse((18, 8, 24, 14), outline=color, width=line)
        draw.line((11, 16, 11, 25), fill=color, width=line)
        draw.line((21, 16, 21, 25), fill=color, width=line)
        draw.line((11, 20, 21, 20), fill=color, width=line)
    elif simbolo in ('box', 'inventario'):
        draw.line((8, 12, 16, 8, 24, 12, 16, 16, 8, 12), fill=color, width=line)
        draw.line((8, 12, 8, 23, 16, 27, 24, 23, 24, 12), fill=color, width=line)
        draw.line((16, 16, 16, 27), fill=color, width=line)
    elif simbolo in ('cash', 'finanzas'):
        draw.rounded_rectangle((7, 10, 25, 22), radius=2, outline=color, width=line)
        draw.ellipse((13, 12, 19, 18), outline=color, width=line)
    elif simbolo in ('performance', 'rendimiento'):
        draw.line((8, 25, 8, 8), fill=color, width=line)
        draw.line((8, 25, 25, 25), fill=color, width=line)
        draw.line((10, 21, 15, 16, 19, 19, 25, 10), fill=color, width=line)
        draw.line((21, 10, 25, 10, 25, 14), fill=color, width=2)
    elif simbolo in ('payroll', 'nominas'):
        draw.rounded_rectangle((8, 6, 24, 27), radius=2, outline=color, width=line)
        draw.line((12, 11, 20, 11), fill=color, width=2)
        draw.ellipse((13, 14, 18, 19), outline=color, width=2)
        draw.arc((11, 18, 21, 26), 205, 335, fill=color, width=2)
    elif simbolo in ('loan', 'prestamos'):
        draw.rounded_rectangle((6, 10, 26, 23), radius=2, outline=color, width=line)
        draw.line((8, 14, 24, 14), fill=color, width=2)
        draw.rectangle((18, 17, 23, 20), outline=color, width=2)
        draw.line((12, 27, 20, 27), fill=color, width=2)
        draw.line((16, 23, 16, 29), fill=color, width=2)
    elif simbolo in ('info', 'informacion'):
        draw.ellipse((14, 7, 18, 11), fill=color)
        draw.line((16, 15, 16, 24), fill=color, width=4)
    elif simbolo in ('gear', 'configuracion'):
        draw.ellipse((12, 12, 20, 20), outline=color, width=line)
        for x1, y1, x2, y2 in ((16, 5, 16, 10), (16, 22, 16, 27), (5, 16, 10, 16), (22, 16, 27, 16), (8, 8, 11, 11), (21, 21, 24, 24), (24, 8, 21, 11), (11, 21, 8, 24)):
            draw.line((x1, y1, x2, y2), fill=color, width=line)
    elif simbolo in ('save', 'guardar'):
        draw.rounded_rectangle((8, 6, 24, 26), radius=2, outline=color, width=line)
        draw.rectangle((11, 8, 20, 13), outline=color, width=line)
        draw.line((12, 21, 20, 21), fill=color, width=line)
    elif simbolo in ('globe', 'pwa', 'web'):
        draw.ellipse((6, 6, 26, 26), outline=color, width=line)
        draw.arc((11, 6, 21, 26), 90, 270, fill=color, width=2)
        draw.arc((11, 6, 21, 26), 270, 90, fill=color, width=2)
        draw.line((7, 16, 25, 16), fill=color, width=2)
    elif simbolo in ('exit', 'salir'):
        draw.line((8, 8, 18, 8, 18, 24, 8, 24, 8, 8), fill=color, width=line)
        draw.line((15, 16, 26, 16), fill=color, width=line)
        draw.line((22, 12, 26, 16, 22, 20), fill=color, width=line)
    elif simbolo in ('report', 'resumen'):
        draw.line((9, 25, 9, 9, 23, 9, 23, 25, 9, 25), fill=color, width=line)
        draw.line((12, 15, 20, 15), fill=color, width=line)
        draw.line((12, 20, 18, 20), fill=color, width=line)
    else:
        draw.ellipse((14, 14, 18, 18), fill=color)
    return img


class ErrorModulo(tk.Frame):
    def __init__(self, parent, titulo, error):
        super().__init__(parent, bg=estilos.COLORS['bg_primary'])
        card = ctk.CTkFrame(self, width=760, height=230, fg_color=estilos.COLORS['white'], corner_radius=10, border_width=1, border_color=estilos.COLORS['border'])
        card.place(x=34, y=34)
        ctk.CTkLabel(card, text=f'No se pudo cargar {titulo}', font=ctk.CTkFont(family='Poppins', size=20, weight='bold'), text_color=estilos.COLORS['danger']).place(x=26, y=24)
        ctk.CTkLabel(card, text='El sistema sigue abierto. Este modulo necesita revision antes de usarse.', font=ctk.CTkFont(family='Poppins', size=12), text_color=estilos.COLORS['dark_gray']).place(x=26, y=62)
        ctk.CTkLabel(card, text=str(error), font=ctk.CTkFont(family='Consolas', size=10), text_color=estilos.COLORS['gray'], wraplength=700, justify='left').place(x=26, y=104)


class Tooltip:
    def __init__(self, widget, texto, delay=450):
        self.widget = widget
        self.texto = texto
        self.delay = delay
        self._after_id = None
        self._tip = None
        widget.bind('<Enter>', self._programar, add='+')
        widget.bind('<Leave>', self.ocultar, add='+')
        widget.bind('<ButtonPress>', self.ocultar, add='+')
        widget.bind('<Destroy>', self.ocultar, add='+')

    def _programar(self, _event=None):
        self.ocultar()
        try:
            self._after_id = self.widget.after(self.delay, self.mostrar)
        except Exception:
            self._after_id = None

    def mostrar(self):
        if self._tip or not self.texto:
            return
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() + 8
            y = self.widget.winfo_rooty() + max(0, (self.widget.winfo_height() // 2) - 12)
            self._tip = tk.Toplevel(self.widget)
            self._tip.withdraw()
            self._tip.wm_overrideredirect(True)
            self._tip.configure(bg='#111827')
            label = tk.Label(
                self._tip,
                text=self.texto,
                bg='#111827',
                fg='white',
                padx=9,
                pady=5,
                font=('Poppins', 9, 'bold'),
            )
            label.pack()
            self._tip.update_idletasks()
            ancho = max(24, label.winfo_reqwidth())
            alto = max(20, label.winfo_reqheight())
            self._tip.geometry(f'{ancho}x{alto}+{x}+{y}')
            self._tip.attributes('-topmost', True)
            self._tip.deiconify()
        except Exception:
            self._tip = None

    def ocultar(self, _event=None):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class Container(tk.Frame):
    # Menú compacto: libera más espacio para tablas y formularios.
    SIDEBAR_W = 260
    MENU_BG = '#08121f'
    MENU_SURFACE = '#091523'
    MENU_BORDER = '#1d2937'
    MENU_TEXT = '#91a0af'
    MENU_MUTED = '#718397'
    MENU_ACTIVE = '#0b4774'
    MENU_ACTIVE_HOVER = '#10314d'
    MENU_BLUE = '#159dff'
    HEADER_H = 80
    APP_W = 1920
    APP_H = 996
    CONTENT_W = APP_W - SIDEBAR_W
    CONTENT_H = APP_H
    MODULE_H = APP_H - HEADER_H

    def __init__(self, padre, controlador, usuario_actual=None):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.controlador = controlador
        self.usuario_actual = usuario_actual
        asegurar_tablas_permisos()

        try:
            padre.update_idletasks()
            parent_w = int(padre.winfo_width())
            parent_h = int(padre.winfo_height())
            self.APP_W = max(1100, parent_w if parent_w > 1 else 1920)
            self.APP_H = max(700, parent_h if parent_h > 1 else 996)
            self.CONTENT_W = self.APP_W - self.SIDEBAR_W
            self.CONTENT_H = self.APP_H
            self.MODULE_H = self.APP_H - self.HEADER_H
        except Exception:
            pass

        self.pack(fill='both', expand=True)
        self.configure(width=self.APP_W, height=self.APP_H)
        self.sidebar_expanded = True
        self.current_sidebar_w = self.SIDEBAR_W
        self.modo_oscuro = False
        self._theme_originals = {}

        self.frames = {}
        self.buttons = []
        self.active_button = None
        self.active_container = None
        self.button_map = {}
        self.tooltips = []
        self.titulo_actual = None
        self.subtitulo_actual = None
        self.modo_negocio = 'Sistema administrativo'

        self.widgets_modernos()
        self.crear_modulos()
        self._db_mtime = self.obtener_mtime_db()
        self.show_frames(Inicio)
        # Reafirma el modulo inicial cuando Tk termina de calcular la ventana.
        # Algunos modulos programan ajustes de geometria durante su creacion y,
        # sin esta seleccion final, el ultimo de ellos podia quedar al frente.
        self.after_idle(self._mostrar_inicio_al_arrancar)
        self.after_idle(self._activar_tema_oscuro_inicial)
        self.iniciar_auto_actualizacion()
        self.bind('<Configure>', self._on_container_configure, add='+')
        # Pack calcula el ancho definitivo después del constructor. Sin esta
        # sincronización, el primer módulo podía conservar el mínimo de 1100 px
        # y dejar una franja vacía en monitores Full HD.
        self.after(50, self._sincronizar_layout_inicial)
        self.after(250, self._sincronizar_layout_inicial)
        self.after(1200, self._forzar_sidebar_inicial)

    def _mostrar_inicio_al_arrancar(self):
        try:
            if self.winfo_exists() and Inicio in self.frames:
                self.show_frames(Inicio)
        except Exception:
            pass

    def _activar_tema_oscuro_inicial(self):
        """Abre el panel con el acabado oscuro del dashboard aprobado."""
        try:
            if self.winfo_exists() and not self.modo_oscuro:
                self.establecer_modo_oscuro(True, forzar=True)
        except (tk.TclError, AttributeError):
            pass

    def _configurar_paleta_navegacion(self, oscuro):
        """Mantiene una sola paleta coherente para sidebar y encabezado."""
        if oscuro:
            self.MENU_BG = '#08121f'
            self.MENU_SURFACE = '#091523'
            self.MENU_BORDER = '#1d2937'
            self.MENU_TEXT = '#b5c1ce'
            self.MENU_MUTED = '#7f91a4'
            self.MENU_ACTIVE = '#0b4774'
            self.MENU_ACTIVE_HOVER = '#10314d'
            self.MENU_BLUE = '#159dff'
        else:
            self.MENU_BG = '#f7f9fc'
            self.MENU_SURFACE = '#ffffff'
            self.MENU_BORDER = '#d8e1eb'
            self.MENU_TEXT = '#344054'
            self.MENU_MUTED = '#667085'
            self.MENU_ACTIVE = '#dff1ff'
            self.MENU_ACTIVE_HOVER = '#eaf5ff'
            self.MENU_BLUE = '#087de0'

    def _on_container_configure(self, event=None):
        if event is not None and event.widget is not self:
            return
        nativo = self._obtener_tamano_nativo_layout()
        if nativo:
            nuevo_w, nuevo_h = nativo
        else:
            nuevo_w = max(900, self.winfo_width())
            nuevo_h = max(640, self.winfo_height())
        if abs(nuevo_w - self.APP_W) < 2 and abs(nuevo_h - self.APP_H) < 2:
            return
        self.APP_W = nuevo_w
        self.APP_H = nuevo_h
        self.CONTENT_H = self.APP_H
        self.MODULE_H = max(420, self.APP_H - self.HEADER_H)
        self.aplicar_layout_sidebar()

    def _obtener_tamano_nativo_layout(self):
        """Devuelve píxeles visibles reales, evitando el desborde por DPI 125 %."""
        if os.name != 'nt':
            return None
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = (
                    ('left', ctypes.c_long), ('top', ctypes.c_long),
                    ('right', ctypes.c_long), ('bottom', ctypes.c_long),
                )

            root = self.winfo_toplevel()
            child = root.winfo_id()
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(child) or child
            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return None
            width = int(rect.right - rect.left)
            total_height = int(rect.bottom - rect.top)
            if width < 900 or total_height < 650:
                return None
            title_height = 34
            return width, max(640, total_height - title_height)
        except Exception:
            return None

    def _sincronizar_layout_inicial(self):
        try:
            if not self.winfo_exists():
                return
            if not getattr(self, '_layout_inicial_lista', False):
                self.sidebar_expanded = True
                self.current_sidebar_w = self.SIDEBAR_W
                self._layout_inicial_lista = True
            nativo = self._obtener_tamano_nativo_layout()
            if nativo:
                self.APP_W, self.APP_H = nativo
            else:
                self.APP_W = max(1100, int(self.winfo_width()))
                self.APP_H = max(700, int(self.winfo_height()))
            self.CONTENT_H = self.APP_H
            self.MODULE_H = max(420, self.APP_H - self.HEADER_H)
            self.aplicar_layout_sidebar()
            self.Inicio()
        except (tk.TclError, AttributeError):
            pass

    def _forzar_sidebar_inicial(self):
        """Garantiza que el primer estado visible coincida con la referencia."""
        try:
            if not self.winfo_exists() or self.sidebar_expanded:
                return
            self.sidebar_expanded = True
            self.current_sidebar_w = self.SIDEBAR_W
            self.aplicar_layout_sidebar()
        except (tk.TclError, AttributeError):
            pass

    def crear_modulos(self):
        self.modulos_disponibles = [
            (Inicio, 'inicio', 'Panel de control', 'Resumen general del sistema'),
            (Ventas, 'ventas', 'Ventas', 'Registro y facturación de ventas'),
            (Inventario, 'inventario', 'Inventario', 'Productos, stock y etiquetas'),
            (Clientes, 'clientes', 'Clientes', 'Gestión de clientes'),
            (Pedidos, 'pedidos', 'Pedidos', 'Pedidos y seguimiento'),
            (Proveedor, 'proveedores', 'Proveedores', 'Directorio de proveedores'),
            (Compras, 'compras', 'Compras', 'Entradas y costos'),
            (Rendimiento, 'rendimiento', 'Rendimiento', 'Indicadores y ganancias'),
            (Prestamos, 'rendimiento', 'Préstamos', 'Control de préstamos y abonos'),
            (Nominas, 'rendimiento', 'Nóminas', 'Pagos de empleados y deducciones'),
            (Abonos, 'rendimiento', 'Abonos', 'Registro e historial de abonos'),
            (Informacion, 'informacion', 'Información', 'Datos generales del sistema'),
        ]
        self.modulos_permitidos = []
        for clase, clave, titulo, subtitulo in self.modulos_disponibles:
            if clave == 'inicio' or tiene_permiso(self.usuario_actual, clave):
                self.modulos_permitidos.append((clase, clave, titulo, subtitulo))

        if len(self.modulos_permitidos) == 1:
            self.modulos_permitidos.append((Informacion, 'informacion', 'Información', 'Datos generales del sistema'))

        self.modulos_carniceria = list(self.modulos_permitidos)
        self.modulos_empacadora = [
            (EmpacadoraInicio, 'empacadora_inicio', 'Panel de Empacadora', 'Resumen operativo de la empacadora'),
            (EmpacadoraVentas, 'empacadora_ventas', 'Ventas de Empacadora', 'Fecha, cliente, folio, monto y lote'),
            (EmpacadoraLotes, 'empacadora_lotes', 'Lotes y producto', 'Compras y división mensual en cuatro lotes'),
            (EmpacadoraClientes, 'empacadora_clientes', 'Clientes de Empacadora', 'Directorio de clientes'),
            (EmpacadoraCobranza, 'empacadora_cobranza', 'Cobranza de Empacadora', 'Abonos, saldos y recordatorios'),
        ]
        todos_modulos = self.modulos_carniceria + self.modulos_empacadora
        for clase, _clave, titulo, _subtitulo in todos_modulos:
            try:
                frame = clase(self.module_host)
            except Exception as error:
                traceback.print_exc()
                frame = ErrorModulo(self.module_host, titulo, error)
            self.frames[clase] = frame
            try:
                frame.configure(bg=estilos.COLORS['bg_primary'])
            except Exception:
                pass
            frame.place(x=0, y=0, width=self.CONTENT_W, height=self.MODULE_H)
            frame.place_forget()

    def show_frames(self, container):
        frame = self.frames.get(container)
        if not frame:
            return
        for otro in self.frames.values():
            if otro is not frame:
                otro.place_forget()
        frame.place(x=0, y=0, width=self.CONTENT_W, height=self.MODULE_H)
        frame.tkraise()
        self.actualizar_boton_activo(container)
        self.refrescar_frame(frame)
        self._configurar_tablas_tema(self.modo_oscuro)
        for clase, _clave, titulo, subtitulo in self.modulos_permitidos:
            if clase == container:
                self.titulo_actual.configure(text=titulo)
                self.subtitulo_actual.configure(text=subtitulo)
                break

    def obtener_mtime_db(self):
        try:
            ruta = os.path.join(os.getcwd(), 'database.db')
            return os.path.getmtime(ruta) if os.path.exists(ruta) else 0
        except Exception:
            return 0

    def iniciar_auto_actualizacion(self):
        self.revisar_cambios_base_datos()

    def revisar_cambios_base_datos(self):
        try:
            actual = self.obtener_mtime_db()
            if actual and getattr(self, '_db_mtime', 0) and actual != self._db_mtime:
                self._db_mtime = actual
                self.refrescar_modulos()
            elif actual and not getattr(self, '_db_mtime', 0):
                self._db_mtime = actual
        except Exception:
            pass
        self.after(1800, self.revisar_cambios_base_datos)

    def refrescar_modulos(self):
        for frame in list(self.frames.values()):
            self.refrescar_frame(frame)
        try:
            self.actualizar_alertas_periodicas()
        except Exception:
            pass

    def refrescar_frame(self, frame):
        metodos = (
            'cargar_datos',
            'cargar_articulos',
            'cargar_registros',
            'cargar_compras',
            'cargar_prestamos',
            'cargar_nominas',
            'cargar_ventas_pendientes',
            'cargar_productos',
            'cargar_clientes',
            'refrescar_iva',
            'actualizar_total_hoy',
            'cargar_estadisticas',
            'cargar_resumen_inventario',
            'cargar_actividad_reciente',
        )
        for nombre in metodos:
            metodo = getattr(frame, nombre, None)
            if not callable(metodo):
                continue
            try:
                metodo()
            except TypeError:
                continue
            except Exception:
                continue

    def Inicio(self):
        self.show_frames(Inicio)

    def Ventas(self):
        self.show_frames(Ventas)

    def capturar_nota_en_ventas(self, datos, ruta_imagen=''):
        frame = self.frames.get(Ventas)
        if frame is None:
            raise RuntimeError('El modulo de Ventas no esta disponible.')
        self.show_frames(Ventas)
        cargar = getattr(frame, 'cargar_nota_detectada', None)
        if not callable(cargar):
            raise RuntimeError('Ventas no puede recibir la nota en este momento.')
        cargar(datos, ruta_imagen)

    def Inventario(self):
        self.show_frames(Inventario)

    def Clientes(self):
        self.show_frames(Clientes)

    def Pedidos(self):
        self.show_frames(Pedidos)

    def Proveedor(self):
        self.show_frames(Proveedor)

    def Compras(self):
        self.show_frames(Compras)

    def Rendimiento(self):
        self.show_frames(Rendimiento)

    def Prestamos(self):
        self.show_frames(Prestamos)

    def Nominas(self):
        self.show_frames(Nominas)

    def Abonos(self):
        self.show_frames(Abonos)

    def Informacion(self):
        self.show_frames(Informacion)

    def EmpacadoraInicio(self):
        self.show_frames(EmpacadoraInicio)

    def EmpacadoraVentas(self):
        self.show_frames(EmpacadoraVentas)

    def EmpacadoraLotes(self):
        self.show_frames(EmpacadoraLotes)

    def EmpacadoraClientes(self):
        self.show_frames(EmpacadoraClientes)

    def EmpacadoraCobranza(self):
        self.show_frames(EmpacadoraCobranza)

    def Configuracion(self):
        if not tiene_permiso(self.usuario_actual, 'configuracion'):
            messagebox.showwarning('Acceso restringido', 'No tiene permiso para abrir Configuración.')
            return
        try:
            from modulos.configuracion.gestor_configuracion import GestorConfiguracion
            gestor = GestorConfiguracion(self)
            gestor.abrir_ventana_configuracion()
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo abrir Configuración: {e}')

    def AsistenteIA(self):
        try:
            self.limpiar_badge_jelox()
            from modulos.asistente_ia import AsistenteIA
            if not hasattr(self, '_asistente_ia'):
                self._asistente_ia = AsistenteIA(self, self.usuario_actual)
            self._asistente_ia.abrir()
        except Exception as e:
            messagebox.showerror('JELOX', f'No se pudo abrir JELOX: {e}')

    def alternar_asistente_ia(self):
        """La burbuja flotante abre JELOX o lo minimiza si ya está visible."""
        try:
            asistente = getattr(self, '_asistente_ia', None)
            ventana = getattr(asistente, 'ventana', None) if asistente else None
            if ventana and ventana.winfo_exists() and ventana.state() != 'withdrawn':
                ventana.withdraw()
                return
        except Exception:
            pass
        self.AsistenteIA()

    def obtener_iniciales_usuario(self):
        nombre = (self.usuario_actual or 'Usuario').strip()
        partes = [parte for parte in nombre.split() if parte]
        if not partes:
            return 'U'
        return ''.join(parte[0].upper() for parte in partes[:2])

    def mostrar_alert_dialog(self, titulo, mensaje, texto_confirmar, texto_cancelar, accion_confirmar):
        dialog = ctk.CTkToplevel(self)
        dialog.title(titulo)
        dialog.geometry('420x230')
        dialog.configure(fg_color=estilos.COLORS['bg_primary'])
        dialog.resizable(False, False)
        dialog.transient(self.controlador)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.controlador.winfo_x() + (self.controlador.winfo_width() // 2) - 210
        y = self.controlador.winfo_y() + (self.controlador.winfo_height() // 2) - 115
        dialog.geometry(f'420x230+{x}+{y}')

        card = ctk.CTkFrame(dialog, fg_color=estilos.COLORS['white'], corner_radius=10, border_width=1, border_color=estilos.COLORS['border'])
        card.pack(fill='both', expand=True, padx=18, pady=18)
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(family='Poppins', size=18, weight='bold'), text_color=estilos.COLORS['dark']).pack(anchor='w', padx=24, pady=(22, 8))
        ctk.CTkLabel(card, text=mensaje, font=ctk.CTkFont(family='Poppins', size=12), text_color=estilos.COLORS['dark_gray'], wraplength=340, justify='left').pack(anchor='w', padx=24)

        actions = ctk.CTkFrame(card, fg_color='transparent')
        actions.pack(side='bottom', fill='x', padx=20, pady=20)

        def confirmar():
            dialog.grab_release()
            dialog.destroy()
            accion_confirmar()

        ctk.CTkButton(actions, text=texto_cancelar, command=lambda: (dialog.grab_release(), dialog.destroy()), width=120, height=34, corner_radius=8, fg_color=estilos.COLORS['light'], hover_color=estilos.COLORS['border'], text_color=estilos.COLORS['dark_gray']).pack(side='right', padx=(8, 0))
        ctk.CTkButton(actions, text=texto_confirmar, command=confirmar, width=150, height=34, corner_radius=8, fg_color=estilos.COLORS['primary1'], hover_color=estilos.COLORS['success_dark'], text_color=estilos.COLORS['white']).pack(side='right')
        dialog.focus_force()

    def guardar_cambios_programa(self):
        self.mostrar_alert_dialog(
            'Guardar cambios',
            '¿Deseas guardar cambios o actualizar tu programa ahora?',
            'Guardar cambios',
            'Cancelar',
            lambda: messagebox.showinfo('Cambios guardados', 'Tu programa se guardó y actualizó correctamente.'),
        )

    def cerrar_sesion(self):
        def confirmar_cierre():
            try:
                from modulos.auth.seguridad import close_session
                close_session(getattr(self.controlador, 'session_id', None), 'cierre manual')
            except Exception:
                pass
            self.controlador.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

        self.mostrar_alert_dialog(
            'Cerrar sesión',
            '¿Seguro que deseas cerrar tu sesión actual? Volverás a la pantalla de inicio.',
            'Cerrar sesión',
            'Cancelar',
            confirmar_cierre,
        )

    def widgets_modernos(self):
        self.header = tk.Frame(self, bg='#06111e', highlightbackground='#14283b', highlightthickness=1)
        self.header.place(x=self.current_sidebar_w, y=0, width=self.CONTENT_W, height=self.HEADER_H)

        self.sidebar = tk.Frame(self, bg=self.MENU_BG)
        self.sidebar.place(x=0, y=0, width=self.current_sidebar_w, height=self.APP_H)

        self.content = tk.Frame(self, bg='#050f1b')
        self.content.place(x=self.current_sidebar_w, y=self.HEADER_H, width=self.CONTENT_W, height=self.MODULE_H)

        self.module_host = tk.Frame(self.content, bg='#050f1b')
        self.module_host.place(x=0, y=0, width=self.CONTENT_W, height=self.MODULE_H)

        self._crear_header()
        self._crear_sidebar()
        self._crear_boton_ia_flotante()

    def _crear_boton_ia_flotante(self):
        try:
            imagen = Image.open(resource_path('media/icons/jelox_v2.png')).convert('RGBA')
            lado = min(imagen.size)
            margen = int(lado * .09)
            imagen = imagen.crop(((imagen.width-lado)//2+margen, (imagen.height-lado)//2+margen,
                                  (imagen.width+lado)//2-margen, (imagen.height+lado)//2-margen)).resize((58, 58), Image.LANCZOS)
            mascara = Image.new('L', (58, 58), 0)
            ImageDraw.Draw(mascara).ellipse((0, 0, 57, 57), fill=255)
            imagen.putalpha(mascara)
            self.ai_float_image = ImageTk.PhotoImage(imagen)
        except Exception:
            self.ai_float_image = None

        transparente = '#ff00fe'
        self.ai_float_window = tk.Toplevel(self.controlador)
        self.ai_float_window.withdraw()
        self.ai_float_window.overrideredirect(True)
        self.ai_float_window.configure(bg=transparente)
        self.ai_float_window.transient(self.controlador)
        try:
            self.ai_float_window.wm_attributes('-transparentcolor', transparente)
        except tk.TclError:
            pass
        self.controlador.update_idletasks()
        x = self.controlador.winfo_rootx() + self.controlador.winfo_width() - 108
        y = self.controlador.winfo_rooty() + self.controlador.winfo_height() - 128
        x = max(0, min(x, self.controlador.winfo_screenwidth() - 92))
        y = max(0, min(y, self.controlador.winfo_screenheight() - 92))
        self.ai_float_window.geometry(f'92x92+{x}+{y}')

        self.ai_float_canvas = tk.Canvas(self.ai_float_window, width=92, height=92, bg=transparente,
                                         highlightthickness=0, bd=0, cursor='hand2')
        self.ai_float_canvas.pack(fill='both', expand=True)
        self.ai_halo_outer = self.ai_float_canvas.create_oval(7, 7, 85, 85, outline='#163d65', width=1)
        self.ai_halo_inner = self.ai_float_canvas.create_oval(13, 13, 79, 79, outline='#00b8ff', width=2)
        self.ai_core = self.ai_float_canvas.create_oval(16, 16, 76, 76, fill='#071426',
                                                        outline='#00c8ff', width=1)
        if self.ai_float_image:
            self.ai_icon_item = self.ai_float_canvas.create_image(46, 46, image=self.ai_float_image)
        else:
            self.ai_icon_item = self.ai_float_canvas.create_text(
                46, 46, text='J', fill='#00c8ff', font=('Poppins', 15, 'bold'))
        self._jelox_pendientes = 0
        self.ai_badge_circle = self.ai_float_canvas.create_oval(
            66, 4, 90, 28, fill='#dc2626', outline='#ffffff', width=2, state='hidden')
        self.ai_badge_text = self.ai_float_canvas.create_text(
            78, 16, text='', fill='#ffffff', font=('Poppins', 9, 'bold'), state='hidden')

        self._ai_drag = {'x': 0, 'y': 0, 'wx': 0, 'wy': 0, 'movido': False}
        def iniciar_arrastre(event):
            self._ai_drag.update(x=event.x_root, y=event.y_root,
                                 wx=self.ai_float_window.winfo_x(), wy=self.ai_float_window.winfo_y(),
                                 movido=False)
        def arrastrar(event):
            dx, dy = event.x_root-self._ai_drag['x'], event.y_root-self._ai_drag['y']
            if abs(dx) + abs(dy) > 4:
                self._ai_drag['movido'] = True
            nx, ny = self._ai_drag['wx']+dx, self._ai_drag['wy']+dy
            nx = max(0, min(nx, self.ai_float_window.winfo_screenwidth()-92))
            ny = max(0, min(ny, self.ai_float_window.winfo_screenheight()-92))
            self.ai_float_window.geometry(f'+{nx}+{ny}')
        def soltar(_event):
            if not self._ai_drag['movido']:
                self.alternar_asistente_ia()
        self.ai_float_canvas.bind('<ButtonPress-1>', iniciar_arrastre)
        self.ai_float_canvas.bind('<B1-Motion>', arrastrar)
        self.ai_float_canvas.bind('<ButtonRelease-1>', soltar)
        self._agregar_tooltip(self.ai_float_canvas, 'Abrir o minimizar JELOX')
        self.ai_float_window.deiconify()
        self.ai_float_window.lift()
        # El contenedor se construye antes de que la ventana principal termine
        # de aparecer. Volvemos a elevar la burbuja cuando Windows ya la mapeó.
        self.after(350, self._mostrar_boton_ia_flotante)
        self.controlador.bind('<Map>', lambda _e: self.after(120, self._mostrar_boton_ia_flotante), add='+')
        self.controlador.bind('<FocusIn>', lambda _e: self.after(30, self._mostrar_boton_ia_flotante), add='+')
        self._animar_boton_jelox()

    def _mostrar_boton_ia_flotante(self):
        try:
            if not self.ai_float_window.winfo_exists():
                return
            self.ai_float_window.deiconify()
            self.ai_float_window.attributes('-topmost', True)
            self.ai_float_window.lift()
        except Exception:
            pass

    def limpiar_badge_jelox(self):
        self._jelox_pendientes = 0
        if hasattr(self, 'ai_badge_circle'):
            self.ai_float_canvas.itemconfigure(self.ai_badge_circle, state='hidden')
            self.ai_float_canvas.itemconfigure(self.ai_badge_text, state='hidden')

    def notificar_respuesta_jelox(self, mensaje, inventario_actualizado=False):
        """Registra y muestra una respuesta terminada de JELOX."""
        if not self.winfo_exists():
            return
        resumen = ' '.join(str(mensaje or '').split())
        if len(resumen) > 92:
            resumen = resumen[:89].rstrip() + '...'
        self._jelox_pendientes = getattr(self, '_jelox_pendientes', 0) + 1
        if hasattr(self, 'ai_badge_circle'):
            self.ai_float_canvas.itemconfigure(self.ai_badge_text,
                                               text=str(min(self._jelox_pendientes, 99)), state='normal')
            self.ai_float_canvas.itemconfigure(self.ai_badge_circle, state='normal')
            self.ai_float_canvas.tag_raise(self.ai_badge_circle)
            self.ai_float_canvas.tag_raise(self.ai_badge_text)
        titulo = 'JELOX actualizó el inventario' if inventario_actualizado else 'Mensaje nuevo de JELOX'
        self.registrar_notificacion('mensaje', titulo, resumen or 'Tu respuesta está lista.')
        self.mostrar_toast_notificacion(
            titulo, resumen or 'Tu respuesta está lista.',
            duracion=12000, sonido=True,
            accion=self.Inventario if inventario_actualizado else self.AsistenteIA)

    def _animar_boton_jelox(self, paso=0):
        if not hasattr(self, 'ai_float_canvas') or not self.ai_float_canvas.winfo_exists():
            return
        pulso = (math.sin(paso * .16) + 1) / 2
        radio_exterior = 34 + (pulso * 7)
        radio_interior = 31 + (pulso * 3)
        centro = 46
        self.ai_float_canvas.coords(self.ai_halo_outer, centro-radio_exterior, centro-radio_exterior,
                                    centro+radio_exterior, centro+radio_exterior)
        self.ai_float_canvas.coords(self.ai_halo_inner, centro-radio_interior, centro-radio_interior,
                                    centro+radio_interior, centro+radio_interior)
        paleta = ('#12345a','#145b82','#168fbd','#00c8ff','#168fbd','#145b82')
        color = paleta[(paso // 2) % len(paleta)]
        self.ai_float_canvas.itemconfigure(self.ai_halo_outer, outline=color, width=1)
        self.ai_float_canvas.itemconfigure(self.ai_halo_inner, outline='#00d9ff', width=2)
        brillo = '#0b2038' if pulso < .5 else '#0e2947'
        self.ai_float_canvas.itemconfigure(self.ai_core, fill=brillo)
        self._jelox_anim_after = self.after(80, lambda: self._animar_boton_jelox(paso + 1))
    def _crear_sidebar(self):
        self.icon_rail = tk.Frame(self.sidebar, bg=self.MENU_BG)
        self.menu_viewport = tk.Frame(
            self.sidebar, bg=self.MENU_BG,
            highlightbackground=self.MENU_BORDER, highlightthickness=1,
        )
        self.menu_canvas = tk.Canvas(
            self.menu_viewport, bg=self.MENU_BG, bd=0,
            highlightthickness=0, yscrollincrement=24,
        )
        self.menu_panel = tk.Frame(
            self.menu_canvas, bg=self.MENU_BG, bd=0,
        )
        self.menu_canvas_window = self.menu_canvas.create_window(
            (0, 0), window=self.menu_panel, anchor='nw',
            width=self.SIDEBAR_W,
        )
        self.menu_scrollbar = ctk.CTkScrollbar(
            self.menu_viewport, orientation='vertical', width=8,
            height=max(40, self.APP_H - 8),
            command=self.menu_canvas.yview,
            fg_color='transparent', button_color=self.MENU_BORDER,
            button_hover_color=self.MENU_BLUE,
        )
        self.menu_canvas.configure(yscrollcommand=self.menu_scrollbar.set)
        self.menu_canvas.place(x=0, y=0, width=self.SIDEBAR_W - 18, height=self.APP_H)
        self.menu_viewport.place(x=0, y=0, width=self.SIDEBAR_W, height=self.APP_H)
        self.menu_panel.bind('<Configure>', self._actualizar_scroll_sidebar, add='+')
        self.bind_all('<MouseWheel>', self._scroll_sidebar_mousewheel, add='+')

        # Filete luminoso en la orilla derecha: varias capas estrechas crean
        # un halo azul suave sin convertir la linea en un bloque grueso.
        self.sidebar_glow_soft = tk.Frame(self.sidebar, bg='#0a2138', bd=0)
        self.sidebar_glow_mid = tk.Frame(self.sidebar, bg='#0b3f68', bd=0)
        self.sidebar_glow_bright = tk.Frame(self.sidebar, bg='#138ed2', bd=0)
        self.sidebar_glow_core = tk.Frame(self.sidebar, bg='#37b9ff', bd=0)
        self._posicionar_filete_sidebar(self.SIDEBAR_W)

        self.sidebar_animating = False
        self.sidebar_icon_cache = {}
        self.submenus_open = {}
        self.category_colors = {
            'INICIO': '#d7b56d',
            'COMERCIAL': '#68707d',
            'ALMACEN': '#68707d',
            'FINANZAS': '#68707d',
            'SISTEMA': '#68707d',
        }
        self.nav_defs = [
            {
                'type': 'item',
                'label': 'Inicio',
                'icon': 'home',
                'color': self.category_colors['INICIO'],
                'command': self.Inicio,
                'module': Inicio,
                'permiso': 'inicio',
            },
            {
                'type': 'section',
                'label': 'COMERCIAL',
                'color': self.category_colors['COMERCIAL'],
                'items': [
                    {'label': 'Ventas', 'icon': 'cart', 'command': self.Ventas, 'module': Ventas, 'permiso': 'ventas'},
                    {'label': 'Compras', 'icon': 'bag', 'command': self.Compras, 'module': Compras, 'permiso': 'compras'},
                    {'label': 'Pedidos', 'icon': 'truck', 'command': self.Pedidos, 'module': Pedidos, 'permiso': 'pedidos'},
                    {'label': 'Clientes', 'icon': 'user', 'command': self.Clientes, 'module': Clientes, 'permiso': 'clientes'},
                    {'label': 'Proveedores', 'icon': 'provider', 'command': self.Proveedor, 'module': Proveedor, 'permiso': 'proveedores'},
                ],
            },
            {
                'type': 'section',
                'label': 'ALMACÉN',
                'color': self.category_colors['ALMACEN'],
                'items': [
                    {'label': 'Inventario', 'icon': 'box', 'command': self.Inventario, 'module': Inventario, 'permiso': 'inventario'},
                    {'label': 'Rendimiento', 'icon': 'performance', 'command': self.Rendimiento, 'module': Rendimiento, 'permiso': 'rendimiento'},
                ],
            },
            {
                'type': 'section',
                'label': 'FINANZAS',
                'color': self.category_colors['FINANZAS'],
                'items': [
                    {'label': 'Nóminas', 'icon': 'payroll', 'command': self.Nominas, 'module': Nominas, 'permiso': 'rendimiento'},
                    {'label': 'Abonos', 'icon': 'cash', 'command': self.Abonos, 'module': Abonos, 'permiso': 'rendimiento'},
                ],
            },
            {
                'type': 'section',
                'label': 'SISTEMA',
                'color': self.category_colors['SISTEMA'],
                'items': [
                    {'label': 'Configuración', 'icon': 'gear', 'command': self.Configuracion, 'module': None, 'permiso': 'configuracion'},
                    {'label': 'Información', 'icon': 'info', 'command': self.Informacion, 'module': Informacion, 'permiso': 'informacion'},
                ],
            },
        ]
        self.nav_defs_carniceria = self.nav_defs
        self.nav_defs_empacadora = [
            {
                'type': 'item', 'label': 'Inicio', 'icon': 'home',
                'color': self.category_colors['INICIO'], 'command': self.EmpacadoraInicio,
                'module': EmpacadoraInicio, 'permiso': 'inicio',
            },
            {
                'type': 'section', 'label': 'EMPACADORA', 'color': self.category_colors['COMERCIAL'],
                'items': [
                    {'label': 'Ventas', 'icon': 'cart', 'command': self.EmpacadoraVentas,
                     'module': EmpacadoraVentas, 'permiso': 'inicio'},
                    {'label': 'Lotes y producto', 'icon': 'box', 'command': self.EmpacadoraLotes,
                     'module': EmpacadoraLotes, 'permiso': 'inicio'},
                    {'label': 'Clientes', 'icon': 'user', 'command': self.EmpacadoraClientes,
                     'module': EmpacadoraClientes, 'permiso': 'inicio'},
                    {'label': 'Cobranza', 'icon': 'cash', 'command': self.EmpacadoraCobranza,
                     'module': EmpacadoraCobranza, 'permiso': 'inicio'},
                ],
            },
        ]

        self.icon_buttons = []
        self.nav_widgets = []
        self.buttons = []
        self.button_map = {}
        self.button_items = {}
        self._render_icon_rail()
        self._render_sidebar_menu()

    def _actualizar_scroll_sidebar(self, _event=None):
        if not hasattr(self, 'menu_canvas'):
            return
        try:
            alto_contenido = max(
                int(getattr(self, '_sidebar_content_height', self.APP_H)),
                int(self.menu_panel.winfo_reqheight()),
            )
            self.menu_canvas.itemconfigure(
                self.menu_canvas_window, width=self.SIDEBAR_W,
                height=alto_contenido,
            )
            self.menu_canvas.configure(
                scrollregion=(0, 0, self.SIDEBAR_W, alto_contenido),
            )
            alto_visible = max(1, int(self.menu_canvas.winfo_height()))
            if self.sidebar_expanded:
                self.menu_scrollbar.configure(height=max(40, alto_visible - 8))
                self.menu_scrollbar.place(x=self.SIDEBAR_W - 18, y=4)
                self.menu_scrollbar.lift()
            else:
                self.menu_scrollbar.place_forget()
        except (tk.TclError, ValueError):
            pass

    def _scroll_sidebar_mousewheel(self, event):
        if not self.sidebar_expanded or not hasattr(self, 'menu_canvas'):
            return
        try:
            pointer_x = self.winfo_pointerx()
            pointer_y = self.winfo_pointery()
            left = self.sidebar.winfo_rootx()
            top = self.sidebar.winfo_rooty()
            inside = (
                left <= pointer_x < left + self.current_sidebar_w
                and top <= pointer_y < top + self.APP_H
            )
            if not inside:
                return
            direction = -1 if event.delta > 0 else 1
            self.menu_canvas.yview_scroll(direction * 3, 'units')
        except (tk.TclError, AttributeError):
            pass

    def _posicionar_filete_sidebar(self, ancho):
        """Alinea y eleva el filete luminoso con el borde visible."""
        capas = (
            (self.sidebar_glow_soft, 7, 7),
            (self.sidebar_glow_mid, 4, 4),
            (self.sidebar_glow_bright, 2, 2),
            (self.sidebar_glow_core, 1, 1),
        )
        for widget, desplazamiento, grosor in capas:
            widget.place(x=max(0, ancho - desplazamiento), y=0,
                         width=grosor, height=self.APP_H)
            widget.lift()

    def _item_permitido(self, item):
        permiso = item.get('permiso', 'inicio')
        return permiso == 'inicio' or tiene_permiso(self.usuario_actual, permiso)

    def _iter_menu_items(self, incluir_submenus=False):
        for entry in self.nav_defs:
            section_color = entry.get('color', estilos.COLORS['gold'])
            if entry.get('type') == 'item':
                entry['_section_color'] = section_color
                if self._item_permitido(entry):
                    yield entry
                continue
            for item in entry.get('items', []):
                item['_section_color'] = section_color
                if item.get('items'):
                    visibles = []
                    for sub in item['items']:
                        sub['_section_color'] = section_color
                        if self._item_permitido(sub):
                            visibles.append(sub)
                    if visibles:
                        yield item
                        if incluir_submenus:
                            for sub in visibles:
                                yield sub
                elif self._item_permitido(item):
                    yield item

    def _menu_icon(self, icon_key, size=(20, 20), color='#d7b56d'):
        color_icono = color or '#91a6b9'
        cache_key = (icon_key, size, color_icono)
        if cache_key in self.sidebar_icon_cache:
            return self.sidebar_icon_cache[cache_key]
        icon = ctk.CTkImage(light_image=crear_icono_menu(icon_key, color_icono), size=size)
        self.sidebar_icon_cache[cache_key] = icon
        return icon

    def _agregar_tooltip(self, widget, texto):
        try:
            self.tooltips.append(Tooltip(widget, texto))
        except Exception:
            pass

    def _render_icon_rail(self):
        for child in self.icon_rail.winfo_children():
            child.destroy()
        try:
            logo_color = (238, 245, 252) if self.modo_oscuro else (31, 41, 55)
            rail_logo = crear_logo_sidebar_hd(logo_color)
            self._rail_logo = ctk.CTkImage(
                light_image=rail_logo, dark_image=rail_logo, size=(42, 42)
            )
            ctk.CTkLabel(self.icon_rail, text='', image=self._rail_logo,
                         fg_color=self.MENU_BG).place(x=19, y=18)
        except Exception:
            ctk.CTkLabel(self.icon_rail, text='CO', font=ctk.CTkFont(family='Poppins', size=13, weight='bold'), text_color=estilos.COLORS['gold']).place(x=20, y=22)
        tk.Frame(self.icon_rail, bg=self.MENU_BORDER).place(x=20, y=78, width=32, height=1)
        self.icon_buttons = []
        y = 92
        for item in self._iter_menu_items(incluir_submenus=False):
            btn = ctk.CTkButton(
                self.icon_rail,
                text='',
                image=self._menu_icon(item.get('icon'), size=(24, 24), color=item.get('_section_color', estilos.COLORS['gold'])),
                command=item.get('command'),
                width=44,
                height=36,
                corner_radius=8,
                fg_color='transparent',
                hover_color=self.MENU_ACTIVE_HOVER,
                text_color=self.MENU_TEXT,
                font=ctk.CTkFont(family='Poppins', size=15, weight='bold'),
            )
            btn.place(x=14, y=y)
            self._agregar_tooltip(btn, item.get('label', ''))
            self.icon_buttons.append((item.get('module'), btn))
            y += 43
        avatar = ctk.CTkFrame(
            self.icon_rail,
            fg_color='#081a2b' if self.modo_oscuro else '#e8f3fc',
            width=42, height=42, corner_radius=21,
            border_width=1, border_color=self.MENU_BLUE,
        )
        avatar.place(x=15, y=self.APP_H - 62)
        self._rail_user_icon = ctk.CTkImage(
            light_image=crear_icono_usuario_hd('#f8fbff' if self.modo_oscuro else '#1f2937'),
            dark_image=crear_icono_usuario_hd('#f8fbff'), size=(24, 24),
        )
        ctk.CTkLabel(avatar, text='', image=self._rail_user_icon, fg_color='transparent').place(relx=0.5, rely=0.5, anchor='center')
        self._agregar_tooltip(avatar, 'Perfil de usuario')

    def _render_sidebar_menu(self):
        for widget in self.nav_widgets:
            try:
                widget.destroy()
            except Exception:
                pass
        self.nav_widgets = []
        self.buttons = []
        self.button_map = {}
        self.button_items = {}
        self.active_indicators = {}

        compact = self.APP_H < 820
        logo_size = 88 if compact else 100
        brand_y = logo_size + (16 if compact else 18)
        subtitle_y = brand_y + 27
        separator_y = subtitle_y + 25
        # La interfaz trabaja con escalado DPI de Windows. Estos pasos dejan
        # aire real entre filas y reparten el menu a lo alto de la pantalla.
        if self.APP_H < 820:
            self.sidebar_item_step, self.sidebar_item_height = 29, 27
            self.sidebar_section_step = 20
            self.sidebar_section_gap = 5
            self.sidebar_divider_gap = 8
        elif self.APP_H < 860:
            self.sidebar_item_step, self.sidebar_item_height = 30, 28
            self.sidebar_section_step = 21
            self.sidebar_section_gap = 5
            self.sidebar_divider_gap = 8
        else:
            self.sidebar_item_step, self.sidebar_item_height = 31, 29
            self.sidebar_section_step = 22
            self.sidebar_section_gap = 6
            self.sidebar_divider_gap = 9

        try:
            logo_color = (238, 245, 252) if self.modo_oscuro else (31, 41, 55)
            sidebar_logo = crear_logo_sidebar_hd(logo_color)
            self._sidebar_logo = ctk.CTkImage(
                light_image=sidebar_logo,
                dark_image=sidebar_logo,
                size=(logo_size, logo_size),
            )
            logo = ctk.CTkLabel(self.menu_panel, text='', image=self._sidebar_logo)
            logo.configure(fg_color=self.MENU_BG)
            logo.place(relx=0.5, y=9, anchor='n')
            self.nav_widgets.append(logo)
        except Exception:
            pass
        nombre_area = 'Empacadora' if self.modo_negocio == 'Empacadora' else 'Sistema administrativo'
        brand = ctk.CTkLabel(
            self.menu_panel, text='Carnes Luévanos',
            font=ctk.CTkFont(family='Poppins', size=14, weight='bold'),
            text_color='#f4f8fc' if self.modo_oscuro else '#172033', fg_color='transparent',
            anchor='center', width=self.SIDEBAR_W - 26,
        )
        brand.place(x=13, y=brand_y)
        self.nav_widgets.append(brand)
        subtitle = ctk.CTkLabel(
            self.menu_panel, text=nombre_area,
            font=ctk.CTkFont(family='Poppins', size=10),
            text_color=self.MENU_MUTED, fg_color='transparent',
            anchor='center', width=self.SIDEBAR_W - 26,
        )
        subtitle.place(x=13, y=subtitle_y)
        self.nav_widgets.append(subtitle)
        sep = tk.Frame(self.menu_panel, bg=self.MENU_BORDER)
        sep.place(x=18, y=separator_y, width=self.SIDEBAR_W - 42, height=1)
        self.nav_widgets.append(sep)

        y = separator_y + 12
        for entry in self.nav_defs:
            if entry.get('type') == 'item':
                if self._item_permitido(entry):
                    entry['_section_color'] = entry.get('color', estilos.COLORS['gold'])
                    y = self._crear_item_menu(entry, y, destacado=True)
                y += self.sidebar_section_gap
                continue

            visibles = []
            for item in entry.get('items', []):
                if item.get('items'):
                    if any(self._item_permitido(sub) for sub in item['items']):
                        visibles.append(item)
                elif self._item_permitido(item):
                    visibles.append(item)
            if not visibles:
                continue

            section_label = ctk.CTkLabel(
                self.menu_panel, text=entry.get('label', ''), height=16,
                font=ctk.CTkFont(family='Poppins', size=10, weight='bold'),
                text_color=self.MENU_MUTED, fg_color='transparent',
            )
            section_label.place(x=20, y=y)
            self.nav_widgets.append(section_label)
            y += self.sidebar_section_step
            for item in visibles:
                item['_section_color'] = entry.get('color', estilos.COLORS['gold'])
                y = self._crear_item_menu(item, y)
                submenu = item.get('submenu')
                if submenu and self.submenus_open.get(submenu):
                    for sub in item.get('items', []):
                        if self._item_permitido(sub):
                            sub['_section_color'] = entry.get('color', estilos.COLORS['gold'])
                            y = self._crear_item_menu(sub, y, indentado=True)
            divider = tk.Frame(self.menu_panel, bg=self.MENU_BORDER)
            divider.place(x=18, y=y + 1, width=self.SIDEBAR_W - 42, height=1)
            self.nav_widgets.append(divider)
            y += self.sidebar_divider_gap

        # El bloque de sesión forma parte del contenido desplazable. Así nunca
        # se monta sobre las opciones cuando la pantalla tiene poca altura.
        session_y = y + 12
        session_divider = tk.Frame(self.menu_panel, bg=self.MENU_BORDER)
        session_divider.place(x=18, y=session_y, width=self.SIDEBAR_W - 42, height=1)
        self.nav_widgets.append(session_divider)
        session_label = ctk.CTkLabel(
            self.menu_panel, text='SESIÓN', height=16,
            font=ctk.CTkFont(family='Poppins', size=10, weight='bold'),
            text_color=self.MENU_MUTED, fg_color='transparent',
        )
        session_label.place(x=20, y=session_y + 7)
        self.nav_widgets.append(session_label)
        exit_button = ctk.CTkButton(
            self.menu_panel, text='Cerrar sesión',
            image=self._menu_icon(
                'exit', size=(24, 24),
                color='#edf6ff' if self.modo_oscuro else '#344054',
            ),
            compound='left', anchor='w', command=self.cerrar_sesion,
            width=self.SIDEBAR_W - 36, height=34, corner_radius=7,
            fg_color='transparent', hover_color=self.MENU_ACTIVE_HOVER,
            text_color=self.MENU_TEXT,
            font=ctk.CTkFont(family='Poppins', size=12), cursor='hand2',
        )
        exit_button.place(x=18, y=session_y + 25)
        self.sidebar_exit_button = exit_button
        self.nav_widgets.append(exit_button)
        self._agregar_tooltip(exit_button, 'Cerrar la sesión actual')

        user = ctk.CTkFrame(
            self.menu_panel, fg_color=self.MENU_SURFACE, corner_radius=9,
            border_width=1, border_color=self.MENU_BORDER,
            width=self.SIDEBAR_W - 36, height=64,
        )
        user.place(x=18, y=session_y + 64)
        self.sidebar_user_card = user
        self.nav_widgets.append(user)
        avatar_glow = ctk.CTkFrame(
            user, fg_color='#082b47' if self.modo_oscuro else '#dcefff',
            width=48, height=48, corner_radius=24,
            border_width=2, border_color=self.MENU_BLUE,
        )
        avatar_glow.place(x=7, y=8)
        avatar = ctk.CTkFrame(
            avatar_glow, fg_color='#0a1727' if self.modo_oscuro else '#ffffff', width=38, height=38,
            corner_radius=19, border_width=1, border_color='#159dff',
        )
        avatar.place(x=5, y=5)
        avatar_label = ctk.CTkLabel(avatar, text=self.obtener_iniciales_usuario(), font=ctk.CTkFont(family='Poppins', size=12, weight='bold'), text_color='#ffffff' if self.modo_oscuro else '#172033')
        avatar_label.place(relx=0.5, rely=0.5, anchor='center')
        datos_usuario = self._datos_usuario_navbar()
        rol = str(datos_usuario.get('rol') or '').casefold()
        nombre_visible = 'Administrador' if rol in {'super', 'admin', 'administrador'} else datos_usuario.get('nombre', self.usuario_actual or 'Usuario')
        user_name = ctk.CTkLabel(user, text=nombre_visible, font=ctk.CTkFont(family='Poppins', size=11, weight='bold'), text_color='#f4f7fb' if self.modo_oscuro else '#172033')
        user_name.place(x=64, y=10)
        sesion_activa = bool(getattr(self.controlador, 'session_id', None))
        estado_texto = 'Sesión activa' if sesion_activa else 'Sesión local'
        user_status = ctk.CTkLabel(user, text=estado_texto, font=ctk.CTkFont(family='Poppins', size=9), text_color=self.MENU_MUTED)
        user_status.place(x=64, y=32)
        status_dot = ctk.CTkFrame(user, width=7, height=7, corner_radius=4,
                                  fg_color='#2eb872' if sesion_activa else '#f3a51b')
        status_dot.place(x=129, y=42)
        chevron = ctk.CTkLabel(user, text='›', width=18, text_color='#7f93a6',
                               font=ctk.CTkFont(family='Poppins', size=20))
        chevron.place(x=self.SIDEBAR_W - 72, y=17)
        for widget in (user, avatar_glow, avatar, avatar_label, user_name, user_status, status_dot, chevron):
            widget.bind('<Button-1>', lambda _event: self.mostrar_perfil())
        self._sidebar_content_height = session_y + 140
        self.menu_panel.configure(
            width=self.SIDEBAR_W, height=self._sidebar_content_height,
        )
        self.after_idle(self._actualizar_scroll_sidebar)

    def _crear_item_menu(self, item, y, destacado=False, indentado=False):
        label = item.get('label', '')
        submenu = item.get('submenu')
        icon_color = '#edf6ff' if self.modo_oscuro else '#344054'
        icon = self._menu_icon(item.get('icon'), size=(21, 21), color=icon_color)
        prefix = '      ' if indentado else ''
        suffix = '  v' if submenu and self.submenus_open.get(submenu) else ('  >' if submenu else '')
        btn = ctk.CTkButton(
            self.menu_panel,
            text=f'{prefix}{label}{suffix}',
            image=icon,
            compound='left',
            command=item.get('command'),
            width=self.SIDEBAR_W - (54 if indentado else 36),
            height=getattr(self, 'sidebar_item_height', 26),
            corner_radius=6,
            anchor='w',
            fg_color='transparent',
            hover_color=self.MENU_ACTIVE_HOVER,
            border_width=0,
            border_color=self.MENU_BLUE,
            text_color=self.MENU_TEXT,
            font=ctk.CTkFont(family='Poppins', size=11 if indentado else 12, weight='bold' if destacado else 'normal'),
            cursor='hand2',
        )
        btn.place(x=30 if indentado else 18, y=y)
        self._agregar_tooltip(btn, label)
        self.nav_widgets.append(btn)
        self.buttons.append(btn)
        self.button_items[btn] = item
        module = item.get('module')
        if module is not None:
            self.button_map[module] = btn
            indicator_height = max(
                10, getattr(self, 'sidebar_item_height', 22) - 6
            )
            indicator = ctk.CTkFrame(
                self.menu_panel, fg_color=self.MENU_BLUE,
                width=3, height=indicator_height,
                corner_radius=2, border_width=0,
            )
            indicator.place(x=17, y=y + 2)
            indicator.place_forget()
            self.active_indicators[module] = (
                indicator, y + 2, indicator_height
            )
            self.nav_widgets.append(indicator)
        return y + getattr(self, 'sidebar_item_step', 31)
    def _toggle_submenu(self, submenu):
        self.submenus_open[submenu] = not self.submenus_open.get(submenu, False)
        self._animar_submenu_render()

    def _animar_submenu_render(self, paso=0):
        if paso == 0:
            for widget in self.nav_widgets:
                try:
                    widget.configure(fg_color=self.MENU_BG)
                except Exception:
                    pass
        if paso < 3:
            self.after(22, lambda: self._animar_submenu_render(paso + 1))
            return
        self._render_sidebar_menu()
        if self.active_container:
            self.actualizar_boton_activo(self.active_container)

    def _crear_tarjeta_creativa(self):
        card_y = min(max(430, self.APP_H - 250), self.APP_H - 188)
        card = ctk.CTkFrame(
            self.menu_panel,
            width=self.SIDEBAR_W - 36,
            height=104,
            corner_radius=8,
            fg_color=estilos.COLORS['white'],
            border_width=1,
            border_color=estilos.COLORS['border'],
        )
        card.place(x=18, y=card_y)
        self.nav_widgets.append(card)

        title = ctk.CTkLabel(
            card,
            text='Idea rápida',
            font=ctk.CTkFont(family='Poppins', size=12, weight='bold'),
            text_color=estilos.COLORS['wine'],
        )
        title.place(x=14, y=12)
        self.nav_widgets.append(title)

        ideas = [
            'Oferta del día: paquete familiar con descuento.',
            'Promoción: compra 3 kg y recibe marinador gratis.',
            'Recordatorio: revisar cortes con baja existencia.',
            'Sugerencia: destacar productos premium al iniciar.',
        ]
        idx = datetime_label().count(':') % len(ideas)
        self.idea_creativa = tk.StringVar(value=ideas[idx])
        idea = ctk.CTkLabel(
            card,
            textvariable=self.idea_creativa,
            font=ctk.CTkFont(family='Poppins', size=10),
            text_color=estilos.COLORS['dark_gray'],
            wraplength=self.SIDEBAR_W - 70,
            justify='left',
        )
        idea.place(x=14, y=36)
        self.nav_widgets.append(idea)

        def nueva_idea():
            actual = self.idea_creativa.get()
            siguiente = ideas[(ideas.index(actual) + 1) % len(ideas)] if actual in ideas else ideas[0]
            self.idea_creativa.set(siguiente)

        btn = ctk.CTkButton(
            card,
            text='Cambiar idea',
            command=nueva_idea,
            width=self.SIDEBAR_W - 66,
            height=24,
            corner_radius=7,
            fg_color=estilos.COLORS['primary_light'],
            hover_color=estilos.COLORS['bg_hover'],
            text_color=estilos.COLORS['wine'],
            font=ctk.CTkFont(family='Poppins', size=10, weight='bold'),
        )
        btn.place(x=14, y=72)
        self.nav_widgets.append(btn)

    def _toggle_section(self, section):
        self.section_open[section] = not self.section_open.get(section, False)
        self._render_sidebar_menu()
        if self.active_container:
            self.actualizar_boton_activo(self.active_container)

    def crear_boton_sidebar(self, text, command, y_pos):
        btn = ctk.CTkButton(
            self.menu_panel,
            text=text,
            command=command,
            width=self.SIDEBAR_W - 56,
            height=28,
            corner_radius=7,
            anchor='w',
            fg_color='transparent',
            hover_color=estilos.COLORS['primary_light'],
            text_color=estilos.COLORS['dark'],
            font=ctk.CTkFont(family='Poppins', size=11),
            cursor='hand2',
        )
        btn.place(x=34, y=y_pos)
        return btn

    def _cambiar_unidad_negocio(self, unidad):
        nueva = 'Empacadora' if str(unidad).strip().lower().startswith('emp') else 'Sistema administrativo'
        self.modo_negocio = nueva
        if nueva == 'Empacadora':
            self.modulos_permitidos = self.modulos_empacadora
            self.nav_defs = self.nav_defs_empacadora
            destino = EmpacadoraInicio
        else:
            self.modulos_permitidos = self.modulos_carniceria
            self.nav_defs = self.nav_defs_carniceria
            destino = Inicio
        self._render_icon_rail()
        self._render_sidebar_menu()
        self.show_frames(destino)
        try:
            self.unidad_var.set(nueva)
        except Exception:
            pass

    def _crear_header(self):
        self.titulo_actual = tk.Label(self.header, text='', bg='#06111e', fg='#f4f8fc', font=('Poppins', 1), anchor='w')
        self.subtitulo_actual = tk.Label(self.header, text='', bg='#06111e', fg='#94a6b8', font=('Poppins', 1), anchor='w')

        self.menu_icon_img = ctk.CTkImage(light_image=crear_icono_hamburguesa('#f7fbff'), dark_image=crear_icono_hamburguesa('#f7fbff'), size=(30, 30))
        self.menu_toggle_btn = ctk.CTkButton(self.header, text='', image=self.menu_icon_img, command=self.alternar_sidebar, width=48, height=44, corner_radius=10, fg_color='transparent', hover_color='#102a40')
        self.menu_toggle_btn.place(x=16, y=18)
        self._agregar_tooltip(self.menu_toggle_btn, 'Menu')

        # El navbar queda limpio: el selector de negocio vive fuera de esta
        # barra y el buscador conserva una posición global estable.
        self.unidad_var = tk.StringVar(value='')
        self.unidad_selector = None
        self.unidad_divider = None

        self.search_var = tk.StringVar()
        search_x = self._posicion_x_buscador()
        self.search_entry = ctk.CTkEntry(self.header, textvariable=self.search_var, placeholder_text='Buscar en el sistema...', width=470, height=44, corner_radius=22, border_width=1, border_color='#142b40', fg_color='#091725', text_color='#f4f8fc', placeholder_text_color='#718397', font=ctk.CTkFont(family='Poppins', size=11))
        self.search_entry.place(x=search_x, y=17)
        self.search_entry.bind('<Return>', lambda _event: self.buscar_modulo())
        search_icon = crear_icono_busqueda('#94a6b8')
        self.search_icon_img = ctk.CTkImage(light_image=search_icon, dark_image=search_icon, size=(20, 20))
        self.search_btn = ctk.CTkButton(self.header, text='', image=self.search_icon_img, command=self.buscar_modulo, width=34, height=34, corner_radius=17, fg_color='transparent', hover_color='#102a40')
        self.search_btn.place(x=search_x + 424, y=22)
        self._agregar_tooltip(self.search_btn, 'Buscar')

        save_icon = crear_icono_menu('save', '#dce7f1')
        self.save_tool_icon_img = ctk.CTkImage(light_image=save_icon, dark_image=save_icon, size=(19, 19))
        self.doc_btn = ctk.CTkButton(self.header, text='Guardar', image=self.save_tool_icon_img, compound='left', command=self.guardar_cambios_programa, width=106, height=36, corner_radius=6, fg_color='transparent', hover_color='#102a40', text_color='#f4f8fc', font=ctk.CTkFont(family='Poppins', size=12, weight='bold'))
        self.doc_btn.place(x=self.CONTENT_W - 486, y=21)
        self._agregar_tooltip(self.doc_btn, 'Guardar')

        sun_icon = crear_icono_tema(False, '#f7fbff')
        self.info_tool_icon_img = ctk.CTkImage(light_image=sun_icon, dark_image=sun_icon, size=(20, 20))
        self.info_btn = ctk.CTkButton(self.header, text='', image=self.info_tool_icon_img, command=lambda: self.establecer_modo_oscuro(False), width=36, height=36, corner_radius=18, fg_color='transparent', hover_color='#102a40', border_width=0)
        self.info_btn.place(x=self.CONTENT_W - 372, y=22)
        self._agregar_tooltip(self.info_btn, 'Modo claro')
        moon_icon = crear_icono_tema(True, '#159dff')
        self.config_tool_icon_img = ctk.CTkImage(light_image=moon_icon, dark_image=moon_icon, size=(20, 20))
        self.config_btn = ctk.CTkButton(self.header, text='', image=self.config_tool_icon_img, command=lambda: self.establecer_modo_oscuro(True), width=36, height=36, corner_radius=18, fg_color='transparent', hover_color='#102a40', border_width=0)
        self.config_btn.place(x=self.CONTENT_W - 300, y=22)
        self._agregar_tooltip(self.config_btn, 'Tema oscuro')
        noti_icon = crear_icono_campana('#f7fbff')
        self.msg_icon_img = ctk.CTkImage(light_image=noti_icon, dark_image=noti_icon, size=(24, 24))
        self.msg_btn = ctk.CTkButton(self.header, text='', image=self.msg_icon_img, command=self.mostrar_mensajes, width=40, height=36, corner_radius=18, fg_color='transparent', hover_color='#102a40', border_width=0)
        self.msg_btn.place(x=self.CONTENT_W - 228, y=21)
        self._agregar_tooltip(self.msg_btn, 'Notificaciones')
        self.msg_badge = ctk.CTkLabel(self.header, text='', width=18, height=16, corner_radius=8, fg_color='#dc2626', text_color=estilos.COLORS['white'], font=ctk.CTkFont(family='Poppins', size=8, weight='bold'))
        self.msg_badge.place(x=self.CONTENT_W - 208, y=7)
        self.msg_badge.place_forget()

        self._header_user_vector = ctk.CTkImage(
            light_image=crear_icono_usuario_hd('#f7fbff'),
            dark_image=crear_icono_usuario_hd('#f7fbff'), size=(25, 25),
        )
        self.profile_card = ctk.CTkLabel(
            self.header, text='', image=self._header_user_vector, width=42, height=42, corner_radius=21,
            fg_color='#0b4c7a', text_color=estilos.COLORS['white'],
            font=ctk.CTkFont(family='Poppins', size=12, weight='bold'), cursor='hand2')
        self.profile_card.place(x=self.CONTENT_W - 71, y=18)
        self.header_avatar_label = self.profile_card
        self._actualizar_avatar_header()
        self.profile_card.bind('<Button-1>', lambda _event: self.mostrar_perfil())
        self._agregar_tooltip(self.profile_card, 'Perfil de usuario')

        self.date_range_var = tk.StringVar(value='Hoy')
        self.reloj_var = tk.StringVar(value='')
        self._reloj_after = None
        self.bind('<Destroy>', self._cancelar_reloj, add='+')
        self.actualizar_reloj()
        self.preparar_notificaciones()
        usuario_notificacion = self.usuario_actual or 'Usuario'
        self.registrar_notificacion('mensaje', 'Nuevo inicio de sesion', f'{usuario_notificacion} inicio sesion en el sistema')
        self.after(700, lambda: self.mostrar_toast_notificacion('Sesion iniciada', f'Bienvenido, {usuario_notificacion}'))
        self.actualizar_notificaciones_navbar()

    def _actualizar_header_tema(self, oscuro):
        """Repinta el navbar y regenera sus iconos HD para el tema activo."""
        header_bg = '#06111e' if oscuro else '#ffffff'
        header_border = '#14283b' if oscuro else '#dce3eb'
        surface = '#091725' if oscuro else '#f4f7fb'
        hover = '#102a40' if oscuro else '#e8f1f8'
        text = '#f7fbff' if oscuro else '#1f2937'
        muted = '#8fa2b5' if oscuro else '#667085'
        border = '#142b40' if oscuro else '#d7e0e9'
        bright = '#f7fbff' if oscuro else '#263445'

        self.header.tk.call(
            self.header._w, 'configure', '-background', header_bg,
            '-highlightbackground', header_border,
        )
        self.titulo_actual.configure(bg=header_bg, fg=text)
        self.subtitulo_actual.configure(bg=header_bg, fg=muted)

        menu_icon = crear_icono_hamburguesa(bright)
        self.menu_icon_img = ctk.CTkImage(
            light_image=menu_icon, dark_image=menu_icon, size=(30, 30)
        )
        self.menu_toggle_btn.configure(
            image=self.menu_icon_img, bg_color=header_bg,
            fg_color='transparent', hover_color=hover,
        )

        search_icon = crear_icono_busqueda(muted)
        self.search_icon_img = ctk.CTkImage(
            light_image=search_icon, dark_image=search_icon, size=(20, 20)
        )
        self.search_entry.configure(
            bg_color=header_bg, fg_color=surface,
            border_color=border, text_color=text,
            placeholder_text_color=muted,
        )
        self.search_btn.configure(
            image=self.search_icon_img, bg_color=surface,
            fg_color='transparent', hover_color=hover,
        )

        save_icon = crear_icono_menu('save', bright)
        self.save_tool_icon_img = ctk.CTkImage(
            light_image=save_icon, dark_image=save_icon, size=(19, 19)
        )
        self.doc_btn.configure(
            image=self.save_tool_icon_img, bg_color=header_bg, text_color=text,
            fg_color='transparent', hover_color=hover,
        )

        sun_color = self.MENU_BLUE if not oscuro else bright
        moon_color = self.MENU_BLUE if oscuro else muted
        sun_icon = crear_icono_tema(False, sun_color)
        moon_icon = crear_icono_tema(True, moon_color)
        self.info_tool_icon_img = ctk.CTkImage(
            light_image=sun_icon, dark_image=sun_icon, size=(21, 21)
        )
        self.config_tool_icon_img = ctk.CTkImage(
            light_image=moon_icon, dark_image=moon_icon, size=(21, 21)
        )
        self.info_btn.configure(
            image=self.info_tool_icon_img, bg_color=header_bg,
            fg_color='#e2f2ff' if not oscuro else 'transparent',
            hover_color=hover,
        )
        self.config_btn.configure(
            image=self.config_tool_icon_img, bg_color=header_bg,
            fg_color='#0b3657' if oscuro else 'transparent',
            hover_color=hover,
        )

        noti_icon = crear_icono_campana(bright)
        self.msg_icon_img = ctk.CTkImage(
            light_image=noti_icon, dark_image=noti_icon, size=(24, 24)
        )
        self.msg_btn.configure(
            image=self.msg_icon_img, bg_color=header_bg,
            fg_color='transparent', hover_color=hover,
        )
        self.profile_card.configure(
            bg_color=header_bg,
            fg_color='#0b3657' if oscuro else '#e2f2ff',
            text_color='#ffffff' if oscuro else '#172033',
        )
        self.msg_badge.configure(bg_color=header_bg)

    @staticmethod
    def _color_modo_oscuro(value):
        if isinstance(value, (tuple, list)):
            converted = [Container._color_modo_oscuro(item) for item in value]
            return tuple(converted) if isinstance(value, tuple) else converted
        if not isinstance(value, str):
            return value
        palette = {
            # Superficies del diseño aprobado.
            'white': '#091725', '#fff': '#091725', '#ffffff': '#091725',
            '#f5f5f5': '#050f1b', '#f5f6f8': '#050f1b', '#f8f8f7': '#050f1b',
            '#fbfbfa': '#071522', '#fcfbf9': '#071522', '#faf9f7': '#071522',
            '#f8fafd': '#0b1d2d', '#f7f8fa': '#0b1d2d',
            '#f7f0e5': '#0a3659', '#f6efe4': '#0b2943', '#f4eee4': '#0b2943',
            '#f2eee7': '#0b2943', '#eef0f2': '#10263a', '#eef0f4': '#10263a',
            '#eef2ff': '#10263a', '#dfe2e6': '#18334b', '#f0f1f3': '#0d2031',
            '#f1f3f4': '#0d2031', '#f1f3f5': '#0d2031',

            # Bordes y estados de interacción.
            '#e7e4df': '#173149', '#e3e6ea': '#173149', '#e5e7eb': '#173149',
            '#dedbd5': '#173149', '#ded9d0': '#173149', '#d9dde3': '#173149',
            '#e2ded7': '#173149', '#ece9e4': '#173149', '#eee7dc': '#173149',
            '#e1ddd6': '#173149', '#cfc9bf': '#28445c', '#c2e7ff': '#123e64',
            '#f6dede': '#123e64', '#e8eaed': '#1b344b',

            # Texto principal y secundario.
            '#20242c': '#f4f7fb', '#20242a': '#f4f7fb', '#202124': '#f4f7fb',
            '#111827': '#f4f7fb', '#343941': '#e7edf4', '#343942': '#e7edf4',
            '#3c424b': '#d8e1ea', '#454b55': '#ced8e3', '#4b515b': '#c1ccd8',
            '#505762': '#b7c4d1', '#5f6671': '#a9b7c5', '#5f6368': '#a9b7c5',
            '#667085': '#94a6b8', '#68707c': '#94a6b8', '#68707d': '#94a6b8',
            '#737985': '#94a6b8', '#858b94': '#94a6b8', '#8b9099': '#94a6b8',
            '#8b9098': '#94a6b8', '#a6a9ae': '#8294a6',

            # Acentos azul, verde y ámbar.
            '#b38a47': '#159dff', '#8b682f': '#087de0', '#ead9b9': '#0d3655',
            '#d7b56d': '#159dff', '#8f070c': '#087ff5', '#6f0509': '#0067d8',
            '#18964b': '#18c96e', '#11743a': '#0da85a', '#e69500': '#f3a51b',
        }
        return palette.get(value.lower(), value)

    @staticmethod
    def _color_modo_claro(value):
        if isinstance(value, (tuple, list)):
            converted = [Container._color_modo_claro(item) for item in value]
            return tuple(converted) if isinstance(value, tuple) else converted
        if not isinstance(value, str):
            return value
        palette = {
            # Superficies que pudieron quedar guardadas desde modo oscuro.
            '#091725': '#ffffff', '#050f1b': '#f5f6f8', '#071522': '#faf9f7',
            '#0b1d2d': '#f7f8fa', '#0a3659': '#f7f0e5', '#0b2943': '#f6efe4',
            '#10263a': '#eef0f2', '#18334b': '#dfe2e6', '#0d2031': '#f0f1f3',

            # Bordes y seleccionados.
            '#173149': '#e3e6ea', '#28445c': '#cfc9bf', '#123e64': '#f6dede',
            '#1b344b': '#e8eaed',

            # Texto.
            '#f4f7fb': '#20242a', '#e7edf4': '#343941', '#d8e1ea': '#3c424b',
            '#ced8e3': '#454b55', '#c1ccd8': '#4b515b', '#b7c4d1': '#505762',
            '#a9b7c5': '#68707c', '#94a6b8': '#68707c', '#8294a6': '#8b9098',

            # Acentos oscuros usados por el tema nocturno.
            '#159dff': '#b38a47', '#087de0': '#8b682f', '#087ff5': '#8f070c',
            '#0067d8': '#6f0509', '#0d3655': '#ead9b9', '#18c96e': '#18964b',
            '#0da85a': '#11743a', '#f3a51b': '#e69500',
        }
        return palette.get(value.lower(), value)

    def _aplicar_tema_widget(self, widget, oscuro, incluir_hijos=True):
        ctk_options = (
            'fg_color', 'text_color', 'hover_color', 'border_color',
            'placeholder_text_color', 'button_color', 'button_hover_color',
            'dropdown_fg_color', 'dropdown_hover_color', 'dropdown_text_color',
            'progress_color', 'scrollbar_button_color', 'scrollbar_button_hover_color',
        )
        tk_options = ('background', 'foreground', 'highlightbackground', 'highlightcolor', 'insertbackground')
        options = ctk_options if isinstance(widget, ctk.CTkBaseClass) else tk_options
        saved = self._theme_originals.setdefault(widget, {})
        for option in options:
            try:
                if option not in saved:
                    saved[option] = widget.cget(option)
                original = saved[option]
                value = self._color_modo_oscuro(original) if oscuro else self._color_modo_claro(original)
                widget.configure(**{option: value})
            except Exception:
                continue
        if not oscuro:
            try:
                if isinstance(widget, ctk.CTkEntry):
                    widget.configure(
                        fg_color='#ffffff',
                        border_color='#e3e6ea',
                        text_color='#20242a',
                        placeholder_text_color='#68707c',
                    )
                elif isinstance(widget, ctk.CTkComboBox):
                    widget.configure(
                        fg_color='#ffffff',
                        border_color='#e3e6ea',
                        text_color='#20242a',
                        dropdown_fg_color='#ffffff',
                        dropdown_text_color='#20242a',
                        dropdown_hover_color='#f6dede',
                    )
                elif isinstance(widget, ctk.CTkLabel):
                    current_fg = str(widget.cget('fg_color')).lower()
                    if current_fg in {'#091725', '#050f1b', '#071522', '#0b1d2d'}:
                        widget.configure(fg_color='transparent')
                elif isinstance(widget, ctk.CTkScrollableFrame):
                    widget.configure(
                        fg_color='#f5f6f8',
                        scrollbar_button_color='#dfe2e6',
                        scrollbar_button_hover_color='#cfd5dc',
                    )
                elif isinstance(widget, ctk.CTkFrame):
                    current_fg = str(widget.cget('fg_color')).lower()
                    if current_fg in {'#091725', '#050f1b', '#071522', '#0b1d2d'}:
                        widget.configure(fg_color='#ffffff')
                elif isinstance(widget, tk.Canvas):
                    current_bg = str(widget.cget('background')).lower()
                    if current_bg in {'#091725', '#050f1b', '#071522', '#0b1d2d'}:
                        widget.configure(bg='#ffffff')
            except Exception:
                pass
        if incluir_hijos:
            for child in widget.winfo_children():
                self._aplicar_tema_widget(child, oscuro)

    def _aplicar_tema_progresivo(self, oscuro=True):
        """Recolorea la interfaz por lotes sin bloquear ni vaciar el menú."""
        self._theme_job_version = getattr(self, '_theme_job_version', 0) + 1
        version = self._theme_job_version
        pendientes = [self.controlador]

        def aplicar_lote():
            if version != getattr(self, '_theme_job_version', 0) or not self.winfo_exists():
                return
            procesados = 0
            while pendientes and procesados < 4:
                widget = pendientes.pop()
                if widget in (
                    self.header, self.menu_panel, self.menu_viewport,
                    self.menu_canvas, self.icon_rail,
                ) or isinstance(widget, Inicio):
                    # El menú usa una paleta fija y no debe ser reconfigurado por
                    # CustomTkinter después de destruir/recrear sus controles.
                    procesados += 1
                    continue
                try:
                    hijos = list(widget.winfo_children())
                except (tk.TclError, AttributeError):
                    hijos = []
                pendientes.extend(hijos)
                self._aplicar_tema_widget(widget, oscuro, incluir_hijos=False)
                procesados += 1
            if pendientes:
                self.after(1, aplicar_lote)

        self.after_idle(aplicar_lote)

    def establecer_modo_oscuro(self, oscuro, forzar=False):
        """Aplica claro u oscuro a navegación, dashboard, módulos y tablas."""
        oscuro = bool(oscuro)
        if self.modo_oscuro == oscuro and not forzar:
            return
        self.modo_oscuro = oscuro
        ctk.set_appearance_mode('dark' if oscuro else 'light')
        self._configurar_paleta_navegacion(oscuro)

        app_bg = '#050f1b' if oscuro else '#f4f7fb'
        self.configure(bg=app_bg)
        self.sidebar.tk.call(
            self.sidebar._w, 'configure', '-background', self.MENU_BG
        )
        self.menu_panel.tk.call(
            self.menu_panel._w, 'configure', '-background', self.MENU_BG,
            '-highlightbackground', self.MENU_BORDER,
        )
        self.menu_viewport.configure(
            bg=self.MENU_BG, highlightbackground=self.MENU_BORDER,
        )
        self.menu_canvas.configure(bg=self.MENU_BG)
        self.menu_scrollbar.configure(
            button_color=self.MENU_BORDER,
            button_hover_color=self.MENU_BLUE,
        )
        self.icon_rail.tk.call(
            self.icon_rail._w, 'configure', '-background', self.MENU_BG
        )
        self.content.tk.call(self.content._w, 'configure', '-background', app_bg)
        self.module_host.tk.call(
            self.module_host._w, 'configure', '-background', app_bg
        )
        glow_colors = (
            ('#0a2138', '#0b3f68', '#138ed2', '#37b9ff')
            if oscuro else
            ('#e7f3fb', '#b9def5', '#4aa9df', '#168fd3')
        )
        for widget, color in zip((
            self.sidebar_glow_soft, self.sidebar_glow_mid,
            self.sidebar_glow_bright, self.sidebar_glow_core,
        ), glow_colors):
            widget.configure(bg=color)

        self.sidebar_icon_cache.clear()
        self._render_icon_rail()
        self._render_sidebar_menu()
        if self.active_container:
            self.actualizar_boton_activo(self.active_container)
        self._actualizar_header_tema(oscuro)

        try:
            self.controlador.configure(bg=app_bg)
        except Exception:
            pass
        for frame in self.frames.values():
            aplicar = getattr(frame, 'aplicar_tema', None)
            if callable(aplicar):
                aplicar(oscuro)

        # Fuerza el primer repintado antes de procesar el resto de los módulos.
        self.update_idletasks()
        self._aplicar_tema_progresivo(oscuro)
        self._configurar_tablas_tema(oscuro)

    def alternar_modo_oscuro(self):
        self.establecer_modo_oscuro(not self.modo_oscuro)

    def _configurar_tablas_tema(self, oscuro=True):
        """Unifica tablas y encabezados ttk con la paleta moderna del sistema."""
        style = ttk.Style(self)
        if oscuro:
            table_bg = '#ffffff'
            heading_bg = '#f0f1f3'
            text = '#20242a'
            heading_text = '#20242a'
            selected = '#0a4774'
            border = '#c9d3df'
            input_bg = '#ffffff'
            input_text = '#20242a'
            arrow = '#20242a'
        else:
            table_bg = '#ffffff'
            heading_bg = '#f0f1f3'
            text = '#20242a'
            heading_text = '#20242a'
            selected = '#dbeeff'
            border = '#e3e6ea'
            input_bg = '#ffffff'
            input_text = '#20242a'
            arrow = '#20242a'

        table_styles = (
            'Treeview', 'Ventas.Treeview', 'Compras.Treeview', 'Clientes.Treeview',
            'Pedidos.Treeview', 'Prestamos.Treeview', 'Nominas.Treeview',
            'Abonos.Treeview', 'Proveedores.Treeview', 'Inventario.Treeview',
            'Users.Treeview', 'Historial.Treeview', 'Empacadora.Treeview',
            'Modern.Treeview',
        )
        for style_name in table_styles:
            style.configure(
                style_name,
                background=table_bg,
                fieldbackground=table_bg,
                foreground=text,
                bordercolor=border,
                lightcolor=border,
                darkcolor=border,
            )
            style.map(
                style_name,
                background=[('selected', selected)],
                foreground=[('selected', '#ffffff' if oscuro else text)],
            )
            style.configure(
                f'{style_name}.Heading',
                background=heading_bg,
                foreground=heading_text,
                bordercolor=border,
                lightcolor=border,
                darkcolor=border,
                relief='flat',
            )
            style.map(
                f'{style_name}.Heading',
                background=[('active', heading_bg), ('pressed', heading_bg)],
                foreground=[('active', heading_text), ('pressed', heading_text)],
            )

        style.configure(
            'TCombobox', fieldbackground=input_bg, background=input_bg,
            foreground=input_text, arrowcolor=arrow, bordercolor=border,
        )
        style.configure(
            'TEntry', fieldbackground=input_bg, background=input_bg,
            foreground=input_text, insertcolor=input_text, bordercolor=border,
        )
        for input_style in ('Modern.TEntry', 'Modern.TCombobox'):
            style.configure(
                input_style,
                fieldbackground=input_bg,
                background=input_bg,
                foreground=input_text,
                insertcolor=input_text,
                arrowcolor=arrow,
                bordercolor=border,
                lightcolor=border,
                darkcolor=border,
            )
            style.map(
                input_style,
                fieldbackground=[('readonly', input_bg), ('focus', input_bg)],
                foreground=[('readonly', input_text), ('focus', input_text)],
                selectbackground=[('focus', selected)],
                selectforeground=[('focus', input_text)],
            )
    def _panel_navbar(self, titulo, ancho=330, alto=300):
        panel = ctk.CTkToplevel(self)
        panel.title(titulo)
        panel.geometry(f'{ancho}x{alto}+{self.controlador.winfo_x() + self.controlador.winfo_width() - ancho - 80}+{self.controlador.winfo_y() + 84}')
        panel.configure(fg_color=estilos.COLORS['white'])
        panel.resizable(False, False)
        panel.transient(self.controlador)
        panel.grab_set()
        ctk.CTkLabel(panel, text=titulo, font=ctk.CTkFont(family='Poppins', size=15, weight='bold'), text_color=estilos.COLORS['primary1']).pack(anchor='w', padx=18, pady=(16, 8))
        return panel

    def _datos_usuario_navbar(self):
        import sqlite3
        datos = {'id': None, 'nombre': self.usuario_actual or 'Usuario', 'username': self.usuario_actual or '',
                 'rol': 'usuario', 'estado': 'activo', 'numero': 'Sin asignar', 'sucursal': 'Sin asignar',
                 'ultimo': 'Sin registro', 'foto': None, 'sesiones': 0}
        try:
            with sqlite3.connect('database.db') as conn:
                cols = {r[1] for r in conn.execute('PRAGMA table_info(usuarios)').fetchall()}
                foto = 'foto_perfil' if 'foto_perfil' in cols else 'NULL'
                row = conn.execute(f'''SELECT id,COALESCE(nombre,username),username,COALESCE(rol,'usuario'),
                    COALESCE(estado,'activo'),COALESCE(numero_empleado,'Sin asignar'),COALESCE(sucursal,'Sin asignar'),
                    COALESCE(ultimo_acceso,'Sin registro'),{foto} FROM usuarios WHERE username=?''', (self.usuario_actual,)).fetchone()
                if row:
                    for clave, valor in zip(('id','nombre','username','rol','estado','numero','sucursal','ultimo','foto'), row): datos[clave] = valor
                    try:
                        datos['sesiones'] = conn.execute('SELECT COUNT(*) FROM sesiones_usuario WHERE usuario_id=? AND cerrada IS NULL', (row[0],)).fetchone()[0]
                    except sqlite3.Error: pass
        except sqlite3.Error:
            pass
        return datos

    def _imagen_perfil(self, ruta, tamano):
        if not ruta or not os.path.isfile(ruta): return None
        try:
            img = ImageOps.exif_transpose(Image.open(ruta)).convert('RGBA')
            lado = min(img.size); x = (img.width-lado)//2; y = (img.height-lado)//2
            img = img.crop((x,y,x+lado,y+lado)).resize((tamano,tamano), Image.LANCZOS)
            mascara = Image.new('L', (tamano,tamano), 0); ImageDraw.Draw(mascara).ellipse((0,0,tamano-1,tamano-1), fill=255)
            img.putalpha(mascara)
            return ctk.CTkImage(light_image=img, dark_image=img, size=(tamano,tamano))
        except Exception:
            return None

    def _actualizar_avatar_header(self):
        if not hasattr(self, 'header_avatar_label'): return
        imagen = self._imagen_perfil(self._datos_usuario_navbar().get('foto'), 40)
        self._header_profile_image = imagen
        self.header_avatar_label.configure(
            image=imagen or getattr(self, '_header_user_vector', None),
            text='',
            fg_color='transparent' if imagen else '#0b4c7a')

    def _cambiar_foto_navbar(self, panel=None):
        from tkinter import filedialog
        import sqlite3, shutil, uuid
        ruta = filedialog.askopenfilename(parent=panel or self, title='Seleccionar foto de perfil',
                                          filetypes=[('Imagenes','*.png *.jpg *.jpeg *.webp'),('Todos','*.*')])
        if not ruta: return
        datos = self._datos_usuario_navbar()
        if not datos['id']: return
        carpeta = os.path.abspath(os.path.join('media','perfiles')); os.makedirs(carpeta, exist_ok=True)
        destino = os.path.join(carpeta, f"usuario_{datos['id']}_{uuid.uuid4().hex[:8]}{os.path.splitext(ruta)[1].lower() or '.jpg'}")
        shutil.copy2(ruta, destino)
        with sqlite3.connect('database.db') as conn: conn.execute('UPDATE usuarios SET foto_perfil=? WHERE id=?', (destino, datos['id']))
        self._actualizar_avatar_header()
        if panel and panel.winfo_exists(): panel.destroy(); self.mostrar_perfil()

    def _cambiar_password_navbar(self, panel):
        from tkinter import simpledialog, messagebox
        from modulos.auth.seguridad import change_password
        actual = simpledialog.askstring('Cambiar contraseña', 'Contraseña actual:', show='*', parent=panel)
        if not actual: return
        nueva = simpledialog.askstring('Cambiar contraseña', 'Nueva contraseña (minimo 10 caracteres):', show='*', parent=panel)
        if not nueva: return
        confirmar = simpledialog.askstring('Cambiar contraseña', 'Repite la nueva contraseña:', show='*', parent=panel)
        if nueva != confirmar:
            messagebox.showwarning('No coincide', 'Las contraseñas nuevas no coinciden.', parent=panel); return
        try: correcto = change_password(self._datos_usuario_navbar()['id'], actual, nueva)
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror('No se pudo cambiar', str(exc), parent=panel); return
        if not correcto:
            messagebox.showerror('Contraseña incorrecta', 'La contraseña actual no es correcta.', parent=panel); return
        messagebox.showinfo('Contraseña actualizada', 'Se cerraron las sesiones abiertas por seguridad.', parent=panel)
        panel.destroy(); self.cerrar_sesion()

    def mostrar_perfil(self):
        datos = self._datos_usuario_navbar()
        panel = self._panel_navbar('Mi cuenta', 410, 510)
        cab = ctk.CTkFrame(panel, fg_color='#f5f6f8', corner_radius=14, height=112, border_width=1, border_color='#e3e6ea')
        cab.pack(fill='x', padx=16, pady=(5, 12)); cab.pack_propagate(False)
        imagen = self._imagen_perfil(datos['foto'], 66); self._panel_profile_image = imagen
        avatar_marco = ctk.CTkFrame(cab, width=74, height=74, corner_radius=37, fg_color='#8f070c')
        avatar_marco.place(x=16, y=19)
        avatar_marco.pack_propagate(False)
        avatar_foto = ctk.CTkLabel(avatar_marco, text='' if imagen else self.obtener_iniciales_usuario(), image=imagen,
                                   width=66, height=66, corner_radius=33, fg_color='transparent',
                                   text_color='white', font=ctk.CTkFont('Poppins',16,'bold'))
        avatar_foto.place(relx=.5, rely=.5, anchor='center')
        ctk.CTkLabel(cab, text=datos['nombre'], font=ctk.CTkFont('Poppins',15,'bold'), text_color='#20242a').place(x=106,y=19)
        ctk.CTkLabel(cab, text=f"@{datos['username']} · {datos['rol'].title()}", font=ctk.CTkFont('Poppins',10), text_color='#68707c').place(x=106,y=47)
        ctk.CTkLabel(cab, text=f"● {datos['estado'].title()}", font=ctk.CTkFont('Poppins',9,'bold'), text_color='#23834a').place(x=106,y=73)
        resumen = ctk.CTkFrame(panel, fg_color='transparent'); resumen.pack(fill='x', padx=16)
        for i,(titulo,valor) in enumerate((('Empleado',datos['numero']),('Sucursal',datos['sucursal']),('Sesiones abiertas',str(datos['sesiones'])),('Ultimo acceso',str(datos['ultimo']).replace('T',' ')[:16]))):
            tarjeta=ctk.CTkFrame(resumen,fg_color='#ffffff',corner_radius=10,height=64,border_width=1,border_color='#e3e6ea')
            tarjeta.grid(row=i//2,column=i%2,sticky='ew',padx=(0 if i%2==0 else 5,5 if i%2==0 else 0),pady=5)
            resumen.grid_columnconfigure(i%2,weight=1)
            ctk.CTkLabel(tarjeta,text=titulo,font=ctk.CTkFont('Poppins',9),text_color='#68707c').place(x=12,y=9)
            ctk.CTkLabel(tarjeta,text=str(valor),font=ctk.CTkFont('Poppins',10,'bold'),text_color='#20242a').place(x=12,y=32)
        botones=ctk.CTkFrame(panel,fg_color='transparent'); botones.pack(fill='x',padx=16,pady=(12,0))
        ctk.CTkButton(botones,text='Cambiar foto',command=lambda:self._cambiar_foto_navbar(panel),height=36,corner_radius=8,fg_color='#343941',hover_color='#20242a').pack(fill='x',pady=3)
        ctk.CTkButton(botones,text='Cambiar contraseña',command=lambda:self._cambiar_password_navbar(panel),height=36,corner_radius=8,fg_color='#ffffff',border_width=1,border_color='#d9dde3',text_color='#343941',hover_color='#f1f3f5').pack(fill='x',pady=3)
        ctk.CTkButton(botones,text='Administrar usuarios y configuracion',command=lambda:(panel.destroy(),self.Configuracion()),height=36,corner_radius=8,fg_color='#ffffff',border_width=1,border_color='#d9dde3',text_color='#343941',hover_color='#f1f3f5').pack(fill='x',pady=3)
        ctk.CTkButton(botones,text='Cerrar sesion',command=lambda:(panel.destroy(),self.cerrar_sesion()),height=36,corner_radius=8,fg_color='#8f070c',hover_color='#71070a').pack(fill='x',pady=(8,3))

    def mostrar_mensajes(self):
        panel = self._panel_navbar('Notificaciones', 390, 360)
        mensajes = self.obtener_notificaciones(None, 10)
        self.marcar_notificaciones_leidas('mensaje')
        self.marcar_notificaciones_leidas('alerta')
        self.msg_row_icon_img = ctk.CTkImage(light_image=crear_icono_campana(estilos.COLORS['wine']), size=(20, 20))
        try:
            icono_jelox = Image.open(resource_path('media/icons/jelox_v2.png')).convert('RGBA')
            lado = min(icono_jelox.size)
            icono_jelox = icono_jelox.crop(((icono_jelox.width-lado)//2, (icono_jelox.height-lado)//2,
                                            (icono_jelox.width+lado)//2, (icono_jelox.height+lado)//2))
            icono_jelox = ImageOps.fit(icono_jelox, (24, 24), method=Image.LANCZOS)
            mascara = Image.new('L', (24, 24), 0)
            ImageDraw.Draw(mascara).ellipse((0, 0, 23, 23), fill=255)
            icono_jelox.putalpha(mascara)
            self.jelox_row_icon_img = ctk.CTkImage(light_image=icono_jelox, dark_image=icono_jelox, size=(24, 24))
        except Exception:
            self.jelox_row_icon_img = self.msg_row_icon_img
        if not mensajes:
            mensajes = [('Sistema al dia', 'No hay mensajes pendientes', '', '')]
        for titulo, detalle, fecha, hora in mensajes:
            fila = ctk.CTkFrame(panel, fg_color=estilos.COLORS['bg_primary'], corner_radius=10, height=64)
            fila.pack(fill='x', padx=14, pady=5)
            icono_fila = self.jelox_row_icon_img if 'JELOX' in titulo.upper() else self.msg_row_icon_img
            ctk.CTkLabel(fila, text='', image=icono_fila).place(x=14, y=20)
            ctk.CTkLabel(fila, text=titulo, font=ctk.CTkFont(family='Poppins', size=12, weight='bold'), text_color=estilos.COLORS['dark']).place(x=46, y=10)
            ctk.CTkLabel(fila, text=detalle, font=ctk.CTkFont(family='Poppins', size=10), text_color=estilos.COLORS['gray'], wraplength=285, justify='left').place(x=46, y=31)
            if fecha:
                ctk.CTkLabel(fila, text=hora, font=ctk.CTkFont(family='Poppins', size=9), text_color=estilos.COLORS['dark_gray']).place(x=318, y=12)
            self._hacer_notificacion_navegable(
                fila, panel, self._accion_para_notificacion(titulo, detalle))
        ctk.CTkButton(panel, text='Cerrar', command=lambda: (panel.grab_release(), panel.destroy()), fg_color=estilos.COLORS['wine'], hover_color=estilos.COLORS['primary_dark1']).pack(pady=10)

    def mostrar_alertas(self):
        panel = self._panel_navbar('Centro de alertas', 390, 390)
        alertas = self.obtener_notificaciones('alerta', 10)
        self.marcar_notificaciones_leidas('alerta')
        if not alertas:
            alertas = [('Todo en orden', 'No hay alertas activas por ahora', '', '')]
        for titulo, detalle, fecha, hora in alertas:
            fila = ctk.CTkFrame(panel, fg_color=estilos.COLORS['white'], corner_radius=10, height=58, border_width=1, border_color=estilos.COLORS['border'])
            fila.pack(fill='x', padx=14, pady=5)
            self.alert_row_icon_img = ctk.CTkImage(light_image=crear_icono_campana(estilos.COLORS['gold']), size=(18, 18))
            ctk.CTkLabel(fila, text='', image=self.alert_row_icon_img).place(x=14, y=17)
            ctk.CTkLabel(fila, text=titulo, font=ctk.CTkFont(family='Poppins', size=11, weight='bold'), text_color=estilos.COLORS['dark']).place(x=48, y=8)
            ctk.CTkLabel(fila, text=detalle, font=ctk.CTkFont(family='Poppins', size=9), text_color=estilos.COLORS['gray'], wraplength=285, justify='left').place(x=48, y=28)
            self._hacer_notificacion_navegable(
                fila, panel, self._accion_para_notificacion(titulo, detalle))
        ctk.CTkButton(panel, text='Cerrar', command=lambda: panel.destroy(),
                      fg_color=estilos.COLORS['wine'],
                      hover_color=estilos.COLORS['primary_dark1']).pack(pady=8)

    def _hacer_notificacion_navegable(self, fila, panel, accion):
        if not accion:
            return

        def abrir(_event=None):
            try:
                panel.grab_release()
            except Exception:
                pass
            try:
                panel.destroy()
            finally:
                self.after(0, accion)

        def enlazar(widget):
            try:
                widget.configure(cursor='hand2')
                widget.bind('<Button-1>', abrir, add='+')
            except Exception:
                pass
            for hijo in widget.winfo_children():
                enlazar(hijo)

        enlazar(fila)

    def _reproducir_sonido_jelox(self):
        """Genera una firma sonora corta sin depender de archivos externos."""
        try:
            import winsound
            for frecuencia, duracion in ((660, 75), (880, 90), (1175, 135)):
                winsound.Beep(frecuencia, duracion)
        except Exception:
            try:
                self.bell()
            except Exception:
                pass

    def _accion_para_notificacion(self, titulo, mensaje=''):
        texto = f'{titulo} {mensaje}'.casefold()
        rutas = (
            (('inventario', 'stock', 'existencia'), self.Inventario),
            (('venta', 'folio'), self.Ventas),
            (('compra', 'proveedor'), self.Compras),
            (('cliente',), self.Clientes),
            (('pedido',), self.Pedidos),
            (('abono', 'cobranza'), self.Abonos),
        )
        for palabras, accion in rutas:
            if any(palabra in texto for palabra in palabras):
                return accion
        if 'jelox' in texto:
            return self.AsistenteIA
        return None

    def mostrar_toast_notificacion(self, titulo, mensaje, duracion=8000, sonido=False, accion=None):
        toast = None
        try:
            # CTkToplevel puede fallar al aplicar transparencia en Windows y
            # dejar una ventana gris 200x200 sin contenido. Tk Toplevel es
            # estable para esta notificación breve.
            toast = tk.Toplevel(self)
            toast.overrideredirect(True)
            transparente = '#fefefe'
            toast.configure(bg=transparente)
            try:
                toast.wm_attributes('-transparentcolor', transparente)
            except tk.TclError:
                pass
            ancho = 320
            partes = str(mensaje or '').splitlines() or ['']
            lineas = sum(max(1, math.ceil(len(parte) / 39)) for parte in partes)
            alto = min(182, max(86, 72 + max(0, lineas - 1) * 15))
            raiz_x = self.controlador.winfo_rootx()
            raiz_y = self.controlador.winfo_rooty()
            x = raiz_x + self.controlador.winfo_width() - ancho - 34
            y_final = raiz_y + 6
            y_inicial = y_final - alto - 12
            toast.geometry(f'{ancho}x{alto}+{x}+{y_inicial}')
            toast.attributes('-topmost', True)
            card = ctk.CTkFrame(toast, width=ancho-4, height=alto-4, corner_radius=18,
                                fg_color='#fff8f5', border_width=1, border_color='#ead8d1')
            card.place(x=2, y=2)
            try:
                icono = Image.open(resource_path('media/icons/jelox_v2.png')).convert('RGBA')
                lado = min(icono.size)
                margen = int(lado * .09)
                icono = icono.crop(((icono.width-lado)//2+margen, (icono.height-lado)//2+margen,
                                    (icono.width+lado)//2-margen, (icono.height+lado)//2-margen))
                icono = ImageOps.fit(icono, (26, 26), method=Image.LANCZOS)
                mascara = Image.new('L', (26, 26), 0)
                ImageDraw.Draw(mascara).ellipse((0, 0, 25, 25), fill=255)
                icono.putalpha(mascara)
                toast._jelox_icono = ctk.CTkImage(light_image=icono, dark_image=icono, size=(26, 26))
            except Exception:
                toast._jelox_icono = None
            etiqueta_icono = ctk.CTkLabel(
                card, text='' if toast._jelox_icono else 'J', image=toast._jelox_icono,
                width=28, height=28, corner_radius=14, fg_color='transparent',
                font=ctk.CTkFont(family='Poppins', size=12, weight='bold'), text_color='#00c8ff')
            etiqueta_icono.place(x=14, y=17)
            etiqueta_titulo = ctk.CTkLabel(
                card, text=titulo, font=ctk.CTkFont(family='Poppins', size=13, weight='bold'),
                text_color=estilos.COLORS['dark'])
            etiqueta_titulo.place(x=58, y=14)
            etiqueta_mensaje = ctk.CTkLabel(
                card, text=mensaje, font=ctk.CTkFont(family='Poppins', size=10),
                text_color=estilos.COLORS['gray'], wraplength=232, justify='left', anchor='nw')
            etiqueta_mensaje.place(x=58, y=39)

            accion = accion or self._accion_para_notificacion(titulo, mensaje)
            if accion:
                def abrir_modulo(_event=None):
                    try:
                        toast.destroy()
                    finally:
                        self.after(0, accion)
                for widget in (toast, card, etiqueta_icono, etiqueta_titulo, etiqueta_mensaje):
                    widget.configure(cursor='hand2')
                    widget.bind('<Button-1>', abrir_modulo, add='+')

            if sonido:
                threading.Thread(target=self._reproducir_sonido_jelox, daemon=True).start()

            toast.update_idletasks()

            def deslizar_hacia(destino, paso, al_terminar=None):
                if not toast.winfo_exists():
                    return
                actual = toast.winfo_y()
                if (paso > 0 and actual >= destino) or (paso < 0 and actual <= destino):
                    toast.geometry(f'+{x}+{destino}')
                    if al_terminar:
                        al_terminar()
                    return
                siguiente = min(destino, actual + paso) if paso > 0 else max(destino, actual + paso)
                toast.geometry(f'+{x}+{siguiente}')
                toast.after(14, lambda: deslizar_hacia(destino, paso, al_terminar))

            def programar_salida():
                toast.after(max(1000, int(duracion)),
                            lambda: deslizar_hacia(y_inicial, -8, toast.destroy))

            deslizar_hacia(y_final, 8, programar_salida)
        except Exception:
            if toast is not None:
                try:
                    toast.destroy()
                except Exception:
                    pass
    def preparar_notificaciones(self):
        import sqlite3
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS notificaciones_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    leida INTEGER DEFAULT 0,
                    clave TEXT UNIQUE
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f'No se pudieron preparar notificaciones: {e}')
        self._inventario_snapshot = self.obtener_snapshot_inventario()

    def registrar_notificacion(self, tipo, titulo, mensaje, clave=None):
        import sqlite3
        from datetime import datetime
        try:
            ahora = datetime.now()
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS notificaciones_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    leida INTEGER DEFAULT 0,
                    clave TEXT UNIQUE
                )
            ''')
            if clave:
                cur.execute('''INSERT OR IGNORE INTO notificaciones_sistema (tipo, titulo, mensaje, fecha, hora, clave) VALUES (?, ?, ?, ?, ?, ?)''', (tipo, titulo, mensaje, ahora.strftime('%d/%m/%Y'), ahora.strftime('%H:%M'), clave))
            else:
                cur.execute('''INSERT INTO notificaciones_sistema (tipo, titulo, mensaje, fecha, hora) VALUES (?, ?, ?, ?, ?)''', (tipo, titulo, mensaje, ahora.strftime('%d/%m/%Y'), ahora.strftime('%H:%M')))
            conn.commit()
            conn.close()
            if hasattr(self, 'msg_badge'):
                self.actualizar_badges_notificaciones()
        except Exception as e:
            print(f'No se pudo registrar notificacion: {e}')

    def obtener_notificaciones(self, tipo=None, limite=8):
        import sqlite3
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            if tipo:
                cur.execute('SELECT titulo, mensaje, fecha, hora FROM notificaciones_sistema WHERE tipo = ? ORDER BY id DESC LIMIT ?', (tipo, limite))
            else:
                cur.execute('SELECT titulo, mensaje, fecha, hora FROM notificaciones_sistema ORDER BY id DESC LIMIT ?', (limite,))
            rows = cur.fetchall()
            conn.close()
            return rows
        except Exception:
            return []

    def marcar_notificaciones_leidas(self, tipo):
        import sqlite3
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('UPDATE notificaciones_sistema SET leida = 1 WHERE tipo = ?', (tipo,))
            conn.commit()
            conn.close()
            self.actualizar_badges_notificaciones()
        except Exception:
            pass

    def contar_notificaciones_no_leidas(self, tipo):
        import sqlite3
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM notificaciones_sistema WHERE tipo = ? AND COALESCE(leida, 0) = 0', (tipo,))
            total = cur.fetchone()[0] or 0
            conn.close()
            return total
        except Exception:
            return 0

    def obtener_snapshot_inventario(self):
        import sqlite3
        snapshot = {}
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            for tabla, nombre_col in [('articulos', 'articulo'), ('productos', 'nombre')]:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
                if not cur.fetchone():
                    continue
                cols = [row[1] for row in cur.execute(f'PRAGMA table_info({tabla})')]
                if 'stock' not in cols:
                    continue
                codigo_col = 'codigo' if 'codigo' in cols else nombre_col
                nombre = nombre_col if nombre_col in cols else codigo_col
                cur.execute(f'SELECT COALESCE({codigo_col}, {nombre}), COALESCE({nombre}, {codigo_col}), COALESCE(stock, 0) FROM {tabla}')
                for codigo, nombre_producto, stock in cur.fetchall():
                    snapshot[f'{tabla}:{codigo}'] = (str(nombre_producto), int(stock or 0))
            conn.close()
        except Exception:
            pass
        return snapshot

    def revisar_alertas_inventario(self):
        actual = self.obtener_snapshot_inventario()
        anterior = getattr(self, '_inventario_snapshot', {})
        for clave, (nombre, stock) in actual.items():
            if clave in anterior and anterior[clave][1] != stock:
                antes = anterior[clave][1]
                mensaje = f'{nombre}: stock {antes} -> {stock}'
                self.registrar_notificacion('mensaje', 'JELOX actualizó el inventario', mensaje, f'inv-change-{clave}-{stock}')
                self.mostrar_toast_notificacion(
                    'JELOX actualizó el inventario', mensaje, duracion=12000, sonido=True,
                    accion=self.Inventario)
            if stock <= 5:
                self.registrar_notificacion('alerta', 'Stock bajo', f'{nombre} tiene {stock} unidades disponibles', f'low-stock-{clave}-{stock}')
        self._inventario_snapshot = actual

    def actualizar_badges_notificaciones(self):
        alertas = self.contar_notificaciones_no_leidas('alerta')
        mensajes = self.contar_notificaciones_no_leidas('mensaje')
        if hasattr(self, 'msg_btn') and hasattr(self, 'msg_icon_img'):
            self.msg_btn.configure(text='', image=self.msg_icon_img)
        if hasattr(self, 'msg_badge'):
            total_notificaciones = mensajes + alertas
            if total_notificaciones:
                self.msg_badge.configure(text=str(min(total_notificaciones, 99)))
                self.msg_badge.place(x=self.CONTENT_W - 208, y=7)
                self.msg_badge.lift()
            else:
                self.msg_badge.place_forget()

    def actualizar_notificaciones_navbar(self):
        try:
            if not self.winfo_exists():
                return
            self.revisar_alertas_inventario()
            self.actualizar_badges_notificaciones()
            self.after(12000, self.actualizar_notificaciones_navbar)
        except Exception as e:
            print(f'Error actualizando notificaciones: {e}')

    def _normalizar_busqueda(self, texto):
        texto = str(texto or '').strip().lower()
        return ''.join(
            char for char in unicodedata.normalize('NFD', texto)
            if unicodedata.category(char) != 'Mn'
        )

    def buscar_modulo(self):
        termino = self._normalizar_busqueda(self.search_var.get())
        if not termino:
            return

        opciones = list(self._iter_menu_items(incluir_submenus=True))
        opciones.append({
            'label': 'Configuracion',
            'command': self.Configuracion,
            'permiso': 'configuracion',
        })
        opciones.append({
            'label': 'Informacion',
            'command': self.Informacion,
            'permiso': 'informacion',
        })

        for item in opciones:
            label = self._normalizar_busqueda(item.get('label', ''))
            permiso = item.get('permiso', 'inicio')
            command = item.get('command')
            if not callable(command) or termino not in label:
                continue
            if permiso != 'inicio' and not tiene_permiso(self.usuario_actual, permiso):
                messagebox.showwarning('Acceso restringido', 'No tiene permiso para abrir este modulo.')
                return
            command()
            try:
                self.search_var.set('')
                self.search_entry.focus_set()
            except Exception:
                pass
            return

        messagebox.showinfo('Busqueda', 'No encontre un modulo con ese nombre.')

    def actualizar_reloj(self):
        from datetime import datetime
        try:
            if not self.winfo_exists():
                return
            self.reloj_var.set(datetime.now().strftime('%d/%m/%Y  %I:%M %p'))
            self._reloj_after = self.after(30000, self.actualizar_reloj)
        except Exception:
            pass

    def _cancelar_reloj(self, _event=None):
        try:
            if getattr(self, '_reloj_after', None):
                self.after_cancel(self._reloj_after)
                self._reloj_after = None
        except Exception:
            pass
    def alternar_sidebar(self):
        if getattr(self, 'sidebar_animating', False):
            return
        self.sidebar_expanded = not self.sidebar_expanded
        destino = self.SIDEBAR_W if self.sidebar_expanded else 72
        if self.sidebar_expanded:
            self.icon_rail.place_forget()
            self.menu_viewport.place(x=0, y=0, width=self.SIDEBAR_W, height=self.APP_H)
        else:
            self.menu_viewport.place_forget()
            self.icon_rail.place(x=0, y=0, width=72, height=self.APP_H)
        # El cambio es inmediato para que los módulos pesados no dejen la
        # interfaz detenida a mitad de la animación.
        self.current_sidebar_w = destino
        self.aplicar_layout_sidebar()
        self.after_idle(self._ajustar_modulo_activo)
        self.after(50, self._ajustar_modulo_activo)

    def _animar_sidebar(self, destino):
        self.sidebar_animating = True
        actual = int(self.current_sidebar_w)
        if actual == destino:
            self.sidebar_animating = False
            self.aplicar_layout_sidebar()
            self.after_idle(self._ajustar_modulo_activo)
            self.after(60, self._ajustar_modulo_activo)
            return
        paso = 18 if destino > actual else -18
        siguiente = actual + paso
        if (paso > 0 and siguiente > destino) or (paso < 0 and siguiente < destino):
            siguiente = destino
        self.current_sidebar_w = siguiente
        self.aplicar_layout_sidebar(animando=True)
        self.after(12, lambda: self._animar_sidebar(destino))

    def aplicar_layout_sidebar(self, animando=False):
        if not animando:
            self.current_sidebar_w = self.SIDEBAR_W if self.sidebar_expanded else 72
        self.CONTENT_W = self.APP_W - self.current_sidebar_w
        self.sidebar.place_configure(x=0, y=0, width=self.current_sidebar_w, height=self.APP_H)
        if hasattr(self, 'sidebar_glow_core'):
            self._posicionar_filete_sidebar(self.current_sidebar_w)
        self.header.place_configure(x=self.current_sidebar_w, y=0, width=self.CONTENT_W, height=self.HEADER_H)
        self.content.place_configure(x=self.current_sidebar_w, y=self.HEADER_H, width=self.CONTENT_W, height=self.MODULE_H)
        self.module_host.place_configure(width=self.CONTENT_W, height=self.MODULE_H)
        if not animando:
            if self.sidebar_expanded:
                self.icon_rail.place_forget()
                self.menu_viewport.place(
                    x=0, y=0, width=self.SIDEBAR_W, height=self.APP_H,
                )
                self.menu_canvas.place_configure(
                    x=0, y=0, width=self.SIDEBAR_W - 18, height=self.APP_H,
                )
                self.menu_canvas.itemconfigure(
                    self.menu_canvas_window, width=self.SIDEBAR_W,
                )
                self._actualizar_scroll_sidebar()
            else:
                self.menu_viewport.place_forget()
                self.icon_rail.place(x=0, y=0, width=72, height=self.APP_H)
        for clase, frame in self.frames.items():
            try:
                if animando and clase != self.active_container:
                    continue
                if clase == self.active_container:
                    frame.place_configure(x=0, y=0, width=self.CONTENT_W, height=self.MODULE_H)
                else:
                    frame.configure(width=self.CONTENT_W, height=self.MODULE_H)
                ajustar = getattr(frame, 'ajustar_layout', None)
                if callable(ajustar) and not animando:
                    ajustar(self.CONTENT_W, self.MODULE_H)
            except Exception:
                pass
        self.reacomodar_header()

    def _ajustar_modulo_activo(self):
        """Asienta el ancho del módulo después de expandir/contraer el menú."""
        try:
            frame = self.frames.get(self.active_container)
            if frame is None or not frame.winfo_exists():
                return
            frame.place_configure(x=0, y=0, width=self.CONTENT_W, height=self.MODULE_H)
            frame.update_idletasks()
            ajustar = getattr(frame, 'ajustar_layout', None)
            if callable(ajustar):
                ajustar(self.CONTENT_W, self.MODULE_H)
        except (tk.TclError, AttributeError):
            pass

    def _posicion_x_buscador(self):
        """Mantiene el buscador adelantado a la izquierda y sin saltos."""
        ancho_buscador = 470
        x_global = max(0, (self.APP_W - ancho_buscador) // 2 - 140)
        x_local = x_global - int(self.current_sidebar_w)
        # Mantiene aire respecto al menú y al botón Guardar en ventanas menores.
        limite_derecho = max(90, self.CONTENT_W - 982)
        return max(90, min(x_local, limite_derecho))

    def reacomodar_header(self):
        search_x = self._posicion_x_buscador()
        if hasattr(self, 'search_entry'):
            self.search_entry.place_configure(x=search_x)
        if hasattr(self, 'search_btn'):
            self.search_btn.place_configure(x=search_x + 424, y=22)
        if hasattr(self, 'doc_btn'):
            self.doc_btn.place_configure(x=self.CONTENT_W - 486, y=21)
        if hasattr(self, 'info_btn'):
            self.info_btn.place_configure(x=self.CONTENT_W - 372, y=22)
        if hasattr(self, 'config_btn'):
            self.config_btn.place_configure(x=self.CONTENT_W - 300, y=22)
        if hasattr(self, 'msg_btn'):
            self.msg_btn.place_configure(x=self.CONTENT_W - 228, y=21)
        if hasattr(self, 'msg_badge') and self.msg_badge.winfo_ismapped():
            self.msg_badge.place_configure(x=self.CONTENT_W - 208, y=7)
        if hasattr(self, 'profile_card'):
            self.profile_card.place_configure(x=self.CONTENT_W - 72, y=18)
        if hasattr(self, 'ai_float_canvas'):
            self.ai_float_canvas.place_configure(relx=1.0, rely=1.0, x=-8, y=-8, anchor='se')
            self.ai_float_canvas.tk.call('raise', self.ai_float_canvas._w)
    def actualizar_boton_activo(self, container):
        self.active_container = container
        self.active_button = None

        for btn in self.buttons:
            item = getattr(self, 'button_items', {}).get(btn, {})
            btn.configure(
                fg_color='transparent', text_color=self.MENU_TEXT,
                hover_color=self.MENU_ACTIVE_HOVER,
                border_width=0,
                image=self._menu_icon(
                    item.get('icon'), size=(21, 21),
                    color='#edf6ff' if self.modo_oscuro else '#344054',
                ),
            )

        for indicator, _y, _height in getattr(self, 'active_indicators', {}).values():
            indicator.place_forget()

        for module, icon_btn in getattr(self, 'icon_buttons', []):
            icon_btn.configure(fg_color='transparent')
            if module == container:
                icon_btn.configure(fg_color=self.MENU_ACTIVE, text_color=self.MENU_BLUE)

        if container in self.button_map:
            active_btn = self.button_map[container]
            active_item = getattr(self, 'button_items', {}).get(active_btn, {})
            active_btn.configure(
                fg_color=self.MENU_ACTIVE, hover_color=self.MENU_ACTIVE_HOVER,
                text_color='#f4f8fc' if self.modo_oscuro else '#075985',
                border_width=1, border_color=self.MENU_BLUE,
                image=self._menu_icon(
                    active_item.get('icon'), size=(24, 24), color=self.MENU_BLUE
                ),
            )
            indicator_data = self.active_indicators.get(container)
            if indicator_data:
                indicator, indicator_y, indicator_height = indicator_data
                indicator.place(x=17, y=indicator_y)
                indicator.lift()
            self.active_button = active_btn

def datetime_label():
    from datetime import datetime
    return 'Fecha: ' + datetime.now().strftime('%d/%m/%Y')














