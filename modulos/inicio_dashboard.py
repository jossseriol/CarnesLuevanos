"""Dashboard principal oscuro de Carnes Luevanos.

La pantalla se construye por completo con Tkinter/CustomTkinter. Los iconos se
dibujan con Pillow sobre maestros 4x (128 px) y CustomTkinter los presenta a
20--56 px, evitando ampliar PNG pequenos y conservando bordes suaves.
"""

from __future__ import annotations

import math
import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta

import customtkinter as ctk
from PIL import Image, ImageDraw

from modulos.utils.utils import resource_path


BG = "#050f1b"
CARD = "#091725"
CARD_ALT = "#0a1928"
TEXT = "#f4f8fc"
MUTED = "#94a6b8"
BORDER = "#173149"
BLUE = "#159dff"
BLUE_DARK = "#087de0"
GREEN = "#18c96e"
ORANGE = "#f3a51b"
GRID = "#142b40"
ACTION_BG = "#0a1928"
ACTION_HOVER = "#102a40"
ACTION_BORDER = "#142b40"
GLOW_BACKGROUNDS = {
    BLUE: "#092c4c", GREEN: "#0a3528", ORANGE: "#3a2910",
}
GLOW_BORDERS = {
    BLUE: "#0c426e", GREEN: "#10563e", ORANGE: "#624313",
}
LINE_GLOW_OUTER = "#0a4774"
LINE_GLOW_INNER = "#0d70b8"
POINT_GLOW = "#0a3150"


def _set_palette(oscuro: bool):
    """Actualiza los tokens usados al reconstruir el dashboard."""
    global BG, CARD, CARD_ALT, TEXT, MUTED, BORDER, BLUE, BLUE_DARK
    global GREEN, ORANGE, GRID, ACTION_BG, ACTION_HOVER, ACTION_BORDER
    global GLOW_BACKGROUNDS, GLOW_BORDERS
    global LINE_GLOW_OUTER, LINE_GLOW_INNER, POINT_GLOW
    if oscuro:
        BG, CARD, CARD_ALT = "#050f1b", "#091725", "#0a1928"
        TEXT, MUTED, BORDER = "#f4f8fc", "#94a6b8", "#173149"
        BLUE, BLUE_DARK = "#159dff", "#087de0"
        GREEN, ORANGE, GRID = "#18c96e", "#f3a51b", "#142b40"
        ACTION_BG, ACTION_HOVER, ACTION_BORDER = "#0a1928", "#102a40", "#142b40"
        LINE_GLOW_OUTER, LINE_GLOW_INNER, POINT_GLOW = "#0a4774", "#0d70b8", "#0a3150"
        GLOW_BACKGROUNDS = {
            BLUE: "#092c4c", GREEN: "#0a3528", ORANGE: "#3a2910",
        }
        GLOW_BORDERS = {
            BLUE: "#0c426e", GREEN: "#10563e", ORANGE: "#624313",
        }
    else:
        BG, CARD, CARD_ALT = "#f4f7fb", "#ffffff", "#f8fafc"
        TEXT, MUTED, BORDER = "#101828", "#667085", "#dce3eb"
        BLUE, BLUE_DARK = "#087de0", "#0568bd"
        GREEN, ORANGE, GRID = "#0b9f55", "#d47a00", "#e5ebf1"
        ACTION_BG, ACTION_HOVER, ACTION_BORDER = "#f8fafc", "#eaf3fb", "#dce5ee"
        LINE_GLOW_OUTER, LINE_GLOW_INNER, POINT_GLOW = "#cbe9ff", "#75c2f7", "#d9efff"
        GLOW_BACKGROUNDS = {
            BLUE: "#e8f5ff", GREEN: "#e9f9f1", ORANGE: "#fff4df",
        }
        GLOW_BORDERS = {
            BLUE: "#b9ddf7", GREEN: "#bde8d0", ORANGE: "#f4d49d",
        }


class _Vector4x:
    """Adapta coordenadas logicas de 32x32 a un lienzo RGBA de 128x128."""

    SCALE = 4

    def __init__(self, image: Image.Image):
        self.draw = ImageDraw.Draw(image)

    @classmethod
    def xy(cls, values):
        return tuple(round(value * cls.SCALE) for value in values)

    @classmethod
    def width(cls, value):
        return max(1, round(value * cls.SCALE))

    def line(self, values, **kwargs):
        if "width" in kwargs:
            kwargs["width"] = self.width(kwargs["width"])
        self.draw.line(self.xy(values), **kwargs)

    def ellipse(self, values, **kwargs):
        if "width" in kwargs:
            kwargs["width"] = self.width(kwargs["width"])
        self.draw.ellipse(self.xy(values), **kwargs)

    def rectangle(self, values, **kwargs):
        if "width" in kwargs:
            kwargs["width"] = self.width(kwargs["width"])
        self.draw.rectangle(self.xy(values), **kwargs)

    def rounded_rectangle(self, values, **kwargs):
        if "width" in kwargs:
            kwargs["width"] = self.width(kwargs["width"])
        if "radius" in kwargs:
            kwargs["radius"] = self.width(kwargs["radius"])
        self.draw.rounded_rectangle(self.xy(values), **kwargs)

    def arc(self, values, start, end, **kwargs):
        if "width" in kwargs:
            kwargs["width"] = self.width(kwargs["width"])
        self.draw.arc(self.xy(values), start, end, **kwargs)


def crear_icono_dashboard_4x(tipo: str, color: str = BLUE) -> Image.Image:
    """Crea un icono lineal antialias en un maestro transparente de 128 px."""

    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    pen = _Vector4x(image)
    line = 1.8
    tipo = str(tipo).casefold()

    if tipo in {"hand", "ventas", "venta"}:
        pen.line((4, 22, 10, 25, 15, 20, 23, 20, 28, 15), fill=color, width=line)
        pen.line((4, 22, 9, 28, 22, 28, 29, 20), fill=color, width=line)
        pen.ellipse((13, 5, 24, 16), outline=color, width=line)
        pen.line((18.5, 7.5, 18.5, 13.5), fill=color, width=1.4)
        pen.arc((15, 8, 22, 13), 65, 275, fill=color, width=1.2)
    elif tipo in {"clipboard", "mes", "reporte"}:
        pen.rounded_rectangle((8, 7, 25, 28), radius=2.5, outline=color, width=line)
        pen.rounded_rectangle((12, 4.5, 21, 10), radius=2, outline=color, width=line)
        pen.line((11, 16, 14, 19, 18, 14), fill=color, width=line)
        pen.line((19, 18, 22, 18), fill=color, width=1.4)
        pen.line((12, 23, 22, 23), fill=color, width=1.4)
    elif tipo in {"box", "inventario", "productos"}:
        pen.line((6, 11, 16, 6, 26, 11, 16, 17, 6, 11), fill=color, width=line)
        pen.line((6, 11, 6, 23, 16, 29, 26, 23, 26, 11), fill=color, width=line)
        pen.line((16, 17, 16, 29), fill=color, width=line)
        pen.line((11, 8.5, 21, 14), fill=color, width=1.2)
    elif tipo in {"users", "clientes", "cliente"}:
        pen.ellipse((12, 5, 20, 13), outline=color, width=line)
        pen.arc((8, 13, 24, 28), 200, 340, fill=color, width=line)
        pen.ellipse((3, 9, 10, 16), outline=color, width=1.5)
        pen.arc((1, 16, 13, 28), 200, 330, fill=color, width=1.5)
        pen.ellipse((22, 9, 29, 16), outline=color, width=1.5)
        pen.arc((19, 16, 31, 28), 210, 340, fill=color, width=1.5)
    elif tipo in {"check", "abonos"}:
        pen.rounded_rectangle((6, 6, 26, 26), radius=3, outline=color, width=line)
        pen.line((10, 17, 14, 21, 23, 11), fill=color, width=2.1)
    elif tipo in {"profit", "ganancias", "dinero"}:
        pen.line((5, 24, 12, 17, 18, 20, 27, 10), fill=color, width=line)
        pen.line((22, 10, 27, 10, 27, 15), fill=color, width=line)
        pen.ellipse((11, 5, 21, 15), outline=color, width=line)
        pen.line((16, 7.5, 16, 12.5), fill=color, width=1.2)
        pen.arc((13, 8, 19, 12), 65, 275, fill=color, width=1.0)
    elif tipo in {"cart", "compras"}:
        pen.line((5, 7, 9, 7, 12, 21, 25, 21), fill=color, width=line)
        pen.line((10, 11, 27, 11, 24, 18, 12, 18), fill=color, width=line)
        pen.ellipse((12, 23, 16, 27), outline=color, width=1.5)
        pen.ellipse((22, 23, 26, 27), outline=color, width=1.5)
    elif tipo in {"plus", "nuevo", "agregar"}:
        pen.line((16, 7, 16, 25), fill=color, width=2.4)
        pen.line((7, 16, 25, 16), fill=color, width=2.4)
    else:
        pen.ellipse((7, 7, 25, 25), outline=color, width=line)
        pen.line((16, 11, 16, 21), fill=color, width=line)
        pen.ellipse((15, 23, 17, 25), fill=color)
    return image


def crear_textura_hero() -> Image.Image:
    """Genera las ondas azules tenues del saludo sin usar una imagen externa."""

    image = Image.new("RGBA", (960, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for index in range(32):
        points = []
        base = 116 + index * 2.2
        for x in range(340, 980, 10):
            y = base + math.sin((x / 55) + index * .14) * (13 + index * .8)
            y -= max(0, x - 650) * .08
            points.append((x, y))
        alpha = max(2, 18 - index // 2)
        draw.line(points, fill=(21, 157, 255, alpha), width=1)
    for radius, alpha in ((210, 12), (150, 9), (90, 7)):
        draw.ellipse((560 - radius, 110 - radius, 560 + radius, 110 + radius),
                     outline=(21, 157, 255, alpha), width=2)
    return image


class InicioDashboard(tk.Frame):
    """Panel principal responsive, optimizado para un area util de 1920x1040."""

    def __init__(self, padre):
        _set_palette(True)
        super().__init__(padre, bg=BG)
        self._modo_oscuro = True
        self.usuario_actual = self._obtener_usuario_actual(padre)
        self.usuario_nombre = self._db_one(
            "SELECT COALESCE(nombre, username) FROM usuarios WHERE username = ?",
            (self.usuario_actual,), self.usuario_actual,
        )
        self.usuario_rol = str(self._db_one(
            "SELECT COALESCE(rol, 'usuario') FROM usuarios WHERE username = ?",
            (self.usuario_actual,), "usuario",
        )).casefold()
        self._images: list[ctk.CTkImage] = []
        self._charts: list[tk.Canvas] = []
        self.period_days = 7
        self._resize_after = None
        self._build()
        self.bind("<Configure>", self._on_resize, add="+")
        self.cargar_datos()

    def _obtener_usuario_actual(self, widget):
        current = widget
        while current is not None:
            usuario = getattr(current, "usuario_actual", None)
            if usuario:
                return str(usuario).strip()
            current = getattr(current, "master", None)
        return "admin"

    def _db_one(self, query, params=(), default=0):
        try:
            with sqlite3.connect("database.db") as conn:
                row = conn.execute(query, params).fetchone()
            return row[0] if row and row[0] is not None else default
        except (sqlite3.Error, TypeError, ValueError):
            return default

    def _db_all(self, query, params=()):
        try:
            with sqlite3.connect("database.db") as conn:
                return conn.execute(query, params).fetchall()
        except sqlite3.Error:
            return []

    def _build(self):
        self.viewport = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.viewport.pack(fill="both", expand=True)
        self.scroll_canvas = tk.Canvas(
            self.viewport, bg=BG, highlightthickness=0, bd=0,
        )
        self.scroll_canvas.place(x=0, y=0)
        self.scrollbar = ctk.CTkScrollbar(
            self.viewport, orientation="vertical", command=self.scroll_canvas.yview,
        )
        self.scrollbar.place(relx=1, rely=0, relheight=1, anchor="ne")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content = ctk.CTkFrame(
            self.scroll_canvas, width=1000, height=850,
            fg_color="transparent", corner_radius=0,
        )
        self.content_window = self.scroll_canvas.create_window(
            32, 22, window=self.content, anchor="nw",
        )
        self.content.bind("<Configure>", self._update_scroll_region, add="+")
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.scroll_canvas.bind("<Button-4>", self._on_mousewheel, add="+")
        self.scroll_canvas.bind("<Button-5>", self._on_mousewheel, add="+")
        self.content.grid_propagate(False)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(3, weight=1)

        self._build_title(self.content)
        self._build_hero(self.content)
        self._build_stats(self.content)
        self._build_charts(self.content)

    def _build_title(self, parent):
        title = ctk.CTkFrame(parent, fg_color="transparent", height=80, corner_radius=0)
        title.grid(row=0, column=0, sticky="ew")
        title.grid_propagate(False)
        ctk.CTkLabel(
            title, text="Panel de control", text_color=TEXT,
            font=ctk.CTkFont("Poppins", 27, "bold"), anchor="w",
        ).place(x=10, y=1)
        ctk.CTkLabel(
            title, text="Resumen general del sistema y actividad reciente",
            text_color=MUTED, font=ctk.CTkFont("Poppins", 11), anchor="w",
        ).place(x=10, y=38)
        tk.Frame(title, bg=BLUE, height=2, width=44).place(x=10, y=65)
        watermark = self._load_cow_watermark((260, 88))
        self.header_watermark = ctk.CTkLabel(title, text="", image=watermark)
        self.header_watermark.place(relx=1.0, x=-2, y=-18, anchor="ne")

    def _card(self, parent, height=None, radius=12):
        options = dict(
            fg_color=CARD, corner_radius=radius,
            border_width=1, border_color=BORDER,
        )
        if height is not None:
            options["height"] = height
        return ctk.CTkFrame(parent, **options)

    def _load_icon(self, tipo, size=(32, 32), color=BLUE):
        image = crear_icono_dashboard_4x(tipo, color)
        icon = ctk.CTkImage(light_image=image, dark_image=image, size=size)
        self._images.append(icon)
        return icon

    def _load_cow_watermark(self, size=(260, 88)):
        try:
            image = Image.open(
                resource_path("media/icons/dashboard_cow_watermark.png")
            ).convert("RGBA")
            alpha = image.getchannel("A")
            gray = image.convert("L")
            mask = Image.new("L", image.size)
            mask.putdata([
                min(original, max(0, int((255 - light) * .13)))
                for light, original in zip(gray.getdata(), alpha.getdata())
            ])
            faded = Image.new("RGBA", image.size, (113, 145, 174, 0))
            faded.putalpha(mask)
        except Exception:
            faded = Image.new("RGBA", (512, 180), (0, 0, 0, 0))
        icon = ctk.CTkImage(light_image=faded, dark_image=faded, size=size)
        self._images.append(icon)
        return icon

    def _build_hero(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=210)
        row.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        row.grid_propagate(False)
        row.grid_columnconfigure(0, weight=53, uniform="hero")
        row.grid_columnconfigure(1, weight=47, uniform="hero")

        hero = self._card(row, height=210)
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        hero.grid_propagate(False)
        texture = crear_textura_hero()
        self.hero_texture = ctk.CTkImage(
            light_image=texture, dark_image=texture, size=(720, 165)
        )
        self._images.append(self.hero_texture)
        ctk.CTkLabel(hero, text="", image=self.hero_texture).place(
            relx=1, rely=1, anchor="se", x=-2, y=-2
        )

        nombre = (
            "Administrador"
            if self.usuario_rol in {"super", "admin", "administrador"}
            else (self.usuario_nombre or "Usuario")
        )
        ctk.CTkLabel(
            hero, text=f"¡Bienvenido, {nombre}!", text_color=TEXT,
            font=ctk.CTkFont("Poppins", 21, "bold"), anchor="w",
        ).place(x=28, y=26)
        self.session_label = ctk.CTkLabel(
            hero, text="", text_color=BLUE,
            font=ctk.CTkFont("Poppins", 10, "bold"), anchor="w",
        )
        self.session_label.place(x=28, y=65)
        ctk.CTkLabel(
            hero, text="Ventas, compras, inventario y clientes en un solo lugar.",
            text_color=MUTED, font=ctk.CTkFont("Poppins", 10), anchor="w",
        ).place(x=28, y=98)
        ctk.CTkButton(
            hero, text="Nueva venta", image=self._load_icon("plus", (17, 17), "#ffffff"),
            compound="left", width=142, height=42, corner_radius=8,
            fg_color="#0757ad", hover_color=BLUE_DARK, text_color="#ffffff",
            font=ctk.CTkFont("Poppins", 10, "bold"),
            command=lambda: self._abrir_area("Ventas"),
        ).place(x=28, y=141)

        summary = self._card(row, height=210)
        summary.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        summary.grid_propagate(False)
        ctk.CTkLabel(
            summary, text="RESUMEN OPERATIVO", text_color=MUTED,
            font=ctk.CTkFont("Poppins", 8, "bold"), anchor="w",
        ).place(x=24, y=24)
        ctk.CTkLabel(
            summary, text="Todo bajo control", text_color=TEXT,
            font=ctk.CTkFont("Poppins", 20, "bold"), anchor="w",
        ).place(x=24, y=47)
        ctk.CTkLabel(
            summary, text="Accesos rápidos del sistema", text_color=MUTED,
            font=ctk.CTkFont("Poppins", 10), anchor="w",
        ).place(x=24, y=84)

        actions = ctk.CTkFrame(summary, fg_color="transparent", height=61)
        actions.place(relx=.5, y=125, relwidth=.94, anchor="n")
        for column, (label, kind, area, color) in enumerate((
            ("Inventario", "box", "Inventario", BLUE),
            ("Abonos", "check", "Abonos", GREEN),
            ("Compras", "cart", "Compras", ORANGE),
        )):
            actions.grid_columnconfigure(column, weight=1, uniform="actions")
            ctk.CTkButton(
                actions, text=label, image=self._load_icon(kind, (22, 22), color),
                compound="left", height=58, corner_radius=9,
                fg_color=ACTION_BG, hover_color=ACTION_HOVER,
                border_width=1, border_color=ACTION_BORDER, text_color=TEXT,
                font=ctk.CTkFont("Poppins", 9, "bold"),
                command=lambda name=area: self._abrir_area(name),
            ).grid(row=0, column=column, sticky="nsew", padx=5)

    def _build_stats(self, parent):
        stats = ctk.CTkFrame(parent, fg_color="transparent", height=145)
        stats.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        stats.grid_propagate(False)
        definitions = (
            ("Ventas del día", "hand", BLUE, "Ventas", "Actividad de hoy"),
            ("Capital invertido", "clipboard", GREEN, "Inventario", "Inventario valorizado"),
            ("Productos bajos", "box", ORANGE, "Inventario", "Inventario saludable"),
            ("Ganancias del día", "profit", GREEN, "Rendimiento", "Utilidad real de hoy"),
        )
        self.stat_widgets = []
        for column, (title, kind, color, area, default_note) in enumerate(definitions):
            stats.grid_columnconfigure(column, weight=1, uniform="stats")
            card = self._card(stats, height=145)
            card.grid(
                row=0, column=column, sticky="nsew",
                padx=(0 if column == 0 else 8, 0 if column == 3 else 8),
            )
            card.grid_propagate(False)
            glow = ctk.CTkFrame(
                card, width=66, height=66, corner_radius=33,
                fg_color=GLOW_BACKGROUNDS[color],
                border_width=1,
                border_color=GLOW_BORDERS[color],
            )
            glow.place(x=18, rely=.5, anchor="w")
            ctk.CTkLabel(
                glow, text="", image=self._load_icon(kind, (40, 40), color)
            ).place(relx=.5, rely=.5, anchor="center")
            ctk.CTkLabel(
                card, text=title, text_color=MUTED,
                font=ctk.CTkFont("Poppins", 10), anchor="w",
            ).place(x=102, y=22)
            value = ctk.CTkLabel(
                card, text="--", text_color=TEXT,
                font=ctk.CTkFont("Poppins", 19, "bold"), anchor="w",
            )
            value.place(x=102, y=50)
            note = ctk.CTkLabel(
                card, text=default_note, text_color=color,
                font=ctk.CTkFont("Poppins", 9, "bold"), anchor="w",
            )
            note.place(x=102, y=91)
            for widget in card.winfo_children():
                widget.bind("<Button-1>", lambda _event, name=area: self._abrir_area(name))
                try:
                    widget.configure(cursor="hand2")
                except tk.TclError:
                    pass
            for widget in (card, glow, value, note):
                widget.bind("<Button-1>", lambda _event, name=area: self._abrir_area(name))
                try:
                    widget.configure(cursor="hand2")
                except tk.TclError:
                    pass
            self.stat_widgets.append((value, note))

    def _build_charts(self, parent):
        charts = ctk.CTkFrame(parent, fg_color="transparent")
        charts.grid(row=3, column=0, sticky="nsew")
        charts.grid_columnconfigure((0, 1), weight=1, uniform="charts")
        charts.grid_rowconfigure(0, weight=1)
        titles = ("Ventas de los últimos 7 días",)
        self.chart_titles = []
        self.period_buttons = []
        for column, title in enumerate(titles):
            panel = self._card(charts)
            panel.grid(
                row=0, column=column, sticky="nsew",
                padx=(0, 10),
            )
            panel.grid_columnconfigure(0, weight=1)
            panel.grid_rowconfigure(1, weight=1)
            header = ctk.CTkFrame(panel, fg_color="transparent", height=58)
            header.grid(row=0, column=0, sticky="ew", padx=18, pady=(8, 0))
            header.grid_propagate(False)
            label = ctk.CTkLabel(
                header, text=title, text_color=TEXT,
                font=ctk.CTkFont("Poppins", 12, "bold"), anchor="w",
            )
            label.place(x=0, y=9)
            button = ctk.CTkButton(
                header, text="7 días", width=78, height=32, corner_radius=8,
                fg_color=ACTION_BG, hover_color=ACTION_HOVER, text_color=MUTED,
                font=ctk.CTkFont("Poppins", 8), command=self._cycle_period,
            )
            button.place(relx=1, x=0, y=5, anchor="ne")
            canvas = tk.Canvas(panel, bg=CARD, highlightthickness=0, bd=0)
            canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
            canvas.bind("<Configure>", self._schedule_draw, add="+")
            self.chart_titles.append(label)
            self.period_buttons.append(button)
            self._charts.append(canvas)
        try:
            self._build_login_activity(charts)
        except Exception as exc:
            self.login_rows_frame = None
            fallback = self._card(charts)
            fallback.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
            ctk.CTkLabel(
                fallback, text="Actividad de inicio de sesión", text_color=TEXT,
                font=ctk.CTkFont("Poppins", 14, "bold"), anchor="w",
            ).place(x=24, y=24)
            ctk.CTkLabel(
                fallback, text=f"No se pudo cargar el panel: {exc}", text_color=MUTED,
                font=ctk.CTkFont("Poppins", 10), anchor="w",
            ).place(x=24, y=58)

    def _build_login_activity(self, parent):
        panel = self._card(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(panel, fg_color="transparent", height=74)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(12, 0))
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="Actividad de inicio de sesión", text_color=TEXT,
            font=ctk.CTkFont("Poppins", 13, "bold"), anchor="w",
        ).place(x=0, y=4)
        ctk.CTkLabel(
            header, text="Comprueba cuándo y dónde has iniciado sesión en tu cuenta.",
            text_color=MUTED, font=ctk.CTkFont("Poppins", 9), anchor="w",
        ).place(x=0, y=31)
        ctk.CTkButton(
            header, text="Cerrar otras sesiones", width=152, height=28,
            corner_radius=15, fg_color=ACTION_BG, hover_color=ACTION_HOVER,
            border_width=1, border_color="#9cc4ff", text_color="#0b66ff",
            font=ctk.CTkFont("Poppins", 9), command=self._cerrar_sesiones_remotas,
        ).place(relx=1, x=0, y=4, anchor="ne")

        table_header = ctk.CTkFrame(panel, fg_color="#cfe1f8", height=36, corner_radius=0)
        table_header.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 0))
        table_header.grid_propagate(False)
        for index, (text, width) in enumerate((
            ("Dispositivo", .22), ("Ubicación", .25), ("Fecha", .27), ("Navegador", .18),
        )):
            ctk.CTkLabel(
                table_header, text=text, text_color="#03133a",
                font=ctk.CTkFont("Poppins", 8), anchor="w",
            ).place(relx=sum((.22, .25, .27, .18)[:index]) + .025, rely=.5, anchor="w")

        self.login_rows_frame = ctk.CTkFrame(panel, fg_color="#f8fafc", corner_radius=0)
        self.login_rows_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self.login_rows_frame.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkFrame(panel, fg_color="#f8fafc", height=34, corner_radius=0)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_propagate(False)
        history = ctk.CTkLabel(
            footer, text="Ver historial de inicio de sesión", text_color="#0066ff",
            font=ctk.CTkFont("Poppins", 8),
        )
        history.place(x=24, y=9)
        try:
            history.configure(cursor="hand2")
        except tk.TclError:
            pass
        history.bind("<Button-1>", lambda _event: self._mostrar_historial_sesiones())

    def _obtener_session_id_actual(self):
        current = self.master
        while current is not None:
            session_id = getattr(current, "session_id", None)
            if session_id:
                return session_id
            current = getattr(current, "master", None)
        return None

    def _session_device_label(self, row):
        device = str(row.get("dispositivo_id") or "").lower()
        ip = str(row.get("ip") or "")
        if "iphone" in device or "ios" in device:
            return "iPhone"
        if "android" in device:
            return "Android"
        if ip and ip not in {"127.0.0.1", "::1"}:
            return "Dispositivo móvil"
        return "Windows"

    def _session_browser_label(self, row):
        ip = str(row.get("ip") or "")
        return "PWA/Safari" if ip and ip not in {"127.0.0.1", "::1"} else "Sistema"

    def _session_location_label(self, row):
        ip = str(row.get("ip") or "").strip()
        if not ip:
            return "Desconocida"
        if ip.startswith("192.168.") or ip.startswith("10.") or ip == "127.0.0.1":
            return f"Red local ({ip})"
        return ip

    def _session_date_label(self, value):
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", ""))
            return parsed.strftime("%d %b %Y, %H:%M").lstrip("0")
        except (TypeError, ValueError):
            return str(value or "Sin fecha")

    def _login_activity_rows(self, limit=3):
        try:
            with sqlite3.connect("database.db") as conn:
                conn.row_factory = sqlite3.Row
                user = conn.execute(
                    "SELECT id FROM usuarios WHERE lower(username)=lower(?)",
                    (self.usuario_actual,),
                ).fetchone()
                if not user:
                    return []
                rows = conn.execute(
                    """
                    SELECT id, dispositivo_id, inicio, ultima_actividad, cerrada, ip
                    FROM sesiones_usuario
                    WHERE usuario_id=?
                    ORDER BY datetime(inicio) DESC
                    LIMIT ?
                    """,
                    (user["id"], limit),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error:
            return []

    def _render_login_activity(self):
        if not getattr(self, "login_rows_frame", None):
            return
        for child in self.login_rows_frame.winfo_children():
            child.destroy()
        rows = self._login_activity_rows()
        if not rows:
            rows = [{
                "dispositivo_id": "windows", "inicio": datetime.now().isoformat(timespec="minutes"),
                "ip": "127.0.0.1", "cerrada": None,
            }]
        for index, row in enumerate(rows[:3]):
            item = ctk.CTkFrame(self.login_rows_frame, fg_color="#ffffff", height=52, corner_radius=0)
            item.grid(row=index, column=0, sticky="ew")
            item.grid_propagate(False)
            icon = "[PC]" if self._session_device_label(row) != "Android" else "[Móvil]"
            values = (
                f"{icon}  {self._session_device_label(row)}",
                self._session_location_label(row),
                self._session_date_label(row.get("inicio")),
                self._session_browser_label(row),
            )
            x_positions = (.025, .245, .495, .765)
            for value, x in zip(values, x_positions):
                ctk.CTkLabel(
                    item, text=value, text_color="#03133a",
                    font=ctk.CTkFont("Poppins", 8, "bold" if x == .025 else "normal"),
                    anchor="w",
                ).place(relx=x, rely=.5, anchor="w")
            ctk.CTkButton(
                item, text=">", width=30, height=30, corner_radius=15,
                fg_color="#f8fbff", hover_color="#e9f2ff",
                border_width=1, border_color="#c6ddff", text_color="#0066ff",
                command=lambda selected=row: self._mostrar_detalle_sesion(selected),
            ).place(relx=.965, rely=.5, anchor="e")
            tk.Frame(item, bg="#d8e0ea", height=1).place(relx=0, rely=1, relwidth=1, anchor="sw")

    def _mostrar_detalle_sesion(self, row):
        detalle = (
            f"Dispositivo: {self._session_device_label(row)}\n"
            f"Ubicación: {self._session_location_label(row)}\n"
            f"Fecha: {self._session_date_label(row.get('inicio'))}\n"
            f"Navegador: {self._session_browser_label(row)}\n"
            f"Estado: {'Cerrada' if row.get('cerrada') else 'Activa'}"
        )
        messagebox.showinfo("Detalle de sesión", detalle, parent=self)

    def _mostrar_historial_sesiones(self):
        rows = self._login_activity_rows(limit=12)
        if not rows:
            messagebox.showinfo("Historial de inicio de sesión", "No hay sesiones registradas todavía.", parent=self)
            return
        lines = [
            f"{self._session_date_label(row.get('inicio'))} · {self._session_device_label(row)} · {self._session_location_label(row)}"
            for row in rows
        ]
        messagebox.showinfo("Historial de inicio de sesión", "\n".join(lines), parent=self)

    def _cerrar_sesiones_remotas(self):
        actual = self._obtener_session_id_actual()
        try:
            with sqlite3.connect("database.db") as conn:
                user = conn.execute(
                    "SELECT id FROM usuarios WHERE lower(username)=lower(?)",
                    (self.usuario_actual,),
                ).fetchone()
                if not user:
                    return
                params = [datetime.now().isoformat(timespec="seconds"), "cerrada desde dashboard", user[0]]
                where = "usuario_id=? AND cerrada IS NULL"
                if actual:
                    where += " AND id<>?"
                    params.append(actual)
                cursor = conn.execute(
                    f"UPDATE sesiones_usuario SET cerrada=?, motivo_cierre=? WHERE {where}",
                    params,
                )
                conn.commit()
            self._render_login_activity()
            messagebox.showinfo(
                "Sesiones cerradas",
                f"Se cerraron {cursor.rowcount} sesión(es) en otros dispositivos.",
                parent=self,
            )
        except sqlite3.Error as exc:
            messagebox.showerror("No se pudo cerrar sesión", str(exc), parent=self)

    def _on_resize(self, event=None):
        if event is not None and event.widget is not self:
            return
        width = max(860, self.winfo_width())
        height = max(650, self.winfo_height())
        self._apply_content_size(width, height)

    def _update_scroll_region(self, _event=None):
        if hasattr(self, "scroll_canvas"):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_mousewheel(self, event):
        if not hasattr(self, "scroll_canvas"):
            return
        if getattr(event, "num", None) == 4:
            self.scroll_canvas.yview_scroll(-3, "units")
        elif getattr(event, "num", None) == 5:
            self.scroll_canvas.yview_scroll(3, "units")
        else:
            self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _apply_content_size(self, width, height):
        horizontal = 22 if width < 1200 else 32
        vertical = 14 if height < 760 else 22
        scrollbar_width = 18
        canvas_width = max(820, width - scrollbar_width)
        canvas_height = max(610, height)
        content_width = max(820, width - horizontal * 2 - scrollbar_width)
        content_height = max(850, height - vertical - 20)
        self.scroll_canvas.place_configure(x=0, y=0, width=canvas_width, height=canvas_height)
        self.content.configure(
            width=content_width,
            height=content_height,
        )
        self.scroll_canvas.itemconfigure(
            self.content_window, width=content_width, height=content_height,
        )
        self.scroll_canvas.coords(
            self.content_window, horizontal, vertical,
        )
        self._update_scroll_region()
        self._schedule_draw()

    def _schedule_draw(self, _event=None):
        if self._resize_after:
            try:
                self.after_cancel(self._resize_after)
            except tk.TclError:
                pass
        self._resize_after = self.after(35, self._draw_charts)

    def _cycle_period(self):
        self.period_days = 30 if self.period_days == 7 else 7
        period = f"{self.period_days} días"
        for button in self.period_buttons:
            button.configure(text=period)
        self.chart_titles[0].configure(text=f"Ventas de los últimos {self.period_days} días")
        self.cargar_datos()

    def _abrir_area(self, nombre):
        rutas = {
            "Ventas": "Ventas",
            "Inventario": "Inventario",
            "Abonos": "Abonos",
            "Compras": "Compras",
            "Rendimiento": "Rendimiento",
            "Clientes": "Clientes",
            "Pedidos": "Pedidos",
            "Proveedores": "Proveedor",
            "Configuracion": "Configuracion",
            "Informacion": "Informacion",
        }
        nombre = rutas.get(str(nombre), str(nombre))
        current = self.master
        while current is not None:
            method = getattr(current, nombre, None)
            if callable(method):
                method()
                return
            current = getattr(current, "master", None)

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        text = str(value).strip().split(" ")[0]
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def cargar_datos(self):
        now = datetime.now()
        self.session_label.configure(
            text=now.strftime("Sesión activa | %d/%m/%Y | %I:%M %p")
        )
        sales = [
            (self._parse_date(day), float(total or 0))
            for day, total in self._db_all("SELECT fecha, COALESCE(total, 0) FROM ventas")
        ]
        purchases = [
            (self._parse_date(day), float(total or 0))
            for day, total in self._db_all("SELECT fecha, COALESCE(total, 0) FROM compras")
        ]
        today = now.date()
        start_month = today.replace(day=1)
        today_total = sum(total for day, total in sales if day == today)
        invested_capital = self._db_one(
            """
            SELECT SUM(total) FROM (
                SELECT COALESCE(stock, 0) * COALESCE(costo, precio, 0) AS total FROM articulos
                UNION ALL
                SELECT COALESCE(stock, 0) * COALESCE(costo, precio, 0) AS total FROM productos
            )
            """, default=0
        )
        low = int(self._db_one(
            """
            SELECT SUM(cantidad) FROM (
                SELECT COUNT(*) AS cantidad FROM articulos WHERE COALESCE(stock, 0) <= 5
                UNION ALL
                SELECT COUNT(*) AS cantidad FROM productos WHERE COALESCE(stock, 0) <= 5
            )
            """, default=0
        ))
        profit_today = sum(
            (
                float(subtotal or 0)
                if subtotal is not None
                else float(total or 0) - float(iva or 0)
            ) - float(costo or 0)
            for day, total, subtotal, iva, costo in self._db_all(
                "SELECT fecha, total, subtotal, iva, costo FROM ventas"
            )
            if self._parse_date(day) == today
        )
        values = (
            (f"${today_total:,.2f}", "Actividad de hoy", BLUE),
            (f"${float(invested_capital or 0):,.2f}", "Inventario valorizado", GREEN),
            (str(low), "Atención requerida" if low else "Inventario saludable",
             ORANGE if low else GREEN),
            (f"${profit_today:,.2f}", "Utilidad real de hoy", GREEN if profit_today >= 0 else ORANGE),
        )
        for (value_widget, note_widget), (value, note, color) in zip(self.stat_widgets, values):
            value_widget.configure(text=value)
            note_widget.configure(text=note, text_color=color)

        days = [today - timedelta(days=offset) for offset in range(self.period_days - 1, -1, -1)]
        totals = [sum(total for day, total in sales if day == current) for current in days]
        operations = [
            sum(total for day, total in sales if day == current)
            + sum(total for day, total in purchases if day == current)
            for current in days
        ]
        self._series = days, totals, operations
        self._render_login_activity()
        self._schedule_draw()

    def _draw_charts(self):
        self._resize_after = None
        if not hasattr(self, "_series") or not self._charts:
            return
        days, sales, operations = self._series
        self._draw_line(self._charts[0], days, sales)

    @staticmethod
    def _nice_maximum(values):
        maximum = max(values or [0])
        if maximum <= 0:
            return 10000.0
        magnitude = 10 ** math.floor(math.log10(maximum))
        normalized = maximum / magnitude
        nice = 2 if normalized <= 2 else 5 if normalized <= 5 else 10
        return float(nice * magnitude)

    def _draw_line(self, canvas, days, values):
        try:
            width = max(420, canvas.winfo_width())
            height = max(120, canvas.winfo_height())
        except tk.TclError:
            return
        canvas.delete("all")
        left, top, right, bottom = 58, 16, width - 18, height - 34
        maximum = self._nice_maximum(values)
        for index in range(4):
            y = top + (bottom - top) * index / 3
            canvas.create_line(left, y, right, y, fill=GRID, width=1)
            amount = maximum * (3 - index) / 3
            label = f"{amount / 1000:.0f}K" if amount >= 1000 else f"{amount:.0f}"
            canvas.create_text(
                left - 12, y, text=label, anchor="e",
                fill=MUTED, font=("Poppins", 8),
            )

        points = []
        length = len(values)
        label_step = 1 if length <= 7 else 5
        for index, value in enumerate(values):
            x = left + (right - left) * index / max(1, length - 1)
            y = bottom - (bottom - top) * min(max(value, 0), maximum) / maximum
            points.extend((x, y))
            if index % label_step == 0 or index == length - 1:
                if length <= 7:
                    label = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")[days[index].weekday()]
                else:
                    label = days[index].strftime("%d/%m")
                canvas.create_text(
                    x, bottom + 19, text=label, fill=MUTED, font=("Poppins", 8)
                )
        if len(points) >= 4:
            canvas.create_line(*points, fill=LINE_GLOW_OUTER, width=7, smooth=True)
            canvas.create_line(*points, fill=LINE_GLOW_INNER, width=4, smooth=True)
            canvas.create_line(*points, fill=BLUE, width=2, smooth=True)
        for index in range(0, len(points), 2):
            if length > 14 and (index // 2) % label_step:
                continue
            x, y = points[index], points[index + 1]
            canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill=POINT_GLOW, outline="")
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=TEXT, outline=BLUE, width=2)

    def aplicar_tema(self, oscuro=False):
        """Reconstruye el panel con tokens claros u oscuros consistentes."""
        oscuro = bool(oscuro)
        if self._modo_oscuro == oscuro:
            self.tk.call(self._w, 'configure', '-background', BG)
            self._schedule_draw()
            return
        self._modo_oscuro = oscuro
        if self._resize_after is not None:
            try:
                self.after_cancel(self._resize_after)
            except (tk.TclError, ValueError):
                pass
            self._resize_after = None

        _set_palette(oscuro)
        for child in self.winfo_children():
            child.destroy()
        self._images.clear()
        self._charts.clear()
        self.tk.call(self._w, 'configure', '-background', BG)
        self._build()
        self.cargar_datos()
        self.after_idle(self._on_resize)

    def ajustar_layout(self, ancho=None, alto=None):
        if ancho is not None and alto is not None:
            self._apply_content_size(max(860, int(ancho)), max(650, int(alto)))
        self.after_idle(self._on_resize)
