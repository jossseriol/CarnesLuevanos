import calendar
import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import customtkinter as ctk

from modulos.utils.estilos_modernos import estilos


DB = 'database.db'
BG = '#f5f3f2'
CARD = '#ffffff'
TEXT = '#241719'
MUTED = '#74676a'
WINE = '#8f070c'
WINE_DARK = '#5a0508'
GOLD = '#d7b56d'
BORDER = '#e7ddda'
GREEN = '#23834a'


def conectar():
    return sqlite3.connect(DB)


def asegurar_tablas_empacadora():
    with conectar() as conn:
        conn.executescript(
            '''
            CREATE TABLE IF NOT EXISTS empacadora_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL, cliente TEXT NOT NULL, folio TEXT NOT NULL,
                monto REAL NOT NULL DEFAULT 0, lote INTEGER NOT NULL,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS empacadora_lotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lote INTEGER NOT NULL, periodo_inicio TEXT NOT NULL, periodo_fin TEXT NOT NULL,
                canal TEXT, fecha_introduccion TEXT NOT NULL, proveedor TEXT, producto TEXT NOT NULL,
                peso REAL DEFAULT 0, precio REAL DEFAULT 0, monto REAL DEFAULT 0,
                observaciones TEXT, destino TEXT, origen TEXT, folio_venta TEXT,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS empacadora_clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL, telefono TEXT, direccion TEXT, notas TEXT,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS empacadora_cobranza (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lote INTEGER NOT NULL, periodo_inicio TEXT NOT NULL, periodo_fin TEXT NOT NULL,
                fecha_compra TEXT NOT NULL, cliente TEXT NOT NULL, folio TEXT NOT NULL,
                monto REAL DEFAULT 0, abono REAL DEFAULT 0, saldo REAL DEFAULT 0,
                status TEXT DEFAULT 'Pendiente', fecha_pago TEXT, usuario_recibe TEXT,
                nota TEXT, recordatorio TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );
            '''
        )


def fecha_valida(texto):
    texto = (texto or '').strip()
    for formato in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError('La fecha debe escribirse como AAAA-MM-DD.')


def datos_periodo(texto_fecha):
    fecha = fecha_valida(texto_fecha)
    ultimo = calendar.monthrange(fecha.year, fecha.month)[1]
    limites = ((1, 7), (8, 14), (15, 21), (22, ultimo))
    for indice, (inicio, fin) in enumerate(limites, 1):
        if inicio <= fecha.day <= fin:
            return indice, date(fecha.year, fecha.month, inicio).isoformat(), date(fecha.year, fecha.month, fin).isoformat()
    return 4, date(fecha.year, fecha.month, 22).isoformat(), date(fecha.year, fecha.month, ultimo).isoformat()


class ModuloEmpacadoraBase(tk.Frame):
    tabla = ''
    titulo = ''
    subtitulo = ''
    campos = ()
    requeridos = ()
    numericos = ()

    def __init__(self, padre):
        super().__init__(padre, bg=BG)
        asegurar_tablas_empacadora()
        self.edit_id = None
        self.vars = {}
        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        cab = tk.Frame(self, bg=BG, height=70)
        cab.pack(fill='x', padx=20, pady=(10, 0))
        cab.pack_propagate(False)
        tk.Label(cab, text=self.titulo, bg=BG, fg=TEXT, font=('Poppins', 18, 'bold'), anchor='w').pack(fill='x')
        tk.Label(cab, text=self.subtitulo, bg=BG, fg=MUTED, font=('Poppins', 9), anchor='w').pack(fill='x')

        self.form = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        self.form.pack(fill='x', padx=20, pady=(4, 10))
        columnas = min(4, max(1, len(self.campos)))
        for columna in range(columnas):
            self.form.grid_columnconfigure(columna, weight=1, uniform='campos')
        hoy = date.today().isoformat()
        for indice, (clave, etiqueta) in enumerate(self.campos):
            fila, columna = divmod(indice, columnas)
            celda = ctk.CTkFrame(self.form, fg_color='transparent')
            celda.grid(row=fila, column=columna, sticky='ew', padx=10, pady=(8, 3))
            ctk.CTkLabel(celda, text=etiqueta, text_color=MUTED,
                         font=ctk.CTkFont('Poppins', 9, 'bold')).pack(anchor='w')
            valor = hoy if clave.startswith('fecha') else ''
            var = tk.StringVar(value=valor)
            entrada = ctk.CTkEntry(celda, textvariable=var, height=32, corner_radius=7,
                                   fg_color='#ffffff', border_color='#d9d0ce', text_color=TEXT,
                                   font=ctk.CTkFont('Poppins', 10))
            entrada.pack(fill='x', pady=(2, 0))
            entrada.bind('<KeyRelease>', self._campo_modificado, add='+')
            self.vars[clave] = var

        acciones = ctk.CTkFrame(self.form, fg_color='transparent')
        acciones.grid(row=(len(self.campos) + columnas - 1) // columnas, column=0,
                       columnspan=columnas, sticky='ew', padx=10, pady=(8, 12))
        self.btn_guardar = ctk.CTkButton(acciones, text='Registrar', command=self.guardar,
                                         width=120, height=34, corner_radius=8,
                                         fg_color=WINE, hover_color=WINE_DARK,
                                         font=ctk.CTkFont('Poppins', 10, 'bold'))
        self.btn_guardar.pack(side='left')
        ctk.CTkButton(acciones, text='Limpiar', command=self.limpiar, width=92, height=34,
                      corner_radius=8, fg_color='#ece8e7', hover_color='#ded7d5',
                      text_color=TEXT).pack(side='left', padx=7)
        ctk.CTkButton(acciones, text='Eliminar', command=self.eliminar, width=92, height=34,
                      corner_radius=8, fg_color='#ffffff', hover_color='#fff0f0',
                      border_width=1, border_color='#e4b5b7', text_color=WINE).pack(side='left')
        self.buscar_var = tk.StringVar()
        buscar = ctk.CTkEntry(acciones, textvariable=self.buscar_var, placeholder_text='Buscar en registros...',
                              width=230, height=34, corner_radius=16, border_color='#d9d0ce')
        buscar.pack(side='right')
        buscar.bind('<KeyRelease>', lambda _e: self.cargar_datos())

        tabla_card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        tabla_card.pack(fill='both', expand=True, padx=20, pady=(0, 18))
        nombres = [clave for clave, _ in self.campos]
        self.tree = ttk.Treeview(tabla_card, columns=('id', *nombres), show='headings', style='Empacadora.Treeview')
        estilo = ttk.Style()
        estilo.configure('Empacadora.Treeview', font=('Poppins', 9), rowheight=29,
                          background='#ffffff', fieldbackground='#ffffff', foreground=TEXT)
        estilo.configure('Empacadora.Treeview.Heading', font=('Poppins', 9, 'bold'),
                          background='#f0eceb', foreground=TEXT)
        self.tree.heading('id', text='ID')
        self.tree.column('id', width=45, minwidth=40, anchor='center', stretch=False)
        for clave, etiqueta in self.campos:
            self.tree.heading(clave, text=etiqueta)
            ancho = 125 if clave not in ('observaciones', 'nota', 'direccion') else 190
            self.tree.column(clave, width=ancho, minwidth=80, anchor='w')
        sy = ttk.Scrollbar(tabla_card, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(tabla_card, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew', padx=(12, 0), pady=(12, 0))
        sy.grid(row=0, column=1, sticky='ns', pady=(12, 0))
        sx.grid(row=1, column=0, sticky='ew', padx=(12, 0), pady=(0, 12))
        tabla_card.grid_rowconfigure(0, weight=1)
        tabla_card.grid_columnconfigure(0, weight=1)
        self.tree.bind('<Double-1>', self._cargar_seleccion)

    def _campo_modificado(self, _event=None):
        pass

    def preparar(self, valores):
        return valores

    def guardar(self):
        try:
            valores = {clave: var.get().strip() for clave, var in self.vars.items()}
            for clave in self.requeridos:
                if not valores.get(clave):
                    raise ValueError(f'Falta capturar: {dict(self.campos).get(clave, clave)}.')
            for clave in self.numericos:
                valores[clave] = float(valores.get(clave) or 0)
            valores = self.preparar(valores)
            columnas = [clave for clave, _ in self.campos]
            with conectar() as conn:
                if self.edit_id:
                    sets = ', '.join(f'{col}=?' for col in columnas)
                    conn.execute(f'UPDATE {self.tabla} SET {sets} WHERE id=?',
                                 [valores.get(col, '') for col in columnas] + [self.edit_id])
                else:
                    marcas = ','.join('?' for _ in columnas)
                    conn.execute(f'INSERT INTO {self.tabla} ({",".join(columnas)}) VALUES ({marcas})',
                                 [valores.get(col, '') for col in columnas])
            self.limpiar()
            self.cargar_datos()
        except (ValueError, sqlite3.Error) as error:
            messagebox.showwarning('Revisa los datos', str(error), parent=self)

    def cargar_datos(self):
        if not hasattr(self, 'tree'):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        columnas = [clave for clave, _ in self.campos]
        filtro = self.buscar_var.get().strip()
        consulta = f'SELECT id,{",".join(columnas)} FROM {self.tabla}'
        parametros = []
        if filtro:
            consulta += ' WHERE ' + ' OR '.join(f'CAST({col} AS TEXT) LIKE ?' for col in columnas)
            parametros = [f'%{filtro}%'] * len(columnas)
        consulta += ' ORDER BY id DESC'
        try:
            with conectar() as conn:
                filas = conn.execute(consulta, parametros).fetchall()
            for fila in filas:
                self.tree.insert('', 'end', values=fila)
        except sqlite3.Error:
            pass

    cargar_registros = cargar_datos

    def _cargar_seleccion(self, _event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], 'values')
        self.edit_id = int(valores[0])
        for (clave, _), valor in zip(self.campos, valores[1:]):
            self.vars[clave].set(valor)
        self.btn_guardar.configure(text='Guardar cambios')

    def limpiar(self):
        self.edit_id = None
        for clave, var in self.vars.items():
            var.set(date.today().isoformat() if clave.startswith('fecha') else '')
        self.btn_guardar.configure(text='Registrar')

    def eliminar(self):
        seleccion = self.tree.selection()
        ident = self.edit_id or (int(self.tree.item(seleccion[0], 'values')[0]) if seleccion else None)
        if not ident:
            messagebox.showinfo('Selecciona un registro', 'Selecciona la fila que deseas eliminar.', parent=self)
            return
        if not messagebox.askyesno('Confirmar', '¿Eliminar el registro seleccionado?', parent=self):
            return
        with conectar() as conn:
            conn.execute(f'DELETE FROM {self.tabla} WHERE id=?', (ident,))
        self.limpiar()
        self.cargar_datos()


class EmpacadoraVentas(ModuloEmpacadoraBase):
    tabla = 'empacadora_ventas'
    titulo = 'Ventas de Empacadora'
    subtitulo = 'Registra fecha, cliente, folio y monto; el lote mensual se asigna automáticamente.'
    campos = (('fecha', 'Fecha'), ('cliente', 'Cliente'), ('folio', 'Folio'), ('monto', 'Monto'), ('lote', 'Lote'))
    requeridos = ('fecha', 'cliente', 'folio')
    numericos = ('monto',)

    def preparar(self, valores):
        lote, _inicio, _fin = datos_periodo(valores['fecha'])
        valores['fecha'] = fecha_valida(valores['fecha']).isoformat()
        valores['lote'] = lote
        return valores

    def _campo_modificado(self, _event=None):
        try:
            lote, _a, _b = datos_periodo(self.vars['fecha'].get())
            self.vars['lote'].set(str(lote))
        except ValueError:
            pass


class EmpacadoraLotes(ModuloEmpacadoraBase):
    tabla = 'empacadora_lotes'
    titulo = 'Lotes y compra de producto'
    subtitulo = 'Cada mes se divide en cuatro lotes: 1–7, 8–14, 15–21 y 22–fin de mes.'
    campos = (
        ('lote', 'Lote'), ('periodo_inicio', 'Inicio'), ('periodo_fin', 'Fin'), ('canal', 'Canal'),
        ('fecha_introduccion', 'Fecha introducción'), ('proveedor', 'Proveedor'), ('producto', 'Producto'),
        ('peso', 'Peso'), ('precio', 'Precio'), ('monto', 'Monto'), ('observaciones', 'Observaciones'),
        ('destino', 'Destino'), ('origen', 'Origen'), ('folio_venta', 'Folio de venta'),
    )
    requeridos = ('fecha_introduccion', 'producto')
    numericos = ('peso', 'precio', 'monto')

    def preparar(self, valores):
        lote, inicio, fin = datos_periodo(valores['fecha_introduccion'])
        valores.update(lote=lote, periodo_inicio=inicio, periodo_fin=fin)
        valores['fecha_introduccion'] = fecha_valida(valores['fecha_introduccion']).isoformat()
        valores['monto'] = valores['peso'] * valores['precio']
        return valores

    def _campo_modificado(self, _event=None):
        try:
            lote, inicio, fin = datos_periodo(self.vars['fecha_introduccion'].get())
            self.vars['lote'].set(str(lote)); self.vars['periodo_inicio'].set(inicio); self.vars['periodo_fin'].set(fin)
        except ValueError:
            pass
        try:
            monto = float(self.vars['peso'].get() or 0) * float(self.vars['precio'].get() or 0)
            self.vars['monto'].set(f'{monto:.2f}')
        except ValueError:
            pass


class EmpacadoraClientes(ModuloEmpacadoraBase):
    tabla = 'empacadora_clientes'
    titulo = 'Clientes de Empacadora'
    subtitulo = 'Directorio independiente de clientes de la unidad Empacadora.'
    campos = (('nombre', 'Nombre'), ('telefono', 'Teléfono'), ('direccion', 'Dirección'), ('notas', 'Notas'))
    requeridos = ('nombre',)


class EmpacadoraCobranza(ModuloEmpacadoraBase):
    tabla = 'empacadora_cobranza'
    titulo = 'Cobranza de Empacadora'
    subtitulo = 'Controla compras, abonos, saldos, responsable de cobro y recordatorios.'
    campos = (
        ('lote', 'Lote'), ('periodo_inicio', 'Inicio'), ('periodo_fin', 'Fin'), ('fecha_compra', 'Fecha compra'),
        ('cliente', 'Cliente'), ('folio', 'Folio'), ('monto', 'Monto'), ('abono', 'Abono'),
        ('saldo', 'Saldo'), ('status', 'Estado'), ('fecha_pago', 'Fecha de pago'),
        ('usuario_recibe', 'Usuario que recibe'), ('nota', 'Nota / observación'), ('recordatorio', 'Recordatorio'),
    )
    requeridos = ('fecha_compra', 'cliente', 'folio')
    numericos = ('monto', 'abono', 'saldo')

    def preparar(self, valores):
        lote, inicio, fin = datos_periodo(valores['fecha_compra'])
        valores.update(lote=lote, periodo_inicio=inicio, periodo_fin=fin)
        valores['fecha_compra'] = fecha_valida(valores['fecha_compra']).isoformat()
        valores['saldo'] = max(0, valores['monto'] - valores['abono'])
        valores['status'] = 'Pagado' if valores['saldo'] <= 0 else ('Abonado' if valores['abono'] > 0 else 'Pendiente')
        if valores['status'] == 'Pagado' and not valores.get('fecha_pago'):
            valores['fecha_pago'] = date.today().isoformat()
        if not valores.get('recordatorio') and valores['saldo'] > 0:
            valores['recordatorio'] = (fecha_valida(valores['fecha_compra']) + timedelta(days=30)).isoformat()
        return valores

    def _campo_modificado(self, _event=None):
        try:
            lote, inicio, fin = datos_periodo(self.vars['fecha_compra'].get())
            self.vars['lote'].set(str(lote)); self.vars['periodo_inicio'].set(inicio); self.vars['periodo_fin'].set(fin)
        except ValueError:
            pass
        try:
            saldo = max(0, float(self.vars['monto'].get() or 0) - float(self.vars['abono'].get() or 0))
            self.vars['saldo'].set(f'{saldo:.2f}')
            self.vars['status'].set('Pagado' if saldo <= 0 else ('Abonado' if float(self.vars['abono'].get() or 0) > 0 else 'Pendiente'))
        except ValueError:
            pass


class EmpacadoraInicio(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre, bg=BG)
        asegurar_tablas_empacadora()
        self.cards = []
        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        hero = ctk.CTkFrame(self, height=128, corner_radius=14, fg_color=WINE_DARK)
        hero.pack(fill='x', padx=20, pady=(18, 14)); hero.pack_propagate(False)
        ctk.CTkLabel(hero, text='Panel de control · Empacadora', text_color='white',
                     font=ctk.CTkFont('Poppins', 22, 'bold')).place(x=24, y=22)
        ctk.CTkLabel(hero, text='Ventas, lotes, producto y cobranza en una operación independiente.',
                     text_color='#ead9d7', font=ctk.CTkFont('Poppins', 10)).place(x=26, y=62)
        ctk.CTkLabel(hero, text='4 LOTES POR MES', text_color=GOLD,
                     font=ctk.CTkFont('Poppins', 13, 'bold')).place(relx=.98, y=38, anchor='e')
        self.card_area = tk.Frame(self, bg=BG, height=105)
        self.card_area.pack(fill='x', padx=20); self.card_area.pack_propagate(False)
        panel = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        panel.pack(fill='both', expand=True, padx=20, pady=(14, 20))
        ctk.CTkLabel(panel, text='Actividad reciente', text_color=TEXT,
                     font=ctk.CTkFont('Poppins', 14, 'bold')).pack(anchor='w', padx=18, pady=(14, 8))
        self.tree = ttk.Treeview(panel, columns=('tipo', 'fecha', 'cliente', 'folio', 'monto', 'lote'),
                                 show='headings', style='Empacadora.Treeview')
        for col, txt, ancho in (('tipo','Movimiento',110),('fecha','Fecha',100),('cliente','Cliente',190),
                                ('folio','Folio',110),('monto','Monto',120),('lote','Lote',70)):
            self.tree.heading(col, text=txt); self.tree.column(col, width=ancho, anchor='w')
        self.tree.pack(fill='both', expand=True, padx=18, pady=(0, 18))

    def cargar_datos(self):
        with conectar() as conn:
            ventas = conn.execute('SELECT COALESCE(SUM(monto),0),COUNT(*) FROM empacadora_ventas').fetchone()
            lotes = conn.execute('SELECT COUNT(*) FROM empacadora_lotes').fetchone()[0]
            clientes = conn.execute('SELECT COUNT(*) FROM empacadora_clientes').fetchone()[0]
            saldo = conn.execute('SELECT COALESCE(SUM(saldo),0) FROM empacadora_cobranza').fetchone()[0]
            recientes = conn.execute('SELECT "Venta",fecha,cliente,folio,monto,lote FROM empacadora_ventas ORDER BY id DESC LIMIT 8').fetchall()
        for card in self.cards: card.destroy()
        self.cards.clear()
        datos = (('Ventas acumuladas', f'${ventas[0]:,.2f}', WINE), ('Operaciones', str(ventas[1]), '#c23a40'),
                 ('Compras en lotes', str(lotes), GOLD), ('Clientes', str(clientes), '#3b8d72'),
                 ('Saldo por cobrar', f'${saldo:,.2f}', '#d17b32'))
        for i, (titulo, valor, color) in enumerate(datos):
            card = ctk.CTkFrame(self.card_area, fg_color=CARD, corner_radius=11, border_width=1, border_color=BORDER)
            card.place(relx=i / 5, rely=0, relwidth=.19, relheight=1)
            ctk.CTkLabel(card, text=titulo, text_color=MUTED, font=ctk.CTkFont('Poppins', 9)).place(x=14, y=16)
            ctk.CTkLabel(card, text=valor, text_color=color, font=ctk.CTkFont('Poppins', 16, 'bold')).place(x=14, y=43)
            self.cards.append(card)
        for item in self.tree.get_children(): self.tree.delete(item)
        for fila in recientes: self.tree.insert('', 'end', values=fila)

    cargar_registros = cargar_datos
