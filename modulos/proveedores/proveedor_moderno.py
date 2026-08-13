import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from modulos.utils.estilos_modernos import estilos

# Configurar CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ProveedorModerno(tk.Frame):
    
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.crear_tabla_proveedores()
        self.widgets()
        self.cargar_registros()
    
    def actualizar_moneda(self, nueva_moneda):
        """Actualizar cuando cambia la moneda (proveedores no tiene precios)"""
        try:
            print(f"Módulo Proveedores actualizado a moneda: {nueva_moneda}")
        except Exception as e:
            print(f"Error al actualizar moneda en Proveedores: {e}")
        
    def crear_tabla_proveedores(self):
        """Crear tabla de proveedores si no existe"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT NOT NULL,
                    rif TEXT UNIQUE NOT NULL,
                    celular TEXT,
                    direccion TEXT,
                    correo TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al crear tabla: {e}")
        
    def widgets(self):
        # Frame principal de formulario con estilo moderno
        form_frame = tk.LabelFrame(self, text="🏢 Gestión de Proveedores", 
                                  font=('Poppins', 16, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        form_frame.place(x=20, y=20, width=300, height=600)

        # Título del formulario
        title_label = tk.Label(form_frame, text="📝 Datos del Proveedor", 
                              font=('Poppins', 14, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['secondary'])
        title_label.place(x=10, y=10)

        # Campo Empresa
        tk.Label(form_frame, text="🏢 Empresa:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=50)
        
        self.empresa = tk.Entry(form_frame, font=('Poppins', 12), 
                               relief='solid', bd=1)
        self.empresa.place(x=10, y=80, width=270, height=35)

        # Campo RIF
        tk.Label(form_frame, text="🆔 RFC:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=130)
        
        self.rif = tk.Entry(form_frame, font=('Poppins', 12), 
                           relief='solid', bd=1)
        self.rif.place(x=10, y=160, width=270, height=35)

        # Campo Celular
        tk.Label(form_frame, text="📱 Celular:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=210)
        
        self.celular = tk.Entry(form_frame, font=('Poppins', 12), 
                               relief='solid', bd=1)
        self.celular.place(x=10, y=240, width=270, height=35)

        # Campo Dirección
        tk.Label(form_frame, text="🏠 Dirección:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=290)
        
        self.direccion = tk.Entry(form_frame, font=('Poppins', 12), 
                                 relief='solid', bd=1)
        self.direccion.place(x=10, y=320, width=270, height=35)

        # Campo Correo
        tk.Label(form_frame, text="📧 Correo:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=370)
        
        self.correo = tk.Entry(form_frame, font=('Poppins', 12), 
                              relief='solid', bd=1)
        self.correo.place(x=10, y=400, width=270, height=35)

        # Botones modernos con CustomTkinter
        btn_buscar = ctk.CTkButton(
            form_frame, 
            text="🔍 Buscar Proveedor", 
            command=self.buscar_proveedor,
            width=270,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
            fg_color=estilos.COLORS['info'],
            hover_color="#b30d12"
        )
        btn_buscar.place(x=10, y=460)

        btn_registrar = ctk.CTkButton(
            form_frame, 
            text="➕ Registrar Proveedor", 
            command=self.registrar_proveedor,
            width=270,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
            fg_color=estilos.COLORS['success'],
            hover_color="#8f070c"
        )
        btn_registrar.place(x=10, y=520)

        # Frame para la tabla con estilo moderno
        table_frame = tk.LabelFrame(self, text="📋 Lista de Proveedores", 
                                   font=('Poppins', 16, 'bold'), 
                                   bg=estilos.COLORS['white'],
                                   fg=estilos.COLORS['primary'])
        table_frame.place(x=340, y=20, width=880, height=720)

        # Configurar Treeview con estilo moderno
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores del Treeview
        style.configure("Treeview",
                       background=estilos.COLORS['white'],
                       foreground=estilos.COLORS['dark'],
                       fieldbackground=estilos.COLORS['white'],
                       font=('Poppins', 10))
        
        style.configure("Treeview.Heading",
                       background=estilos.COLORS['primary'],
                       foreground='white',
                       font=('Poppins', 11, 'bold'))
        
        style.map('Treeview',
                 background=[('selected', estilos.COLORS['primary'])],
                 foreground=[('selected', 'white')])

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient='vertical')
        scrollbar_y.pack(side='right', fill='y')

        scrollbar_x = ttk.Scrollbar(table_frame, orient='horizontal')
        scrollbar_x.pack(side='bottom', fill='x')

        # Treeview
        self.tree = ttk.Treeview(table_frame, 
                                yscrollcommand=scrollbar_y.set, 
                                xscrollcommand=scrollbar_x.set,
                                columns=("ID", "Empresa", "RIF", "Celular", "Direccion", "Correo"), 
                                show="headings",
                                height=30)

        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        # Configurar scrollbars
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # Configurar encabezados con iconos
        self.tree.heading("ID", text="🆔 ID")
        self.tree.heading("Empresa", text="🏢 Empresa")
        self.tree.heading("RIF", text="🆔 RIF")
        self.tree.heading("Celular", text="📱 Celular")
        self.tree.heading("Direccion", text="🏠 Dirección")
        self.tree.heading("Correo", text="📧 Correo")

        # Configurar columnas
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Empresa", width=150, anchor="w")
        self.tree.column("RIF", width=120, anchor="center")
        self.tree.column("Celular", width=120, anchor="center")
        self.tree.column("Direccion", width=200, anchor="w")
        self.tree.column("Correo", width=200, anchor="w")

        # Bind para selección
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.modificar_proveedor)

        # Frame de estadísticas
        stats_frame = tk.Frame(self, bg=estilos.COLORS['white'], relief='solid', bd=1)
        stats_frame.place(x=20, y=640, width=300, height=100)
        
        tk.Label(stats_frame, text="📊 Estadísticas", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['primary']).place(x=10, y=10)
        
        self.stats_label = tk.Label(stats_frame, text="Total de proveedores: 0", 
                                   font=('Poppins', 10), 
                                   bg=estilos.COLORS['white'],
                                   fg=estilos.COLORS['dark'])
        self.stats_label.place(x=10, y=40)

    def widgets(self):
        """Interfaz minimalista y adaptable, alineada con Ventas y Compras."""
        self.configure(bg='#f5f6f8')
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg='#f5f6f8', height=54)
        header.grid(row=0, column=0, sticky='ew')
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text='Módulo de Proveedores', bg='#f5f6f8', fg='#20242a',
                 font=('Poppins', 17, 'bold'), anchor='w').grid(row=0, column=0, sticky='ew', padx=18, pady=(8, 0))
        tk.Label(header, text='Directorio, contacto y administración de proveedores.',
                 bg='#f5f6f8', fg='#68707c', font=('Poppins', 9), anchor='w').grid(
                     row=1, column=0, sticky='ew', padx=20, pady=(0, 7))

        body = tk.Frame(self, bg='#f5f6f8')
        body.grid(row=1, column=0, sticky='nsew', padx=14, pady=(4, 12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        form = ctk.CTkFrame(body, fg_color='#ffffff', corner_radius=12,
                            border_width=1, border_color='#e3e6ea')
        form.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        for col in range(7):
            form.grid_columnconfigure(col, weight=1, uniform='proveedor')
        ctk.CTkLabel(form, text='Datos del proveedor', fg_color='transparent', bg_color='#ffffff', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, columnspan=7, sticky='w', padx=14, pady=(10, 6))
        self.empresa = self._entry_proveedor(form, 'Empresa', 0)
        self.rif = self._entry_proveedor(form, 'RIF / identificación', 1)
        self.celular = self._entry_proveedor(form, 'Celular', 2)
        self.direccion = self._entry_proveedor(form, 'Dirección', 3, span=2)
        self.correo = self._entry_proveedor(form, 'Correo electrónico', 5)
        ctk.CTkButton(form, text='Registrar', command=self.registrar_proveedor, height=34,
                      corner_radius=8, fg_color='#8f070c', hover_color='#6f0509',
                      font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=1, column=6, sticky='ew', padx=(6, 14), pady=(0, 12))

        toolbar = ctk.CTkFrame(body, fg_color='#ffffff', corner_radius=12,
                               border_width=1, border_color='#e3e6ea')
        toolbar.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)
        self.stats_label = tk.Label(toolbar, text='Total de proveedores: 0', bg='#ffffff',
                                    fg='#8f070c', font=('Poppins', 10, 'bold'))
        self.stats_label.grid(row=0, column=0, padx=(14, 12), pady=14)
        self.busqueda = ctk.CTkEntry(toolbar, placeholder_text='Buscar empresa, RIF, celular, dirección o correo',
                                     height=34, corner_radius=8, border_color='#e3e6ea', fg_color='#f7f8fa',
                                     font=ctk.CTkFont(family='Poppins', size=9))
        self.busqueda.grid(row=0, column=1, sticky='ew', padx=6, pady=10)
        self.busqueda.bind('<KeyRelease>', self.filtrar_proveedores)
        ctk.CTkButton(toolbar, text='Actualizar', command=self.cargar_registros, width=86, height=34,
                      corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6', text_color='#20242a',
                      font=ctk.CTkFont(family='Poppins', size=8, weight='bold')).grid(
                          row=0, column=2, padx=6, pady=10)
        ctk.CTkButton(toolbar, text='Modificar', command=self.modificar_proveedor, width=82, height=34,
                      corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6', text_color='#20242a',
                      font=ctk.CTkFont(family='Poppins', size=8, weight='bold')).grid(
                          row=0, column=3, padx=6, pady=10)
        ctk.CTkButton(toolbar, text='Limpiar', command=self.limpiar_campos, width=72, height=34,
                      corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6', text_color='#20242a',
                      font=ctk.CTkFont(family='Poppins', size=8, weight='bold')).grid(
                          row=0, column=4, padx=(6, 12), pady=10)

        table_card = ctk.CTkFrame(body, fg_color='#ffffff', corner_radius=12,
                                  border_width=1, border_color='#e3e6ea')
        table_card.grid(row=2, column=0, sticky='nsew')
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(table_card, text='Lista de proveedores', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, sticky='w', padx=14, pady=(10, 6))

        style = ttk.Style()
        style.configure('Proveedores.Treeview', background='#ffffff', fieldbackground='#ffffff',
                        foreground='#20242a', rowheight=27, borderwidth=0, font=('Poppins', 9))
        style.configure('Proveedores.Treeview.Heading', background='#f0f1f3', foreground='#20242a',
                        font=('Poppins', 9, 'bold'), relief='flat')
        style.map('Proveedores.Treeview', background=[('selected', '#f6dede')],
                  foreground=[('selected', '#20242a')])
        grid = tk.Frame(table_card, bg='#ffffff')
        grid.grid(row=1, column=0, sticky='nsew', padx=12, pady=(0, 12))
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_columnconfigure(0, weight=1)
        columnas = ('ID', 'Empresa', 'RIF', 'Celular', 'Direccion', 'Correo')
        self.tree = ttk.Treeview(grid, columns=columnas, show='headings', style='Proveedores.Treeview')
        anchos = {'ID':55, 'Empresa':180, 'RIF':130, 'Celular':130, 'Direccion':250, 'Correo':220}
        titulos = {'ID':'ID', 'Empresa':'Empresa', 'RIF':'RIF', 'Celular':'Celular',
                   'Direccion':'Dirección', 'Correo':'Correo'}
        for col in columnas:
            self.tree.heading(col, text=titulos[col])
            self.tree.column(col, width=anchos[col], anchor='w' if col in ('Empresa','Direccion','Correo') else 'center',
                             stretch=col != 'ID')
        sy = ttk.Scrollbar(grid, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(grid, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.modificar_proveedor)

    def _entry_proveedor(self, parent, placeholder, column, span=1):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=34, corner_radius=8,
                             border_color='#e3e6ea', fg_color='#ffffff',
                             font=ctk.CTkFont(family='Poppins', size=9))
        entry.grid(row=1, column=column, columnspan=span, sticky='ew',
                   padx=(14 if column == 0 else 6, 14 if column + span == 7 else 6), pady=(0, 12))
        return entry

    def filtrar_proveedores(self, _event=None):
        texto = self.busqueda.get().strip().lower()
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('''
                SELECT id, empresa, rif, celular, direccion, correo
                FROM proveedores
                WHERE ? = '' OR LOWER(COALESCE(empresa, '')) LIKE ?
                   OR LOWER(COALESCE(rif, '')) LIKE ? OR LOWER(COALESCE(celular, '')) LIKE ?
                   OR LOWER(COALESCE(direccion, '')) LIKE ? OR LOWER(COALESCE(correo, '')) LIKE ?
                ORDER BY empresa
            ''', (texto, *(f'%{texto}%',) * 5))
            rows = cur.fetchall()
            conn.close()
            self.limpiar_treeview()
            for row in rows:
                self.tree.insert('', 'end', values=row)
            self.stats_label.config(text=f'Resultados: {len(rows)}')
        except sqlite3.Error as error:
            messagebox.showerror('Error', f'No se pudo filtrar proveedores: {error}')

    def widgets(self):
        """Misma estructura visual de Ventas: captura, lista y resumen lateral."""
        self.configure(bg='#f5f6f8')
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg='#f5f6f8', height=54)
        header.grid(row=0, column=0, sticky='ew')
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text='Módulo de Proveedores', bg='#f5f6f8', fg='#20242a',
                 font=('Poppins', 17, 'bold'), anchor='w').grid(row=0, column=0, sticky='ew', padx=18, pady=(8, 0))
        tk.Label(header, text='Directorio, contacto y administración de proveedores.',
                 bg='#f5f6f8', fg='#68707c', font=('Poppins', 9), anchor='w').grid(
                     row=1, column=0, sticky='ew', padx=20, pady=(0, 7))

        self.proveedores_content = tk.Frame(self, bg='#f5f6f8')
        self.proveedores_content.grid(row=1, column=0, sticky='nsew', padx=14, pady=(4, 12))
        self.proveedores_content.grid_rowconfigure(1, weight=1)
        self.proveedores_content.grid_columnconfigure(0, weight=4, minsize=480)
        self.proveedores_content.grid_columnconfigure(1, weight=1, minsize=235)

        form = ctk.CTkFrame(self.proveedores_content, fg_color='#ffffff', corner_radius=12,
                            border_width=1, border_color='#e3e6ea')
        form.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        for col in range(6):
            form.grid_columnconfigure(col, weight=1, uniform='datos_proveedor')
        ctk.CTkLabel(form, text='Datos del proveedor', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, columnspan=6, sticky='w', padx=14, pady=(10, 6))
        self.empresa = self._campo_proveedor(form, 'Empresa', 1, 0, 2)
        self.rif = self._campo_proveedor(form, 'RIF / identificación', 1, 2)
        self.celular = self._campo_proveedor(form, 'Celular', 1, 3)
        self.direccion = self._campo_proveedor(form, 'Dirección', 1, 4, 2)
        self.correo = self._campo_proveedor(form, 'Correo electrónico', 2, 0, 3, pady=(8, 12))
        ctk.CTkButton(form, text='Registrar proveedor', command=self.registrar_proveedor,
                      height=34, corner_radius=8, fg_color='#8f070c', hover_color='#6f0509',
                      font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=2, column=3, columnspan=2, sticky='ew', padx=6, pady=(8, 12))
        ctk.CTkButton(form, text='Limpiar', command=self.limpiar_campos,
                      height=34, corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6',
                      text_color='#20242a', font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=2, column=5, sticky='ew', padx=(6, 14), pady=(8, 12))

        lista = ctk.CTkFrame(self.proveedores_content, fg_color='#ffffff', corner_radius=12,
                             border_width=1, border_color='#e3e6ea')
        lista.grid(row=1, column=0, sticky='nsew', padx=(0, 10))
        lista.grid_rowconfigure(2, weight=1)
        lista.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lista, text='Lista de proveedores', fg_color='transparent', bg_color='#ffffff', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, sticky='w', padx=14, pady=(10, 5))
        self.busqueda = ctk.CTkEntry(lista, placeholder_text='Buscar empresa, RIF, celular, dirección o correo',
                                     height=34, corner_radius=8, border_color='#e3e6ea', fg_color='#f7f8fa',
                                     text_color='#20242a', placeholder_text_color='#68707c',
                                     font=ctk.CTkFont(family='Poppins', size=9))
        self.busqueda.grid(row=1, column=0, sticky='ew', padx=14, pady=(0, 10))
        self.busqueda.bind('<KeyRelease>', self.filtrar_proveedores)

        tabla_frame = tk.Frame(lista, bg='#ffffff')
        tabla_frame.grid(row=2, column=0, sticky='nsew', padx=12, pady=(0, 12))
        tabla_frame.grid_rowconfigure(0, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)
        style = ttk.Style()
        style.configure('Proveedores.Treeview', background='#ffffff', fieldbackground='#ffffff',
                        foreground='#20242a', rowheight=27, borderwidth=0, font=('Poppins', 9))
        style.configure('Proveedores.Treeview.Heading', background='#f0f1f3', foreground='#20242a',
                        font=('Poppins', 9, 'bold'), relief='flat')
        style.map('Proveedores.Treeview', background=[('selected', '#f6dede')],
                  foreground=[('selected', '#20242a')])
        columnas = ('ID', 'Empresa', 'RIF', 'Celular', 'Direccion', 'Correo')
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show='headings', style='Proveedores.Treeview')
        anchos = {'ID':50, 'Empresa':160, 'RIF':115, 'Celular':115, 'Direccion':200, 'Correo':190}
        titulos = {'ID':'ID', 'Empresa':'Empresa', 'RIF':'RIF', 'Celular':'Celular', 'Direccion':'Dirección', 'Correo':'Correo'}
        for col in columnas:
            self.tree.heading(col, text=titulos[col])
            self.tree.column(col, width=anchos[col], anchor='w' if col in ('Empresa','Direccion','Correo') else 'center',
                             stretch=col != 'ID')
        sy = ttk.Scrollbar(tabla_frame, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(tabla_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.modificar_proveedor)

        resumen = ctk.CTkFrame(self.proveedores_content, fg_color='#ffffff', corner_radius=12,
                               border_width=1, border_color='#e3e6ea')
        resumen.grid(row=1, column=1, sticky='nsew')
        resumen.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(resumen, text='Resumen', fg_color='transparent', bg_color='#ffffff', text_color='#20242a',
                     font=ctk.CTkFont(family='Poppins', size=11, weight='bold')).grid(
                         row=0, column=0, sticky='w', padx=16, pady=(14, 8))
        self.stats_label = tk.Label(resumen, text='Total de proveedores: 0', bg='#ffffff',
                                    fg='#8f070c', font=('Poppins', 13, 'bold'), anchor='w')
        self.stats_label.grid(row=1, column=0, sticky='ew', padx=16, pady=(4, 16))
        tk.Label(resumen, text='Selecciona un proveedor para editar sus datos o haz doble clic en la tabla.',
                 bg='#ffffff', fg='#68707c', font=('Poppins', 8), justify='left', wraplength=190,
                 anchor='w').grid(row=2, column=0, sticky='ew', padx=16, pady=(0, 18))
        ctk.CTkButton(resumen, text='Modificar seleccionado', command=self.modificar_proveedor,
                      height=34, corner_radius=8, fg_color='#8f070c', hover_color='#6f0509',
                      font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=3, column=0, sticky='ew', padx=16, pady=(0, 8))
        ctk.CTkButton(resumen, text='Actualizar lista', command=self.cargar_registros,
                      height=34, corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6',
                      text_color='#20242a', font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=4, column=0, sticky='ew', padx=16, pady=(0, 8))
        ctk.CTkButton(resumen, text='Limpiar campos', command=self.limpiar_campos,
                      height=34, corner_radius=8, fg_color='#eef0f2', hover_color='#dfe2e6',
                      text_color='#20242a', font=ctk.CTkFont(family='Poppins', size=9, weight='bold')).grid(
                          row=5, column=0, sticky='ew', padx=16, pady=(0, 16))

    def _campo_proveedor(self, parent, placeholder, row, column, span=1, pady=(0, 6)):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=34, corner_radius=8,
                             border_color='#e3e6ea', fg_color='#ffffff',
                             text_color='#20242a', placeholder_text_color='#68707c',
                             font=ctk.CTkFont(family='Poppins', size=9))
        entry.grid(row=row, column=column, columnspan=span, sticky='ew',
                   padx=(14 if column == 0 else 6, 14 if column + span == 6 else 6), pady=pady)
        return entry

    def validar_campos(self):
        """Validar que todos los campos estén llenos"""
        if not all([self.empresa.get().strip(), 
                   self.rif.get().strip(), 
                   self.celular.get().strip(), 
                   self.direccion.get().strip(), 
                   self.correo.get().strip()]):
            messagebox.showerror("❌ Error", "Todos los campos son requeridos")
            return False
        
        # Validar formato de correo básico
        correo = self.correo.get().strip()
        if '@' not in correo or '.' not in correo:
            messagebox.showerror("❌ Error", "El formato del correo no es válido")
            return False
            
        return True

    def registrar_proveedor(self):
        """Registrar un nuevo proveedor"""
        if not self.validar_campos():
            return
        
        empresa = self.empresa.get().strip()
        rif = self.rif.get().strip()
        celular = self.celular.get().strip()
        direccion = self.direccion.get().strip()
        correo = self.correo.get().strip()

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Verificar si el RIF ya existe
            cursor.execute("SELECT id FROM proveedores WHERE rif = ?", (rif,))
            if cursor.fetchone():
                messagebox.showerror("❌ Error", "Ya existe un proveedor con este RIF")
                conn.close()
                return
            
            cursor.execute("""INSERT INTO proveedores (empresa, rif, celular, direccion, correo) 
                            VALUES (?,?,?,?,?)""", 
                          (empresa, rif, celular, direccion, correo))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✅ Éxito", "Proveedor registrado correctamente")
            self.limpiar_treeview()
            self.limpiar_campos()
            self.cargar_registros()

        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"No se pudo registrar el proveedor: {e}")

    def buscar_proveedor(self):
        """Buscar proveedor por empresa o RIF"""
        termino_busqueda = self.empresa.get().strip() or self.rif.get().strip()
        
        if not termino_busqueda:
            messagebox.showwarning("⚠️ Advertencia", "Ingrese el nombre de la empresa o RIF para buscar")
            return
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM proveedores 
                            WHERE empresa LIKE ? OR rif LIKE ?""", 
                          (f"%{termino_busqueda}%", f"%{termino_busqueda}%"))
            resultados = cursor.fetchall()
            conn.close()
            
            # Limpiar y mostrar resultados
            self.limpiar_treeview()
            
            if resultados:
                for row in resultados:
                    self.tree.insert("", "end", values=row)
                self.stats_label.config(text=f"Resultados encontrados: {len(resultados)}")
                messagebox.showinfo("🔍 Búsqueda", f"Se encontraron {len(resultados)} proveedor(es)")
            else:
                messagebox.showinfo("🔍 Búsqueda", "No se encontraron proveedores con ese criterio")
                self.cargar_registros()  # Recargar todos si no hay resultados
                
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error en la búsqueda: {e}")

    def cargar_registros(self):
        """Cargar todos los registros en el Treeview"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM proveedores ORDER BY empresa")
            rows = cursor.fetchall()
            
            for row in rows:
                self.tree.insert("", "end", values=row)
            
            # Actualizar estadísticas
            self.stats_label.config(text=f"Total de proveedores: {len(rows)}")
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los registros: {e}")

    def limpiar_treeview(self):
        """Limpiar todos los elementos del Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def limpiar_campos(self):
        """Limpiar todos los campos del formulario"""
        self.empresa.delete(0, 'end')
        self.rif.delete(0, 'end')
        self.celular.delete(0, 'end')
        self.direccion.delete(0, 'end')
        self.correo.delete(0, 'end')

    def on_select(self, event):
        """Manejar selección en el Treeview"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            
            # Llenar campos con los datos seleccionados
            self.limpiar_campos()
            if len(values) >= 6:
                self.empresa.insert(0, values[1])
                self.rif.insert(0, values[2])
                self.celular.insert(0, values[3])
                self.direccion.insert(0, values[4])
                self.correo.insert(0, values[5])

    def modificar_proveedor(self, event=None):
        """Modificar un proveedor existente"""
        if not self.tree.selection():
            messagebox.showerror("❌ Error", "Por favor seleccione un proveedor para modificar")
            return
        
        item = self.tree.selection()[0]
        id_proveedor = self.tree.item(item, "values")[0]
        values = self.tree.item(item, "values")

        # Crear ventana modal moderna para modificar
        top_modificar = tk.Toplevel(self)
        top_modificar.title("✏️ Modificar Proveedor")
        top_modificar.geometry("500x600+400+50")
        top_modificar.configure(bg=estilos.COLORS['white'])
        top_modificar.resizable(False, False)
        top_modificar.grab_set()
        top_modificar.focus_set()
        top_modificar.lift()

        # Título
        title_label = tk.Label(top_modificar, text="✏️ Modificar Datos del Proveedor", 
                              font=('Poppins', 16, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=20)

        # Frame principal
        main_frame = tk.Frame(top_modificar, bg=estilos.COLORS['white'])
        main_frame.pack(fill='both', expand=True, padx=30, pady=10)

        # Campos de entrada con valores actuales
        tk.Label(main_frame, text="🏢 Empresa:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=20)
        empresa_nuevo = tk.Entry(main_frame, font=('Poppins', 12), relief='solid', bd=1)
        empresa_nuevo.insert(0, values[1])
        empresa_nuevo.place(x=20, y=50, width=400, height=35)

        tk.Label(main_frame, text="🆔 RIF:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=100)
        rif_nuevo = tk.Entry(main_frame, font=('Poppins', 12), relief='solid', bd=1)
        rif_nuevo.insert(0, values[2])
        rif_nuevo.place(x=20, y=130, width=400, height=35)

        tk.Label(main_frame, text="📱 Celular:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=180)
        celular_nuevo = tk.Entry(main_frame, font=('Poppins', 12), relief='solid', bd=1)
        celular_nuevo.insert(0, values[3])
        celular_nuevo.place(x=20, y=210, width=400, height=35)

        tk.Label(main_frame, text="🏠 Dirección:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=260)
        direccion_nuevo = tk.Entry(main_frame, font=('Poppins', 12), relief='solid', bd=1)
        direccion_nuevo.insert(0, values[4])
        direccion_nuevo.place(x=20, y=290, width=400, height=35)

        tk.Label(main_frame, text="📧 Correo:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=340)
        correo_nuevo = tk.Entry(main_frame, font=('Poppins', 12), relief='solid', bd=1)
        correo_nuevo.insert(0, values[5])
        correo_nuevo.place(x=20, y=370, width=400, height=35)

        def guardar_modificado():
            """Guardar los cambios del proveedor"""
            nueva_empresa = empresa_nuevo.get().strip()
            nuevo_rif = rif_nuevo.get().strip()
            nuevo_celular = celular_nuevo.get().strip()
            nueva_direccion = direccion_nuevo.get().strip()
            nuevo_correo = correo_nuevo.get().strip()

            # Validaciones
            if not all([nueva_empresa, nuevo_rif, nuevo_celular, nueva_direccion, nuevo_correo]):
                messagebox.showerror("❌ Error", "Todos los campos son requeridos")
                return

            if '@' not in nuevo_correo or '.' not in nuevo_correo:
                messagebox.showerror("❌ Error", "El formato del correo no es válido")
                return

            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                
                # Verificar si el nuevo RIF ya existe en otro proveedor
                if nuevo_rif != values[2]:  # Si cambió el RIF
                    cursor.execute("SELECT id FROM proveedores WHERE rif = ? AND id != ?", 
                                 (nuevo_rif, id_proveedor))
                    if cursor.fetchone():
                        messagebox.showerror("❌ Error", "Ya existe otro proveedor con este RIF")
                        conn.close()
                        return
                
                cursor.execute("""UPDATE proveedores SET empresa = ?, rif = ?, celular = ?, 
                                direccion = ?, correo = ? WHERE id = ?""", 
                             (nueva_empresa, nuevo_rif, nuevo_celular, 
                              nueva_direccion, nuevo_correo, id_proveedor))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("✅ Éxito", "Proveedor modificado correctamente")
                self.limpiar_treeview()
                self.cargar_registros()
                top_modificar.destroy()

            except sqlite3.Error as e:
                messagebox.showerror("❌ Error", f"No se pudo modificar el proveedor: {e}")

        def eliminar_proveedor():
            """Eliminar el proveedor seleccionado"""
            respuesta = messagebox.askyesno("⚠️ Confirmar Eliminación", 
                                          f"¿Estás seguro de que quieres eliminar al proveedor '{values[1]}'?\n\nEsta acción no se puede deshacer.")
            
            if respuesta:
                try:
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM proveedores WHERE id = ?", (id_proveedor,))
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("✅ Éxito", "Proveedor eliminado correctamente")
                    self.limpiar_treeview()
                    self.limpiar_campos()
                    self.cargar_registros()
                    top_modificar.destroy()
                    
                except sqlite3.Error as e:
                    messagebox.showerror("❌ Error", f"No se pudo eliminar el proveedor: {e}")

        # Frame para botones
        btn_frame = tk.Frame(main_frame, bg=estilos.COLORS['white'])
        btn_frame.place(x=20, y=440, width=400, height=80)

        # Botones modernos
        btn_guardar = ctk.CTkButton(btn_frame, text='💾 Guardar Cambios', 
                                   font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                   command=guardar_modificado, width=180, height=40,
                                   fg_color=estilos.COLORS['success'],
                                   hover_color="#8f070c")
        btn_guardar.pack(side='left', padx=5, pady=10)

        btn_eliminar = ctk.CTkButton(btn_frame, text='🗑️ Eliminar', 
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    command=eliminar_proveedor, width=100, height=40,
                                    fg_color=estilos.COLORS['danger'],
                                    hover_color="#c21f28")
        btn_eliminar.pack(side='left', padx=5, pady=10)

        btn_cancelar = ctk.CTkButton(btn_frame, text='❌ Cancelar', 
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    command=top_modificar.destroy, width=100, height=40,
                                    fg_color=estilos.COLORS['secondary'],
                                    hover_color="#5a4b48")
        btn_cancelar.pack(side='right', padx=5, pady=10)



