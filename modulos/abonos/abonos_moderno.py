import datetime
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from modulos.utils.estilos_modernos import estilos


class AbonosModerno(tk.Frame):
    db_name = "database.db"
    COLORS = estilos.COLORS

    def __init__(self, padre):
        super().__init__(padre, bg=self.COLORS.get('bg_primary', '#f5f5f5'))
        self.venta_actual = None
        self.setup_styles()
        self.asegurar_tablas()
        self.crear_interfaz()
        self.cargar_ventas_pendientes()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Abonos.Treeview', font=('Poppins', 10), rowheight=28)
        style.configure('Abonos.Treeview.Heading', font=('Poppins', 10, 'bold'))

    def crear_interfaz(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg=self.COLORS.get('primary', '#7a1f2b'))
        header.grid(row=0, column=0, sticky='ew')
        header.grid_columnconfigure(0, weight=1)
        tk.Label(
            header,
            text='Abonos',
            bg=self.COLORS.get('primary', '#7a1f2b'),
            fg=self.COLORS.get('white', '#ffffff'),
            font=('Poppins', 16, 'bold'),
            anchor='w',
        ).grid(row=0, column=0, sticky='ew', padx=18, pady=10)

        body = tk.Frame(self, bg=self.COLORS.get('bg_primary', '#f5f5f5'))
        body.grid(row=1, column=0, sticky='nsew', padx=16, pady=14)
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=1)

        form = tk.Frame(body, bg=self.COLORS.get('white', '#ffffff'), highlightthickness=1, highlightbackground='#e5e7eb')
        form.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        for col in range(6):
            form.grid_columnconfigure(col, weight=1)

        tk.Label(form, text='Registrar abono', bg=self.COLORS.get('white', '#ffffff'),
                 fg=self.COLORS.get('primary', '#7a1f2b'), font=('Poppins', 12, 'bold'),
                 anchor='w').grid(row=0, column=0, columnspan=6, sticky='ew', padx=14, pady=(12, 8))

        self.crear_label(form, 'Folio', 1, 0)
        self.entry_folio = ttk.Entry(form, font=('Poppins', 11))
        self.entry_folio.grid(row=2, column=0, columnspan=2, sticky='ew', padx=(14, 8), pady=(0, 12), ipady=5)
        self.entry_folio.bind('<Return>', lambda _event: self.buscar_por_folio())

        self.crear_label(form, 'Cantidad abonada', 1, 2)
        self.entry_monto = ttk.Entry(form, font=('Poppins', 11))
        self.entry_monto.grid(row=2, column=2, sticky='ew', padx=8, pady=(0, 12), ipady=5)
        self.entry_monto.bind('<Return>', lambda _event: self.registrar_abono())

        self.label_saldo = tk.Label(form, text='Resta: $0.00', bg=self.COLORS.get('white', '#ffffff'),
                                    fg=self.COLORS.get('warning', '#b7791f'), font=('Poppins', 12, 'bold'),
                                    anchor='w')
        self.label_saldo.grid(row=2, column=3, sticky='ew', padx=8, pady=(0, 12))

        btn_buscar = tk.Button(form, text='Buscar', command=self.buscar_por_folio,
                               bg=self.COLORS.get('secondary', '#3b82f6'), fg=self.COLORS.get('white', '#ffffff'),
                               font=('Poppins', 10, 'bold'), relief='flat', cursor='hand2', bd=0)
        btn_buscar.grid(row=2, column=4, sticky='ew', padx=8, pady=(0, 12), ipady=7)

        btn_abonar = tk.Button(form, text='Registrar abono', command=self.registrar_abono,
                               bg=self.COLORS.get('success', '#16a34a'), fg=self.COLORS.get('white', '#ffffff'),
                               font=('Poppins', 10, 'bold'), relief='flat', cursor='hand2', bd=0)
        btn_abonar.grid(row=2, column=5, sticky='ew', padx=(8, 14), pady=(0, 12), ipady=7)

        lista_frame = tk.Frame(body, bg=self.COLORS.get('white', '#ffffff'), highlightthickness=1, highlightbackground='#e5e7eb')
        lista_frame.grid(row=1, column=0, sticky='nsew')
        lista_frame.grid_rowconfigure(1, weight=1)
        lista_frame.grid_columnconfigure(0, weight=1)

        top_lista = tk.Frame(lista_frame, bg=self.COLORS.get('white', '#ffffff'))
        top_lista.grid(row=0, column=0, sticky='ew', padx=14, pady=(12, 8))
        top_lista.grid_columnconfigure(0, weight=1)
        tk.Label(top_lista, text='Cuentas pendientes — Buscar por cliente, folio o fecha', bg=self.COLORS.get('white', '#ffffff'),
                 fg=self.COLORS.get('primary', '#7a1f2b'), font=('Poppins', 12, 'bold'),
                 anchor='w').grid(row=0, column=0, sticky='ew')
        self.entry_busqueda = ttk.Entry(top_lista, font=('Poppins', 10))
        self.entry_busqueda.grid(row=0, column=1, padx=(12, 6), ipady=4, sticky='ew')
        self.entry_busqueda.insert(0, '')
        self.entry_busqueda.bind('<Return>', lambda _event: self.buscar_ventas())
        self.entry_busqueda.bind('<KeyRelease>', lambda _event: self.buscar_ventas())
        top_lista.grid_columnconfigure(1, weight=1)
        tk.Button(top_lista, text='Buscar', command=self.buscar_ventas,
                  bg=self.COLORS.get('secondary', '#3b82f6'), fg=self.COLORS.get('white', '#ffffff'),
                  font=('Poppins', 9, 'bold'), relief='flat', cursor='hand2', bd=0).grid(row=0, column=2, padx=(0, 6), ipadx=10, ipady=4)
        tk.Button(top_lista, text='Limpiar', command=self.limpiar_busqueda,
                  bg=self.COLORS.get('light', '#f3f4f6'), fg=self.COLORS.get('dark', '#111827'),
                  font=('Poppins', 9, 'bold'), relief='flat', cursor='hand2', bd=0).grid(row=0, column=3, padx=(0, 6), ipadx=10, ipady=4)
        tk.Button(top_lista, text='Actualizar', command=self.cargar_ventas_pendientes,
                  bg=self.COLORS.get('light', '#f3f4f6'), fg=self.COLORS.get('dark', '#111827'),
                  font=('Poppins', 9, 'bold'), relief='flat', cursor='hand2', bd=0).grid(row=0, column=4, padx=(0, 6), ipadx=10, ipady=4)
        tk.Button(top_lista, text='Historial de compras', command=self.mostrar_historial_compras_clientes,
                  bg=self.COLORS.get('primary', '#7a1f2b'), fg=self.COLORS.get('white', '#ffffff'),
                  font=('Poppins', 9, 'bold'), relief='flat', cursor='hand2', bd=0).grid(
                      row=0, column=5, padx=(0, 0), ipadx=10, ipady=4)

        table_frame = tk.Frame(lista_frame, bg=self.COLORS.get('white', '#ffffff'))
        table_frame.grid(row=1, column=0, sticky='nsew', padx=14, pady=(0, 14))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ('ID', 'Folio', 'Cliente', 'Total', 'Abonado', 'Resta', 'Estado', 'Fecha')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', style='Abonos.Treeview')
        widths = {
            'ID': 0, 'Folio': 130, 'Cliente': 240,
            'Total': 110, 'Abonado': 110, 'Resta': 110, 'Estado': 100, 'Fecha': 100,
        }
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor='center' if col != 'Cliente' else 'w', stretch=True)
        self.tree.column('ID', width=0, minwidth=0, stretch=False)

        sy = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')

        self.tree.bind('<<TreeviewSelect>>', lambda _event: self.cargar_seleccion())
        self.tree.bind('<Double-1>', lambda _event: self.abrir_historial_cliente())

    def crear_label(self, parent, texto, row, column):
        tk.Label(parent, text=texto, bg=self.COLORS.get('white', '#ffffff'),
                 fg=self.COLORS.get('primary', '#7a1f2b'), font=('Poppins', 9, 'bold'),
                 anchor='w').grid(row=row, column=column, sticky='ew', padx=14 if column == 0 else 8, pady=(0, 3))

    def conectar(self):
        return sqlite3.connect(self.db_name)

    def asegurar_tablas(self):
        conn = self.conectar()
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
        self.asegurar_columnas_ventas(c)
        c.execute("""CREATE TABLE IF NOT EXISTS abonos_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER,
            monto REAL DEFAULT 0,
            fecha TEXT,
            hora TEXT,
            nota TEXT
        )""")
        self.asegurar_columnas_abonos(c)
        conn.commit()
        conn.close()

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
        }
        for columna, definicion in extras.items():
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE ventas ADD COLUMN {columna} {definicion}")

    def asegurar_columnas_abonos(self, cursor):
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

    def cargar_ventas_pendientes(self, filtro=''):
        self.asegurar_tablas()
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.conectar()
        c = conn.cursor()
        c.execute("""
            SELECT
                rowid,
                COALESCE(folio, ''),
                COALESCE(cliente, 'Cliente General'),
                COALESCE(total, 0),
                COALESCE(monto_recibido, 0),
                COALESCE(saldo, 0),
                COALESCE(estado_pago, ''),
                COALESCE(fecha, '')
            FROM ventas
            WHERE (COALESCE(saldo, 0) > 0 OR LOWER(COALESCE(estado_pago, '')) = 'credito')
              AND (? = '' OR LOWER(COALESCE(cliente, '')) LIKE ?
                   OR LOWER(COALESCE(folio, '')) LIKE ? OR LOWER(COALESCE(fecha, '')) LIKE ?)
            ORDER BY rowid DESC
        """, (filtro, f'%{filtro.lower()}%', f'%{filtro.lower()}%', f'%{filtro.lower()}%'))
        rows = c.fetchall()
        conn.close()

        for venta_id, folio, cliente, total, abonado, saldo, estado, fecha in rows:
            folio_visible = folio or 'Sin folio'
            self.tree.insert('', 'end', values=(
                venta_id,
                folio_visible,
                cliente,
                self.moneda(total),
                self.moneda(abonado),
                self.moneda(saldo),
                estado or ('Credito' if saldo > 0 else 'Pagado'),
                fecha,
            ))

        if hasattr(self, 'resumen_pendientes'):
            total_saldo = sum(float(row[5] or 0) for row in rows)
            self.resumen_pendientes.config(
                text=f'Cuentas pendientes: {len(rows)}\nSaldo total: {self.moneda(total_saldo)}'
            )

        self.venta_actual = None
        self.label_saldo.config(text='Resta: $0.00')

    def buscar_ventas(self):
        self.cargar_ventas_pendientes(self.entry_busqueda.get().strip())

    def limpiar_busqueda(self):
        self.entry_busqueda.delete(0, tk.END)
        self.cargar_ventas_pendientes()

    def cargar_seleccion(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], 'values')
        if not valores:
            return
        self.venta_actual = int(valores[0])
        self.entry_folio.delete(0, tk.END)
        self.entry_folio.insert(0, valores[1])
        self.label_saldo.config(text=f'Resta: {valores[5]}')
        self.entry_monto.focus_set()

    def buscar_por_folio(self):
        folio = self.entry_folio.get().strip()
        if not folio:
            messagebox.showwarning('Folio requerido', 'Escribe el folio de la venta.')
            return

        conn = self.conectar()
        c = conn.cursor()
        c.execute("""
            SELECT rowid, COALESCE(saldo, 0)
            FROM ventas
            WHERE folio = ?
            ORDER BY rowid DESC
            LIMIT 1
        """, (folio,))
        row = c.fetchone()
        conn.close()

        if not row:
            messagebox.showwarning('No encontrado', 'No encontré una venta con ese folio.')
            return

        self.venta_actual = row[0]
        self.label_saldo.config(text=f'Resta: {self.moneda(row[1])}')
        for item in self.tree.get_children():
            if str(self.tree.item(item, 'values')[0]) == str(self.venta_actual):
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                break

    def registrar_abono(self):
        if not self.venta_actual:
            self.buscar_por_folio()
            if not self.venta_actual:
                return

        try:
            monto = self.parse_monto(self.entry_monto.get())
        except ValueError:
            messagebox.showerror('Monto invalido', 'Escribe una cantidad valida para el abono.')
            return

        if monto <= 0:
            messagebox.showerror('Monto invalido', 'El abono debe ser mayor a 0.')
            return

        conn = self.conectar()
        c = conn.cursor()
        c.execute("""
            SELECT COALESCE(total, 0), COALESCE(monto_recibido, 0), COALESCE(saldo, 0),
                   COALESCE(cliente, 'Cliente General'), COALESCE(folio, '')
            FROM ventas
            WHERE rowid = ?
        """, (self.venta_actual,))
        venta = c.fetchone()
        if not venta:
            conn.close()
            messagebox.showerror('Error', 'No se encontro la venta seleccionada.')
            return

        total, abonado_actual, saldo_actual, cliente, folio = venta
        saldo_base = saldo_actual if saldo_actual > 0 else max(total - abonado_actual, 0)
        if saldo_base <= 0:
            conn.close()
            messagebox.showinfo('Sin saldo', 'Esta venta ya esta pagada.')
            self.cargar_ventas_pendientes()
            return

        monto_aplicado = min(monto, saldo_base)
        nuevo_abonado = abonado_actual + monto_aplicado
        nuevo_saldo = max(total - nuevo_abonado, 0)
        nuevo_estado = 'Pagado' if nuevo_saldo <= 0.009 else 'Credito'
        fecha = datetime.datetime.now().strftime('%d/%m/%Y')
        hora = datetime.datetime.now().strftime('%H:%M:%S')
        folio_visible = folio or 'Sin folio'

        nota_abono = f'Liquidacion de folio {folio_visible} - Pagado' if nuevo_estado == 'Pagado' else f'Abono a folio {folio_visible}'
        c.execute("""
            INSERT INTO abonos_ventas (venta_id, monto, fecha, hora, nota)
            VALUES (?, ?, ?, ?, ?)
        """, (self.venta_actual, monto_aplicado, fecha, hora, nota_abono))
        c.execute("""
            UPDATE ventas
            SET monto_recibido = ?, saldo = ?, estado_pago = ?
            WHERE rowid = ?
        """, (nuevo_abonado, nuevo_saldo, nuevo_estado, self.venta_actual))
        conn.commit()
        conn.close()

        self.entry_monto.delete(0, tk.END)
        self.label_saldo.config(text=f'Resta: {self.moneda(nuevo_saldo)}')
        self.cargar_ventas_pendientes()
        estado_mensaje = 'Pagado' if nuevo_estado == 'Pagado' else 'Credito'
        messagebox.showinfo(
            'Abono registrado',
            f'Cliente: {cliente}\nFolio: {folio_visible}\nAbono: {self.moneda(monto_aplicado)}\nResta: {self.moneda(nuevo_saldo)}\nEstado: {estado_mensaje}'
        )

    def abrir_historial_cliente(self):
        seleccion = self.tree.selection()
        if not seleccion:
            self.mostrar_historial_general_abonos()
            return
        valores = self.tree.item(seleccion[0], 'values')
        cliente = valores[2]
        self.mostrar_historial_cliente(cliente)

    def mostrar_historial_general_abonos(self):
        ventana = tk.Toplevel(self)
        ventana.title('Historial general de abonos')
        ventana.geometry('980x540')
        ventana.configure(bg='#f5f6f8')
        ventana.transient(self)
        ventana.grab_set()

        header = tk.Frame(ventana, bg='#f5f6f8')
        header.pack(fill='x')
        tk.Label(header, text='Historial general de abonos', bg='#f5f6f8', fg='#20242a',
                 font=('Poppins', 15, 'bold'), anchor='w').pack(fill='x', padx=18, pady=(14, 0))
        tk.Label(header, text='Todos los pagos registrados, con cliente y folio.',
                 bg='#f5f6f8', fg='#68707c', font=('Poppins', 9), anchor='w').pack(
                     fill='x', padx=20, pady=(0, 10))

        barra = ctk.CTkFrame(ventana, fg_color='#ffffff', corner_radius=10,
                             border_width=1, border_color='#e3e6ea')
        barra.pack(fill='x', padx=16, pady=(0, 10))
        entrada = ctk.CTkEntry(barra, placeholder_text='Buscar cliente, folio, fecha o nota',
                               height=34, corner_radius=8, border_color='#e3e6ea', fg_color='#f7f8fa',
                               text_color='#20242a', placeholder_text_color='#68707c',
                               font=ctk.CTkFont(family='Poppins', size=9))
        entrada.pack(side='left', fill='x', expand=True, padx=12, pady=10)
        total_label = tk.Label(barra, text='', bg='#ffffff', fg='#8f070c',
                               font=('Poppins', 9, 'bold'))
        total_label.pack(side='right', padx=14)

        card = ctk.CTkFrame(ventana, fg_color='#ffffff', corner_radius=12,
                            border_width=1, border_color='#e3e6ea')
        card.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        frame = tk.Frame(card, bg='#ffffff')
        frame.pack(fill='both', expand=True, padx=12, pady=12)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        columnas = ('Cliente', 'Folio', 'Fecha', 'Hora', 'Abono', 'Resta', 'Estado', 'Nota')
        tabla = ttk.Treeview(frame, columns=columnas, show='headings', style='Abonos.Treeview')
        anchos = {'Cliente':180, 'Folio':110, 'Fecha':95, 'Hora':75, 'Abono':100,
                  'Resta':100, 'Estado':90, 'Nota':210}
        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=anchos[col], anchor='w' if col in ('Cliente', 'Nota') else 'center')
        sy = ttk.Scrollbar(frame, orient='vertical', command=tabla.yview)
        sx = ttk.Scrollbar(frame, orient='horizontal', command=tabla.xview)
        tabla.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tabla.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')

        def cargar(_event=None):
            texto = entrada.get().strip().lower()
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(v.cliente, 'Cliente General'),
                       COALESCE(NULLIF(v.folio, ''), 'Sin folio'),
                       COALESCE(a.fecha, ''), COALESCE(a.hora, ''),
                       COALESCE(a.monto, 0), COALESCE(v.saldo, 0),
                       COALESCE(v.estado_pago, ''), COALESCE(a.nota, '')
                FROM abonos_ventas a
                JOIN ventas v ON v.rowid = a.venta_id
                WHERE (? = '' OR LOWER(COALESCE(v.cliente, '')) LIKE ?
                       OR LOWER(COALESCE(v.folio, '')) LIKE ?
                       OR LOWER(COALESCE(a.fecha, '')) LIKE ?
                       OR LOWER(COALESCE(a.nota, '')) LIKE ?)
                ORDER BY a.id DESC
            """, (texto, *(f'%{texto}%',) * 4))
            rows = cur.fetchall()
            conn.close()
            tabla.delete(*tabla.get_children())
            total = 0.0
            for cliente, folio, fecha, hora, monto, saldo, estado, nota in rows:
                total += float(monto or 0)
                tabla.insert('', 'end', values=(cliente, folio, fecha, hora,
                    self.moneda(monto), self.moneda(saldo),
                    'Pagado' if float(saldo or 0) <= .009 else (estado or 'Crédito'), nota))
            total_label.config(text=f'{len(rows)} movimientos · {self.moneda(total)}')

        entrada.bind('<KeyRelease>', cargar)
        cargar()
        entrada.focus_set()

    def mostrar_historial_cliente(self, cliente):
        ventana = tk.Toplevel(self)
        ventana.title(f'Historial de abonos - {cliente}')
        ventana.geometry('780x430')
        ventana.configure(bg=self.COLORS.get('bg_primary', '#f5f5f5'))
        ventana.transient(self)
        ventana.grab_set()

        tk.Label(ventana, text=f'Historial de abonos de {cliente}',
                 bg=self.COLORS.get('primary', '#7a1f2b'), fg=self.COLORS.get('white', '#ffffff'),
                 font=('Poppins', 14, 'bold'), anchor='w').pack(fill='x', padx=0, pady=0, ipady=10)

        frame = tk.Frame(ventana, bg=self.COLORS.get('white', '#ffffff'))
        frame.pack(fill='both', expand=True, padx=16, pady=16)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        cols = ('Fecha', 'Hora', 'Folio', 'Abono', 'Resta', 'Estado', 'Nota')
        tabla = ttk.Treeview(frame, columns=cols, show='headings', style='Abonos.Treeview')
        for col, ancho in {'Fecha': 95, 'Hora': 80, 'Folio': 120, 'Abono': 105, 'Resta': 105, 'Estado': 95, 'Nota': 220}.items():
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor='center' if col != 'Nota' else 'w', stretch=True)
        sy = ttk.Scrollbar(frame, orient='vertical', command=tabla.yview)
        tabla.configure(yscrollcommand=sy.set)
        tabla.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')

        conn = self.conectar()
        c = conn.cursor()
        c.execute("""
            SELECT COALESCE(a.fecha, ''), COALESCE(a.hora, ''), COALESCE(v.folio, ''),
                   COALESCE(a.monto, 0),
                   COALESCE(v.saldo, 0), COALESCE(v.estado_pago, ''), COALESCE(a.nota, '')
            FROM abonos_ventas a
            JOIN ventas v ON v.rowid = a.venta_id
            WHERE COALESCE(v.cliente, 'Cliente General') = ?
            ORDER BY a.id DESC
        """, (cliente,))
        rows = c.fetchall()
        conn.close()

        total = 0
        for fecha, hora, folio, monto, saldo, estado, nota in rows:
            total += monto or 0
            estado_visible = 'Pagado' if float(saldo or 0) <= 0.009 else (estado or 'Credito')
            tabla.insert('', 'end', values=(
                fecha,
                hora,
                folio or 'Sin folio',
                self.moneda(monto),
                self.moneda(saldo),
                estado_visible,
                nota,
            ))

        tk.Label(ventana, text=f'Total abonado: {self.moneda(total)}',
                 bg=self.COLORS.get('bg_primary', '#f5f5f5'), fg=self.COLORS.get('success', '#16a34a'),
                 font=('Poppins', 12, 'bold')).pack(anchor='e', padx=18, pady=(0, 12))

    def mostrar_historial_compras_clientes(self):
        """Muestra todas las ventas históricas, estén pagadas o pendientes."""
        ventana = tk.Toplevel(self)
        ventana.title('Historial de compras de clientes')
        ancho = min(1040, max(820, self.winfo_toplevel().winfo_width() - 120))
        alto = min(620, max(480, self.winfo_toplevel().winfo_height() - 110))
        ventana.geometry(f'{ancho}x{alto}')
        ventana.configure(bg=self.COLORS.get('bg_primary', '#f5f5f5'))
        ventana.transient(self)
        ventana.grab_set()

        header = tk.Frame(ventana, bg=self.COLORS.get('primary', '#7a1f2b'))
        header.pack(fill='x')
        tk.Label(header, text='Historial de compras de clientes',
                 bg=self.COLORS.get('primary', '#7a1f2b'), fg='white',
                 font=('Poppins', 14, 'bold'), anchor='w').pack(fill='x', padx=18, pady=(10, 0))
        tk.Label(header, text='Incluye compras pagadas, a crédito y con saldo pendiente.',
                 bg=self.COLORS.get('primary', '#7a1f2b'), fg='#f3d9d6',
                 font=('Poppins', 9), anchor='w').pack(fill='x', padx=18, pady=(0, 10))

        barra = tk.Frame(ventana, bg='white', highlightthickness=1, highlightbackground='#e5e7eb')
        barra.pack(fill='x', padx=16, pady=(14, 8))
        tk.Label(barra, text='Buscar:', bg='white', fg=self.COLORS.get('dark', '#111827'),
                 font=('Poppins', 9, 'bold')).pack(side='left', padx=(12, 6), pady=10)
        entrada = ttk.Entry(barra, font=('Poppins', 10))
        entrada.pack(side='left', fill='x', expand=True, padx=(0, 8), pady=8, ipady=4)
        resumen = tk.Label(barra, text='', bg='white', fg=self.COLORS.get('primary', '#7a1f2b'),
                           font=('Poppins', 9, 'bold'))
        resumen.pack(side='right', padx=12)

        frame = tk.Frame(ventana, bg='white', highlightthickness=1, highlightbackground='#e5e7eb')
        frame.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        columnas = ('ID', 'Folio', 'Cliente', 'Fecha', 'Total', 'Abonado', 'Resta', 'Estado')
        tabla = ttk.Treeview(frame, columns=columnas, show='headings', style='Abonos.Treeview')
        anchos = {'ID': 0, 'Folio': 120, 'Cliente': 220, 'Fecha': 105, 'Total': 110,
                  'Abonado': 110, 'Resta': 110, 'Estado': 100}
        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=anchos[col], minwidth=0 if col == 'ID' else 60,
                         anchor='w' if col == 'Cliente' else 'center', stretch=col != 'ID')
        tabla.column('ID', width=0, minwidth=0, stretch=False)
        sy = ttk.Scrollbar(frame, orient='vertical', command=tabla.yview)
        sx = ttk.Scrollbar(frame, orient='horizontal', command=tabla.xview)
        tabla.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tabla.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')

        def cargar(_event=None):
            texto = entrada.get().strip().lower()
            for item in tabla.get_children():
                tabla.delete(item)
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT rowid, COALESCE(NULLIF(folio, ''), 'Sin folio'),
                       COALESCE(cliente, 'Cliente General'), COALESCE(fecha, ''),
                       COALESCE(total, 0), COALESCE(monto_recibido, 0),
                       COALESCE(saldo, 0), COALESCE(estado_pago, '')
                FROM ventas
                WHERE (? = '' OR LOWER(COALESCE(cliente, '')) LIKE ?
                       OR LOWER(COALESCE(folio, '')) LIKE ?
                       OR LOWER(COALESCE(fecha, '')) LIKE ?)
                ORDER BY rowid DESC
            """, (texto, f'%{texto}%', f'%{texto}%', f'%{texto}%'))
            rows = cur.fetchall()
            conn.close()
            total_general = 0.0
            for venta_id, folio, cliente, fecha, total, abonado, saldo, estado in rows:
                total_general += float(total or 0)
                estado_visible = 'Pagado' if float(saldo or 0) <= 0.009 else (estado or 'Crédito')
                tabla.insert('', 'end', values=(venta_id, folio, cliente, fecha,
                    self.moneda(total), self.moneda(abonado), self.moneda(saldo), estado_visible))
            resumen.config(text=f'{len(rows)} compras  ·  {self.moneda(total_general)}')

        def abrir_abonos(_event=None):
            seleccion = tabla.selection()
            if not seleccion:
                return
            valores = tabla.item(seleccion[0], 'values')
            ventana.grab_release()
            ventana.destroy()
            self.mostrar_historial_cliente(valores[2])

        entrada.bind('<KeyRelease>', cargar)
        tabla.bind('<Double-1>', abrir_abonos)
        cargar()
        entrada.focus_set()

    def crear_interfaz(self):
        self.configure(bg='#f5f6f8');self.grid_rowconfigure(1,weight=1);self.grid_columnconfigure(0,weight=1)
        h=tk.Frame(self,bg='#f5f6f8');h.grid(row=0,column=0,sticky='ew');h.grid_columnconfigure(0,weight=1);tk.Label(h,text='Módulo de Abonos',bg='#f5f6f8',fg='#20242a',font=('Poppins',17,'bold'),anchor='w').grid(row=0,column=0,sticky='ew',padx=18,pady=(8,0));tk.Label(h,text='Saldos, pagos e historial de compras de clientes.',bg='#f5f6f8',fg='#68707c',font=('Poppins',9),anchor='w').grid(row=1,column=0,sticky='ew',padx=20,pady=(0,7))
        c=tk.Frame(self,bg='#f5f6f8');c.grid(row=1,column=0,sticky='nsew',padx=14,pady=(4,12));c.grid_rowconfigure(1,weight=1);c.grid_columnconfigure(0,weight=4,minsize=480);c.grid_columnconfigure(1,weight=1,minsize=235)
        form=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');form.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,10))
        for col in range(6):form.grid_columnconfigure(col,weight=1,uniform='abono')
        ctk.CTkLabel(form,text='Registrar abono',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,columnspan=6,sticky='w',padx=14,pady=(10,6))
        self.entry_folio=ctk.CTkEntry(form,placeholder_text='Folio',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',text_color='#20242a',placeholder_text_color='#68707c',font=ctk.CTkFont(family='Poppins',size=9));self.entry_folio.grid(row=1,column=0,columnspan=2,sticky='ew',padx=(14,6),pady=(0,12));self.entry_folio.bind('<Return>',lambda _e:self.buscar_por_folio())
        self.entry_monto=ctk.CTkEntry(form,placeholder_text='Cantidad abonada',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',text_color='#20242a',placeholder_text_color='#68707c',font=ctk.CTkFont(family='Poppins',size=9));self.entry_monto.grid(row=1,column=2,sticky='ew',padx=6,pady=(0,12));self.entry_monto.bind('<Return>',lambda _e:self.registrar_abono())
        self.label_saldo=tk.Label(form,text='Resta: $0.00',bg='#fff',fg='#8f070c',font=('Poppins',10,'bold'),anchor='w');self.label_saldo.grid(row=1,column=3,sticky='ew',padx=8,pady=(0,12))
        ctk.CTkButton(form,text='Buscar folio',command=self.buscar_por_folio,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a').grid(row=1,column=4,sticky='ew',padx=6,pady=(0,12));ctk.CTkButton(form,text='Registrar abono',command=self.registrar_abono,height=34,corner_radius=8,fg_color='#8f070c',hover_color='#6f0509').grid(row=1,column=5,sticky='ew',padx=(6,14),pady=(0,12))
        lista=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');lista.grid(row=1,column=0,sticky='nsew',padx=(0,10));lista.grid_rowconfigure(2,weight=1);lista.grid_columnconfigure(0,weight=1);ctk.CTkLabel(lista,text='Cuentas pendientes',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=14,pady=(10,5))
        self.entry_busqueda=ctk.CTkEntry(lista,placeholder_text='Buscar cliente, folio o fecha',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#f7f8fa',text_color='#20242a',placeholder_text_color='#68707c',font=ctk.CTkFont(family='Poppins',size=9));self.entry_busqueda.grid(row=1,column=0,sticky='ew',padx=14,pady=(0,10));self.entry_busqueda.bind('<KeyRelease>',lambda _e:self.buscar_ventas())
        tf=tk.Frame(lista,bg='#fff');tf.grid(row=2,column=0,sticky='nsew',padx=12,pady=(0,12));tf.grid_rowconfigure(0,weight=1);tf.grid_columnconfigure(0,weight=1);cols=('ID','Folio','Cliente','Total','Abonado','Resta','Estado','Fecha');self.tree=ttk.Treeview(tf,columns=cols,show='headings',style='Abonos.Treeview');widths={'ID':0,'Folio':120,'Cliente':190,'Total':100,'Abonado':100,'Resta':100,'Estado':90,'Fecha':95}
        for col in cols:self.tree.heading(col,text=col);self.tree.column(col,width=widths[col],minwidth=0 if col=='ID' else 60,anchor='w' if col=='Cliente' else 'center',stretch=col!='ID')
        sy=ttk.Scrollbar(tf,orient='vertical',command=self.tree.yview);sx=ttk.Scrollbar(tf,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);self.tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');self.tree.bind('<<TreeviewSelect>>',lambda _e:self.cargar_seleccion());self.tree.bind('<Double-1>',lambda _e:self.abrir_historial_cliente())
        side=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');side.grid(row=1,column=1,sticky='nsew');side.grid_columnconfigure(0,weight=1);ctk.CTkLabel(side,text='Resumen',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=16,pady=(14,8));self.resumen_pendientes=tk.Label(side,text='Cuentas pendientes: 0',bg='#fff',fg='#8f070c',font=('Poppins',12,'bold'),justify='left',anchor='w');self.resumen_pendientes.grid(row=1,column=0,sticky='ew',padx=16,pady=(5,18))
        for row,(text,cmd,color,fg) in enumerate((('Historial de compras',self.mostrar_historial_compras_clientes,'#8f070c','#fff'),('Historial de abonos',self.abrir_historial_cliente,'#eef0f2','#20242a'),('Actualizar cuentas',self.cargar_ventas_pendientes,'#eef0f2','#20242a'),('Limpiar búsqueda',self.limpiar_busqueda,'#eef0f2','#20242a')),2):ctk.CTkButton(side,text=text,command=cmd,height=34,corner_radius=8,fg_color=color,hover_color='#6f0509' if color=='#8f070c' else '#dfe2e6',text_color=fg,font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=row,column=0,sticky='ew',padx=16,pady=(0,8 if row<5 else 16))

    def mostrar_historial_cliente(self, cliente):
        ventana=tk.Toplevel(self);ventana.title(f'Historial de abonos - {cliente}');ventana.geometry('900x520');ventana.configure(bg='#f5f6f8');ventana.transient(self);ventana.grab_set()
        h=tk.Frame(ventana,bg='#f5f6f8');h.pack(fill='x');tk.Label(h,text=f'Historial de abonos · {cliente}',bg='#f5f6f8',fg='#20242a',font=('Poppins',15,'bold'),anchor='w').pack(fill='x',padx=18,pady=(14,0));tk.Label(h,text='Movimientos, folios y saldos del cliente.',bg='#f5f6f8',fg='#68707c',font=('Poppins',9),anchor='w').pack(fill='x',padx=20,pady=(0,10))
        barra=ctk.CTkFrame(ventana,fg_color='#fff',corner_radius=10,border_width=1,border_color='#e3e6ea');barra.pack(fill='x',padx=16,pady=(0,10));entrada=ctk.CTkEntry(barra,placeholder_text='Buscar folio, fecha o nota',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#f7f8fa',text_color='#20242a',placeholder_text_color='#68707c',font=ctk.CTkFont(family='Poppins',size=9));entrada.pack(side='left',fill='x',expand=True,padx=12,pady=10);total_label=tk.Label(barra,text='',bg='#fff',fg='#8f070c',font=('Poppins',9,'bold'));total_label.pack(side='right',padx=14)
        card=ctk.CTkFrame(ventana,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');card.pack(fill='both',expand=True,padx=16,pady=(0,16));frame=tk.Frame(card,bg='#fff');frame.pack(fill='both',expand=True,padx=12,pady=12);frame.grid_rowconfigure(0,weight=1);frame.grid_columnconfigure(0,weight=1)
        cols=('Fecha','Hora','Folio','Abono','Resta','Estado','Nota');tabla=ttk.Treeview(frame,columns=cols,show='headings',style='Abonos.Treeview');widths={'Fecha':95,'Hora':75,'Folio':120,'Abono':100,'Resta':100,'Estado':90,'Nota':230}
        for col in cols:tabla.heading(col,text=col);tabla.column(col,width=widths[col],anchor='w' if col=='Nota' else 'center',stretch=True)
        sy=ttk.Scrollbar(frame,orient='vertical',command=tabla.yview);sx=ttk.Scrollbar(frame,orient='horizontal',command=tabla.xview);tabla.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);tabla.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew')
        def cargar(_event=None):
            texto=entrada.get().strip().lower();conn=self.conectar();cur=conn.cursor();cur.execute("""SELECT COALESCE(a.fecha,''),COALESCE(a.hora,''),COALESCE(NULLIF(v.folio,''),'Sin folio'),COALESCE(a.monto,0),COALESCE(v.saldo,0),COALESCE(v.estado_pago,''),COALESCE(a.nota,'') FROM abonos_ventas a JOIN ventas v ON v.rowid=a.venta_id WHERE COALESCE(v.cliente,'Cliente General')=? AND (?='' OR LOWER(COALESCE(v.folio,'')) LIKE ? OR LOWER(COALESCE(a.fecha,'')) LIKE ? OR LOWER(COALESCE(a.nota,'')) LIKE ?) ORDER BY a.id DESC""",(cliente,texto,*(f'%{texto}%',)*3));rows=cur.fetchall();conn.close();tabla.delete(*tabla.get_children());total=0
            for fecha,hora,folio,monto,saldo,estado,nota in rows:total+=float(monto or 0);tabla.insert('', 'end', values=(fecha,hora,folio,self.moneda(monto),self.moneda(saldo),'Pagado' if float(saldo or 0)<=.009 else (estado or 'Crédito'),nota))
            total_label.config(text=f'{len(rows)} movimientos · {self.moneda(total)}')
        entrada.bind('<KeyRelease>',cargar);cargar();entrada.focus_set()

    def parse_monto(self, valor):
        limpio = str(valor or '').replace('$', '').replace(',', '').strip()
        if not limpio:
            raise ValueError
        return float(limpio)

    def moneda(self, valor):
        try:
            return f'${float(valor or 0):,.2f}'
        except Exception:
            return '$0.00'

