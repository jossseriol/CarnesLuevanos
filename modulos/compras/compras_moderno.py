import sqlite3
import tkinter as tk
import unicodedata
from tkinter import ttk, messagebox
from datetime import datetime
import customtkinter as ctk

from modulos.utils.estilos_modernos import estilos


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ComprasModerno(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.compra_seleccionada = None
        self.crear_tabla_compras()
        self.widgets()
        self.cargar_compras()

    def crear_tabla_compras(self):
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proveedor TEXT NOT NULL,
                    factura TEXT,
                    producto TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    costo_unitario REAL NOT NULL,
                    total REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    notas TEXT
                )
            ''')
            self.asegurar_columnas_compras(cursor)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS abonos_compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    nota TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo crear la tabla compras: {e}")

    def asegurar_columnas_compras(self, cursor):
        columnas = [row[1] for row in cursor.execute("PRAGMA table_info(compras)")]
        extras = {
            'tipo_pago': 'TEXT DEFAULT "Contado"',
            'monto_pagado': 'REAL DEFAULT 0',
            'saldo': 'REAL DEFAULT 0',
            'estado_pago': 'TEXT DEFAULT "Pagado"'
        }
        for columna, definicion in extras.items():
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE compras ADD COLUMN {columna} {definicion}")

    def asegurar_tabla_articulos(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                articulo TEXT NOT NULL,
                precio REAL NOT NULL,
                costo REAL NOT NULL,
                stock INTEGER NOT NULL,
                estado TEXT NOT NULL,
                imagen_path TEXT
            )
        ''')

    def normalizar_producto(self, texto):
        texto = str(texto or '').strip().lower()
        texto = ' '.join(texto.split())
        return ''.join(
            char for char in unicodedata.normalize('NFD', texto)
            if unicodedata.category(char) != 'Mn'
        )

    def sincronizar_compra_con_inventario(self, cursor, producto, cantidad, costo_unitario):
        self.asegurar_tabla_articulos(cursor)
        producto_normalizado = self.normalizar_producto(producto)
        cursor.execute("SELECT id, articulo, precio, stock FROM articulos")
        articulo_existente = None
        for articulo_id, nombre, precio, stock in cursor.fetchall():
            if self.normalizar_producto(nombre) == producto_normalizado:
                articulo_existente = (articulo_id, precio, stock)
                break

        if articulo_existente:
            articulo_id, precio_actual, stock_actual = articulo_existente
            precio_final = precio_actual if precio_actual and precio_actual > 0 else costo_unitario
            cursor.execute(
                """
                UPDATE articulos
                SET stock = ?, costo = ?, precio = ?, estado = 'activo'
                WHERE id = ?
                """,
                ((stock_actual or 0) + cantidad, costo_unitario, precio_final, articulo_id)
            )
            return 'actualizado'

        cursor.execute(
            """
            INSERT INTO articulos (codigo, articulo, precio, costo, stock, estado, imagen_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (None, producto.strip(), costo_unitario, costo_unitario, cantidad, 'activo', 'media/icons/img_default.png')
        )
        return 'creado'

    def widgets(self):
        """Interfaz minimalista y fluida, sin coordenadas fijas."""
        self.configure(bg='#f5f6f8')
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg='#f5f6f8', height=54)
        header.grid(row=0, column=0, sticky='ew')
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text='Módulo de Compras', bg='#f5f6f8', fg='#20242a',
                 font=('Poppins', 17, 'bold'), anchor='w').grid(row=0, column=0, sticky='ew', padx=18, pady=(8, 0))
        tk.Label(header, text='Entradas, proveedores, costos y saldos en una sola vista.',
                 bg='#f5f6f8', fg='#68707c', font=('Poppins', 9), anchor='w').grid(
                     row=1, column=0, sticky='ew', padx=20, pady=(0, 7))

        body = tk.Frame(self, bg='#f5f6f8')
        body.grid(row=1, column=0, sticky='nsew', padx=14, pady=(4, 12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        self.form_frame = ctk.CTkFrame(body, fg_color='#ffffff', corner_radius=12,
                                       border_width=1, border_color='#e3e6ea')
        self.form_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        for col in range(6):
            self.form_frame.grid_columnconfigure(col, weight=1, uniform='compra')
        ctk.CTkLabel(self.form_frame, text='Datos de la compra', fg_color='transparent', bg_color='#ffffff', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, columnspan=6, sticky='w', padx=14, pady=(10, 6))

        self.proveedor = self._entry_compra('Proveedor', 1, 0)
        self.factura = self._entry_compra('Factura / referencia', 1, 1)
        self.producto = self._entry_compra('Producto comprado', 1, 2, span=2)
        self.cantidad = self._entry_compra('Cantidad', 1, 4)
        self.costo_unitario = self._entry_compra('Costo unitario', 1, 5)

        self.tipo_pago = ctk.CTkComboBox(self.form_frame, values=['Contado', 'Credito'], height=34,
                                         corner_radius=8, border_color='#e3e6ea', fg_color='#ffffff',
                                         text_color='#20242a', dropdown_fg_color='#ffffff',
                                         dropdown_text_color='#20242a', dropdown_hover_color='#f6dede',
                                         button_color='#8f070c', button_hover_color='#6f0509',
                                         font=ctk.CTkFont(family='Poppins', size=9))
        self.tipo_pago.set('Contado')
        self.tipo_pago.grid(row=2, column=0, sticky='ew', padx=(14, 6), pady=(8, 12))
        self.monto_pagado = self._entry_compra('Pago inicial', 2, 1, pady=(8, 12))
        self.estado = ctk.CTkComboBox(self.form_frame, values=['Pendiente', 'Recibida', 'Pagada', 'Cancelada'],
                                      height=34, corner_radius=8, border_color='#e3e6ea', fg_color='#ffffff',
                                      text_color='#20242a', dropdown_fg_color='#ffffff',
                                      dropdown_text_color='#20242a', dropdown_hover_color='#f6dede',
                                      button_color='#8f070c', button_hover_color='#6f0509',
                                      font=ctk.CTkFont(family='Poppins', size=9))
        self.estado.set('Recibida')
        self.estado.grid(row=2, column=2, sticky='ew', padx=6, pady=(8, 12))
        self.notas = self._entry_compra('Notas', 2, 3, span=1, pady=(8, 12))
        ctk.CTkButton(self.form_frame, text='Registrar compra', command=self.registrar_compra,
                      height=34, corner_radius=8, fg_color='#8f070c', hover_color='#6f0509',
                      font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=2, column=4, sticky='ew', padx=6, pady=(8, 12))
        ctk.CTkButton(self.form_frame, text='Limpiar', command=self.limpiar_campos,
                      height=34, corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6',
                      text_color='#20242a', font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=2, column=5, sticky='ew', padx=(6, 14), pady=(8, 12))

        toolbar = ctk.CTkFrame(body, fg_color='#ffffff', corner_radius=12,
                               border_width=1, border_color='#e3e6ea')
        toolbar.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        toolbar.grid_columnconfigure(3, weight=1)
        self.metricas = {}
        for idx, (titulo, valor) in enumerate((('Compras', '0'), ('Invertido', '$ 0.00'), ('Pendientes', '0'))):
            box = tk.Frame(toolbar, bg='#f7f8fa', highlightthickness=1, highlightbackground='#eceef1')
            box.grid(row=0, column=idx, sticky='nsew', padx=(10 if idx == 0 else 4, 4), pady=10)
            tk.Label(box, text=titulo, bg='#f7f8fa', fg='#68707c', font=('Poppins', 8)).pack(anchor='w', padx=10, pady=(5, 0))
            value = tk.Label(box, text=valor, bg='#f7f8fa', fg='#8f070c', font=('Poppins', 12, 'bold'))
            value.pack(anchor='w', padx=10, pady=(0, 5))
            self.metricas[titulo] = value

        self.buscar = ctk.CTkEntry(toolbar, placeholder_text='Buscar proveedor, referencia, producto, estado o fecha',
                                   height=34, corner_radius=8, border_color='#e3e6ea', fg_color='#f7f8fa',
                                   text_color='#20242a', placeholder_text_color='#68707c',
                                   font=ctk.CTkFont(family='Poppins', size=9))
        self.buscar.grid(row=0, column=3, sticky='ew', padx=(12, 6), pady=15)
        self.buscar.bind('<KeyRelease>', self.filtrar_compras)
        ctk.CTkButton(toolbar, text='Actualizar', command=self.cargar_compras, width=86, height=34,
                      corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6', text_color='#20242a',
                      font=ctk.CTkFont(family='Poppins', size=8, weight='bold')).grid(row=0, column=4, padx=6, pady=15)
        ctk.CTkButton(toolbar, text='Eliminar', command=self.eliminar_compra, width=76, height=34,
                      corner_radius=8, fg_color='#b4232c', hover_color='#8f070c',
                      font=ctk.CTkFont(family='Poppins', size=8, weight='bold')).grid(
                          row=0, column=5, padx=(6, 12), pady=15)

        self._crear_tabla_responsive(body)

    def _entry_compra(self, placeholder, row, column, span=1, pady=(0, 6)):
        entry = ctk.CTkEntry(self.form_frame, placeholder_text=placeholder, height=34, corner_radius=8,
                             border_color='#e3e6ea', fg_color='#ffffff',
                             text_color='#20242a', placeholder_text_color='#68707c',
                             font=ctk.CTkFont(family='Poppins', size=9))
        entry.grid(row=row, column=column, columnspan=span, sticky='ew',
                   padx=(14 if column == 0 else 6, 14 if column + span == 6 else 6), pady=pady)
        return entry

    def _crear_tabla_responsive(self, parent):
        table_frame = ctk.CTkFrame(parent, fg_color='#ffffff', corner_radius=12,
                                   border_width=1, border_color='#e3e6ea')
        table_frame.grid(row=2, column=0, sticky='nsew')
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(table_frame, text='Historial de compras', fg_color='transparent', bg_color='#ffffff', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, sticky='w', padx=14, pady=(10, 6))

        style = ttk.Style()
        style.configure('Compras.Treeview', background='#ffffff', fieldbackground='#ffffff',
                        foreground='#20242a', rowheight=27, borderwidth=0, font=('Poppins', 9))
        style.configure('Compras.Treeview.Heading', background='#f0f1f3', foreground='#20242a',
                        font=('Poppins', 9, 'bold'), relief='flat')
        style.map('Compras.Treeview', background=[('selected', '#f6dede')], foreground=[('selected', '#20242a')])
        columns = ('ID', 'Proveedor', 'Factura', 'Producto', 'Cantidad', 'Costo', 'Total', 'Tipo', 'Saldo', 'Pago', 'Fecha', 'Estado')
        grid = tk.Frame(table_frame, bg='#ffffff')
        grid.grid(row=1, column=0, sticky='nsew', padx=12, pady=(0, 12))
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(grid, columns=columns, show='headings', style='Compras.Treeview')
        widths = {'ID':45, 'Proveedor':120, 'Factura':90, 'Producto':140, 'Cantidad':70,
                  'Costo':80, 'Total':90, 'Tipo':70, 'Saldo':85, 'Pago':75, 'Fecha':90, 'Estado':80}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor='center', stretch=col in ('Proveedor', 'Producto'))
        sy = ttk.Scrollbar(grid, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(grid, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        self.tree.bind('<<TreeviewSelect>>', self.seleccionar_compra)
        self.tree.bind('<Double-1>', self.abrir_historial_abonos_compra)

    def crear_header(self):
        header = tk.Frame(self, bg=estilos.COLORS['bg_primary'])
        header.place(x=20, y=15, width=1360, height=70)

        tk.Label(
            header,
            text="Modulo de Compras",
            font=('Poppins', 24, 'bold'),
            bg=estilos.COLORS['bg_primary'],
            fg=estilos.COLORS['primary2']
        ).place(x=0, y=0)

        tk.Label(
            header,
            text="Controla entradas, proveedores, facturas y costo real de mercancia",
            font=('Poppins', 11),
            bg=estilos.COLORS['bg_primary'],
            fg=estilos.COLORS['dark_gray']
        ).place(x=3, y=42)

    def crear_formulario(self):
        self.form_frame = ctk.CTkFrame(
            self,
            width=350,
            height=700,
            corner_radius=18,
            fg_color=estilos.COLORS['white'],
            border_width=1,
            border_color=estilos.COLORS['border']
        )
        self.form_frame.place(x=20, y=100)

        ctk.CTkLabel(
            self.form_frame,
            text="Nueva compra",
            font=ctk.CTkFont(family="Poppins", size=20, weight="bold"),
            text_color=estilos.COLORS['primary2']
        ).place(x=22, y=18)

        ctk.CTkLabel(
            self.form_frame,
            text="Registra compras de proveedores y revisa el historial.",
            font=ctk.CTkFont(family="Poppins", size=11),
            text_color=estilos.COLORS['gray']
        ).place(x=22, y=50)

        self.proveedor = self.crear_entry("Proveedor", 92)
        self.factura = self.crear_entry("Factura / referencia", 160)
        self.producto = self.crear_entry("Producto comprado", 228)
        self.cantidad = self.crear_entry("Cantidad", 296)
        self.costo_unitario = self.crear_entry("Costo unitario", 364)

        self.tipo_pago = ctk.CTkComboBox(
            self.form_frame,
            values=["Contado", "Credito"],
            width=306,
            height=38,
            corner_radius=10,
            border_color=estilos.COLORS['border'],
            fg_color=estilos.COLORS['white'],
            button_color=estilos.COLORS['primary2'],
            button_hover_color=estilos.COLORS['secondary1'],
            font=ctk.CTkFont(family="Poppins", size=12)
        )
        self.tipo_pago.set("Contado")
        self.tipo_pago.place(x=22, y=432)
        self.monto_pagado = self.crear_entry("Pago inicial / monto pagado", 480)

        self.estado = ctk.CTkComboBox(
            self.form_frame,
            values=["Pendiente", "Recibida", "Pagada", "Cancelada"],
            width=306,
            height=38,
            corner_radius=10,
            border_color=estilos.COLORS['border'],
            fg_color=estilos.COLORS['white'],
            button_color=estilos.COLORS['primary2'],
            button_hover_color=estilos.COLORS['secondary1'],
            font=ctk.CTkFont(family="Poppins", size=12)
        )
        self.estado.set("Recibida")
        self.estado.place(x=22, y=528)

        self.notas = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="Notas",
            width=306,
            height=38,
            corner_radius=10,
            border_color=estilos.COLORS['border'],
            fg_color=estilos.COLORS['white'],
            font=ctk.CTkFont(family="Poppins", size=12)
        )
        self.notas.place(x=22, y=578)

        ctk.CTkButton(
            self.form_frame,
            text="Registrar compra",
            command=self.registrar_compra,
            width=146,
            height=42,
            corner_radius=12,
            fg_color=estilos.COLORS['primary2'],
            hover_color=estilos.COLORS['secondary1'],
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold")
        ).place(x=22, y=638)

        ctk.CTkButton(
            self.form_frame,
            text="Limpiar",
            command=self.limpiar_campos,
            width=146,
            height=42,
            corner_radius=12,
            fg_color=estilos.COLORS['dark_gray'],
            hover_color=estilos.COLORS['gray'],
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold")
        ).place(x=182, y=638)

    def crear_entry(self, placeholder, y):
        entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text=placeholder,
            width=306,
            height=38,
            corner_radius=10,
            border_color=estilos.COLORS['border'],
            fg_color=estilos.COLORS['white'],
            font=ctk.CTkFont(family="Poppins", size=12)
        )
        entry.place(x=22, y=y)
        return entry

    def crear_metricas(self):
        self.metricas = {}
        cards = [
            ("Compras", "0", estilos.COLORS['primary2']),
            ("Invertido", "$ 0.00", estilos.COLORS['secondary1']),
            ("Pendientes", "0", estilos.COLORS['warning']),
        ]
        x = 395
        for titulo, valor, color in cards:
            card = ctk.CTkFrame(self, width=285, height=94, corner_radius=16, fg_color=color)
            card.place(x=x, y=100)
            tk.Label(
                card,
                text=titulo,
                bg=color,
                fg=estilos.COLORS['white'],
                font=('Poppins', 11, 'bold')
            ).place(x=18, y=15)
            value_label = tk.Label(
                card,
                text=valor,
                bg=color,
                fg=estilos.COLORS['white'],
                font=('Poppins', 22, 'bold')
            )
            value_label.place(x=18, y=42)
            self.metricas[titulo] = value_label
            x += 300

    def crear_busqueda(self):
        search_frame = ctk.CTkFrame(
            self,
            width=885,
            height=78,
            corner_radius=16,
            fg_color=estilos.COLORS['white'],
            border_width=1,
            border_color=estilos.COLORS['border']
        )
        search_frame.place(x=395, y=214)

        ctk.CTkLabel(
            search_frame,
            text="Buscar compras",
            font=ctk.CTkFont(family="Poppins", size=14, weight="bold"),
            text_color=estilos.COLORS['primary2']
        ).place(x=18, y=12)

        self.buscar = ctk.CTkEntry(
            search_frame,
            placeholder_text="Proveedor, factura, producto, estado o fecha",
            width=600,
            height=36,
            corner_radius=10,
            border_color=estilos.COLORS['border'],
            fg_color=estilos.COLORS['light'],
            font=ctk.CTkFont(family="Poppins", size=12)
        )
        self.buscar.place(x=18, y=38)
        self.buscar.bind("<KeyRelease>", self.filtrar_compras)

        ctk.CTkButton(
            search_frame,
            text="Actualizar",
            command=self.cargar_compras,
            width=116,
            height=36,
            corner_radius=10,
            fg_color=estilos.COLORS['info'],
            hover_color=estilos.COLORS['dark_gray']
        ).place(x=642, y=38)

        ctk.CTkButton(
            search_frame,
            text="Eliminar",
            command=self.eliminar_compra,
            width=100,
            height=36,
            corner_radius=10,
            fg_color=estilos.COLORS['danger'],
            hover_color="#8f070c"
        ).place(x=766, y=38)

    def crear_tabla(self):
        table_frame = ctk.CTkFrame(
            self,
            width=885,
            height=410,
            corner_radius=16,
            fg_color=estilos.COLORS['white'],
            border_width=1,
            border_color=estilos.COLORS['border']
        )
        table_frame.place(x=395, y=310)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Compras.Treeview",
            background=estilos.COLORS['white'],
            fieldbackground=estilos.COLORS['white'],
            foreground=estilos.COLORS['dark'],
            rowheight=30,
            borderwidth=0,
            font=('Poppins', 10)
        )
        style.configure(
            "Compras.Treeview.Heading",
            background=estilos.COLORS['primary2'],
            foreground=estilos.COLORS['white'],
            font=('Poppins', 10, 'bold')
        )
        style.map(
            "Compras.Treeview",
            background=[('selected', estilos.COLORS['secondary1'])],
            foreground=[('selected', estilos.COLORS['white'])]
        )

        columns = ("ID", "Proveedor", "Factura", "Producto", "Cantidad", "Costo", "Total", "Tipo", "Saldo", "Pago", "Fecha", "Estado")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Compras.Treeview")
        self.tree.place(x=15, y=15, width=835, height=365)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.place(x=852, y=15, height=365)
        self.tree.configure(yscrollcommand=scrollbar.set)

        widths = {
            "ID": 45,
            "Proveedor": 120,
            "Factura": 90,
            "Producto": 130,
            "Cantidad": 70,
            "Costo": 75,
            "Total": 85,
            "Tipo": 75,
            "Saldo": 80,
            "Pago": 75,
            "Fecha": 90,
            "Estado": 80,
        }
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_compra)
        self.tree.bind("<Double-1>", self.abrir_historial_abonos_compra)

    def registrar_compra(self):
        proveedor = self.proveedor.get().strip()
        factura = self.factura.get().strip()
        producto = self.producto.get().strip()
        cantidad_texto = self.cantidad.get().strip()
        costo_texto = self.costo_unitario.get().strip()
        tipo_pago = self.tipo_pago.get().strip() or "Contado"
        monto_pagado_texto = self.monto_pagado.get().strip()
        estado = self.estado.get().strip()
        notas = self.notas.get().strip()

        if not proveedor or not producto or not cantidad_texto or not costo_texto:
            messagebox.showwarning("Campos incompletos", "Proveedor, producto, cantidad y costo son obligatorios.")
            return

        try:
            cantidad = int(cantidad_texto)
            costo_unitario = float(costo_texto)
        except ValueError:
            messagebox.showerror("Datos invalidos", "Cantidad debe ser entera y costo debe ser numerico.")
            return

        if cantidad <= 0 or costo_unitario < 0:
            messagebox.showerror("Datos invalidos", "Cantidad debe ser mayor a cero y costo no puede ser negativo.")
            return

        total = cantidad * costo_unitario
        if monto_pagado_texto:
            try:
                monto_pagado = float(monto_pagado_texto)
            except ValueError:
                messagebox.showerror("Datos invalidos", "El monto pagado debe ser numerico.")
                return
        else:
            monto_pagado = total if tipo_pago == "Contado" else 0
        if tipo_pago == "Contado" and monto_pagado < total:
            messagebox.showerror("Pago insuficiente", "Una compra de contado debe quedar pagada completa.")
            return
        saldo = max(total - monto_pagado, 0) if tipo_pago == "Credito" else 0
        estado_pago = "Pagado" if saldo <= 0 else "Credito"
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            self.asegurar_columnas_compras(cursor)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS abonos_compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    nota TEXT
                )
            ''')
            cursor.execute(
                """
                INSERT INTO compras (proveedor, factura, producto, cantidad, costo_unitario, total, fecha, estado, notas, tipo_pago, monto_pagado, saldo, estado_pago)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (proveedor, factura, producto, cantidad, costo_unitario, total, fecha, estado, notas, tipo_pago, monto_pagado, saldo, estado_pago)
            )
            compra_id = cursor.lastrowid
            if monto_pagado > 0:
                cursor.execute(
                    "INSERT INTO abonos_compras (compra_id, monto, fecha, hora, nota) VALUES (?, ?, ?, ?, ?)",
                    (compra_id, monto_pagado, fecha, hora, "Pago inicial")
                )
            movimiento_inventario = None
            if estado.lower() != "cancelada":
                movimiento_inventario = self.sincronizar_compra_con_inventario(cursor, producto, cantidad, costo_unitario)
            conn.commit()
            conn.close()
            detalle_inventario = ""
            if movimiento_inventario == "actualizado":
                detalle_inventario = "\nInventario actualizado: se sumo al producto existente."
            elif movimiento_inventario == "creado":
                detalle_inventario = "\nInventario actualizado: se creo el producto nuevo."
            messagebox.showinfo("Compra registrada", f"La compra fue registrada correctamente.{detalle_inventario}")
            self.limpiar_campos()
            self.cargar_compras()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo registrar la compra: {e}")
    def cargar_compras(self):
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, proveedor, factura, producto, cantidad, costo_unitario, total, tipo_pago, saldo, estado_pago, fecha, estado
                FROM compras
                ORDER BY id DESC
            """)
            compras = cursor.fetchall()
            conn.close()
            self.pintar_compras(compras)
            self.actualizar_metricas(compras)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudieron cargar las compras: {e}")

    def pintar_compras(self, compras):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for compra in compras:
            id_compra, proveedor, factura, producto, cantidad, costo, total, tipo_pago, saldo, estado_pago, fecha, estado = compra
            self.tree.insert(
                "",
                "end",
                values=(
                    id_compra,
                    proveedor,
                    factura or "-",
                    producto,
                    cantidad,
                    f"$ {costo:.2f}",
                    f"$ {total:.2f}",
                    tipo_pago,
                    f"$ {saldo:.2f}",
                    estado_pago,
                    fecha,
                    estado,
                )
            )

    def actualizar_metricas(self, compras):
        total_compras = len(compras)
        total_invertido = sum(float(compra[6]) for compra in compras)
        pendientes = sum(1 for compra in compras if str(compra[9]).lower() != "pagado")
        self.metricas["Compras"].configure(text=str(total_compras))
        self.metricas["Invertido"].configure(text=f"$ {total_invertido:.2f}")
        self.metricas["Pendientes"].configure(text=str(pendientes))

    def filtrar_compras(self, event=None):
        texto = self.buscar.get().strip().lower()
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            if texto:
                like = f"%{texto}%"
                cursor.execute("""
                    SELECT id, proveedor, factura, producto, cantidad, costo_unitario, total, tipo_pago, saldo, estado_pago, fecha, estado
                    FROM compras
                    WHERE lower(proveedor) LIKE ?
                       OR lower(factura) LIKE ?
                       OR lower(producto) LIKE ?
                       OR lower(fecha) LIKE ?
                       OR lower(estado) LIKE ?
                       OR lower(tipo_pago) LIKE ?
                       OR lower(estado_pago) LIKE ?
                    ORDER BY id DESC
                """, (like, like, like, like, like, like, like))
            else:
                cursor.execute("""
                    SELECT id, proveedor, factura, producto, cantidad, costo_unitario, total, tipo_pago, saldo, estado_pago, fecha, estado
                    FROM compras
                    ORDER BY id DESC
                """)
            compras = cursor.fetchall()
            conn.close()
            self.pintar_compras(compras)
            self.actualizar_metricas(compras)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo filtrar compras: {e}")

    def seleccionar_compra(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], "values")
        if not valores:
            return
        self.compra_seleccionada = valores[0]
        self.limpiar_campos()
        self.proveedor.insert(0, valores[1])
        self.factura.insert(0, "" if valores[2] == "-" else valores[2])
        self.producto.insert(0, valores[3])
        self.cantidad.insert(0, valores[4])
        self.costo_unitario.insert(0, str(valores[5]).replace("$", "").strip())
        self.tipo_pago.set(valores[7])
        self.monto_pagado.insert(0, "")
        self.estado.set(valores[11])

    def abrir_historial_abonos_compra(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], "values")
        if not valores:
            return
        compra_id, proveedor, factura, producto, saldo = valores[0], valores[1], valores[2], valores[3], valores[8]
        ventana = tk.Toplevel(self)
        ventana.title(f"Historial de abonos - Compra {factura}")
        ventana.geometry("560x520")
        ventana.configure(bg=estilos.COLORS['bg_primary'])
        ventana.transient(self)
        ventana.grab_set()

        tk.Label(ventana, text=f"{proveedor} - {producto}", font=('Poppins', 16, 'bold'),
                 bg=estilos.COLORS['bg_primary'], fg=estilos.COLORS['primary2']).pack(anchor='w', padx=20, pady=(18, 4))
        tk.Label(ventana, text=f"Saldo actual: {saldo}", font=('Poppins', 12, 'bold'),
                 bg=estilos.COLORS['bg_primary'], fg=estilos.COLORS['warning']).pack(anchor='w', padx=20, pady=(0, 12))

        tabla = ttk.Treeview(ventana, columns=("Fecha", "Hora", "Monto", "Nota"), show="headings", height=10)
        for col, ancho in {"Fecha": 110, "Hora": 90, "Monto": 110, "Nota": 210}.items():
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor="center")
        tabla.pack(fill='both', expand=True, padx=20, pady=(0, 12))

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT fecha, hora, monto, COALESCE(nota, '') FROM abonos_compras WHERE compra_id = ? ORDER BY id DESC", (compra_id,))
            for fecha, hora, monto, nota in cursor.fetchall():
                tabla.insert("", "end", values=(fecha, hora, f"$ {monto:.2f}", nota))
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")

        form = ctk.CTkFrame(ventana, fg_color=estilos.COLORS['white'], corner_radius=14)
        form.pack(fill='x', padx=20, pady=(0, 20))
        ctk.CTkLabel(form, text="Nuevo abono", font=ctk.CTkFont(family="Poppins", size=14, weight="bold"), text_color=estilos.COLORS['primary2']).grid(row=0, column=0, columnspan=2, sticky='w', padx=12, pady=(10, 4))
        entry_monto = ctk.CTkEntry(form, placeholder_text="Monto", width=200)
        entry_monto.grid(row=1, column=0, padx=12, pady=10, sticky='ew')
        entry_nota = ctk.CTkEntry(form, placeholder_text="Nota", width=220)
        entry_nota.grid(row=1, column=1, padx=12, pady=10, sticky='ew')
        ctk.CTkButton(form, text="Registrar abono", fg_color=estilos.COLORS['primary2'], hover_color=estilos.COLORS['secondary1'],
                      command=lambda: self.registrar_abono_compra(compra_id, entry_monto, entry_nota, ventana)).grid(row=2, column=0, columnspan=2, pady=(0, 12))

    def registrar_abono_compra(self, compra_id, entry_monto, entry_nota, ventana):
        try:
            monto = float(entry_monto.get().strip())
        except ValueError:
            messagebox.showerror("Monto invalido", "Escribe un monto numerico para el abono.")
            return
        if monto <= 0:
            messagebox.showerror("Monto invalido", "El abono debe ser mayor a cero.")
            return
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        nota = entry_nota.get().strip() or "Abono"
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            self.asegurar_columnas_compras(cursor)
            cursor.execute("INSERT INTO abonos_compras (compra_id, monto, fecha, hora, nota) VALUES (?, ?, ?, ?, ?)", (compra_id, monto, fecha, hora, nota))
            cursor.execute("SELECT COALESCE(saldo, 0), COALESCE(monto_pagado, 0) FROM compras WHERE id = ?", (compra_id,))
            saldo_actual, pagado_actual = cursor.fetchone()
            nuevo_saldo = max((saldo_actual or 0) - monto, 0)
            estado_pago = "Pagado" if nuevo_saldo <= 0 else "Credito"
            cursor.execute("UPDATE compras SET saldo = ?, monto_pagado = ?, estado_pago = ? WHERE id = ?", (nuevo_saldo, (pagado_actual or 0) + monto, estado_pago, compra_id))
            conn.commit()
            conn.close()
            ventana.destroy()
            self.cargar_compras()
            messagebox.showinfo("Abono registrado", "El abono se guardo correctamente.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo registrar el abono: {e}")
    def eliminar_compra(self):
        if not self.compra_seleccionada:
            messagebox.showwarning("Seleccion requerida", "Selecciona una compra para eliminar.")
            return

        confirmar = messagebox.askyesno("Confirmar", "Deseas eliminar la compra seleccionada?")
        if not confirmar:
            return

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM compras WHERE id = ?", (self.compra_seleccionada,))
            self.asegurar_columnas_compras(cursor)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS abonos_compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    nota TEXT
                )
            ''')
            conn.commit()
            conn.close()
            self.compra_seleccionada = None
            self.limpiar_campos()
            self.cargar_compras()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo eliminar la compra: {e}")

    def limpiar_campos(self):
        self.proveedor.delete(0, tk.END)
        self.factura.delete(0, tk.END)
        self.producto.delete(0, tk.END)
        self.cantidad.delete(0, tk.END)
        self.costo_unitario.delete(0, tk.END)
        self.tipo_pago.set("Contado")
        self.monto_pagado.delete(0, tk.END)
        self.estado.set("Recibida")
        self.notas.delete(0, tk.END)
        self.compra_seleccionada = None



