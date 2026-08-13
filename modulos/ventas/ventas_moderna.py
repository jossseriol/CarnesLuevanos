import sqlite3
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
import datetime
import threading
from PIL import Image, ImageTk

import sys
import os

from modulos.ventas.crear_factura import generar_factura
from modulos.ventas.obtener_numero_factura import obtener_numero_factura_actual
from modulos.utils.estilos_modernos import estilos
from modulos.configuracion.gestor_configuracion import obtener_configuracion

class VentasModerna(tk.Frame):
    """Versión moderna de la interfaz de ventas con mejor diseño"""
    
    COLORS = estilos.COLORS

    db_name = "database.db"
    UI_BG = '#f5f6f8'
    UI_CARD = '#ffffff'
    UI_BORDER = '#e3e6ea'
    UI_TEXT = '#20242a'
    UI_MUTED = '#68707c'
    UI_ACCENT = '#8f070c'
    
    def __init__(self, padre):
        super().__init__(padre)
        self.configure(bg=self.COLORS['light'])
        self.numero_factura = obtener_numero_factura_actual()
        self.productos_seleccionados = []
        self._nota_sin_iva = False
        self.crear_tablas_credito_abonos()
        self.setup_styles()
        self.widgets_modernos()
        self._ventas_breakpoint = None
        self.bind('<Configure>', self._programar_ajuste_ventas, add='+')
        self.timer_producto = None
        self.timer_cliente = None
        
        # Cargar datos después de crear widgets
        self.cargar_productos()
        self.cargar_clientes()
        
        # Iniciar actualización de hora en tiempo real
        self.actualizar_hora()
    

    def setup_styles(self):
        """Configurar estilos modernos para los widgets"""
        style = ttk.Style()
        
        # Estilo para labels modernos
        style.configure('Modern.TLabel', 
                       background=self.COLORS['light'],
                       foreground=self.COLORS['primary'],
                       font=('Poppins', 11, 'bold'))
        
        # Estilo para botones modernos
        style.configure('Modern.TButton',
                       font=('Poppins', 10, 'bold'),
                       padding=(20, 10))
        
        # Estilo para entries modernos
        style.configure('Modern.TEntry',
                       font=('Poppins', 11),
                       fieldbackground=self.COLORS['white'],
                       foreground='#20242a',
                       insertcolor='#20242a')
        
        # Estilo para combobox modernos
        style.configure('Modern.TCombobox',
                       font=('Poppins', 11),
                       fieldbackground=self.COLORS['white'],
                       foreground='#20242a',
                       selectforeground='#20242a',
                       selectbackground='#ffffff')
        style.configure('Ventas.Treeview', font=('Poppins', 9), rowheight=27,
                        background=self.UI_CARD, fieldbackground=self.UI_CARD,
                        foreground=self.UI_TEXT, borderwidth=0)
        style.configure('Ventas.Treeview.Heading', font=('Poppins', 9, 'bold'),
                        background='#f0f1f3', foreground=self.UI_TEXT, relief='flat')
        style.map('Ventas.Treeview', background=[('selected', '#f6dede')],
                  foreground=[('selected', self.UI_TEXT)])

    def aplicar_tema(self, oscuro=False):
        """Ajusta campos ttk de Ventas para que el texto sea legible."""
        style = ttk.Style()
        if oscuro:
            input_bg = '#ffffff'
            input_text = '#20242a'
            border = '#c9d3df'
            selected_bg = '#dbeeff'
        else:
            input_bg = '#ffffff'
            input_text = '#20242a'
            border = '#e3e6ea'
            selected_bg = '#dbeeff'
        style.configure(
            'Modern.TEntry',
            fieldbackground=input_bg,
            background=input_bg,
            foreground=input_text,
            insertcolor=input_text,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
        )
        style.configure(
            'Modern.TCombobox',
            fieldbackground=input_bg,
            background=input_bg,
            foreground=input_text,
            selectforeground=input_text,
            selectbackground=selected_bg,
            arrowcolor=input_text,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
        )

    def crear_frame_moderno(self, parent, title, x, y, width, height):
        """Crear un frame moderno con título"""
        # Frame principal con sombra simulada
        shadow_frame = tk.Frame(parent, bg='#e8d8d5', height=height+3, width=width+3)
        shadow_frame.place(x=x+3, y=y+3)
        
        main_frame = tk.Frame(parent, bg=self.COLORS['white'], 
                             relief='flat', bd=1, highlightbackground=self.COLORS['primary'],
                             highlightthickness=1)
        main_frame.place(x=x, y=y, width=width, height=height)
        
        # Título del frame
        title_frame = tk.Frame(main_frame, bg=self.COLORS['primary'], height=30)
        title_frame.pack(fill='x', side='top')
        
        title_label = tk.Label(title_frame, text=title, 
                              bg=self.COLORS['primary'], fg=self.COLORS['white'],
                              font=('Poppins', 12, 'bold'))
        title_label.pack(pady=8)
        
        # Frame de contenido
        content_frame = tk.Frame(main_frame, bg=self.COLORS['white'])
        content_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        return content_frame

    def crear_boton_moderno(self, parent, text, command, color='secondary', x=0, y=0, width=150, height=40):
        """Crear un botón moderno con efectos hover"""
        btn_frame = tk.Frame(parent, bg=self.COLORS['white'])
        btn_frame.place(x=x, y=y, width=width, height=height)
        
        btn = tk.Button(btn_frame, text=text, command=command,
                       bg=self.COLORS[color], fg=self.COLORS['white'],
                       font=('Poppins', 10, 'bold'), relief='flat',
                       cursor='hand2', bd=0)
        btn.pack(fill='both', expand=True)
        
        # Efectos hover
        def on_enter(e):
            btn.configure(bg=self.ajustar_color(self.COLORS[color], -20))
        
        def on_leave(e):
            btn.configure(bg=self.COLORS[color])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def ajustar_color(self, color, amount):
        """Ajustar el brillo de un color hex"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def widgets_modernos(self):
        """Crear una pantalla de ventas minimalista y adaptable."""
        self.configure(bg=self.UI_BG)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title_frame = tk.Frame(self, bg=self.UI_BG, height=54)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        main_title = tk.Label(
            title_frame, text="Módulo de Ventas",
            bg=self.UI_BG, fg=self.UI_TEXT,
            font=('Poppins', 17, 'bold'), anchor='w'
        )
        main_title.grid(row=0, column=0, sticky="ew", padx=18, pady=(8, 0))
        tk.Label(title_frame, text='Registra productos, controla existencias y procesa el cobro.',
                 bg=self.UI_BG, fg=self.UI_MUTED,
                 font=('Poppins', 9), anchor='w').grid(row=1, column=0, sticky='ew', padx=20, pady=(0, 7))

        self.content_frame = tk.Frame(self, bg=self.UI_BG)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 12))
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=4, minsize=480)
        self.content_frame.grid_columnconfigure(1, weight=1, minsize=235)

        info_frame = tk.Frame(self.content_frame, bg=self.UI_CARD, highlightthickness=1,
                              highlightbackground=self.UI_BORDER)
        self.info_frame = info_frame
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for col in range(8):
            info_frame.grid_columnconfigure(col, weight=1, uniform="info")

        tk.Label(info_frame, text="Datos de la venta", bg=self.UI_CARD,
                 fg=self.UI_TEXT, font=('Poppins', 11, 'bold'),
                 anchor='w').grid(row=0, column=0, columnspan=8, sticky="ew", padx=14, pady=(10, 5))

        self.crear_label_campo(info_frame, "Folio de nota", 1, 0)
        self.entry_folio = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_folio.grid(row=2, column=0, sticky="ew", padx=(14, 6), pady=(0, 8), ipady=4)
        self.entry_folio.bind('<KeyRelease>', self._actualizar_identidad_detalle, add='+')

        self.crear_label_campo(info_frame, "Fecha", 1, 1)
        self.entry_fecha = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_fecha.grid(row=2, column=1, sticky="ew", padx=6, pady=(0, 8), ipady=4)
        self.entry_fecha.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))

        self.crear_label_campo(info_frame, "Hora", 1, 2)
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        self.label_hora = tk.Label(info_frame, text=hora_actual, bg=self.UI_CARD,
                                   fg=self.UI_TEXT, font=('Poppins', 10, 'bold'), anchor='w')
        self.label_hora.grid(row=2, column=2, sticky="ew", padx=6, pady=(0, 8))

        self.crear_label_campo(info_frame, "Vendedor / entrega", 1, 3)
        self.entry_vendedor = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_vendedor.grid(row=2, column=3, columnspan=2, sticky="ew", padx=6, pady=(0, 8), ipady=4)

        tk.Label(info_frame, text='Disponibilidad', bg=self.UI_CARD, fg=self.UI_MUTED,
                 font=('Poppins', 9, 'bold'), anchor='w').grid(row=1, column=5, columnspan=3, sticky='ew', padx=6, pady=(2, 3))
        self.label_stock = tk.Label(info_frame, text="Stock: --", bg=self.UI_CARD,
                                    fg=self.UI_ACCENT, font=('Poppins', 10, 'bold'), anchor='w')
        self.label_stock.grid(row=2, column=5, columnspan=3, sticky="ew", padx=(6, 14), pady=(0, 8))

        self.crear_label_campo(info_frame, "Cliente", 3, 0)
        self.entry_cliente = ttk.Combobox(info_frame, font=('Poppins', 10), style='Modern.TCombobox')
        self.entry_cliente.grid(row=4, column=0, columnspan=2, sticky="ew", padx=(14, 6), pady=(0, 8), ipady=4)
        self.entry_cliente.bind('<KeyRelease>', self.filtrar_clientes)
        self.entry_cliente.bind('<<ComboboxSelected>>', self._cliente_seleccionado, add='+')
        self.entry_cliente.bind('<FocusOut>', self._cliente_seleccionado, add='+')

        self.crear_label_campo(info_frame, "Dirección", 3, 2)
        self.entry_direccion = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_direccion.grid(row=4, column=2, columnspan=3, sticky="ew", padx=6, pady=(0, 8), ipady=4)

        self.crear_label_campo(info_frame, "Teléfono", 3, 5)
        self.entry_telefono = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_telefono.grid(row=4, column=5, sticky="ew", padx=6, pady=(0, 8), ipady=4)

        self.crear_label_campo(info_frame, "Abono anotado", 3, 6)
        self.entry_abono_nota = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_abono_nota.grid(row=4, column=6, columnspan=2, sticky="ew", padx=(6, 14), pady=(0, 8), ipady=4)

        # Se conserva para lectores de codigo, pero ya no ocupa espacio en el formulario.
        self.entry_codigo = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_codigo.bind('<KeyRelease>', self.buscar_por_codigo)
        self.entry_codigo.bind('<Return>', self.buscar_por_codigo)

        self.crear_label_campo(info_frame, "Descripción", 5, 0)
        self.entry_producto = ttk.Combobox(info_frame, font=('Poppins', 10), style='Modern.TCombobox', state='normal')
        self.entry_producto.grid(row=6, column=0, columnspan=5, sticky="ew", padx=(14, 6), pady=(0, 12), ipady=4)
        self.entry_producto.bind("<<ComboboxSelected>>", self.actualizar_stock)
        self.entry_producto.bind('<Button-1>', self.mostrar_productos)
        self.entry_producto.bind('<KeyRelease>', self.filtrar_productos)
        self.entry_producto.bind('<Return>', self.actualizar_stock)

        self.crear_label_campo(info_frame, "Cantidad", 5, 5)
        self.entry_cantidad = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_cantidad.grid(row=6, column=5, sticky="ew", padx=6, pady=(0, 12), ipady=4)
        self.entry_cantidad.bind('<Return>', lambda event: self.agregar_producto())

        self.crear_label_campo(info_frame, "P. unitario", 5, 6)
        self.entry_precio_unitario = ttk.Entry(info_frame, font=('Poppins', 10), style='Modern.TEntry')
        self.entry_precio_unitario.grid(row=6, column=6, sticky="ew", padx=6, pady=(0, 12), ipady=4)

        btn_agregar = tk.Button(
            info_frame, text="Agregar",
            command=self.agregar_producto,
            bg=self.UI_ACCENT, fg='white', activebackground='#6f0509', activeforeground='white',
            font=('Poppins', 9, 'bold'), relief='flat',
            cursor='hand2', bd=0, padx=10
        )
        btn_agregar.grid(row=6, column=7, sticky="ew", padx=(6, 14), pady=(0, 12), ipady=6)
        self.configurar_hover_boton(btn_agregar, self.UI_ACCENT)

        productos_frame = tk.Frame(self.content_frame, bg=self.UI_CARD, highlightthickness=1,
                                   highlightbackground=self.UI_BORDER)
        self.productos_frame = productos_frame
        productos_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        productos_frame.grid_rowconfigure(1, weight=1)
        productos_frame.grid_columnconfigure(0, weight=1)

        tk.Label(productos_frame, text="Detalle de la venta", bg=self.UI_CARD,
                 fg=self.UI_TEXT, font=('Poppins', 11, 'bold'),
                 anchor='w').grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))

        table_frame = tk.Frame(productos_frame, bg=self.COLORS['white'])
        table_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree_productos = ttk.Treeview(
            table_frame, columns=("Folio", "Cliente", "Producto", "Precio", "Cantidad", "Total"),
            show="headings", height=12, style='Ventas.Treeview'
        )
        columnas = {
            "Folio": (90, "center"),
            "Cliente": (150, "w"),
            "Producto": (220, "w"),
            "Precio": (90, "center"),
            "Cantidad": (80, "center"),
            "Total": (100, "center"),
        }
        for columna, (ancho, alineacion) in columnas.items():
            self.tree_productos.heading(columna, text=columna)
            self.tree_productos.column(columna, width=ancho, anchor=alineacion, stretch=True)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_productos.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_productos.xview)
        self.tree_productos.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree_productos.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        acciones_productos = tk.Frame(productos_frame, bg=self.COLORS['white'])
        acciones_productos.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        acciones_productos.grid_columnconfigure(0, weight=1)

        btn_eliminar_producto = tk.Button(
            acciones_productos, text="Eliminar seleccionado",
            command=self.eliminar_producto_seleccionado,
            bg=self.COLORS['danger'], fg=self.COLORS['white'],
            font=('Poppins', 10, 'bold'), relief='flat',
            cursor='hand2', bd=0
        )
        btn_eliminar_producto.grid(row=0, column=0, sticky="e", ipady=7, ipadx=12)
        self.configurar_hover_boton(btn_eliminar_producto, self.COLORS['danger'])
        self.tree_productos.bind('<Delete>', lambda event: self.eliminar_producto_seleccionado())

        totales_frame = tk.Frame(self.content_frame, bg=self.UI_CARD, highlightthickness=1,
                                 highlightbackground=self.UI_BORDER)
        self.totales_frame = totales_frame
        totales_frame.grid(row=1, column=1, sticky="nsew")
        totales_frame.grid_columnconfigure(0, weight=1)

        tk.Label(totales_frame, text="Resumen de cobro", bg=self.UI_CARD,
                 fg=self.UI_TEXT, font=('Poppins', 11, 'bold'),
                 anchor='w').grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 10))

        self.label_sub_total = tk.Label(totales_frame, text='Subtotal: $0.00',
                                        font=('Poppins', 11, 'bold'), bg=self.COLORS['white'],
                                        fg=self.COLORS['primary'], anchor='w')
        self.label_sub_total.grid(row=1, column=0, sticky="ew", padx=18, pady=(8, 4))

        self.label_iva = tk.Label(totales_frame, text=f'{self.texto_iva()}: $0.00',
                                  font=('Poppins', 11), bg=self.COLORS['white'],
                                  fg=self.COLORS['dark'], anchor='w')
        self.label_iva.grid(row=2, column=0, sticky="ew", padx=18, pady=4)

        self.label_precio_total = tk.Label(totales_frame, text='TOTAL: $0.00',
                                           font=('Poppins', 15, 'bold'), bg=self.COLORS['white'],
                                           fg=self.COLORS['success'], anchor='w')
        self.label_precio_total.grid(row=3, column=0, sticky="ew", padx=18, pady=(8, 18))

        btn_procesar = tk.Button(
            totales_frame, text="Procesar pago",
            command=self.abrir_modal_pago,
            bg=self.UI_ACCENT, fg='white', activebackground='#6f0509', activeforeground='white',
            font=('Poppins', 10, 'bold'), relief='flat',
            cursor='hand2', bd=0
        )
        btn_procesar.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 10), ipady=10)
        self.configurar_hover_boton(btn_procesar, self.UI_ACCENT)

        acciones_frame = tk.Frame(totales_frame, bg=self.COLORS['white'])
        acciones_frame.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 18))
        acciones_frame.grid_columnconfigure(0, weight=1)
        acciones_frame.grid_columnconfigure(1, weight=1)

        btn_ver_ventas = tk.Button(
            acciones_frame, text="Ver ventas",
            command=self.ver_ventas_realizadas,
            bg='#eef0f2', fg=self.UI_TEXT,
            font=('Poppins', 10, 'bold'), relief='flat',
            cursor='hand2', bd=0
        )
        btn_ver_ventas.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=7)
        self.configurar_hover_boton(btn_ver_ventas, '#eef0f2')

        btn_limpiar = tk.Button(
            acciones_frame, text="Limpiar",
            command=self.limpiar_venta,
            bg='#eef0f2', fg=self.UI_TEXT,
            font=('Poppins', 10, 'bold'), relief='flat',
            cursor='hand2', bd=0
        )
        btn_limpiar.grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=7)
        self.configurar_hover_boton(btn_limpiar, '#eef0f2')

    def crear_label_campo(self, parent, texto, row, column):
        tk.Label(parent, text=texto, font=('Poppins', 9, 'bold'),
                 bg=self.UI_CARD, fg=self.UI_MUTED,
                 anchor='w').grid(row=row, column=column, sticky="ew", padx=14 if column == 0 else 8, pady=(2, 3))

    def configurar_hover_boton(self, boton, color):
        boton.bind("<Enter>", lambda event: boton.configure(bg=self.ajustar_color(color, -20)))
        boton.bind("<Leave>", lambda event: boton.configure(bg=color))

    def _programar_ajuste_ventas(self, event=None):
        if event is not None and event.widget is not self:
            return
        if getattr(self, '_ventas_layout_after', None):
            try:
                self.after_cancel(self._ventas_layout_after)
            except Exception:
                pass
        self._ventas_layout_after = self.after(70, self._ajustar_layout_ventas)

    def _ajustar_layout_ventas(self):
        """Cambia entre dos columnas y diseño apilado sin escalar controles."""
        if not hasattr(self, 'content_frame'):
            return
        ancho = max(1, self.winfo_width())
        # La ventana principal garantiza al menos ~860 px para el módulo;
        # en ese rango las dos columnas conservan más área útil que apilarlas.
        compacto = ancho < 760
        if compacto == self._ventas_breakpoint:
            return
        self._ventas_breakpoint = compacto
        if compacto:
            self.content_frame.grid_columnconfigure(0, weight=1, minsize=0)
            self.content_frame.grid_columnconfigure(1, weight=0, minsize=0)
            self.content_frame.grid_rowconfigure(1, weight=1)
            self.content_frame.grid_rowconfigure(2, weight=0)
            self.productos_frame.grid_configure(row=1, column=0, columnspan=2, padx=0, pady=(0, 10))
            self.totales_frame.grid_configure(row=2, column=0, columnspan=2, sticky='ew')
        else:
            self.content_frame.grid_columnconfigure(0, weight=4, minsize=480)
            self.content_frame.grid_columnconfigure(1, weight=1, minsize=235)
            self.content_frame.grid_rowconfigure(1, weight=1)
            self.content_frame.grid_rowconfigure(2, weight=0)
            self.productos_frame.grid_configure(row=1, column=0, columnspan=1, padx=(0, 10), pady=0)
            self.totales_frame.grid_configure(row=1, column=1, columnspan=1, sticky='nsew')

    # Métodos heredados (necesarios para mantener funcionalidad)
    def cargar_productos(self):
        """Cargar productos disponibles desde inventario."""
        self.productos_dict = {}
        self.productos_nombres = []
        self.productos_codigos = []
        self.productos_por_nombre = {}

        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            productos_data = []

            if self.tabla_existe(c, "articulos"):
                c.execute("""
                    SELECT codigo, articulo, precio, stock, 'articulos'
                    FROM articulos
                    WHERE stock > 0 AND LOWER(COALESCE(estado, 'activo')) = 'activo'
                    ORDER BY articulo
                """)
                productos_data.extend(c.fetchall())

            if self.tabla_existe(c, "productos"):
                c.execute("""
                    SELECT codigo, nombre, precio, stock, 'productos'
                    FROM productos
                    WHERE stock > 0
                    ORDER BY nombre
                """)
                productos_data.extend(c.fetchall())

            conn.close()

            vistos = set()
            for codigo, nombre, precio, stock, tabla in productos_data:
                nombre = str(nombre or "").strip()
                codigo = str(codigo or "").strip()
                if not nombre:
                    continue

                clave = (tabla, codigo, nombre.lower())
                if clave in vistos:
                    continue
                vistos.add(clave)

                display = f"{nombre} ({codigo})" if codigo else nombre
                info = {
                    'codigo': codigo,
                    'nombre': nombre,
                    'precio': float(precio or 0),
                    'stock': int(stock or 0),
                    'tabla': tabla,
                    'display': display,
                }

                self.productos_nombres.append(display)
                self.productos_por_nombre[nombre.lower()] = info
                if codigo:
                    self.productos_dict[codigo] = info
                    self.productos_codigos.append(codigo)

            if hasattr(self, 'entry_producto'):
                self.entry_producto['values'] = self.productos_nombres

            if not self.productos_nombres and hasattr(self, 'label_stock'):
                self.label_stock.config(text="Stock: sin productos disponibles", fg=self.COLORS['danger'])
        except sqlite3.Error as e:
            self.productos_nombres = []
            self.productos_dict = {}
            self.productos_codigos = []
            self.productos_por_nombre = {}
            if hasattr(self, 'entry_producto'):
                self.entry_producto['values'] = []
            messagebox.showerror("Error de inventario", f"No se pudieron cargar los productos: {e}")

    def tabla_existe(self, cursor, tabla):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
        return cursor.fetchone() is not None

    def normalizar_cantidad(self, valor):
        valor = valor.strip().replace(",", ".")
        cantidad = float(valor)
        if cantidad <= 0:
            raise ValueError
        return int(cantidad) if cantidad.is_integer() else cantidad

    def obtener_info_producto(self, texto_producto):
        texto_producto = texto_producto.strip()
        if not texto_producto or texto_producto in ("No hay productos disponibles", "Error cargando productos"):
            return None

        codigo = ""
        nombre = texto_producto
        if '(' in texto_producto and ')' in texto_producto:
            inicio = texto_producto.rfind('(')
            fin = texto_producto.rfind(')')
            codigo = texto_producto[inicio + 1:fin].strip()
            nombre = texto_producto[:inicio].strip()

        if codigo and codigo in self.productos_dict:
            return self.productos_dict[codigo]

        nombre_key = nombre.lower()
        if nombre_key in self.productos_por_nombre:
            return self.productos_por_nombre[nombre_key]

        for info in self.productos_por_nombre.values():
            if nombre_key and nombre_key in info['nombre'].lower():
                return info
        return None

    def cargar_clientes(self):
        """Cargar clientes desde la base de datos"""
        self.clientes_info = {}
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Verificar si la tabla clientes existe
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
            if not c.fetchone():
                # Si no existe, crear algunos clientes de ejemplo
                c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            email TEXT,
                            telefono TEXT)''')
                
                # Insertar clientes de ejemplo
                clientes_ejemplo = [
                    ("Cliente Ejemplo 1", "cliente1@email.com", "123-456-7890"),
                    ("Cliente Ejemplo 2", "cliente2@email.com", "123-456-7891"),
                    ("Cliente Ejemplo 3", "cliente3@email.com", "123-456-7892"),
                    ("Cliente General", "general@tienda.com", "123-456-0000")
                ]
                
                c.executemany("INSERT INTO clientes (nombre, email, telefono) VALUES (?, ?, ?)", 
                             clientes_ejemplo)
                conn.commit()
                print("Clientes de ejemplo creados")
            
            columnas = {col[1] for col in c.execute("PRAGMA table_info(clientes)").fetchall()}
            direccion_expr = "direccion" if "direccion" in columnas else "''"
            telefono_expr = "celular" if "celular" in columnas else ("telefono" if "telefono" in columnas else "''")
            correo_expr = "correo" if "correo" in columnas else ("email" if "email" in columnas else "''")

            # Cargar clientes con datos de contacto para autorrellenar la venta.
            c.execute(f"""
                SELECT nombre, COALESCE({direccion_expr}, ''), COALESCE({telefono_expr}, ''), COALESCE({correo_expr}, '')
                FROM clientes
                WHERE TRIM(COALESCE(nombre, '')) != ''
                ORDER BY nombre
            """)
            clientes = c.fetchall()
            self.clientes = []
            for nombre, direccion, telefono, correo in clientes:
                nombre = str(nombre or "").strip()
                if not nombre:
                    continue
                self.clientes.append(nombre)
                self.clientes_info[nombre.lower()] = {
                    'nombre': nombre,
                    'direccion': str(direccion or '').strip(),
                    'telefono': str(telefono or '').strip(),
                    'correo': str(correo or '').strip(),
                }
            
            if self.clientes:
                self.entry_cliente['values'] = self.clientes
                print(f"Cargados {len(self.clientes)} clientes")
            else:
                self.clientes = ["Cliente General"]
                self.entry_cliente['values'] = self.clientes
                print("No se encontraron clientes")
                
            conn.close()
        except sqlite3.Error as e:
            print(f"Error cargando clientes: {e}")
            # Cliente por defecto en caso de error
            self.clientes_info = {}
            self.clientes = ["Cliente General"]
            self.entry_cliente['values'] = self.clientes

    def filtrar_clientes(self, event):
        """Filtrar clientes mientras se escribe"""
        if self.timer_cliente: 
            self.timer_cliente.cancel()
        self.timer_cliente = threading.Timer(0.5, self._filter_clientes)
        self.timer_cliente.start()
        self.after(250, self._autorrellenar_cliente_si_exacto)

    def _filter_clientes(self):
        """Aplicar filtro de clientes"""
        texto = self.entry_cliente.get().lower()
        if texto:
            clientes_filtrados = [c for c in self.clientes if texto in c.lower()]
            self.entry_cliente['values'] = clientes_filtrados
        else:
            self.entry_cliente['values'] = self.clientes

    def _cliente_seleccionado(self, event=None):
        """Autorrellena datos del cliente y sincroniza la tabla de detalle."""
        self._autorrellenar_cliente_si_exacto()
        self._actualizar_identidad_detalle(event)

    def _autorrellenar_cliente_si_exacto(self):
        """Completa direccion y telefono cuando el cliente escrito existe."""
        if not hasattr(self, 'clientes_info'):
            return
        nombre = self.entry_cliente.get().strip().lower()
        cliente = self.clientes_info.get(nombre)
        if not cliente:
            return
        self._escribir_entry(self.entry_direccion, cliente.get('direccion', ''))
        self._escribir_entry(self.entry_telefono, cliente.get('telefono', ''))

    def filtrar_productos(self, event):
        """Filtrar productos mientras se escribe con autocompletado mejorado"""
        if self.timer_producto:
            self.timer_producto.cancel()
        self.timer_producto = threading.Timer(0.3, self._filter_productos)
        self.timer_producto.start()

    def _filter_productos(self):
        """Aplicar filtro de productos"""
        texto = self.entry_producto.get().lower()
        if texto and hasattr(self, 'productos_nombres'):
            productos_filtrados = [p for p in self.productos_nombres if texto in p.lower()]
            self.entry_producto['values'] = productos_filtrados
        else:
            if hasattr(self, 'productos_nombres'):
                self.entry_producto['values'] = self.productos_nombres

    def actualizar_stock(self, event=None):
        """Actualizar el stock del producto seleccionado."""
        try:
            info = self.obtener_info_producto(self.entry_producto.get())
            if not info:
                self.label_stock.config(text="Stock: --", fg=self.COLORS['dark'])
                return

            if info['codigo']:
                self.entry_codigo.delete(0, tk.END)
                self.entry_codigo.insert(0, info['codigo'])

            stock = info['stock']
            self.label_stock.config(
                text=f"Stock: {stock} unidades",
                fg=self.COLORS['success'] if stock > 10 else self.COLORS['warning']
            )
            if hasattr(self, 'entry_precio_unitario'):
                self.entry_precio_unitario.delete(0, tk.END)
                self.entry_precio_unitario.insert(0, f"{info['precio']:.2f}")
        except Exception as e:
            print(f"Error actualizando stock: {e}")
            self.label_stock.config(text="Stock: --", fg=self.COLORS['dark'])

    def agregar_producto(self):
        """Agregar producto a la lista de venta."""
        producto_texto = self.entry_producto.get().strip()
        cantidad_str = self.entry_cantidad.get().strip()

        if not producto_texto or not cantidad_str:
            messagebox.showwarning("Advertencia", "Selecciona un producto e ingresa la cantidad.")
            return

        try:
            cantidad = self.normalizar_cantidad(cantidad_str)
        except ValueError:
            messagebox.showerror("Error de cantidad", "La cantidad debe ser un numero entero valido mayor a 0.")
            return

        info = self.obtener_info_producto(producto_texto)
        precio_escrito = self.entry_precio_unitario.get().strip() if hasattr(self, 'entry_precio_unitario') else ''
        try:
            precio_manual = self.convertir_monto(precio_escrito) if precio_escrito else 0.0
        except ValueError:
            messagebox.showerror("Precio invalido", "Escribe un precio unitario valido.")
            return
        if not info and precio_manual <= 0:
            messagebox.showerror(
                "Falta el precio",
                "La descripcion no esta en Inventario. Escribe el precio unitario para capturarla como renglon de nota fisica."
            )
            return

        if info:
            cantidad_en_carrito = sum(
                p['cantidad'] for p in self.productos_seleccionados
                if (info['codigo'] and p.get('codigo') == info['codigo']) or
                (not info['codigo'] and p['nombre'].lower() == info['nombre'].lower())
            )
            disponible = info['stock'] - cantidad_en_carrito

            if cantidad > disponible:
                messagebox.showerror("Stock insuficiente", f"Solo hay {disponible} unidades disponibles para agregar.")
                return

        precio = precio_manual or (info['precio'] if info else 0.0)
        total = precio * cantidad
        nombre_real = info['nombre'] if info else producto_texto

        folio = self.entry_folio.get().strip() or 'Sin folio'
        cliente = self.entry_cliente.get().strip() or 'Cliente General'
        self.tree_productos.insert("", "end", values=(folio, cliente, nombre_real, f"${precio:,.2f}", cantidad, f"${total:,.2f}"))
        self.productos_seleccionados.append({
            'folio': folio,
            'cliente': cliente,
            'nombre': nombre_real,
            'precio': precio,
            'cantidad': cantidad,
            'total': total,
            'codigo': info['codigo'] if info else '',
            'tabla': info['tabla'] if info else '',
            'origen_nota': not bool(info),
        })

        self.entry_producto.set("")
        self.entry_codigo.delete(0, tk.END)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_precio_unitario.delete(0, tk.END)
        self.label_stock.config(text="Stock: --", fg=self.COLORS['dark'])
        self.actualizar_totales()

    def obtener_porcentaje_iva(self):
        """Obtener porcentaje de IVA configurado."""
        try:
            iva = float(str(obtener_configuracion('iva_porcentaje', '16')).replace(',', '.'))
            if iva < 0 or iva > 100:
                return 16.0
            return iva
        except Exception:
            return 16.0

    def obtener_tasa_iva(self):
        return self.obtener_porcentaje_iva() / 100

    def refrescar_iva(self):
        """Recalcula etiquetas y totales usando el IVA guardado en Configuracion."""
        if hasattr(self, 'label_iva'):
            self.actualizar_totales()

    def convertir_monto(self, valor):
        limpio = str(valor or "").replace("$", "").replace(",", "").strip()
        return float(limpio) if limpio else 0.0

    def reconstruir_productos_desde_tabla(self):
        if not hasattr(self, 'tree_productos') or not hasattr(self, 'productos_seleccionados'):
            return
        if self.productos_seleccionados:
            return

        productos = []
        for item in self.tree_productos.get_children():
            valores = self.tree_productos.item(item, "values")
            if len(valores) < 6:
                continue
            folio = str(valores[0]).strip()
            cliente = str(valores[1]).strip()
            nombre = str(valores[2]).strip()
            try:
                precio = self.convertir_monto(valores[3])
                cantidad = self.normalizar_cantidad(str(valores[4]))
                total = self.convertir_monto(valores[5])
            except Exception:
                continue

            info = self.obtener_info_producto(nombre)
            productos.append({
                'nombre': info['nombre'] if info else nombre,
                'folio': folio,
                'cliente': cliente,
                'precio': precio,
                'cantidad': cantidad,
                'total': total,
                'codigo': info['codigo'] if info else '',
                'tabla': info['tabla'] if info else '',
                'origen_nota': not bool(info),
            })

        if productos:
            self.productos_seleccionados.extend(productos)
            self.actualizar_totales()

    def _actualizar_identidad_detalle(self, _event=None):
        """Mantiene folio y cliente sincronizados en cada renglón del detalle."""
        if not hasattr(self, 'tree_productos'):
            return
        folio = self.entry_folio.get().strip() or 'Sin folio'
        cliente = self.entry_cliente.get().strip() or 'Cliente General'
        for indice, item in enumerate(self.tree_productos.get_children()):
            valores = list(self.tree_productos.item(item, 'values'))
            if len(valores) >= 6:
                valores[0], valores[1] = folio, cliente
                self.tree_productos.item(item, values=valores)
            if indice < len(self.productos_seleccionados):
                self.productos_seleccionados[indice]['folio'] = folio
                self.productos_seleccionados[indice]['cliente'] = cliente

    @staticmethod
    def _escribir_entry(entry, valor):
        entry.delete(0, tk.END)
        entry.insert(0, str(valor or ''))

    def cargar_nota_detectada(self, datos, ruta_imagen=''):
        """Carga una nota leida por JELOX en Ventas sin modificar Inventario."""
        self.productos_seleccionados.clear()
        self.tree_productos.delete(*self.tree_productos.get_children())
        self._escribir_entry(self.entry_folio, datos.get('folio', ''))
        self._escribir_entry(self.entry_fecha, datos.get('fecha') or datetime.datetime.now().strftime('%d/%m/%Y'))
        self.entry_cliente.set(str(datos.get('cliente') or 'Cliente General'))
        self._escribir_entry(self.entry_direccion, datos.get('direccion', ''))
        self._escribir_entry(self.entry_telefono, datos.get('telefono', ''))
        self._escribir_entry(self.entry_vendedor, datos.get('vendedor', ''))
        abono = float(datos.get('abono', 0) or 0)
        self._escribir_entry(self.entry_abono_nota, f'{abono:.2f}' if abono else '')
        self._nota_imagen = ruta_imagen or ''
        self._nota_total_detectado = float(datos.get('total', 0) or 0)
        self._nota_sin_iva = True

        folio = self.entry_folio.get().strip() or 'Sin folio'
        cliente = self.entry_cliente.get().strip() or 'Cliente General'
        for producto in datos.get('productos', []):
            nombre = str(producto.get('nombre') or producto.get('descripcion') or '').strip()
            try:
                cantidad = self.normalizar_cantidad(str(producto.get('cantidad', 1) or 1))
                precio = float(producto.get('precio_unitario', producto.get('precio', 0)) or 0)
                subtotal = float(producto.get('subtotal', 0) or 0)
            except (TypeError, ValueError):
                continue
            if not nombre:
                continue
            if precio <= 0 and subtotal > 0 and cantidad:
                precio = subtotal / cantidad
            if subtotal <= 0:
                subtotal = precio * cantidad
            self.tree_productos.insert('', 'end', values=(
                folio, cliente, nombre, f'${precio:,.2f}', f'{cantidad:g}', f'${subtotal:,.2f}'
            ))
            self.productos_seleccionados.append({
                'folio': folio, 'cliente': cliente, 'nombre': nombre,
                'precio': precio, 'cantidad': cantidad, 'total': subtotal,
                'codigo': '', 'tabla': '', 'origen_nota': True,
            })
        self.label_stock.config(text='Nota fisica: no modifica Inventario', fg=self.COLORS['success'])
        self.actualizar_totales()
        self._actualizar_identidad_detalle()
        self.entry_cliente.focus_set()

    def preparar_productos_para_pago(self):
        self.reconstruir_productos_desde_tabla()
        if self.productos_seleccionados:
            return True

        producto_actual = self.entry_producto.get().strip() if hasattr(self, 'entry_producto') else ""
        cantidad_actual = self.entry_cantidad.get().strip() if hasattr(self, 'entry_cantidad') else ""
        if producto_actual and cantidad_actual:
            self.agregar_producto()
            self.reconstruir_productos_desde_tabla()

        return bool(self.productos_seleccionados)

    def texto_iva(self):
        iva = self.obtener_porcentaje_iva()
        return f"IVA {iva:g}%"

    def actualizar_totales(self):
        """Actualizar los totales de la venta"""
        subtotal = sum(p['total'] for p in self.productos_seleccionados)
        iva = subtotal * self.obtener_tasa_iva()
        total = subtotal + iva
        
        self.label_sub_total.config(text=f'Subtotal: ${subtotal:,.2f}')
        self.label_iva.config(text=f'{self.texto_iva()}: ${iva:,.2f}')
        self.label_precio_total.config(text=f'TOTAL: ${total:,.2f}')

    def eliminar_producto_seleccionado(self):
        seleccion = list(self.tree_productos.selection())
        if not seleccion:
            messagebox.showwarning("Seleccion requerida", "Selecciona un producto de la lista para eliminarlo.")
            return

        items = list(self.tree_productos.get_children())
        indices = sorted(
            [items.index(item) for item in seleccion if item in items],
            reverse=True
        )

        for indice in indices:
            if indice < len(self.productos_seleccionados):
                self.productos_seleccionados.pop(indice)

        for item in seleccion:
            self.tree_productos.delete(item)

        if not self.tree_productos.get_children():
            self.productos_seleccionados.clear()

        self.actualizar_totales()

    def limpiar_venta(self):
        """Limpiar todos los campos de la venta"""
        self.productos_seleccionados.clear()
        for item in self.tree_productos.get_children():
            self.tree_productos.delete(item)
        
        self.entry_cliente.set("")
        self.entry_producto.set("")
        self.entry_cantidad.delete(0, tk.END)
        if hasattr(self, 'entry_folio'):
            self.entry_folio.delete(0, tk.END)
        for nombre in ('entry_direccion', 'entry_telefono', 'entry_vendedor', 'entry_abono_nota', 'entry_precio_unitario'):
            entrada = getattr(self, nombre, None)
            if entrada is not None:
                entrada.delete(0, tk.END)
        if hasattr(self, 'entry_fecha'):
            self._escribir_entry(self.entry_fecha, datetime.datetime.now().strftime('%d/%m/%Y'))
        self._nota_imagen = ''
        self._nota_total_detectado = 0.0
        self._nota_sin_iva = False
        self.label_stock.config(text="Stock: --")
        self.actualizar_totales()
        self.cargar_productos()

    def realizar_pago(self):
        """Procesar el pago de la venta"""
        if not self.preparar_productos_para_pago():
            messagebox.showwarning("Advertencia", "Agrega un producto a la venta antes de procesar el pago.")
            return
        
        cliente = self.entry_cliente.get()
        if not cliente:
            messagebox.showwarning("Advertencia", "Por favor seleccione un cliente")
            return
        
        try:
            # Aquí iría la lógica de pago
            messagebox.showinfo("Éxito", "¡Venta realizada con éxito!")
            self.limpiar_venta()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar la venta: {e}")

    def ver_ventas_realizadas(self):
        """Mostrar ventana moderna de ventas con filtros y totales"""
        # Crear ventana principal
        self.ventana_ventas = tk.Toplevel(self)
        self.ventana_ventas.title("Historial de Ventas")
        self.ventana_ventas.geometry("1200x700")
        self.ventana_ventas.configure(bg=self.COLORS['light'])
        self.ventana_ventas.resizable(True, True)
        self.ventana_ventas.minsize(1000, 600)
        
        # Centrar ventana
        self.ventana_ventas.geometry("+{}+{}".format(
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 50
        ))
        
        # Título principal
        title_frame = tk.Frame(self.ventana_ventas, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x')
        
        title_label = tk.Label(title_frame, text="Historial de Ventas", 
                             bg=self.COLORS['primary'], fg=self.COLORS['white'],
                             font=('Poppins', 18, 'bold'))
        title_label.pack(pady=20)
        
        # Frame de filtros
        filtros_frame = tk.Frame(self.ventana_ventas, bg=self.COLORS['white'], height=80)
        filtros_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Filtro por rango de fechas
        tk.Label(filtros_frame, text="Rango de fechas:", 
                font=('Poppins', 12, 'bold'), bg=self.COLORS['white'],
                fg=self.COLORS['primary']).place(x=20, y=15)
        
        # Fecha desde
        tk.Label(filtros_frame, text="Desde:", 
                font=('Poppins', 10), bg=self.COLORS['white'],
                fg=self.COLORS['dark']).place(x=160, y=15)
        
        self.entry_fecha_desde = tk.Entry(filtros_frame, font=('Poppins', 10), 
                                        relief='solid', bd=1, width=10)
        self.entry_fecha_desde.place(x=200, y=15)
        self.entry_fecha_desde.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))
        
        # Fecha hasta
        tk.Label(filtros_frame, text="Hasta:", 
                font=('Poppins', 10), bg=self.COLORS['white'],
                fg=self.COLORS['dark']).place(x=300, y=15)
        
        self.entry_fecha_hasta = tk.Entry(filtros_frame, font=('Poppins', 10), 
                                        relief='solid', bd=1, width=10)
        self.entry_fecha_hasta.place(x=340, y=15)
        self.entry_fecha_hasta.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))
        
        # Botones de filtro (todos del mismo tamaño)
        btn_filtrar = tk.Button(filtros_frame, text="Filtrar Rango", 
                              command=self.filtrar_ventas_por_rango,
                              bg=self.COLORS['primary'], fg=self.COLORS['white'],
                              font=('Poppins', 10, 'bold'), relief='flat', 
                              cursor='hand2', bd=0, width=12, height=1)
        btn_filtrar.place(x=450, y=12)
        
        btn_hoy = tk.Button(filtros_frame, text="Hoy", 
                          command=self.filtrar_ventas_hoy,
                          bg=self.COLORS['success'], fg=self.COLORS['white'],
                          font=('Poppins', 10, 'bold'), relief='flat', 
                          cursor='hand2', bd=0, width=12, height=1)
        btn_hoy.place(x=580, y=12)
        
        btn_semana = tk.Button(filtros_frame, text="Esta Semana", 
                             command=self.filtrar_ventas_semana,
                             bg=self.COLORS['warning'], fg=self.COLORS['white'],
                             font=('Poppins', 10, 'bold'), relief='flat', 
                             cursor='hand2', bd=0, width=12, height=1)
        btn_semana.place(x=450, y=45)
        
        btn_mes = tk.Button(filtros_frame, text="Este Mes", 
                          command=self.filtrar_ventas_mes,
                          bg=self.COLORS['secondary'], fg=self.COLORS['white'],
                          font=('Poppins', 10, 'bold'), relief='flat', 
                          cursor='hand2', bd=0, width=12, height=1)
        btn_mes.place(x=580, y=45)
        
        btn_todas = tk.Button(filtros_frame, text="Todas", 
                            command=self.mostrar_todas_ventas,
                            bg=self.COLORS['danger'], fg=self.COLORS['white'],
                            font=('Poppins', 10, 'bold'), relief='flat', 
                            cursor='hand2', bd=0, width=12, height=1)
        btn_todas.place(x=710, y=12)
        
        # Labels de totales (reposicionados)
        self.label_total_dia = tk.Label(filtros_frame, text="Total del rango: $0.00", 
                                      font=('Poppins', 14, 'bold'), bg=self.COLORS['white'],
                                      fg=self.COLORS['success'])
        self.label_total_dia.place(x=820, y=15)
        
        # Label específico para total de hoy (mismo tamaño que el de arriba)
        self.label_total_hoy = tk.Label(filtros_frame, text="Ventas HOY: $0.00", 
                                      font=('Poppins', 14, 'bold'), bg=self.COLORS['white'],
                                      fg=self.COLORS['primary'])
        self.label_total_hoy.place(x=820, y=45)
        
        # Frame principal de contenido
        content_frame = tk.Frame(self.ventana_ventas, bg=self.COLORS['light'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Frame para el treeview
        tree_frame = tk.Frame(content_frame, bg=self.COLORS['white'], relief='solid', bd=1)
        tree_frame.pack(fill='both', expand=True)
        
        # Treeview para mostrar ventas
        columns = ("VentaId", "Folio", "Cliente", "Producto", "Precio", "Cantidad", "Total", "Fecha", "Hora")
        self.tree_ventas = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Configurar columnas con anchos específicos
        anchos = {"VentaId": 0, "Folio": 110, "Cliente": 150, "Producto": 200, "Precio": 100, 
                 "Cantidad": 80, "Total": 100, "Fecha": 100, "Hora": 80}
        
        for col in columns:
            self.tree_ventas.heading(col, text=col)
            self.tree_ventas.column(col, width=anchos[col], anchor="center")
        self.tree_ventas.column("VentaId", width=0, minwidth=0, stretch=False)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ventas.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_ventas.xview)
        self.tree_ventas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Pack widgets
        self.tree_ventas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree_ventas.bind("<Double-1>", self.abrir_historial_abonos_venta)
        
        # Cargar total de hoy y ventas iniciales
        self.actualizar_total_hoy()
        self.filtrar_ventas_hoy()

    def filtrar_ventas_por_rango(self):
        """Filtrar ventas por rango de fechas"""
        fecha_desde = self.entry_fecha_desde.get()
        fecha_hasta = self.entry_fecha_hasta.get()
        
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Advertencia", "Por favor ingrese ambas fechas")
            return
        
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Convertir fechas para comparación
            c.execute("""SELECT rowid, COALESCE(NULLIF(folio, ''), 'Sin folio'), cliente, articulo, precio, cantidad, total, fecha, hora 
                        FROM ventas WHERE fecha BETWEEN ? AND ? 
                        ORDER BY fecha DESC, hora DESC""", (fecha_desde, fecha_hasta))
            ventas = c.fetchall()
            conn.close()
            
            if fecha_desde == fecha_hasta:
                descripcion = fecha_desde
            else:
                descripcion = f"{fecha_desde} - {fecha_hasta}"
            
            self.actualizar_tabla_ventas(ventas, descripcion)
            # Siempre actualizar el total de hoy
            self.actualizar_total_hoy()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al filtrar ventas: {e}")

    def filtrar_ventas_hoy(self):
        """Filtrar ventas del día actual"""
        fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
        self.entry_fecha_desde.delete(0, tk.END)
        self.entry_fecha_desde.insert(0, fecha_hoy)
        self.entry_fecha_hasta.delete(0, tk.END)
        self.entry_fecha_hasta.insert(0, fecha_hoy)
        self.filtrar_ventas_por_rango()

    def filtrar_ventas_semana(self):
        """Filtrar ventas de esta semana"""
        hoy = datetime.datetime.now()
        inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + datetime.timedelta(days=6)
        
        fecha_desde = inicio_semana.strftime("%d/%m/%Y")
        fecha_hasta = fin_semana.strftime("%d/%m/%Y")
        
        self.entry_fecha_desde.delete(0, tk.END)
        self.entry_fecha_desde.insert(0, fecha_desde)
        self.entry_fecha_hasta.delete(0, tk.END)
        self.entry_fecha_hasta.insert(0, fecha_hasta)
        self.filtrar_ventas_por_rango()

    def filtrar_ventas_mes(self):
        """Filtrar ventas de este mes"""
        hoy = datetime.datetime.now()
        inicio_mes = hoy.replace(day=1)
        
        # Último día del mes
        if hoy.month == 12:
            fin_mes = hoy.replace(year=hoy.year + 1, month=1, day=1) - datetime.timedelta(days=1)
        else:
            fin_mes = hoy.replace(month=hoy.month + 1, day=1) - datetime.timedelta(days=1)
        
        fecha_desde = inicio_mes.strftime("%d/%m/%Y")
        fecha_hasta = fin_mes.strftime("%d/%m/%Y")
        
        self.entry_fecha_desde.delete(0, tk.END)
        self.entry_fecha_desde.insert(0, fecha_desde)
        self.entry_fecha_hasta.delete(0, tk.END)
        self.entry_fecha_hasta.insert(0, fecha_hasta)
        self.filtrar_ventas_por_rango()

    def mostrar_todas_ventas(self):
        """Mostrar todas las ventas sin filtro"""
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""SELECT rowid, COALESCE(NULLIF(folio, ''), 'Sin folio'), cliente, articulo, precio, cantidad, total, fecha, hora 
                        FROM ventas ORDER BY fecha DESC, hora DESC LIMIT 500""")
            ventas = c.fetchall()
            conn.close()
            
            self.actualizar_tabla_ventas(ventas, "Todas las fechas")
            # Siempre actualizar el total de hoy
            self.actualizar_total_hoy()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar ventas: {e}")

    def actualizar_tabla_ventas(self, ventas, fecha_filtro):
        """Actualizar la tabla de ventas y calcular totales"""
        # Limpiar tabla
        for item in self.tree_ventas.get_children():
            self.tree_ventas.delete(item)
        
        # Calcular total
        total_dia = 0
        
        # Insertar datos
        for venta in ventas:
            venta_id, folio, cliente, producto, precio, cantidad, total, fecha, hora = venta
            total_dia += total
            
            # Formatear datos para mostrar
            venta_formateada = [
                venta_id,
                folio,
                cliente,
                producto,
                f"${precio:,.2f}",
                cantidad,
                f"${total:,.2f}",
                fecha,
                hora
            ]
            self.tree_ventas.insert("", "end", values=venta_formateada)
        
        # Actualizar label de total
        if fecha_filtro == "Todas las fechas":
            self.label_total_dia.config(text=f"Total general: ${total_dia:,.2f}")
        elif " - " in fecha_filtro:
            self.label_total_dia.config(text=f"Total rango: ${total_dia:,.2f}")
        else:
            self.label_total_dia.config(text=f"Total {fecha_filtro}: ${total_dia:,.2f}")
        
        # Mostrar información adicional
        num_ventas = len(ventas)
        if num_ventas == 0:
            self.label_total_dia.config(text=f"Sin ventas para {fecha_filtro}")
        else:
            print(f" {num_ventas} ventas encontradas para {fecha_filtro}, Total: ${total_dia:,.2f}")

    def abrir_historial_abonos_venta(self, event=None):
        seleccion = self.tree_ventas.selection()
        if not seleccion:
            return
        valores = self.tree_ventas.item(seleccion[0], "values")
        if not valores:
            return
        self.mostrar_historial_abonos_venta(valores[0], valores[1], valores[2], valores[6])

    def mostrar_historial_abonos_venta(self, venta_id, folio, cliente, saldo_actual):
        ventana = tk.Toplevel(self)
        ventana.title(f"Historial de abonos - Folio {folio}")
        ventana.geometry("560x520")
        ventana.configure(bg=self.COLORS['light'])
        ventana.transient(self)
        ventana.grab_set()

        tk.Label(ventana, text=f"Folio {folio} - {cliente}", font=('Poppins', 16, 'bold'),
                 bg=self.COLORS['light'], fg=self.COLORS['primary']).pack(anchor='w', padx=20, pady=(18, 4))
        tk.Label(ventana, text=f"Saldo actual: {saldo_actual}", font=('Poppins', 12, 'bold'),
                 bg=self.COLORS['light'], fg=self.COLORS['warning']).pack(anchor='w', padx=20, pady=(0, 12))

        tabla = ttk.Treeview(ventana, columns=("Folio", "Fecha", "Hora", "Monto", "Nota"), show="headings", height=10)
        for col, ancho in {"Folio": 110, "Fecha": 95, "Hora": 75, "Monto": 95, "Nota": 170}.items():
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor="center")
        tabla.pack(fill='both', expand=True, padx=20, pady=(0, 12))

        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT fecha, hora, monto, COALESCE(nota, '') FROM abonos_ventas WHERE venta_id = ? ORDER BY id DESC", (venta_id,))
            for fecha, hora, monto, nota in c.fetchall():
                tabla.insert("", "end", values=(folio or 'Sin folio', fecha, hora, f"${monto:,.2f}", nota))
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")

        form = tk.Frame(ventana, bg=self.COLORS['white'], relief='solid', bd=1)
        form.pack(fill='x', padx=20, pady=(0, 20))
        tk.Label(form, text="Nuevo abono", font=('Poppins', 12, 'bold'), bg=self.COLORS['white'], fg=self.COLORS['primary']).grid(row=0, column=0, columnspan=2, sticky='w', padx=12, pady=(10, 4))
        tk.Label(form, text="Monto", font=('Poppins', 10), bg=self.COLORS['white']).grid(row=1, column=0, sticky='w', padx=12)
        entry_monto = tk.Entry(form, font=('Poppins', 11), relief='solid', bd=1)
        entry_monto.grid(row=2, column=0, padx=12, pady=(2, 10), sticky='ew')
        tk.Label(form, text="Nota", font=('Poppins', 10), bg=self.COLORS['white']).grid(row=1, column=1, sticky='w', padx=12)
        entry_nota = tk.Entry(form, font=('Poppins', 11), relief='solid', bd=1)
        entry_nota.grid(row=2, column=1, padx=12, pady=(2, 10), sticky='ew')
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        tk.Button(form, text="Registrar abono", bg=self.COLORS['success'], fg=self.COLORS['white'],
                  font=('Poppins', 10, 'bold'), relief='flat', cursor='hand2',
                  command=lambda: self.registrar_abono_venta(venta_id, entry_monto, entry_nota, ventana)).grid(row=3, column=0, columnspan=2, pady=(0, 12))

    def registrar_abono_venta(self, venta_id, entry_monto, entry_nota, ventana):
        try:
            monto = float(entry_monto.get().strip())
        except ValueError:
            messagebox.showerror("Monto invalido", "Escribe un monto numerico para el abono.")
            return
        if monto <= 0:
            messagebox.showerror("Monto invalido", "El abono debe ser mayor a cero.")
            return
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        nota = entry_nota.get().strip() or "Abono"
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            self.asegurar_columnas_ventas(c)
            c.execute("INSERT INTO abonos_ventas (venta_id, monto, fecha, hora, nota) VALUES (?, ?, ?, ?, ?)", (venta_id, monto, fecha, hora, nota))
            c.execute("SELECT COALESCE(saldo, 0), COALESCE(monto_recibido, 0) FROM ventas WHERE rowid = ?", (venta_id,))
            saldo_actual, recibido_actual = c.fetchone()
            nuevo_saldo = max((saldo_actual or 0) - monto, 0)
            estado = "Pagado" if nuevo_saldo <= 0 else "Credito"
            c.execute("UPDATE ventas SET saldo = ?, monto_recibido = ?, estado_pago = ? WHERE rowid = ?", (nuevo_saldo, (recibido_actual or 0) + monto, estado, venta_id))
            conn.commit()
            conn.close()
            ventana.destroy()
            self.filtrar_ventas_por_rango()
            messagebox.showinfo("Abono registrado", "El abono se guardo correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el abono: {e}")
    def actualizar_total_hoy(self):
        """Actualizar el total de ventas de hoy (siempre visible)"""
        try:
            fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Obtener total de ventas de hoy
            c.execute("SELECT SUM(total), COUNT(*) FROM ventas WHERE fecha = ?", (fecha_hoy,))
            resultado = c.fetchone()
            
            total_hoy = resultado[0] if resultado[0] else 0
            num_ventas_hoy = resultado[1] if resultado[1] else 0
            
            conn.close()
            
            # Actualizar label de total de hoy
            if hasattr(self, 'label_total_hoy'):
                if num_ventas_hoy > 0:
                    self.label_total_hoy.config(
                        text=f"Ventas HOY: ${total_hoy:,.2f} ({num_ventas_hoy} ventas)",
                        fg=self.COLORS['success']
                    )
                else:
                    self.label_total_hoy.config(
                        text="Ventas HOY: $0.00 (0 ventas)",
                        fg=self.COLORS['secondary']
                    )
            
        except sqlite3.Error as e:
            print(f"Error calculando total de hoy: {e}")
            if hasattr(self, 'label_total_hoy'):
                self.label_total_hoy.config(text="Ventas HOY: Error", fg=self.COLORS['danger'])
    
    def ver_ventas_realizadas(self):
        """Historial adaptable con búsqueda y fechas normalizadas."""
        try:
            if hasattr(self, 'ventana_ventas') and self.ventana_ventas.winfo_exists():
                self.ventana_ventas.lift()
                return
        except Exception:
            pass
        raiz = self.winfo_toplevel(); raiz.update_idletasks()
        ancho = min(1180, max(880, raiz.winfo_width() - 60))
        alto = min(760, max(590, raiz.winfo_height() - 50))
        x = max(8, raiz.winfo_rootx() + (raiz.winfo_width() - ancho) // 2)
        y = max(8, raiz.winfo_rooty() + (raiz.winfo_height() - alto) // 2)
        self.ventana_ventas = ctk.CTkToplevel(self)
        self.ventana_ventas.title('Historial de ventas')
        self.ventana_ventas.geometry(f'{ancho}x{alto}+{x}+{y}')
        self.ventana_ventas.minsize(840, 560)
        self.ventana_ventas.configure(fg_color=self.UI_BG)
        self.ventana_ventas.transient(raiz)
        self.ventana_ventas.grid_rowconfigure(2, weight=1)
        self.ventana_ventas.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.ventana_ventas, height=68, corner_radius=0, fg_color='#7d080c')
        header.grid(row=0, column=0, sticky='ew'); header.grid_propagate(False)
        ctk.CTkLabel(header, text='Historial de ventas', font=ctk.CTkFont('Poppins', 19, 'bold'),
                     text_color='white').place(x=22, y=10)
        ctk.CTkLabel(header, text='Consulta por fecha, folio, cliente o producto',
                     font=ctk.CTkFont('Poppins', 9), text_color='#f0d7d8').place(x=23, y=40)

        filtros = ctk.CTkFrame(self.ventana_ventas, fg_color='white', corner_radius=11,
                               border_width=1, border_color=self.UI_BORDER)
        filtros.grid(row=1, column=0, sticky='ew', padx=14, pady=10)
        for columna in range(8):
            filtros.grid_columnconfigure(columna, weight=1 if columna in (0, 1, 2) else 0)
        self.historial_busqueda_var = tk.StringVar()
        buscador = ctk.CTkEntry(filtros, textvariable=self.historial_busqueda_var,
                                placeholder_text='Buscar folio, cliente o producto…', height=32,
                                corner_radius=8, border_color=self.UI_BORDER,
                                placeholder_text_color='#68707c')
        buscador.grid(row=0, column=0, columnspan=3, sticky='ew', padx=(12, 7), pady=(10, 6))
        buscador.bind('<Return>', lambda _e: self.filtrar_ventas_por_rango())
        buscador.bind('<KeyRelease>', lambda _e: self._programar_busqueda_historial())

        resumen = ctk.CTkFrame(filtros, fg_color='#f7f8fa', corner_radius=8)
        resumen.grid(row=0, column=3, columnspan=5, sticky='ew', padx=(7, 12), pady=(10, 6))
        self.label_total_dia = ctk.CTkLabel(resumen, text='Total mostrado: $0.00',
                                            font=ctk.CTkFont('Poppins', 10, 'bold'), text_color='#0f766e')
        self.label_total_dia.pack(side='left', padx=10, pady=6)
        self.label_total_hoy = ctk.CTkLabel(resumen, text='Hoy: $0.00',
                                            font=ctk.CTkFont('Poppins', 9, 'bold'), text_color='#8f070c')
        self.label_total_hoy.pack(side='right', padx=10, pady=6)

        ctk.CTkLabel(filtros, text='Desde', text_color=self.UI_MUTED,
                     font=ctk.CTkFont('Poppins', 8, 'bold')).grid(row=1, column=0, sticky='w', padx=(12, 4))
        ctk.CTkLabel(filtros, text='Hasta', text_color=self.UI_MUTED,
                     font=ctk.CTkFont('Poppins', 8, 'bold')).grid(row=1, column=1, sticky='w', padx=4)
        self.entry_fecha_desde = ctk.CTkEntry(filtros, height=30, corner_radius=7)
        self.entry_fecha_hasta = ctk.CTkEntry(filtros, height=30, corner_radius=7)
        self.entry_fecha_desde.grid(row=2, column=0, sticky='ew', padx=(12, 4), pady=(1, 10))
        self.entry_fecha_hasta.grid(row=2, column=1, sticky='ew', padx=4, pady=(1, 10))

        acciones = (
            ('Filtrar', self.filtrar_ventas_por_rango, '#8f070c'),
            ('Hoy', self.filtrar_ventas_hoy, '#0f766e'),
            ('Semana', self.filtrar_ventas_semana, '#b7791f'),
            ('Mes', self.filtrar_ventas_mes, '#2563eb'),
            ('Todas', self.mostrar_todas_ventas, '#475569'),
        )
        for indice, (texto, comando, color) in enumerate(acciones, start=3):
            ctk.CTkButton(filtros, text=texto, command=comando, width=70, height=30,
                          corner_radius=7, fg_color=color, hover_color='#65070a',
                          font=ctk.CTkFont('Poppins', 8, 'bold')).grid(
                              row=2, column=indice, padx=3, pady=(1, 10))

        tree_frame = ctk.CTkFrame(self.ventana_ventas, fg_color='white', corner_radius=11,
                                  border_width=1, border_color=self.UI_BORDER)
        tree_frame.grid(row=2, column=0, sticky='nsew', padx=14, pady=(0, 7))
        tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1)
        columnas = ('VentaId', 'Folio', 'Cliente', 'Productos', 'Total', 'Pago', 'Saldo', 'Estado', 'Fecha', 'Hora')
        self.tree_ventas = ttk.Treeview(tree_frame, columns=columnas, show='headings', style='Ventas.Treeview')
        anchos = {'VentaId': 0, 'Folio': 90, 'Cliente': 145, 'Productos': 260, 'Total': 95,
                  'Pago': 80, 'Saldo': 95, 'Estado': 80, 'Fecha': 95, 'Hora': 75}
        for columna in columnas:
            self.tree_ventas.heading(columna, text=columna)
            self.tree_ventas.column(columna, width=anchos[columna], minwidth=65, anchor='center')
        self.tree_ventas.column('VentaId', width=0, minwidth=0, stretch=False)
        self.tree_ventas.column('Productos', anchor='w')
        self.tree_ventas.tag_configure('credito', foreground='#9a6700')
        self.tree_ventas.tag_configure('pagado', foreground='#167444')
        sy = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_ventas.yview)
        sx = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree_ventas.xview)
        self.tree_ventas.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree_ventas.grid(row=0, column=0, sticky='nsew', padx=(7, 0), pady=(7, 0))
        sy.grid(row=0, column=1, sticky='ns', pady=(7, 0)); sx.grid(row=1, column=0, sticky='ew', padx=(7, 0))
        self.tree_ventas.bind('<Double-1>', self.abrir_historial_abonos_venta)
        ctk.CTkLabel(self.ventana_ventas, text='Doble clic sobre una venta para consultar o registrar abonos.',
                     font=ctk.CTkFont('Poppins', 8), text_color=self.UI_MUTED).grid(
                         row=3, column=0, sticky='w', padx=20, pady=(0, 8))
        self.actualizar_total_hoy()
        self.filtrar_ventas_mes()

    def _programar_busqueda_historial(self):
        if hasattr(self, '_historial_busqueda_after') and self._historial_busqueda_after:
            self.after_cancel(self._historial_busqueda_after)
        self._historial_busqueda_after = self.after(220, self.filtrar_ventas_por_rango)

    def _parse_fecha_historial(self, valor):
        texto = str(valor or '').strip()[:19]
        for formato in ('%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'):
            try:
                return datetime.datetime.strptime(texto, formato).date()
            except ValueError:
                continue
        return None

    def _ventas_historial(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                return conn.execute('''
                    SELECT v.rowid,
                           COALESCE(NULLIF(v.folio,''),'Sin folio'),
                           COALESCE(NULLIF(v.cliente,''),'Cliente general'),
                           COALESCE(NULLIF((SELECT GROUP_CONCAT(d.producto || ' ×' || d.cantidad, ', ')
                                                  FROM detalle_ventas d WHERE d.venta_id=v.rowid),''),
                                    NULLIF(v.articulo,''),'Sin detalle'),
                           COALESCE(v.total,0), COALESCE(v.tipo_pago,'Contado'),
                           COALESCE(v.saldo,0), COALESCE(v.estado_pago,'Pagado'),
                           COALESCE(v.fecha,''), COALESCE(v.hora,'')
                    FROM ventas v LIMIT 1000
                ''').fetchall()
        except sqlite3.Error:
            return []

    def _establecer_fechas_historial(self, desde, hasta):
        for entrada, fecha in ((self.entry_fecha_desde, desde), (self.entry_fecha_hasta, hasta)):
            entrada.delete(0, tk.END)
            entrada.insert(0, fecha.strftime('%d/%m/%Y'))

    def filtrar_ventas_por_rango(self):
        texto_desde = self.entry_fecha_desde.get().strip()
        texto_hasta = self.entry_fecha_hasta.get().strip()
        desde = self._parse_fecha_historial(texto_desde) if texto_desde else None
        hasta = self._parse_fecha_historial(texto_hasta) if texto_hasta else None
        if (texto_desde and not desde) or (texto_hasta and not hasta):
            messagebox.showwarning('Fecha inválida', 'Usa el formato DD/MM/AAAA o AAAA-MM-DD.')
            return
        if desde and hasta and desde > hasta:
            messagebox.showwarning('Rango inválido', 'La fecha inicial no puede ser posterior a la final.')
            return
        busqueda = self.historial_busqueda_var.get().strip().casefold() if hasattr(self, 'historial_busqueda_var') else ''
        ventas = []
        for fila in self._ventas_historial():
            fecha = self._parse_fecha_historial(fila[8])
            if desde and (not fecha or fecha < desde):
                continue
            if hasta and (not fecha or fecha > hasta):
                continue
            if busqueda and busqueda not in ' '.join(str(v) for v in fila[1:4]).casefold():
                continue
            fecha_mostrar = fecha.strftime('%d/%m/%Y') if fecha else fila[8]
            ventas.append((*fila[:8], fecha_mostrar, fila[9], fecha or datetime.date.min))
        ventas.sort(key=lambda r: (r[10], str(r[9])), reverse=True)
        descripcion = 'Todas las fechas' if not desde and not hasta else (
            desde.strftime('%d/%m/%Y') if desde == hasta else
            f'{desde.strftime("%d/%m/%Y") if desde else "Inicio"} - {hasta.strftime("%d/%m/%Y") if hasta else "Hoy"}')
        self.actualizar_tabla_ventas([fila[:10] for fila in ventas], descripcion)
        self.actualizar_total_hoy()

    def filtrar_ventas_hoy(self):
        hoy = datetime.date.today(); self._establecer_fechas_historial(hoy, hoy)
        self.filtrar_ventas_por_rango()

    def filtrar_ventas_semana(self):
        hoy = datetime.date.today(); inicio = hoy - datetime.timedelta(days=hoy.weekday())
        self._establecer_fechas_historial(inicio, hoy)
        self.filtrar_ventas_por_rango()

    def filtrar_ventas_mes(self):
        hoy = datetime.date.today(); self._establecer_fechas_historial(hoy.replace(day=1), hoy)
        self.filtrar_ventas_por_rango()

    def mostrar_todas_ventas(self):
        self.entry_fecha_desde.delete(0, tk.END); self.entry_fecha_hasta.delete(0, tk.END)
        self.filtrar_ventas_por_rango()

    def actualizar_tabla_ventas(self, ventas, fecha_filtro):
        for item in self.tree_ventas.get_children():
            self.tree_ventas.delete(item)
        total = 0.0
        for venta in ventas:
            venta_id, folio, cliente, productos, monto, pago, saldo, estado, fecha, hora = venta
            total += float(monto or 0)
            valores = (venta_id, folio, cliente, productos, f'${float(monto or 0):,.2f}', pago,
                       f'${float(saldo or 0):,.2f}', estado, fecha, hora)
            etiqueta = 'credito' if float(saldo or 0) > 0 else 'pagado'
            self.tree_ventas.insert('', 'end', values=valores, tags=(etiqueta,))
        detalle = f'{len(ventas)} venta(s) · ${total:,.2f}'
        if fecha_filtro != 'Todas las fechas':
            detalle += f' · {fecha_filtro}'
        self.label_total_dia.configure(text=detalle)

    def actualizar_total_hoy(self):
        hoy = datetime.date.today()
        ventas = [fila for fila in self._ventas_historial() if self._parse_fecha_historial(fila[8]) == hoy]
        total = sum(float(fila[4] or 0) for fila in ventas)
        if hasattr(self, 'label_total_hoy'):
            self.label_total_hoy.configure(text=f'Hoy: ${total:,.2f} ({len(ventas)})')

    def abrir_historial_abonos_venta(self, event=None):
        seleccion = self.tree_ventas.selection()
        if not seleccion:
            return
        valores = self.tree_ventas.item(seleccion[0], 'values')
        if valores:
            self.mostrar_historial_abonos_venta(valores[0], valores[1], valores[2], valores[6])

    def actualizar_hora(self):
        """Actualizar la hora en tiempo real cada segundo"""
        try:
            hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
            if hasattr(self, 'label_hora'):
                self.label_hora.config(text=hora_actual)
            # Programar la siguiente actualización en 1000ms (1 segundo)
            self.after(1000, self.actualizar_hora)
        except:
            pass  # Si hay algún error, continuar sin actualizar la hora

    def buscar_por_codigo(self, event=None):
        """Buscar producto por código y autocompletar"""
        try:
            codigo = self.entry_codigo.get().upper()
            
            if not codigo:
                self.entry_producto.set("")
                self.label_stock.config(text="Stock: --")
                return
            
            if not hasattr(self, 'productos_codigos') or not hasattr(self, 'productos_dict'):
                return
            
            # Buscar código exacto o parcial
            codigo_encontrado = None
            for cod in self.productos_codigos:
                if cod.startswith(codigo):
                    codigo_encontrado = cod
                    break
            
            if codigo_encontrado and codigo_encontrado in self.productos_dict:
                producto_info = self.productos_dict[codigo_encontrado]
                nombre_completo = f"{producto_info['nombre']} ({codigo_encontrado})"
                
                # Autocompletar campos sin triggear eventos
                self.entry_producto.delete(0, tk.END)
                self.entry_producto.insert(0, nombre_completo)
                
                self.label_stock.config(
                    text=f"Stock: {producto_info['stock']} unidades",
                    fg=self.COLORS['success'] if producto_info['stock'] > 10 else self.COLORS['warning']
                )
                
                # Si presionó Enter, enfocar cantidad
                if event and event.keysym == 'Return':
                    self.entry_cantidad.focus_set()
            else:
                # Limpiar si no encuentra
                if len(codigo) > 2:  # Solo limpiar si escribió algo significativo
                    self.entry_producto.delete(0, tk.END)
                    self.label_stock.config(text="Stock: -- (Código no encontrado)", fg=self.COLORS['danger'])
                    
        except Exception as e:
            print(f"Error buscando por cdigo: {e}")

    def mostrar_productos(self, event=None):
        """Mostrar todos los productos disponibles al hacer clic"""
        if hasattr(self, 'productos_nombres'):
            self.entry_producto['values'] = self.productos_nombres
            self.entry_producto.event_generate('<Down>')

    def filtrar_productos(self, event):
        """Filtrar productos mientras se escribe con autocompletado mejorado"""
        if self.timer_producto:
            self.timer_producto.cancel()
        self.timer_producto = threading.Timer(0.3, self._filter_productos)
        self.timer_producto.start()

    def _filter_productos(self):
        """Aplicar filtro de productos con búsqueda inteligente"""
        texto = self.entry_producto.get().lower()
        if texto and hasattr(self, 'productos_nombres'):
            # Buscar por nombre o código
            productos_filtrados = []
            for producto in self.productos_nombres:
                if texto in producto.lower():
                    productos_filtrados.append(producto)
            
            self.entry_producto['values'] = productos_filtrados
            
            # Si hay solo una coincidencia exacta, seleccionarla
            if len(productos_filtrados) == 1:
                self.entry_producto.set(productos_filtrados[0])
                self.actualizar_stock()
        else:
            if hasattr(self, 'productos_nombres'):
                self.entry_producto['values'] = self.productos_nombres

    def abrir_modal_pago(self):
        """Abrir modal de pago con cálculo de cambio y opciones de factura"""
        if not self.preparar_productos_para_pago():
            messagebox.showwarning("Advertencia", "Agrega un producto a la venta antes de procesar el pago.")
            return
        
        cliente = self.entry_cliente.get()
        if not cliente:
            messagebox.showwarning("Advertencia", "Por favor seleccione un cliente")
            return
        
        # Calcular total
        subtotal = sum(p['total'] for p in self.productos_seleccionados)
        iva = subtotal * self.obtener_tasa_iva()
        total = subtotal + iva
        
        self.modal_pago = tk.Toplevel(self)
        self.modal_pago.title("Caja registradora - Procesar pago")
        self.modal_pago.geometry("560x720")
        self.modal_pago.configure(bg='#f5f6f8')
        self.modal_pago.resizable(False, False)
        self.modal_pago.grab_set()
        self.modal_pago.transient(self)
        
        # Centrar modal
        self.modal_pago.geometry("+{}+{}".format(
            self.winfo_rootx() + 450,
            self.winfo_rooty() + 200
        ))
        
        title_frame = tk.Frame(self.modal_pago, bg='#20242a', height=68)
        title_frame.pack(fill='x')
        
        tk.Label(title_frame, text="CAJA REGISTRADORA",
                 bg='#20242a', fg='#ffffff',
                 font=('Poppins', 17, 'bold')).pack(anchor='w', padx=28, pady=(15, 0))
        tk.Label(title_frame, text="Procesar pago de la venta",
                 bg='#20242a', fg='#cbd5e1',
                 font=('Poppins', 9)).pack(anchor='w', padx=30, pady=(1, 0))
        
        content_frame = tk.Frame(self.modal_pago, bg='#f5f6f8')
        content_frame.pack(fill='both', expand=True, padx=24, pady=20)
        
        info_frame = tk.Frame(content_frame, bg='#ffffff', highlightthickness=1, highlightbackground='#e3e6ea')
        info_frame.pack(fill='x', pady=(0, 14))
        
        tk.Label(info_frame, text=f"Cliente: {cliente}", 
                font=('Poppins', 12, 'bold'), bg='#ffffff',
                fg='#20242a').pack(pady=(14, 8))
        
        tk.Label(info_frame, text=f"Subtotal: ${subtotal:,.2f}", 
                font=('Poppins', 10), bg='#ffffff',
                fg='#343941').pack(pady=2)
        
        tk.Label(info_frame, text=f"{self.texto_iva()}: ${iva:,.2f}", 
                font=('Poppins', 10), bg='#ffffff',
                fg='#343941').pack(pady=2)
        
        tk.Label(info_frame, text=f"TOTAL A PAGAR: ${total:,.2f}", 
                font=('Poppins', 15, 'bold'), bg='#ffffff',
                fg='#18964b').pack(pady=(10, 16))
        
        tipo_frame = tk.Frame(content_frame, bg='#ffffff', highlightthickness=1, highlightbackground='#e3e6ea')
        tipo_frame.pack(fill='x', pady=(0, 14))
        tk.Label(tipo_frame, text="Forma de pago", font=('Poppins', 12, 'bold'),
                 bg='#ffffff', fg='#20242a').pack(anchor='w', padx=16, pady=(12, 6))
        self.tipo_pago_var = tk.StringVar(value="Contado")
        try:
            abono_nota = self.convertir_monto(self.entry_abono_nota.get())
        except Exception:
            abono_nota = 0.0
        if 0 < abono_nota < total:
            self.tipo_pago_var.set('Credito')
        opciones_frame = tk.Frame(tipo_frame, bg=self.COLORS['white'])
        opciones_frame.pack(fill='x', padx=16, pady=(0, 12))
        for opcion in ("Contado", "Credito"):
            tk.Radiobutton(opciones_frame, text=opcion, variable=self.tipo_pago_var, value=opcion,
                           bg='#ffffff', fg='#20242a', selectcolor='#ffffff',
                           activebackground='#ffffff', activeforeground='#20242a',
                           font=('Poppins', 11, 'bold'), command=lambda: self.actualizar_forma_pago(total)).pack(side='left', padx=(0, 28))

        pago_frame = tk.Frame(content_frame, bg='#f5f6f8')
        pago_frame.pack(fill='x', pady=(0, 12))
        
        tk.Label(pago_frame, text="Monto recibido", 
                font=('Poppins', 12, 'bold'), bg='#f5f6f8',
                fg='#20242a').pack(anchor='w', padx=2)
        
        self.entry_monto_recibido = tk.Entry(pago_frame, font=('Poppins', 14), 
                                           relief='solid', bd=1, width=22,
                                           bg='#ffffff', fg='#20242a', insertbackground='#20242a')
        self.entry_monto_recibido.pack(pady=(7, 8), anchor='w', ipady=7)
        monto_inicial = abono_nota if abono_nota > 0 else (0 if self.tipo_pago_var.get() == "Credito" else total)
        self.entry_monto_recibido.insert(0, f"{monto_inicial:.2f}")
        self.entry_monto_recibido.selection_range(0, 'end')
        self.entry_monto_recibido.focus_set()
        self.entry_monto_recibido.bind('<KeyRelease>', lambda e: self.calcular_cambio(total))
        
        # Label para mostrar el cambio
        self.label_cambio = tk.Label(pago_frame, text="Cambio: $0.00", 
                                   font=('Poppins', 14, 'bold'), bg='#f5f6f8',
                                   fg='#8b682f')
        self.label_cambio.pack(pady=(8, 4), anchor='w')
        self.calcular_cambio(total)
        
        botones_frame = tk.Frame(content_frame, bg='#f5f6f8')
        botones_frame.pack(fill='x', pady=(16, 0))
        
        self.crear_boton_modal(botones_frame, "Aceptar", 
                              lambda: self.aceptar_venta(total), 
                              'success', 50, 0, 200, 50, layout='pack')

        self.crear_boton_modal(botones_frame, "Cancelar", 
                              self.cerrar_modal_pago, 
                              'danger', 270, 0, 150, 50, layout='pack')

    def crear_boton_modal(self, parent, text, command, estilo, x, y, width, height, layout='place'):
        """Crear botón para el modal"""
        base_colors = self.COLORS
        # Usar colores base y calcular hover dinámicamente para evitar claves inexistentes
        bg_base = (
            base_colors['primary'] if estilo == 'primary' else
            base_colors['secondary'] if estilo == 'secondary' else
            base_colors['danger'] if estilo == 'danger' else
            base_colors['success']
        )
        hover_bg = self.ajustar_color(bg_base, -20)

        btn = tk.Button(parent, text=text, command=command,
                       bg=bg_base, fg=self.COLORS['white'],
                       font=('Poppins', 10, 'bold'),
                       relief='flat', cursor='hand2', bd=0, height=2)
        if layout == 'pack':
            btn.pack(side='left', fill='x', expand=True, padx=10, ipady=6)
        else:
            btn.place(x=x, y=y, width=width, height=height)

        # Efectos hover
        def on_enter(e):
            btn.configure(bg=hover_bg)

        def on_leave(e):
            btn.configure(bg=bg_base)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def obtener_monto_recibido(self):
        """Leer el monto recibido sin fallar por formato del texto."""
        import re
        import unicodedata

        valor = self.entry_monto_recibido.get()
        valor = unicodedata.normalize("NFKC", str(valor)).strip()
        valor = valor.replace("?", "-").replace("?", "-").replace("?", "-")
        limpio = re.sub(r"[^0-9,.-]", "", valor)

        if not limpio:
            return 0.0

        negativo = limpio.startswith("-")
        limpio = limpio.replace("-", "")
        if not limpio:
            return 0.0

        ultimo_punto = limpio.rfind(".")
        ultima_coma = limpio.rfind(",")

        if ultimo_punto >= 0 and ultima_coma >= 0:
            decimal = "." if ultimo_punto > ultima_coma else ","
            miles = "," if decimal == "." else "."
            limpio = limpio.replace(miles, "").replace(decimal, ".")
        elif "," in limpio:
            partes = limpio.split(",")
            if len(partes) == 2 and len(partes[-1]) in (1, 2):
                limpio = partes[0] + "." + partes[1]
            else:
                limpio = "".join(partes)
        elif "." in limpio:
            partes = limpio.split(".")
            if len(partes) == 2 and len(partes[-1]) in (1, 2):
                limpio = partes[0] + "." + partes[1]
            else:
                limpio = "".join(partes[:-1]) + ("." + partes[-1] if len(partes[-1]) in (1, 2) else partes[-1])

        try:
            monto = float(limpio)
        except ValueError:
            numeros = re.findall(r"\d+", limpio)
            monto = float("".join(numeros)) if numeros else 0.0

        return -monto if negativo else monto

    def actualizar_forma_pago(self, total):
        """Actualiza el monto sugerido cuando cambia la forma de pago."""
        tipo_pago = getattr(self, 'tipo_pago_var', tk.StringVar(value="Contado")).get()
        monto_actual = self.obtener_monto_recibido()
        if tipo_pago == "Credito" and abs(monto_actual - total) < 0.01:
            self.entry_monto_recibido.delete(0, tk.END)
            self.entry_monto_recibido.insert(0, "0.00")
            self.entry_monto_recibido.selection_range(0, 'end')
        elif tipo_pago == "Contado" and monto_actual <= 0:
            self.entry_monto_recibido.delete(0, tk.END)
            self.entry_monto_recibido.insert(0, f"{total:.2f}")
            self.entry_monto_recibido.selection_range(0, 'end')
        self.calcular_cambio(total)

    def calcular_cambio(self, total):
        """Calcular y mostrar el cambio o saldo pendiente."""
        try:
            monto_recibido = self.obtener_monto_recibido()
            tipo_pago = getattr(self, 'tipo_pago_var', tk.StringVar(value="Contado")).get()
            diferencia = monto_recibido - total

            if tipo_pago == "Credito":
                saldo = max(total - monto_recibido, 0)
                color = self.COLORS['danger'] if saldo > 0 else self.COLORS['success']
                self.label_cambio.config(text=f"Saldo pendiente: ${saldo:,.2f}", fg=color)
            elif diferencia >= 0:
                self.label_cambio.config(text=f"Cambio: ${diferencia:,.2f}", fg=self.COLORS['success'])
            else:
                self.label_cambio.config(text=f"Falta: ${abs(diferencia):,.2f}", fg=self.COLORS['danger'])
        except ValueError:
            self.label_cambio.config(text="Cambio: $0.00", fg=self.COLORS['accent'])

    def aceptar_venta(self, total):
        """Aceptar y procesar la venta completa."""
        try:
            monto_recibido = self.obtener_monto_recibido()
            tipo_pago = getattr(self, 'tipo_pago_var', tk.StringVar(value="Contado")).get()
            if tipo_pago == "Contado" and monto_recibido <= 0:
                monto_recibido = total
            if tipo_pago == "Contado" and monto_recibido < total:
                messagebox.showerror("Error", "El monto recibido es insuficiente para una venta de contado")
                return

            cambio = max(monto_recibido - total, 0) if tipo_pago == "Contado" else 0
            saldo = max(total - monto_recibido, 0) if tipo_pago == "Credito" else 0
            folio_actual = self.entry_folio.get().strip() if hasattr(self, 'entry_folio') else ""

            print(" INICIANDO PROCESO DE VENTA...")
            venta_id = self.guardar_venta_en_bd(total, monto_recibido, cambio, tipo_pago)

            if venta_id:
                print(f" Venta guardada exitosamente con ID: {venta_id}")
                self.cerrar_modal_pago()
                factura_pdf = ""
                try:
                    subtotal_venta = sum(p['total'] for p in self.productos_seleccionados)
                    iva_venta = subtotal_venta * self.obtener_tasa_iva()
                    factura_pdf = generar_factura(
                        total,
                        cliente=self.entry_cliente.get() or "Cliente General",
                        productos=list(self.productos_seleccionados),
                        datos_venta={
                            "venta_id": venta_id,
                            "numero_factura": self.numero_factura - 1,
                            "folio": folio_actual or f"V-{venta_id:06d}",
                            "fecha": self.entry_fecha.get().strip() if hasattr(self, 'entry_fecha') else datetime.datetime.now().strftime("%d/%m/%Y"),
                            "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                            "subtotal": subtotal_venta,
                            "iva": iva_venta,
                            "total": total,
                            "tipo_pago": tipo_pago,
                            "monto_recibido": monto_recibido,
                            "cambio": cambio,
                            "saldo": saldo,
                            "direccion_cliente": self.entry_direccion.get().strip() if hasattr(self, 'entry_direccion') else "",
                            "telefono_cliente": self.entry_telefono.get().strip() if hasattr(self, 'entry_telefono') else "",
                            "vendedor": self.entry_vendedor.get().strip() if hasattr(self, 'entry_vendedor') else "",
                        },
                    )
                except Exception as e:
                    print(f"Error generando PDF de factura: {e}")
                self.limpiar_venta()
                messagebox.showinfo(
                    "Venta Completada",
                    f"Transaccion procesada exitosamente!\n\n"
                    f"Folio: {folio_actual or 'Sin folio'}\n"
                    f"Pago: {tipo_pago}\n"
                    f"Total: ${total:,.2f}\n"
                    f"Recibido: ${monto_recibido:,.2f}\n"
                    f"Cambio: ${cambio:,.2f}\n"
                    f"Saldo: ${saldo:,.2f}\n\n"
                    f"Transaccion guardada en base de datos"
                    + (f"\nPDF: {factura_pdf}" if factura_pdf else "")
                )
                print(" VENTA COMPLETADA EXITOSAMENTE")
            else:
                detalle_error = getattr(self, 'ultimo_error_pago', '')
                mensaje = "Error al guardar la venta en la base de datos"
                if detalle_error:
                    mensaje += f"\n\nDetalle: {detalle_error}"
                messagebox.showerror("Error", mensaje)
        except ValueError as e:
            print(f"Error leyendo monto recibido: {e}")
            messagebox.showerror("Error", "No se pudo procesar el pago. Borra el monto recibido y escribe solo numeros, por ejemplo: 100")
        except Exception as e:
            print(f" Error en aceptar_venta: {e}")
            messagebox.showerror("Error", f"Error procesando la venta: {e}")
    def guardar_venta_en_bd(self, total, monto_recibido, cambio, tipo_pago="Contado"):
        """Guardar la venta completa en la base de datos."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            c.execute("""CREATE TABLE IF NOT EXISTS ventas (
                factura INTEGER,
                cliente TEXT,
                articulo TEXT,
                precio REAL,
                cantidad INTEGER,
                total REAL,
                fecha TEXT,
                hora TEXT,
                costo REAL
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER,
                producto TEXT,
                precio_unitario REAL,
                cantidad INTEGER,
                subtotal REAL
            )""")
            self.asegurar_columnas_detalle_ventas(c)
            c.execute("""CREATE TABLE IF NOT EXISTS abonos_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                nota TEXT
            )""")
            self.asegurar_columnas_abonos_ventas(c)
            self.asegurar_columnas_ventas(c)

            cliente = self.entry_cliente.get() or "Cliente General"
            fecha_actual = (self.entry_fecha.get().strip() if hasattr(self, 'entry_fecha') else '') or datetime.datetime.now().strftime("%d/%m/%Y")
            hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
            numero_factura = self.numero_factura
            subtotal = sum(p['total'] for p in self.productos_seleccionados)
            iva = subtotal * self.obtener_tasa_iva()
            costo_estimado = sum((p.get('precio', 0) * p.get('cantidad', 0)) * 0.8 for p in self.productos_seleccionados)
            folio = self.entry_folio.get().strip() if hasattr(self, 'entry_folio') else ""
            saldo = max(total - monto_recibido, 0) if tipo_pago == "Credito" else 0
            estado_pago = "Pagado" if saldo <= 0 else "Credito"
            direccion_cliente = self.entry_direccion.get().strip() if hasattr(self, 'entry_direccion') else ''
            telefono_cliente = self.entry_telefono.get().strip() if hasattr(self, 'entry_telefono') else ''
            vendedor = self.entry_vendedor.get().strip() if hasattr(self, 'entry_vendedor') else ''
            nota_imagen = getattr(self, '_nota_imagen', '')

            c.execute("""
                INSERT INTO ventas (
                    numero_factura, factura, cliente, articulo, precio, cantidad, total, fecha, hora, costo,
                    subtotal, iva, monto_recibido, cambio, folio, tipo_pago, saldo, estado_pago,
                    direccion_cliente, telefono_cliente, vendedor, nota_imagen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero_factura, numero_factura, cliente, "Venta Multiple", subtotal, 1, total, fecha_actual, hora_actual,
                costo_estimado, subtotal, iva, monto_recibido, cambio, folio, tipo_pago, saldo, estado_pago,
                direccion_cliente, telefono_cliente, vendedor, nota_imagen
            ))

            venta_id = c.lastrowid
            if monto_recibido > 0:
                c.execute("""
                    INSERT INTO abonos_ventas (venta_id, monto, fecha, hora, nota)
                    VALUES (?, ?, ?, ?, ?)
                """, (venta_id, monto_recibido, fecha_actual, hora_actual, "Pago inicial"))

            for producto in self.productos_seleccionados:
                c.execute("""
                    INSERT INTO detalle_ventas (venta_id, producto, precio_unitario, cantidad, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (venta_id, producto['nombre'], producto['precio'], producto['cantidad'], producto['total']))
                if not producto.get('origen_nota'):
                    self.actualizar_stock_producto(c, producto['nombre'], producto['cantidad'], producto.get('codigo', ''), producto.get('tabla', ''))

            conn.commit()
            conn.close()
            self.numero_factura += 1
            return venta_id
        except Exception as e:
            print(f"Error guardando venta: {e}")
            self.ultimo_error_pago = str(e)
            if conn:
                conn.rollback()
                conn.close()
            return None
    def crear_tablas_credito_abonos(self):
        """Prepara columnas de credito y la tabla de abonos de ventas."""
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS abonos_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                nota TEXT
            )""")
            self.asegurar_columnas_abonos_ventas(c)
            if self.tabla_existe(c, "ventas"):
                self.asegurar_columnas_ventas(c)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"No se pudo preparar abonos de ventas: {e}")

    def asegurar_columnas_ventas(self, cursor):
        columnas = [row[1] for row in cursor.execute("PRAGMA table_info(ventas)")]
        extras = {
            'numero_factura': 'INTEGER',
            'subtotal': 'REAL DEFAULT 0',
            'iva': 'REAL DEFAULT 0',
            'monto_recibido': 'REAL DEFAULT 0',
            'cambio': 'REAL DEFAULT 0',
            'folio': 'TEXT',
            'tipo_pago': 'TEXT DEFAULT "Contado"',
            'saldo': 'REAL DEFAULT 0',
            'estado_pago': 'TEXT DEFAULT "Pagado"',
            'direccion_cliente': 'TEXT',
            'telefono_cliente': 'TEXT',
            'vendedor': 'TEXT',
            'nota_imagen': 'TEXT'
        }
        for columna, definicion in extras.items():
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE ventas ADD COLUMN {columna} {definicion}")

    def asegurar_columnas_detalle_ventas(self, cursor):
        columnas = [row[1] for row in cursor.execute("PRAGMA table_info(detalle_ventas)")]
        extras = {
            'producto': 'TEXT',
            'precio_unitario': 'REAL DEFAULT 0',
            'cantidad': 'INTEGER DEFAULT 0',
            'subtotal': 'REAL DEFAULT 0',
        }
        for columna, definicion in extras.items():
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE detalle_ventas ADD COLUMN {columna} {definicion}")

    def asegurar_columnas_abonos_ventas(self, cursor):
        columnas = [row[1] for row in cursor.execute("PRAGMA table_info(abonos_ventas)")]
        extras = {
            'venta_id': 'INTEGER',
            'monto': 'REAL DEFAULT 0',
            'fecha': 'TEXT',
            'hora': 'TEXT',
            'nota': 'TEXT',
        }
        for columna, definicion in extras.items():
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE abonos_ventas ADD COLUMN {columna} {definicion}")
    def actualizar_stock_producto(self, cursor, nombre_producto, cantidad_vendida, codigo_producto='', tabla_origen=''):
        """Actualizar stock del producto despues de la venta."""
        try:
            if tabla_origen == 'productos' and self.tabla_existe(cursor, "productos"):
                if codigo_producto:
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE codigo = ?",
                                   (cantidad_vendida, codigo_producto))
                else:
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                                   (cantidad_vendida, nombre_producto))
            elif self.tabla_existe(cursor, "articulos"):
                if codigo_producto:
                    cursor.execute("UPDATE articulos SET stock = stock - ? WHERE codigo = ?",
                                   (cantidad_vendida, codigo_producto))
                else:
                    cursor.execute("UPDATE articulos SET stock = stock - ? WHERE articulo = ?",
                                   (cantidad_vendida, nombre_producto))

            print(f"Stock actualizado para {nombre_producto}: -{cantidad_vendida}")
        except Exception as e:
            print(f"Error actualizando stock: {e}")

    def imprimir_ticket(self, venta_id, total, monto_recibido, cambio):
        """Generar e imprimir ticket de venta"""
        try:
            # Crear contenido del ticket
            ticket_content = self.generar_contenido_ticket(venta_id, total, monto_recibido, cambio)
            
            # Guardar ticket en archivo temporal
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(ticket_content)
                ticket_path = f.name
            
            # Intentar imprimir (simulado)
            messagebox.showinfo("Imprimiendo", 
                              f"Ticket generado y enviado a impresora\n\n"
                              f"Archivo: {ticket_path}\n\n"
                              f"En un sistema real, esto se enviaría\n"
                              f"directamente a la impresora de tickets.")
            
            # Abrir archivo para mostrar contenido
            if os.name == 'nt':  # Windows
                os.startfile(ticket_path)
            else:  # Linux/Mac
                os.system(f'xdg-open {ticket_path}')
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al imprimir ticket: {e}")
    
    def generar_contenido_ticket(self, venta_id, total, monto_recibido, cambio):
        """Generar contenido del ticket de venta"""
        cliente = self.entry_cliente.get() or "Cliente General"
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        
        ticket = f"""
{'='*40}
           MI TIENDA
         SISTEMA DE VENTAS
{'='*40}

Folio: {(self.entry_folio.get().strip() if hasattr(self, 'entry_folio') else '') or 'Sin folio'}
Fecha: {fecha_actual}
Hora: {hora_actual}
Cliente: {cliente}

{'='*40}
PRODUCTOS
{'='*40}
"""
        
        for producto in self.productos_seleccionados:
            nombre = producto['nombre'][:25]  # Limitar longitud
            precio = producto['precio']
            cantidad = producto['cantidad']
            subtotal = producto['total']
            
            ticket += f"{nombre:<25} {cantidad:>3} x ${precio:>6.2f} = ${subtotal:>8.2f}\n"
        
        subtotal_venta = sum(p['total'] for p in self.productos_seleccionados)
        iva = subtotal_venta * self.obtener_tasa_iva()
        
        ticket += f"""
{'='*40}
Subtotal:                    ${subtotal_venta:>8.2f}
{self.texto_iva()}:                   ${iva:>8.2f}
{'='*40}
TOTAL:                       ${total:>8.2f}

Recibido:                    ${monto_recibido:>8.2f}
Cambio:                      ${cambio:>8.2f}

{'='*40}
        ¡GRACIAS POR SU COMPRA!
         Vuelva pronto 
{'='*40}

ID Venta: {venta_id}
"""
        return ticket
    
    def enviar_a_impresora_fiscal(self, venta_id, total, monto_recibido, cambio):
        """Enviar factura a impresora fiscal"""
        try:
            print(" ENVIANDO A IMPRESORA FISCAL...")
            
            # Generar datos de la factura fiscal
            factura_fiscal = self.generar_factura_fiscal(venta_id, total, monto_recibido, cambio)
            
            # En un sistema real, aquí se enviaría a la impresora fiscal
            # Por ahora, simulamos el proceso y guardamos en archivo
            
            import tempfile
            import os
            from datetime import datetime
            
            # Crear archivo de factura fiscal
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"factura_fiscal_{self.numero_factura}_{timestamp}.txt"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                           encoding='utf-8', prefix=f"fiscal_{self.numero_factura}_") as f:
                f.write(factura_fiscal)
                fiscal_path = f.name
            
            print(f" Factura fiscal generada: {fiscal_path}")
            
            # Simular envío a impresora fiscal
            print(" Conectando con impresora fiscal...")
            print(" Enviando datos fiscales...")
            print(" Factura fiscal impresa correctamente")
            
            # Abrir archivo para mostrar (simulación)
            if os.name == 'nt':  # Windows
                os.startfile(fiscal_path)
            
            return True
            
        except Exception as e:
            print(f" Error enviando a impresora fiscal: {e}")
            messagebox.showwarning("Advertencia", 
                                 f"Error al enviar a impresora fiscal:\n{e}\n\n"
                                 f"La venta se guardó correctamente en la base de datos.")
            return False
    
    def generar_factura_fiscal(self, venta_id, total, monto_recibido, cambio):
        """Generar formato de factura fiscal"""
        cliente = self.entry_cliente.get() or "Cliente General"
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Obtener datos de la empresa desde la configuración
        from modulos.configuracion.gestor_configuracion import obtener_configuracion
        nombre_empresa = obtener_configuracion('nombre_empresa', 'Mi Tienda')
        direccion_empresa = obtener_configuracion('direccion_empresa', 'Caracas, Venezuela')
        rif_empresa = obtener_configuracion('rif_empresa', 'J-00000000-0')
        telefono_empresa = obtener_configuracion('telefono_empresa', '+58-212-1234567')
        
        factura = f"""
{'='*50}
              FACTURA FISCAL
{'='*50}

{nombre_empresa}
RIF: {rif_empresa}
{direccion_empresa}

FOLIO: {(self.entry_folio.get().strip() if hasattr(self, 'entry_folio') else '') or 'Sin folio'}
FECHA: {fecha_actual}
HORA: {hora_actual}
CAJERO: Sistema POS

CLIENTE: {cliente}
{'='*50}

DESCRIPCIÓN                QTY    P.UNIT    TOTAL
{'='*50}
"""
        
        for producto in self.productos_seleccionados:
            nombre = producto['nombre'][:20].ljust(20)
            cantidad = str(producto['cantidad']).rjust(3)
            precio = f"${producto['precio']:>7.2f}"
            subtotal = f"${producto['total']:>9.2f}"
            
            factura += f"{nombre} {cantidad} {precio} {subtotal}\n"
        
        subtotal_venta = sum(p['total'] for p in self.productos_seleccionados)
        iva = subtotal_venta * self.obtener_tasa_iva()
        
        factura += f"""
{'='*50}
SUBTOTAL:                           ${subtotal_venta:>9.2f}
{self.texto_iva()}:                          ${iva:>9.2f}
{'='*50}
TOTAL A PAGAR:                      ${total:>9.2f}

EFECTIVO RECIBIDO:                  ${monto_recibido:>9.2f}
CAMBIO:                             ${cambio:>9.2f}

{'='*50}
           GRACIAS POR SU COMPRA
        CONSERVE ESTA FACTURA FISCAL
{'='*50}

CONTROL FISCAL: {venta_id:08d}
SERIAL IMPRESORA: FIS-001-2024
FECHA SISTEMA: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

Esta es una factura fiscal válida
según normativas SENIAT
"""
        return factura

    def cerrar_modal_pago(self):
        """Cerrar el modal de pago"""
        if hasattr(self, 'modal_pago'):
            self.modal_pago.destroy()

