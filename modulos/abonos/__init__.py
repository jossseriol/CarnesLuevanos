import datetime
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

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

        self.crear_label(form, 'Folio o factura', 1, 0)
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
        tk.Label(top_lista, text='Cuentas con saldo pendiente', bg=self.COLORS.get('white', '#ffffff'),
                 fg=self.COLORS.get('primary', '#7a1f2b'), font=('Poppins', 12, 'bold'),
                 anchor='w').grid(row=0, column=0, sticky='ew')
        tk.Button(top_lista, text='Actualizar', command=self.cargar_ventas_pendientes,
                  bg=self.COLORS.get('light', '#f3f4f6'), fg=self.COLORS.get('dark', '#111827'),
                  font=('Poppins', 9, 'bold'), relief='flat', cursor='hand2', bd=0).grid(row=0, column=1, padx=(8, 0), ipadx=10, ipady=4)

        table_frame = tk.Frame(lista_frame, bg=self.COLORS.get('white', '#ffffff'))
        table_frame.grid(row=1, column=0, sticky='nsew', padx=14, pady=(0, 14))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ('ID', 'Folio', 'Factura', 'Cliente', 'Total', 'Abonado', 'Resta', 'Estado', 'Fecha')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', style='Abonos.Treeview')
        widths = {
            'ID': 70, 'Folio': 110, 'Factura': 90, 'Cliente': 220,
            'Total': 110, 'Abonado': 110, 'Resta': 110, 'Estado': 100, 'Fecha': 100,
        }
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor='center' if col != 'Cliente' else 'w', stretch=True)

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

    def cargar_ventas_pendientes(self):
        self.asegurar_tablas()
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.conectar()
        c = conn.cursor()
        c.execute("""
            SELECT
                rowid,
                COALESCE(folio, ''),
                COALESCE(numero_factura, factura, rowid),
                COALESCE(cliente, 'Cliente General'),
                COALESCE(total, 0),
                COALESCE(monto_recibido, 0),
                COALESCE(saldo, 0),
                COALESCE(estado_pago, ''),
                COALESCE(fecha, '')
            FROM ventas
            WHERE COALESCE(saldo, 0) > 0 OR LOWER(COALESCE(estado_pago, '')) = 'credito'
            ORDER BY rowid DESC
        """)
        rows = c.fetchall()
        conn.close()

        for venta_id, folio, factura, cliente, total, abonado, saldo, estado, fecha in rows:
            folio_visible = folio or str(factura)
            self.tree.insert('', 'end', values=(
                venta_id,
                folio_visible,
                factura,
                cliente,
                self.moneda(total),
                self.moneda(abonado),
                self.moneda(saldo),
                estado or ('Credito' if saldo > 0 else 'Pagado'),
                fecha,
            ))

        self.venta_actual = None
        self.label_saldo.config(text='Resta: $0.00')

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
        self.label_saldo.config(text=f'Resta: {valores[6]}')
        self.entry_monto.focus_set()

    def buscar_por_folio(self):
        folio = self.entry_folio.get().strip()
        if not folio:
            messagebox.showwarning('Folio requerido', 'Escribe el folio o numero de factura.')
            return

        conn = self.conectar()
        c = conn.cursor()
        c.execute("""
            SELECT rowid, COALESCE(saldo, 0)
            FROM ventas
            WHERE folio = ?
               OR CAST(numero_factura AS TEXT) = ?
               OR CAST(factura AS TEXT) = ?
            ORDER BY rowid DESC
            LIMIT 1
        """, (folio, folio, folio))
        row = c.fetchone()
        conn.close()

        if not row:
            messagebox.showwarning('No encontrado', 'No encontre una venta con ese folio o factura.')
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
                   COALESCE(cliente, 'Cliente General'), COALESCE(folio, ''), COALESCE(numero_factura, factura, rowid)
            FROM ventas
            WHERE rowid = ?
        """, (self.venta_actual,))
        venta = c.fetchone()
        if not venta:
            conn.close()
            messagebox.showerror('Error', 'No se encontro la venta seleccionada.')
            return

        total, abonado_actual, saldo_actual, cliente, folio, factura = venta
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
        folio_visible = folio or str(factura)

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
            return
        valores = self.tree.item(seleccion[0], 'values')
        cliente = valores[3]
        self.mostrar_historial_cliente(cliente)

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

        cols = ('Fecha', 'Hora', 'Folio', 'Factura', 'Abono', 'Resta', 'Estado', 'Nota')
        tabla = ttk.Treeview(frame, columns=cols, show='headings', style='Abonos.Treeview')
        for col, ancho in {'Fecha': 95, 'Hora': 80, 'Folio': 105, 'Factura': 85, 'Abono': 105, 'Resta': 105, 'Estado': 95, 'Nota': 220}.items():
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
                   COALESCE(v.numero_factura, v.factura, v.rowid), COALESCE(a.monto, 0),
                   COALESCE(v.saldo, 0), COALESCE(v.estado_pago, ''), COALESCE(a.nota, '')
            FROM abonos_ventas a
            JOIN ventas v ON v.rowid = a.venta_id
            WHERE COALESCE(v.cliente, 'Cliente General') = ?
            ORDER BY a.id DESC
        """, (cliente,))
        rows = c.fetchall()
        conn.close()

        total = 0
        for fecha, hora, folio, factura, monto, saldo, estado, nota in rows:
            total += monto or 0
            estado_visible = 'Pagado' if float(saldo or 0) <= 0.009 else (estado or 'Credito')
            tabla.insert('', 'end', values=(
                fecha,
                hora,
                folio or str(factura),
                factura,
                self.moneda(monto),
                self.moneda(saldo),
                estado_visible,
                nota,
            ))

        tk.Label(ventana, text=f'Total abonado: {self.moneda(total)}',
                 bg=self.COLORS.get('bg_primary', '#f5f5f5'), fg=self.COLORS.get('success', '#16a34a'),
                 font=('Poppins', 12, 'bold')).pack(anchor='e', padx=18, pady=(0, 12))

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

