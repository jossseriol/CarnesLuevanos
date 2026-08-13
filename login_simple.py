import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk
import sqlite3
import math
import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageTk

from modulos.utils.estilos_modernos import estilos
from modulos.utils.utils import resource_path

ctk.set_appearance_mode('light')
ctk.set_default_color_theme('blue')

_splash_mostrado = False
USUARIO_ACTUAL = None
SESION_ACTUAL = None


def _database_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "database.db"
    return Path(__file__).resolve().parent / "database.db"


DB_PATH = _database_path()


def cargar_logo_emblema(size=156):
    """Prepara el logo como emblema circular blanco con borde dorado."""
    original = Image.open(resource_path('media/icons/logo_luevanos.png')).convert('RGBA')
    luminosidad = original.convert('L')
    contenido = luminosidad.point(lambda value: 255 if value < 246 else 0)
    bbox = contenido.getbbox()
    if bbox:
        margen = max(8, int(max(original.size) * .025))
        bbox = (
            max(0, bbox[0] - margen), max(0, bbox[1] - margen),
            min(original.width, bbox[2] + margen), min(original.height, bbox[3] + margen),
        )
        original = original.crop(bbox)

    canvas = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((2, 2, size - 3, size - 3), fill='#ffffff', outline='#b38a47', width=3)
    inner_size = size - 18
    logo = ImageOps.contain(original, (inner_size, inner_size), Image.Resampling.LANCZOS)
    x = (size - logo.width) // 2
    y = (size - logo.height) // 2
    mask = Image.new('L', logo.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, logo.width - 1, logo.height - 1), fill=255)
    canvas.paste(logo, (x, y), mask)
    return canvas


def cargar_logo_original(size=200):
    """Redimensiona el emblema original y elimina el fondo cuadrado."""
    logo = Image.open(
        resource_path('media/icons/logo_luevanos.png')
    ).convert('RGBA')
    logo = ImageOps.fit(logo, (size, size), Image.Resampling.LANCZOS)
    mascara = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mascara).ellipse((2, 2, size - 3, size - 3), fill=255)
    emblema = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    emblema.paste(logo, (0, 0), mascara)
    return emblema


def mostrar_splash_bienvenida(duracion=10000):
    """Muestra el splash premium y avanza según verificaciones reales de inicio."""
    global _splash_mostrado
    if _splash_mostrado:
        return
    _splash_mostrado = True

    # El proceso se declara consciente de DPI antes de crear la ventana. Así
    # Canvas conserva las coordenadas reales y el diseño se mantiene nítido
    # en monitores Full HD y con escalado de Windows.
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        pass

    # Proporción 16:9, inspirada en la composición de referencia. El centrado
    # se calcula dinámicamente para que siga funcionando en otros monitores.
    width, height = 800, 450
    corner_radius = 18
    bg_color = '#06101a'
    # Esta ventana es independiente y efímera. Tkinter nativo evita que el
    # temporizador interno de CustomTkinter intente actualizar una ventana ya
    # destruida al cerrar el splash.
    splash = tk.Tk()
    splash.withdraw()
    splash.overrideredirect(True)
    splash.configure(bg=bg_color)
    splash.geometry(f'{width}x{height}')
    splash.resizable(False, False)
    try:
        splash.attributes('-topmost', True)
    except Exception:
        pass

    def centrar_splash():
        """Centra la ventana después de que Windows asigne su DPI real."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
        except Exception:
            screen_width = splash.winfo_screenwidth()
            screen_height = splash.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f'{width}x{height}+{x}+{y}')

    centrar_splash()

    def aplicar_esquinas_redondeadas():
        """Recorta la ventana nativa en Windows sin dibujar un borde rectangular."""
        try:
            import ctypes
            hwnd_child = splash.winfo_id()
            hwnd = ctypes.windll.user32.GetParent(hwnd_child) or hwnd_child
            region = ctypes.windll.gdi32.CreateRoundRectRgn(
                0, 0, width + 1, height + 1,
                corner_radius * 2, corner_radius * 2,
            )
            ctypes.windll.user32.SetWindowRgn(hwnd, region, True)
            preference = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
            )
        except Exception:
            pass

    aplicar_esquinas_redondeadas()
    canvas = tk.Canvas(
        splash, width=width, height=height,
        bg=bg_color, highlightthickness=0, bd=0,
    )
    canvas.pack(fill='both', expand=True)
    splash.deiconify()
    splash.lift()
    # Una segunda pasada cubre el caso en que Windows reajusta el escalado al
    # mostrar por primera vez una ventana sin bordes.
    splash.after(40, centrar_splash)

    # Fondo creado para la interfaz: el contenido central sigue siendo dinámico.
    try:
        background = Image.open(
            resource_path('media/img/splash_background_v2.png')
        ).convert('RGB')
        background = ImageOps.fit(
            background, (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        background_photo = ImageTk.PhotoImage(background)
        splash._splash_background_ref = background_photo
        canvas.create_image(0, 0, image=background_photo, anchor='nw')
    except Exception:
        canvas.create_rectangle(0, 0, width, height, fill=bg_color, outline='')
        for offset, color in ((0, '#734719'), (38, '#a56b21'), (76, '#593914')):
            canvas.create_line(
                -90 + offset, 280, 320 + offset, -55,
                fill=color, width=2,
            )

    center_x = width // 2
    logo_center_y = 135
    logo_size = 127

    try:
        logo_pil = cargar_logo_original(logo_size)
        logo_photo = ImageTk.PhotoImage(logo_pil)
        splash._splash_logo_ref = logo_photo
        canvas.create_image(center_x, logo_center_y, image=logo_photo)
    except Exception:
        canvas.create_oval(
            center_x - 64, logo_center_y - 64,
            center_x + 64, logo_center_y + 64,
            fill='#ffffff', outline='#d79327', width=3,
        )
        canvas.create_text(
            center_x, logo_center_y, text='CL',
            fill='#121923', font=('Poppins', 28, 'bold'),
        )

    canvas.create_text(
        center_x, 255, text='CARNES LUÉVANOS',
        fill='#f1a22b', font=('Poppins', 29, 'bold'),
        justify='center',
    )
    canvas.create_text(
        center_x, 292, text='S i s t e m a   A d m i n i s t r a t i v o',
        fill='#f5f4f1', font=('Poppins', 9, 'normal'),
    )
    canvas.create_line(center_x - 190, 292, center_x - 146, 292, fill='#bd8227', width=1)
    canvas.create_line(center_x + 146, 292, center_x + 190, 292, fill='#bd8227', width=1)

    status_text = canvas.create_text(
        center_x, 370, text='Preparando sistema...',
        fill='#e7e9ec', font=('Poppins', 10), anchor='center',
    )
    percent_text = canvas.create_text(
        center_x + 193, 397, text='0%',
        fill='#f1a62c', font=('Poppins', 10, 'bold'), anchor='w',
    )
    bar_x, bar_y, bar_w, bar_h = center_x - 157, 393, 314, 8
    canvas.create_rectangle(
        bar_x + 3, bar_y, bar_x + bar_w - 3, bar_y + bar_h,
        fill='#34414b', outline='',
    )
    canvas.create_oval(
        bar_x, bar_y, bar_x + bar_h, bar_y + bar_h,
        fill='#34414b', outline='',
    )
    canvas.create_oval(
        bar_x + bar_w - bar_h, bar_y,
        bar_x + bar_w, bar_y + bar_h,
        fill='#34414b', outline='',
    )
    progress_fill = canvas.create_rectangle(
        bar_x + 3, bar_y, bar_x + 3, bar_y + bar_h,
        fill='#e59a22', outline='',
    )
    progress_head = canvas.create_oval(
        bar_x, bar_y, bar_x + bar_h, bar_y + bar_h,
        fill='#f1a62c', outline='',
    )
    progress_glow = canvas.create_oval(0, 0, 0, 0, fill='#ffd875', outline='')
    progress_spark = canvas.create_oval(0, 0, 0, 0, fill='#fff8d7', outline='')

    def verificar_recursos():
        rutas = (
            'media/icons/logo_luevanos.png',
            'media/img/splash_background_v2.png',
        )
        if not all(os.path.isfile(resource_path(ruta)) for ruta in rutas):
            raise FileNotFoundError('Faltan recursos visuales')

    def verificar_base_datos():
        conexion = sqlite3.connect(DB_PATH, timeout=2)
        try:
            conexion.execute('SELECT 1').fetchone()
        finally:
            conexion.close()

    def verificar_seguridad():
        from modulos.auth import seguridad
        if not callable(getattr(seguridad, 'authenticate', None)):
            raise RuntimeError('Servicio de autenticación no disponible')

    def verificar_modulos():
        rutas = (
            'modulos/ventas/ventas_moderna.py',
            'modulos/inventario/inventario_moderno.py',
            'modulos/clientes_moderno.py',
            'container.py',
        )
        if not all(os.path.isfile(resource_path(ruta)) for ruta in rutas):
            raise FileNotFoundError('Módulos administrativos incompletos')

    tareas = [
        (0.16, 'Cargando identidad visual...', verificar_recursos),
        (0.38, 'Conectando con la base de datos...', verificar_base_datos),
        (0.61, 'Validando acceso seguro...', verificar_seguridad),
        (0.84, 'Preparando módulos administrativos...', verificar_modulos),
        (1.00, 'Conexión con el sistema lista', lambda: None),
    ]
    state = {
        'displayed': 0.0,
        'target': 0.0,
        'pulse': 0.0,
        'closing': False,
        'alpha': 1.0,
        'warning': False,
        'started': time.perf_counter(),
    }

    def ejecutar_tarea(index):
        if state['closing'] or index >= len(tareas):
            return
        target, label, action = tareas[index]
        canvas.itemconfigure(status_text, text=label)
        try:
            action()
        except Exception:
            state['warning'] = True
        state['target'] = target
        if index + 1 < len(tareas):
            intervalo = max(360, int(duracion / len(tareas)))
            splash.after(intervalo, ejecutar_tarea, index + 1)

    def cerrar_con_fade():
        if state['closing']:
            return
        state['closing'] = True

        def fade():
            state['alpha'] = max(0.0, state['alpha'] - 0.07)
            try:
                splash.attributes('-alpha', state['alpha'])
            except Exception:
                splash.destroy()
                return
            if state['alpha'] <= 0.02:
                splash.destroy()
            else:
                splash.after(18, fade)

        splash.after(280, fade)

    def animar():
        if state['closing']:
            return

        state['pulse'] += 0.16
        pulse = (math.sin(state['pulse']) + 1) / 2

        elapsed = time.perf_counter() - state['started']
        elapsed_limit = min(1.0, elapsed / max(0.1, duracion / 1000))
        permitted_progress = min(state['target'], elapsed_limit)
        delta = permitted_progress - state['displayed']
        if delta > 0.0005:
            state['displayed'] += max(0.004, delta * 0.09)
            state['displayed'] = min(state['displayed'], state['target'])
        value = state['displayed']
        fill_w = max(bar_h, bar_w * value)
        canvas.coords(
            progress_fill,
            bar_x + 3, bar_y,
            bar_x + max(3, fill_w - 3), bar_y + bar_h,
        )
        canvas.coords(
            progress_head,
            bar_x + max(0, fill_w - bar_h), bar_y,
            bar_x + fill_w, bar_y + bar_h,
        )
        shine_x = bar_x + fill_w
        glow_radius = 9 + int(pulse * 5)
        canvas.coords(
            progress_glow,
            shine_x - glow_radius, bar_y - glow_radius + (bar_h // 2),
            shine_x + glow_radius, bar_y + glow_radius + (bar_h // 2),
        )
        spark_radius = 2 + int(pulse * 2)
        canvas.coords(
            progress_spark,
            shine_x - spark_radius, bar_y + (bar_h // 2) - spark_radius,
            shine_x + spark_radius, bar_y + (bar_h // 2) + spark_radius,
        )
        canvas.itemconfigure(percent_text, text=f'{int(value * 100):d}%')

        if state['target'] >= 1.0 and elapsed_limit >= 1.0 and value >= 0.995:
            canvas.itemconfigure(
                status_text,
                text='Sistema listo con avisos' if state['warning']
                else 'Conexión con el sistema lista',
            )
            cerrar_con_fade()
            return
        splash.after(16, animar)

    splash.after(100, ejecutar_tarea, 0)
    splash.after(20, animar)
    splash.mainloop()

def verificar_login(usuario, password):
    """Autenticar mediante la capa centralizada de seguridad."""
    from modulos.auth.seguridad import authenticate
    return authenticate(usuario, password)


def obtener_usuario_actual():
    return USUARIO_ACTUAL


def obtener_sesion_actual():
    return SESION_ACTUAL


def crear_icono_ojo(tachado=False, color='#5f6368'):
    """Crear icono de ojo estable para el boton de contraseña."""
    img = Image.new('RGBA', (28, 28), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 8, 24, 20), outline=color, width=2)
    draw.ellipse((11, 11, 17, 17), fill=color)
    if tachado:
        draw.line((6, 22, 22, 6), fill=color, width=3)
    return img


def crear_icono_usuario(color='#f2a51a'):
    """Icono de usuario dibujado a alta resolución para el campo de acceso."""
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((24, 8, 40, 24), outline=color, width=5)
    draw.arc((14, 27, 50, 61), 180, 360, fill=color, width=5)
    draw.line((14, 44, 14, 55), fill=color, width=5)
    draw.line((50, 44, 50, 55), fill=color, width=5)
    return image


def crear_icono_candado(color='#f2a51a'):
    """Icono de candado dibujado a alta resolución para el campo de contraseña."""
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((15, 28, 49, 57), radius=5, outline=color, width=5)
    draw.arc((21, 7, 43, 39), 180, 360, fill=color, width=5)
    draw.line((21, 23, 21, 31), fill=color, width=5)
    draw.line((43, 23, 43, 31), fill=color, width=5)
    return image


def crear_fondo_boton(width=560, height=64, hover=False):
    """Crea el degradado dorado del botón principal sin depender de recursos externos."""
    left = (219, 132, 7) if not hover else (197, 112, 5)
    middle = (255, 187, 48) if not hover else (240, 164, 25)
    right = (224, 137, 5) if not hover else (199, 113, 4)
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = image.load()
    radius = 15
    mask = Image.new('L', (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
    for x in range(width):
        position = x / max(1, width - 1)
        if position <= .5:
            amount = position * 2
            start, end = left, middle
        else:
            amount = (position - .5) * 2
            start, end = middle, right
        color = tuple(int(start[i] + (end[i] - start[i]) * amount) for i in range(3))
        for y in range(height):
            pixels[x, y] = (*color, mask.getpixel((x, y)))
    return image


def aplicar_barra_titulo_personalizada(
        root, texto='Sistema administrativo | Carnes Luévanos',
        permitir_maximizar=False, cerrar_callback=None):
    """Añade una barra de título inspirada en la ventana de WhatsApp para Windows."""
    bar_height = 34
    bar_color = '#020b18'
    border_color = '#13202d'
    hover_color = '#112033'
    close_hover = '#c42b1c'
    title_font = 'Segoe UI Variable Text Semibold'

    root.overrideredirect(True)

    def registrar_en_barra_tareas():
        """Mantiene la ventana personalizada visible en Alt+Tab y la barra de tareas."""
        if os.name != 'nt':
            return
        try:
            import ctypes
            root.update_idletasks()
            user32 = ctypes.windll.user32
            hwnd_child = root.winfo_id()
            hwnd = user32.GetParent(hwnd_child) or hwnd_child
            gwl_exstyle = -20
            ws_ex_toolwindow = 0x00000080
            ws_ex_appwindow = 0x00040000
            style = user32.GetWindowLongW(hwnd, gwl_exstyle)
            style = (style & ~ws_ex_toolwindow) | ws_ex_appwindow
            user32.SetWindowLongW(hwnd, gwl_exstyle, style)
            user32.SetWindowTextW(hwnd, texto)
            # Esquinas y borde nativos de Windows 11, como la referencia.
            rounded = ctypes.c_int(2)
            dark_mode = ctypes.c_int(1)
            border_rgb = ctypes.c_int(0x002d2013)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(rounded), ctypes.sizeof(rounded)
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 34, ctypes.byref(border_rgb), ctypes.sizeof(border_rgb)
            )
        except Exception:
            pass

    registrar_en_barra_tareas()
    title_bar = tk.Frame(
        root, height=bar_height, bg=bar_color, bd=0,
        highlightthickness=1, highlightbackground=border_color,
        highlightcolor=border_color,
    )
    title_bar.place(x=0, y=0, relwidth=1)
    title_bar.pack_propagate(False)

    # Fuente grande y reducción LANCZOS: icono nítido incluso con escalado de Windows.
    icon_source = cargar_logo_emblema(512)
    icon_source = icon_source.resize((20, 20), Image.Resampling.LANCZOS)
    icon_photo = ImageTk.PhotoImage(icon_source)
    icon_label = tk.Label(title_bar, image=icon_photo, bg=bar_color, bd=0)
    icon_label.pack(side='left', padx=(12, 8))
    root._titlebar_icon_ref = icon_photo

    title_label = tk.Label(
        title_bar,
        text=texto,
        bg=bar_color,
        fg='#f5f8fc',
        font=(title_font, 10),
        anchor='w',
    )
    title_label.pack(side='left', fill='y')

    def crear_control(tipo, command, hover, enabled=True):
        """Dibuja controles finos para evitar diferencias entre fuentes de símbolos."""
        button = tk.Canvas(
            title_bar, width=48, height=bar_height - 2,
            bg=bar_color, bd=0, highlightthickness=0,
            cursor='hand2' if enabled else 'arrow',
        )
        button.pack(side='right', fill='y')

        def dibujar(icono=tipo):
            button.delete('control')
            color = '#f1f1f1' if enabled else '#687071'
            cx, cy = 24, (bar_height - 2) // 2
            if icono == 'minimize':
                button.create_line(cx - 6, cy + 4, cx + 6, cy + 4,
                                   fill=color, width=1, tags='control')
            elif icono == 'maximize':
                button.create_rectangle(cx - 5, cy - 5, cx + 5, cy + 5,
                                        outline=color, width=1, tags='control')
            elif icono == 'restore':
                button.create_rectangle(cx - 4, cy - 6, cx + 5, cy + 3,
                                        outline=color, width=1, tags='control')
                button.create_line(cx - 6, cy - 3, cx - 6, cy + 6, cx + 3, cy + 6,
                                   fill=color, width=1, tags='control')
            else:
                button.create_line(cx - 5, cy - 5, cx + 5, cy + 5,
                                   fill=color, width=1, tags='control')
                button.create_line(cx + 5, cy - 5, cx - 5, cy + 5,
                                   fill=color, width=1, tags='control')

        button._draw_title_icon = dibujar
        dibujar()
        if enabled:
            button.bind('<Button-1>', lambda _event: command())
            button.bind('<Enter>', lambda _event: button.configure(bg=hover))
            button.bind('<Leave>', lambda _event: button.configure(bg=bar_color))
        return button

    def minimizar():
        root.overrideredirect(False)
        root.iconify()

    ventana = {'maximizada': False, 'geometria': ''}

    def area_trabajo():
        if os.name == 'nt':
            try:
                import ctypes

                class RECT(ctypes.Structure):
                    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                                ('right', ctypes.c_long), ('bottom', ctypes.c_long)]

                rect = RECT()
                if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
                    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
            except Exception:
                pass
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()

    def alternar_maximizado(_event=None):
        if not permitir_maximizar:
            return
        if ventana['maximizada']:
            root.geometry(ventana['geometria'])
            ventana['maximizada'] = False
            maximize_btn._draw_title_icon('maximize')
        else:
            ventana['geometria'] = root.geometry()
            x, y, width, height = area_trabajo()
            root.geometry(f'{width}x{height}+{x}+{y}')
            ventana['maximizada'] = True
            maximize_btn._draw_title_icon('restore')
        title_bar.lift()

    crear_control('close', cerrar_callback or root.destroy, close_hover)
    maximize_btn = crear_control('maximize', alternar_maximizado, hover_color,
                                  enabled=permitir_maximizar)
    crear_control('minimize', minimizar, hover_color)

    drag = {'x': 0, 'y': 0}

    def iniciar_arrastre(event):
        if ventana['maximizada']:
            alternar_maximizado()
        drag['x'] = event.x_root - root.winfo_x()
        drag['y'] = event.y_root - root.winfo_y()

    def arrastrar(event):
        root.geometry(f'+{event.x_root - drag["x"]}+{event.y_root - drag["y"]}')

    def restaurar_marco(_event=None):
        if root.state() == 'normal':
            def aplicar_marco_personalizado():
                root.overrideredirect(True)
                registrar_en_barra_tareas()
                title_bar.lift()
            root.after(10, aplicar_marco_personalizado)

    for draggable in (title_bar, icon_label, title_label):
        draggable.bind('<ButtonPress-1>', iniciar_arrastre)
        draggable.bind('<B1-Motion>', arrastrar)
        if permitir_maximizar:
            draggable.bind('<Double-Button-1>', alternar_maximizado)
    root.bind('<Map>', restaurar_marco, add='+')
    title_bar.lift()
    return title_bar


def crear_icono_escudo_2fa():
    """Escudo sencillo para la ventana de verificación."""
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    gold = '#b38a47'
    draw.ellipse((3, 3, 61, 61), fill='#f7f0e5', outline=gold, width=2)
    draw.polygon(((32, 14), (47, 20), (45, 39), (32, 50), (19, 39), (17, 20)),
                 fill='#20242c', outline=gold)
    draw.line((25, 31, 30, 36, 40, 25), fill='#ffffff', width=4, joint='curve')
    return image


def crear_icono_google():
    """Ícono multicolor inspirado en la identidad visual de Google."""
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    box = (9, 9, 55, 55)
    width = 8
    draw.arc(box, 205, 305, fill='#ea4335', width=width)
    draw.arc(box, 305, 360, fill='#4285f4', width=width)
    draw.arc(box, 0, 48, fill='#4285f4', width=width)
    draw.arc(box, 48, 132, fill='#34a853', width=width)
    draw.arc(box, 132, 205, fill='#fbbc05', width=width)
    draw.rectangle((34, 24, 59, 31), fill=(255, 255, 255, 0))
    draw.line((33, 32, 55, 32), fill='#4285f4', width=8)
    draw.line((51, 32, 51, 44), fill='#4285f4', width=8)
    return image


def solicitar_verificacion_2fa(parent, secret=None):
    """Solicita un código MFA con la identidad visual de Carnes Luévanos."""
    configuracion = bool(secret)
    width, height = (480, 530) if configuracion else (440, 420)
    result = {'code': None}

    dialog = ctk.CTkToplevel(parent)
    dialog.title('Verificación en dos pasos')
    dialog.geometry(f'{width}x{height}')
    dialog.resizable(False, False)
    dialog.configure(fg_color='#f1f3f4')
    dialog.transient(parent)

    dialog.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')

    shell = ctk.CTkFrame(dialog, fg_color='#ffffff', corner_radius=14,
                         border_width=1, border_color='#dadce0')
    shell.pack(fill='both', expand=True, padx=20, pady=20)

    header = ctk.CTkFrame(shell, height=102, fg_color='#ffffff', corner_radius=13,
                          border_width=0)
    header.pack(fill='x')
    header.pack_propagate(False)
    google_icon = ctk.CTkImage(light_image=crear_icono_google(), size=(58, 58))
    dialog._google_icon_ref = google_icon
    ctk.CTkLabel(header, text='', image=google_icon).place(x=22, y=21)
    ctk.CTkLabel(header, text='GOOGLE AUTHENTICATOR', text_color='#1a73e8',
                 font=ctk.CTkFont('Poppins', 9, 'bold'), anchor='w').place(x=96, y=23)
    ctk.CTkLabel(header, text='Verificación en dos pasos', text_color='#202124',
                 font=ctk.CTkFont('Poppins', 18, 'bold'), anchor='w').place(x=96, y=44)
    tk.Frame(header, bg='#e8eaed', height=1).place(x=18, y=100, relwidth=.92)

    body = ctk.CTkFrame(shell, fg_color='transparent')
    body.pack(fill='both', expand=True, padx=28, pady=(18, 18))

    if configuracion:
        ctk.CTkLabel(
            body,
            text='Agrega esta clave en Google Authenticator, Microsoft Authenticator o Authy.',
            text_color='#5f6671', font=ctk.CTkFont('Poppins', 11),
            wraplength=370, justify='center',
        ).pack(pady=(0, 12))
        secret_box = ctk.CTkFrame(body, height=62, fg_color='#f8fafd', corner_radius=9,
                                  border_width=1, border_color='#c2e7ff')
        secret_box.pack(fill='x', pady=(0, 14))
        secret_box.pack_propagate(False)
        ctk.CTkLabel(secret_box, text=str(secret), text_color='#20242c',
                     font=ctk.CTkFont('Consolas', 14, 'bold')).place(x=14, rely=.5, anchor='w')

        def copiar_clave():
            dialog.clipboard_clear()
            dialog.clipboard_append(str(secret))
            copy_button.configure(text='Copiada')

        copy_button = ctk.CTkButton(
            secret_box, text='Copiar', command=copiar_clave, width=72, height=32,
            corner_radius=7, fg_color='#ffffff', hover_color='#eee7dc',
            border_width=1, border_color='#1a73e8', text_color='#1a73e8',
            font=ctk.CTkFont('Poppins', 9, 'bold'),
        )
        copy_button.place(relx=1, x=-12, rely=.5, anchor='e')
        instruction = 'Después escribe el código de 6 dígitos para confirmar la activación.'
    else:
        ctk.CTkLabel(
            body, text='Confirma tu identidad para continuar al sistema.',
            text_color='#5f6671', font=ctk.CTkFont('Poppins', 11), justify='center',
        ).pack(pady=(4, 20))
        instruction = 'Introduce el código de 6 dígitos de tu aplicación autenticadora.'

    ctk.CTkLabel(body, text=instruction, text_color='#20242c',
                 font=ctk.CTkFont('Poppins', 10, 'bold'), wraplength=370,
                 justify='center').pack(pady=(0, 10))

    code_var = tk.StringVar()
    code_entry = ctk.CTkEntry(
        body, textvariable=code_var, width=250, height=48, corner_radius=9,
        border_color='#1a73e8', border_width=2, fg_color='#ffffff',
        text_color='#20242c', placeholder_text='000000', placeholder_text_color='#a6a9ae',
        justify='center', font=ctk.CTkFont('Consolas', 22, 'bold'),
    )
    code_entry.pack(pady=(0, 5))
    error_label = ctk.CTkLabel(body, text='', text_color='#c21f28',
                               font=ctk.CTkFont('Poppins', 9))
    error_label.pack()

    def limitar_codigo(_event=None):
        value = ''.join(character for character in code_var.get() if character.isdigit())[:6]
        if value != code_var.get():
            code_var.set(value)

    def confirmar(_event=None):
        code = code_var.get().strip()
        if len(code) != 6 or not code.isdigit():
            error_label.configure(text='Ingresa un código válido de seis dígitos.')
            code_entry.focus_set()
            return
        result['code'] = code
        dialog.destroy()

    def cancelar():
        result['code'] = None
        dialog.destroy()

    code_entry.bind('<KeyRelease>', limitar_codigo)
    dialog.bind('<Return>', confirmar)
    dialog.protocol('WM_DELETE_WINDOW', cancelar)
    ctk.CTkButton(
        body, text='Verificar y continuar', command=confirmar, height=42,
        corner_radius=8, fg_color='#1a73e8', hover_color='#1557b0',
        text_color='#ffffff', font=ctk.CTkFont('Poppins', 11, 'bold'),
    ).pack(fill='x', pady=(8, 8))
    ctk.CTkLabel(body, text='Tu código es temporal y nunca se almacena.', text_color='#8b9098',
                 font=ctk.CTkFont('Poppins', 8)).pack()

    dialog.after(100, code_entry.focus_set)
    dialog.wait_visibility()
    dialog.grab_set()
    dialog.wait_window()
    return result['code']


def registrar_evento_login(usuario):
    """Registrar ingreso para que Android pueda notificarlo."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eventos_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                usuario TEXT,
                origen TEXT,
                fecha TEXT NOT NULL,
                leido INTEGER DEFAULT 0
            )
        ''')
        from datetime import datetime
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO eventos_sistema (tipo, titulo, mensaje, usuario, origen, fecha, leido)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (
            'login',
            'Ingreso al sistema',
            f'El usuario {usuario} inició sesión en el programa de PC.',
            usuario,
            'PC/Tkinter',
            fecha,
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def guardar_ultimo_usuario(usuario):
    """Recordar solamente la cuenta usada; nunca la contraseña."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clave TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL, descripcion TEXT, fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('''INSERT INTO configuracion_sistema(clave, valor, descripcion)
                VALUES('ultimo_usuario_login', ?, 'Ultimo usuario que inicio sesion')
                ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor,
                fecha_modificacion=CURRENT_TIMESTAMP''', (usuario,))
    except sqlite3.Error:
        pass


def limpiar_ultimo_usuario():
    """Desactiva el recordatorio de cuenta sin borrar información del usuario."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clave TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL, descripcion TEXT, fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('''INSERT INTO configuracion_sistema(clave, valor, descripcion)
                VALUES('ultimo_usuario_login', '', 'Recordatorio de usuario desactivado')
                ON CONFLICT(clave) DO UPDATE SET valor='', descripcion=excluded.descripcion,
                fecha_modificacion=CURRENT_TIMESTAMP''')
    except sqlite3.Error:
        pass


def obtener_ultimo_usuario():
    """Obtener usuario y nombre visible de la ultima sesion correcta."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            fila = conn.execute("SELECT valor FROM configuracion_sistema WHERE clave='ultimo_usuario_login'").fetchone()
            if fila and fila[0]:
                usuario = fila[0]
            elif fila:
                return '', ''
            else:
                reciente = conn.execute('''SELECT username FROM usuarios
                    WHERE ultimo_acceso IS NOT NULL ORDER BY ultimo_acceso DESC LIMIT 1''').fetchone()
                if not reciente:
                    return '', ''
                usuario = reciente[0]
            persona = conn.execute('SELECT COALESCE(nombre, username) FROM usuarios WHERE username=?', (usuario,)).fetchone()
            return usuario, (persona[0] if persona else usuario)
    except sqlite3.Error:
        return '', ''


def mostrar_login_simple():
    """Mostrar el acceso premium de Carnes Luévanos con CustomTkinter."""
    mostrar_splash_bienvenida()
    root = ctk.CTk()
    root.title('Inicio de sesión - Carnes Luévanos')
    root.configure(fg_color='#050d16')
    root.resizable(False, False)
    try:
        root.iconbitmap(resource_path('media/icons/logo_luevanos.ico'))
    except Exception:
        pass

    root.update_idletasks()
    # Proporción horizontal de la referencia. Todos los elementos visuales del
    # cuerpo usan CustomTkinter para compartir exactamente la misma escala DPI.
    base_w, base_h = 1000, 640
    available_w = max(720, root.winfo_screenwidth() - 80)
    available_h = max(520, root.winfo_screenheight() - 80)
    scale = min(0.86, available_w / base_w, available_h / base_h)
    window_w, window_h = int(base_w * scale), int(base_h * scale)
    unit = lambda value: max(1, int(value * scale))
    # Centra el bloque completo debajo de la barra superior. El margen queda
    # equilibrado entre el emblema y el pie de la ventana.
    content_y = lambda value: unit(value + 18)
    def centrar_login():
        try:
            import ctypes
            screen_w = ctypes.windll.user32.GetSystemMetrics(0)
            screen_h = ctypes.windll.user32.GetSystemMetrics(1)
        except Exception:
            screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f'{window_w}x{window_h}+{(screen_w - window_w) // 2}+{(screen_h - window_h) // 2}')

    centrar_login()

    login_exitoso = None
    password_visible = False
    ultimo_usuario, ultimo_nombre = obtener_ultimo_usuario()
    remember_var = tk.BooleanVar(value=bool(ultimo_usuario))

    gold = '#f2a51a'
    gold_hover = '#d98908'
    ink = '#061521'
    field_border = '#526674'
    primary_text = '#f7f8fa'
    muted_text = '#b8c1cc'

    # Fondo HD original, recortado con LANCZOS para conservar definición.
    background = Image.open(resource_path('media/img/splash_background_v2.png')).convert('RGB')
    background = ImageOps.fit(background, (window_w, window_h), method=Image.Resampling.LANCZOS)
    shade = Image.new('RGBA', background.size, (2, 9, 16, 58))
    background = Image.alpha_composite(background.convert('RGBA'), shade)
    background_image = ctk.CTkImage(
        light_image=background, dark_image=background,
        size=(window_w, window_h),
    )
    background_label = ctk.CTkLabel(
        root, text='', image=background_image,
        width=window_w, height=window_h, corner_radius=0,
    )
    background_label.place(x=0, y=0)
    root._login_background_ref = background_image

    try:
        logo = cargar_logo_emblema(320)
        logo_image = ctk.CTkImage(
            light_image=logo, dark_image=logo,
            size=(unit(92), unit(92)),
        )
        logo_label = ctk.CTkLabel(root, text='', image=logo_image)
        logo_label.place(relx=.5, y=content_y(45), anchor='n')
        root._login_logo_ref = logo_image
    except Exception:
        logo_label = ctk.CTkLabel(
            root, text='CL', width=unit(92), height=unit(92),
            corner_radius=unit(46), fg_color='#ffffff',
            text_color='#121923', font=ctk.CTkFont('Poppins', unit(24), 'bold'),
        )
        logo_label.place(relx=.5, y=content_y(45), anchor='n')

    display_name = ultimo_nombre or ultimo_usuario or 'admin'
    ctk.CTkLabel(
        root, text=f'Bienvenido, {display_name}', text_color=primary_text,
        font=ctk.CTkFont('Poppins', unit(28), 'bold'),
    ).place(relx=.5, y=content_y(186), anchor='center')
    ctk.CTkLabel(
        root, text='Inicia sesión para continuar', text_color=muted_text,
        font=ctk.CTkFont('Poppins', unit(12), 'bold'),
    ).place(relx=.5, y=content_y(217), anchor='center')

    def solicitar_desbloqueo(usuario_bloqueado):
        """Solicitar credenciales administrativas sin exponer la contraseña."""
        from modulos.auth.seguridad import unlock_user_with_admin
        while True:
            admin_usuario = simpledialog.askstring(
                'Desbloqueo administrativo',
                f'La cuenta {usuario_bloqueado} está bloqueada.\n\nUsuario administrador:',
                parent=root,
            )
            if not admin_usuario:
                return False
            admin_password = simpledialog.askstring(
                'Contraseña del administrador',
                'Ingresa la contraseña del administrador para desbloquear:',
                show='*',
                parent=root,
            )
            if not admin_password:
                return False
            try:
                desbloqueo = unlock_user_with_admin(usuario_bloqueado, admin_usuario, admin_password)
            except RuntimeError as exc:
                messagebox.showerror('Configuración de seguridad', str(exc), parent=root)
                return False
            if desbloqueo.get('ok'):
                messagebox.showinfo('Cuenta desbloqueada', desbloqueo['message'], parent=root)
                password_entry.delete(0, 'end')
                password_entry.focus_set()
                return True
            reintentar = messagebox.askretrycancel(
                'Desbloqueo rechazado',
                desbloqueo.get('message', 'No se pudo desbloquear la cuenta.'),
                parent=root,
            )
            if not reintentar:
                return False

    def intentar_login():
        nonlocal login_exitoso
        global USUARIO_ACTUAL, SESION_ACTUAL
        usuario = usuario_entry.get().strip()
        password = password_entry.get().strip()
        if not usuario or not password:
            messagebox.showerror('Error', 'Por favor ingrese usuario y contraseña')
            return
        try:
            resultado = verificar_login(usuario, password)
        except RuntimeError as exc:
            messagebox.showerror('Configuración de seguridad', str(exc))
            return
        if resultado.get('mfa_setup_required'):
            secret = resultado['secret']
            codigo = solicitar_verificacion_2fa(root, secret=secret)
            if not codigo:
                return
            from modulos.auth.seguridad import enable_mfa, authenticate
            if not enable_mfa(resultado['user_id'], secret, codigo.strip()):
                messagebox.showerror('Código incorrecto', 'No se pudo activar la autenticación en dos pasos.')
                return
            resultado = authenticate(usuario, password, codigo.strip())
        if resultado.get('mfa_required'):
            codigo = solicitar_verificacion_2fa(root)
            if not codigo:
                return
            from modulos.auth.seguridad import authenticate
            resultado = authenticate(usuario, password, codigo.strip())
        if resultado.get('ok'):
            login_exitoso = usuario
            USUARIO_ACTUAL = resultado['username']
            SESION_ACTUAL = resultado['session_id']
            if remember_var.get():
                guardar_ultimo_usuario(resultado['username'])
            else:
                limpiar_ultimo_usuario()
            registrar_evento_login(usuario)
            root.quit()
            root.destroy()
        else:
            if resultado.get('admin_unlock_required'):
                usuario_bloqueado = resultado.get('locked_username') or usuario
                messagebox.showwarning(
                    'Sistema bloqueado',
                    resultado.get('message', 'La cuenta está bloqueada.'),
                    parent=root,
                )
                solicitar_desbloqueo(usuario_bloqueado)
                return
            messagebox.showerror(
                'Error de autenticación',
                resultado.get('message', 'No se pudo iniciar sesión.'),
            )
            password_entry.delete(0, 'end')
            usuario_entry.focus()

    def alternar_password():
        nonlocal password_visible
        password_visible = not password_visible
        password_entry.configure(show='' if password_visible else '*')
        toggle_password_btn.configure(image=eye_closed_img if password_visible else eye_open_img)

    def abrir_recuperacion():
        dialog = ctk.CTkToplevel(root)
        dialog.title('Restablecer contraseña')
        dialog.geometry(f'{unit(500)}x{unit(590)}')
        dialog.resizable(False, False)
        dialog.configure(fg_color='#06111c')
        dialog.transient(root)
        dialog.grab_set()
        dialog.update_idletasks()
        dx = root.winfo_rootx() + max(0, (root.winfo_width() - unit(500)) // 2)
        dy = root.winfo_rooty() + max(0, (root.winfo_height() - unit(590)) // 2)
        dialog.geometry(f'{unit(500)}x{unit(590)}+{dx}+{dy}')

        ctk.CTkLabel(dialog, text='Recuperar acceso', text_color=primary_text,
                     font=ctk.CTkFont('Poppins', unit(24), 'bold')).pack(pady=(unit(28), unit(4)))
        ctk.CTkLabel(dialog, text='Un administrador debe autorizar el restablecimiento.',
                     text_color=muted_text, font=ctk.CTkFont('Poppins', unit(11)),
                     wraplength=unit(420)).pack(pady=(0, unit(20)))

        fields = []
        specifications = [
            ('Usuario a recuperar', usuario_entry.get().strip(), False),
            ('Usuario administrador', '', False),
            ('Contraseña del administrador', '', True),
            ('Nueva contraseña (mínimo 10 caracteres)', '', True),
            ('Confirmar nueva contraseña', '', True),
        ]
        for placeholder, value, secret in specifications:
            entry = ctk.CTkEntry(dialog, width=unit(410), height=unit(48), corner_radius=unit(12),
                                 fg_color=ink, border_color=field_border, text_color=primary_text,
                                 placeholder_text=placeholder, placeholder_text_color='#8e9aa6',
                                 show='*' if secret else '', font=ctk.CTkFont('Poppins', unit(11)))
            entry.pack(pady=unit(6))
            if value:
                entry.insert(0, value)
            fields.append(entry)

        recovery_error = ctk.CTkLabel(dialog, text='', text_color='#ff6b6b',
                                      font=ctk.CTkFont('Poppins', unit(10)))
        recovery_error.pack(pady=(unit(5), 0))

        def confirmar_restablecimiento():
            target, admin, admin_password, new_password, confirmation = [field.get().strip() for field in fields]
            if new_password != confirmation:
                recovery_error.configure(text='Las contraseñas nuevas no coinciden.')
                return
            from modulos.auth.seguridad import reset_password_with_admin
            result = reset_password_with_admin(target, admin, admin_password, new_password)
            if not result.get('ok'):
                recovery_error.configure(text=result.get('message', 'No se pudo restablecer la contraseña.'))
                return
            messagebox.showinfo('Acceso restablecido', result['message'], parent=dialog)
            usuario_entry.delete(0, 'end')
            usuario_entry.insert(0, target)
            password_entry.delete(0, 'end')
            dialog.destroy()
            password_entry.focus_set()

        ctk.CTkButton(dialog, text='Restablecer contraseña', command=confirmar_restablecimiento,
                      width=unit(410), height=unit(48), corner_radius=unit(12), fg_color=gold,
                      hover_color=gold_hover, text_color='#111820',
                      font=ctk.CTkFont('Poppins', unit(12), 'bold')).pack(pady=unit(12))

    def probar_conexion():
        try:
            with sqlite3.connect(DB_PATH, timeout=2) as connection:
                connection.execute('SELECT 1').fetchone()
            return True, 'Base local disponible'
        except sqlite3.Error as exc:
            return False, f'Base local no disponible: {exc}'

    def actualizar_estado_conexion():
        connected, description = probar_conexion()
        color = '#36d27c' if connected else '#e55757'
        connection_dot.configure(text_color=color)
        connection_text.configure(
            text='Sistema conectado' if connected else 'Sistema sin conexión'
        )
        return connected, description

    def abrir_configuracion():
        dialog = ctk.CTkToplevel(root)
        dialog.title('Estado de conexión')
        dialog.geometry(f'{unit(520)}x{unit(350)}')
        dialog.resizable(False, False)
        dialog.configure(fg_color='#06111c')
        dialog.transient(root)
        dialog.grab_set()
        dialog.update_idletasks()
        dx = root.winfo_rootx() + max(0, (root.winfo_width() - unit(520)) // 2)
        dy = root.winfo_rooty() + max(0, (root.winfo_height() - unit(350)) // 2)
        dialog.geometry(f'{unit(520)}x{unit(350)}+{dx}+{dy}')
        ctk.CTkLabel(dialog, text='Conexión del sistema', text_color=primary_text,
                     font=ctk.CTkFont('Poppins', unit(22), 'bold')).pack(pady=(unit(28), unit(8)))
        status_label = ctk.CTkLabel(dialog, text='', text_color=muted_text,
                                    font=ctk.CTkFont('Poppins', unit(11), 'bold'))
        status_label.pack(pady=unit(8))
        ctk.CTkLabel(dialog, text=str(DB_PATH), text_color='#8e9aa6',
                     font=ctk.CTkFont('Poppins', unit(9)), wraplength=unit(440)).pack(pady=unit(8))

        def refresh():
            connected, description = actualizar_estado_conexion()
            status_label.configure(text=description, text_color='#36d27c' if connected else '#ff6b6b')

        ctk.CTkButton(dialog, text='Probar conexión', command=refresh, width=unit(390),
                      height=unit(46), corner_radius=unit(12), fg_color=gold,
                      hover_color=gold_hover, text_color='#111820',
                      font=ctk.CTkFont('Poppins', unit(11), 'bold')).pack(pady=(unit(22), unit(8)))
        ctk.CTkButton(dialog, text='Cerrar', command=dialog.destroy, width=unit(390),
                      height=unit(42), corner_radius=unit(12), fg_color=ink,
                      border_width=1, border_color=field_border, hover_color='#102636',
                      text_color=primary_text, font=ctk.CTkFont('Poppins', unit(10))).pack()
        refresh()

    form_x = (window_w - unit(560)) // 2
    field_w, field_h = unit(560), unit(46)

    user_field = ctk.CTkFrame(root, width=field_w, height=field_h, corner_radius=unit(16),
                              fg_color=ink, border_width=1, border_color=field_border)
    user_field.place(x=form_x, y=content_y(245))
    user_icon = ctk.CTkImage(light_image=crear_icono_usuario(), size=(unit(21), unit(21)))
    root._user_icon_ref = user_icon
    ctk.CTkLabel(user_field, text='', image=user_icon, width=unit(54)).place(x=unit(16), rely=.5, anchor='w')
    usuario_entry = ctk.CTkEntry(user_field, placeholder_text='Usuario', width=unit(460), height=unit(38),
                                 corner_radius=0, border_width=0, fg_color=ink, text_color=primary_text,
                                 placeholder_text_color=muted_text, font=ctk.CTkFont('Poppins', unit(13), 'bold'))
    usuario_entry.place(x=unit(72), rely=.5, anchor='w')
    if ultimo_usuario:
        usuario_entry.insert(0, ultimo_usuario)

    password_field = ctk.CTkFrame(root, width=field_w, height=field_h, corner_radius=unit(16),
                                  fg_color=ink, border_width=1, border_color=field_border)
    password_field.place(x=form_x, y=content_y(304))
    lock_icon = ctk.CTkImage(light_image=crear_icono_candado(), size=(unit(21), unit(21)))
    root._lock_icon_ref = lock_icon
    ctk.CTkLabel(password_field, text='', image=lock_icon, width=unit(54)).place(x=unit(16), rely=.5, anchor='w')
    password_entry = ctk.CTkEntry(password_field, placeholder_text='Contraseña', width=unit(390), height=unit(38),
                                  corner_radius=0, border_width=0, fg_color=ink, text_color=primary_text,
                                  placeholder_text_color=muted_text, show='*',
                                  font=ctk.CTkFont('Poppins', unit(13), 'bold'))
    password_entry.place(x=unit(72), rely=.5, anchor='w')

    eye_open_img = ctk.CTkImage(light_image=crear_icono_ojo(False, '#9aa9b7'), size=(unit(21), unit(21)))
    eye_closed_img = ctk.CTkImage(light_image=crear_icono_ojo(True, '#9aa9b7'), size=(unit(21), unit(21)))
    root._eye_open_img_ref = eye_open_img
    root._eye_closed_img_ref = eye_closed_img
    toggle_password_btn = ctk.CTkButton(
        password_field, text='', image=eye_open_img, command=alternar_password,
        width=unit(46), height=unit(38), corner_radius=unit(10), fg_color='transparent',
        hover_color='#102636', text_color=muted_text,
    )
    toggle_password_btn.place(relx=1, x=-unit(17), rely=.5, anchor='e')

    remember_checkbox = ctk.CTkCheckBox(
        root, text='Recordarme', variable=remember_var, width=unit(160), height=unit(26),
        checkbox_width=unit(23), checkbox_height=unit(23), corner_radius=unit(6), border_width=1,
        fg_color=gold, hover_color=gold_hover, border_color=gold, checkmark_color='#ffffff',
        text_color=primary_text, font=ctk.CTkFont('Poppins', unit(10), 'bold'),
    )
    remember_checkbox.place(x=form_x, y=content_y(361))

    forgot_button = ctk.CTkButton(
        root, text='¿Olvidaste tu contraseña?', command=abrir_recuperacion,
        width=unit(220), height=unit(28), corner_radius=0, fg_color='transparent',
        hover_color='#10202d', text_color='#ffc052',
        font=ctk.CTkFont('Poppins', unit(10), 'bold'),
    )
    forgot_button.place(x=form_x + field_w - unit(220), y=content_y(359))

    button_w, button_h = field_w, unit(47)
    normal_button_image = ctk.CTkImage(
        light_image=crear_fondo_boton(max(2, button_w), max(2, button_h), False),
        dark_image=crear_fondo_boton(max(2, button_w), max(2, button_h), False),
        size=(button_w, button_h),
    )
    hover_button_image = ctk.CTkImage(
        light_image=crear_fondo_boton(max(2, button_w), max(2, button_h), True),
        dark_image=crear_fondo_boton(max(2, button_w), max(2, button_h), True),
        size=(button_w, button_h),
    )
    root._login_button_images = (normal_button_image, hover_button_image)
    login_button = ctk.CTkLabel(
        root, text='Iniciar sesión', image=normal_button_image, compound='center',
        width=button_w, height=button_h, text_color='#ffffff', cursor='hand2',
        font=ctk.CTkFont('Poppins', unit(14), 'bold'),
    )
    login_button.place(x=form_x, y=content_y(397))
    login_button.bind('<Enter>', lambda _event: login_button.configure(image=hover_button_image))
    login_button.bind('<Leave>', lambda _event: login_button.configure(image=normal_button_image))
    login_button.bind('<Button-1>', lambda _event: intentar_login())

    divider_y = content_y(467)
    ctk.CTkFrame(root, width=unit(190), height=1, fg_color='#687887').place(
        x=form_x, y=divider_y, anchor='w'
    )
    ctk.CTkFrame(root, width=unit(190), height=1, fg_color='#687887').place(
        x=form_x + field_w, y=divider_y, anchor='e'
    )
    ctk.CTkLabel(
        root, text='ACCESO PROTEGIDO', text_color='#aeb8c4',
        font=ctk.CTkFont('Poppins', unit(9), 'bold'),
    ).place(relx=.5, y=divider_y, anchor='center')

    status_y = content_y(502)
    connection_dot = ctk.CTkLabel(
        root, text='●', width=unit(18), text_color='#e55757',
        font=ctk.CTkFont('Poppins', unit(13), 'bold'),
    )
    connection_dot.place(relx=.5, x=-unit(205), y=status_y, anchor='center')
    connection_text = ctk.CTkLabel(
        root, text='Sistema sin conexión', text_color=muted_text,
        font=ctk.CTkFont('Poppins', unit(10), 'bold'),
    )
    connection_text.place(relx=.5, x=-unit(178), y=status_y, anchor='w')
    configure_button = ctk.CTkButton(
        root, text='Configurar', command=abrir_configuracion,
        width=unit(130), height=unit(28), corner_radius=0,
        fg_color='transparent', hover_color='#10202d', text_color='#ffc052',
        font=ctk.CTkFont('Poppins', unit(10), 'bold'),
    )
    configure_button.place(relx=.5, x=unit(130), y=status_y, anchor='center')

    ctk.CTkLabel(
        root, text='© 2026 Carnes Luévanos', text_color='#b8c1cc',
        font=ctk.CTkFont('Poppins', unit(9), 'bold'),
    ).place(relx=.5, y=content_y(570), anchor='center')
    ctk.CTkLabel(
        root, text='Todos los derechos reservados', text_color='#a4afba',
        font=ctk.CTkFont('Poppins', unit(8), 'bold'),
    ).place(relx=.5, y=content_y(593), anchor='center')

    actualizar_estado_conexion()
    aplicar_barra_titulo_personalizada(root)
    root.deiconify()
    root.lift()
    root.after(40, centrar_login)

    def mostrar_login_al_frente():
        """Evita que Windows deje el acceso oculto detrás de la app que lo abrió."""
        try:
            root.attributes('-topmost', True)
            root.lift()
            root.focus_force()
            root.after(450, lambda: root.attributes('-topmost', False))
        except tk.TclError:
            pass

    root.after(80, mostrar_login_al_frente)

    root.bind('<Return>', lambda event: intentar_login())
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    (password_entry if ultimo_usuario else usuario_entry).focus()
    root.mainloop()
    return login_exitoso


if __name__ == '__main__':
    mostrar_splash_bienvenida()
    if mostrar_login_simple():
        print('Login exitoso')
    else:
        print('Login cancelado')







