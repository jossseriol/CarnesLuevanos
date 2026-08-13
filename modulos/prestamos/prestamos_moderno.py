import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import customtkinter as ctk

from modulos.utils.estilos_modernos import estilos


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class PrestamosModerno(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.prestamo_seleccionado = None
        self.crear_tablas()
        self.widgets()
        self.cargar_prestamos()

    def conectar(self):
        return sqlite3.connect('database.db')

    def crear_tablas(self):
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beneficiario TEXT NOT NULL,
                concepto TEXT,
                monto REAL NOT NULL,
                pagado REAL DEFAULT 0,
                saldo REAL NOT NULL,
                fecha TEXT NOT NULL,
                vencimiento TEXT,
                estado TEXT NOT NULL,
                notas TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS abonos_prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prestamo_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                nota TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def widgets(self):
        self.crear_header()
        self.crear_formulario()
        self.crear_metricas()
        self.crear_tabla()

    def crear_header(self):
        header = tk.Frame(self, bg=estilos.COLORS['bg_primary'])
        header.place(x=20, y=15, width=1320, height=70)
        tk.Label(header, text="Modulo de Prestamos", font=('Poppins', 24, 'bold'),
                 bg=estilos.COLORS['bg_primary'], fg=estilos.COLORS['primary2']).place(x=0, y=0)
        tk.Label(header, text="Control de prestamos, abonos, saldos pendientes y vencimientos.",
                 font=('Poppins', 11), bg=estilos.COLORS['bg_primary'],
                 fg=estilos.COLORS['dark_gray']).place(x=3, y=42)

    def crear_formulario(self):
        self.form_frame = ctk.CTkFrame(self, width=350, height=610, corner_radius=18,
                                       fg_color=estilos.COLORS['white'], border_width=1,
                                       border_color=estilos.COLORS['border'])
        self.form_frame.place(x=20, y=100)
        ctk.CTkLabel(self.form_frame, text="Nuevo prestamo",
                     font=ctk.CTkFont(family="Poppins", size=20, weight="bold"),
                     text_color=estilos.COLORS['primary2']).place(x=22, y=18)

        self.beneficiario = self.crear_entry("Beneficiario", 74)
        self.concepto = self.crear_entry("Concepto", 132)
        self.monto = self.crear_entry("Monto", 190)
        self.pagado = self.crear_entry("Pago inicial", 248)
        self.vencimiento = self.crear_entry("Vencimiento YYYY-MM-DD", 306)
        self.estado = ctk.CTkComboBox(self.form_frame, values=["Activo", "Pagado", "Vencido", "Cancelado"],
                                      width=306, height=38, corner_radius=10,
                                      border_color=estilos.COLORS['border'],
                                      fg_color=estilos.COLORS['white'],
                                      button_color=estilos.COLORS['primary2'],
                                      button_hover_color=estilos.COLORS['secondary1'])
        self.estado.set("Activo")
        self.estado.place(x=22, y=364)
        self.notas = self.crear_entry("Notas", 422)

        ctk.CTkButton(self.form_frame, text="Registrar", command=self.registrar_prestamo,
                      width=146, height=42, corner_radius=12,
                      fg_color=estilos.COLORS['primary2'],
                      hover_color=estilos.COLORS['secondary1'],
                      font=ctk.CTkFont(family="Poppins", size=12, weight="bold")).place(x=22, y=494)
        ctk.CTkButton(self.form_frame, text="Limpiar", command=self.limpiar_campos,
                      width=146, height=42, corner_radius=12,
                      fg_color=estilos.COLORS['dark_gray'],
                      hover_color=estilos.COLORS['gray'],
                      font=ctk.CTkFont(family="Poppins", size=12, weight="bold")).place(x=182, y=494)
        ctk.CTkButton(self.form_frame, text="Registrar abono", command=self.registrar_abono,
                      width=306, height=38, corner_radius=12,
                      fg_color=estilos.COLORS['success'],
                      hover_color=estilos.COLORS['success_dark'],
                      font=ctk.CTkFont(family="Poppins", size=12, weight="bold")).place(x=22, y=550)

    def crear_entry(self, placeholder, y):
        entry = ctk.CTkEntry(self.form_frame, placeholder_text=placeholder, width=306, height=38,
                             corner_radius=10, border_color=estilos.COLORS['border'],
                             fg_color=estilos.COLORS['white'],
                             font=ctk.CTkFont(family="Poppins", size=12))
        entry.place(x=22, y=y)
        return entry

    def crear_metricas(self):
        self.metricas = {}
        datos = [
            ("Prestamos", "0", estilos.COLORS['primary2']),
            ("Saldo pendiente", "$ 0.00", estilos.COLORS['warning']),
            ("Pagado", "$ 0.00", estilos.COLORS['success']),
        ]
        x = 395
        for titulo, valor, color in datos:
            card = ctk.CTkFrame(self, width=285, height=94, corner_radius=16, fg_color=color)
            card.place(x=x, y=100)
            tk.Label(card, text=titulo, bg=color, fg=estilos.COLORS['white'],
                     font=('Poppins', 11, 'bold')).place(x=18, y=15)
            label = tk.Label(card, text=valor, bg=color, fg=estilos.COLORS['white'],
                             font=('Poppins', 20, 'bold'))
            label.place(x=18, y=42)
            self.metricas[titulo] = label
            x += 300

    def crear_tabla(self):
        table_frame = ctk.CTkFrame(self, width=885, height=500, corner_radius=16,
                                   fg_color=estilos.COLORS['white'], border_width=1,
                                   border_color=estilos.COLORS['border'])
        table_frame.place(x=395, y=220)
        columns = ("ID", "Beneficiario", "Concepto", "Monto", "Pagado", "Saldo", "Fecha", "Vence", "Estado")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.place(x=15, y=15, width=835, height=450)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.place(x=852, y=15, height=450)
        self.tree.configure(yscrollcommand=scroll.set)
        widths = {"ID": 45, "Beneficiario": 150, "Concepto": 150, "Monto": 90, "Pagado": 90,
                  "Saldo": 90, "Fecha": 95, "Vence": 95, "Estado": 90}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_prestamo)

    def widgets(self):
        self.configure(bg='#f5f6f8');self.grid_rowconfigure(1,weight=1);self.grid_columnconfigure(0,weight=1)
        h=tk.Frame(self,bg='#f5f6f8');h.grid(row=0,column=0,sticky='ew');h.grid_columnconfigure(0,weight=1)
        tk.Label(h,text='Módulo de Préstamos',bg='#f5f6f8',fg='#20242a',font=('Poppins',17,'bold'),anchor='w').grid(row=0,column=0,sticky='ew',padx=18,pady=(8,0));tk.Label(h,text='Préstamos, abonos, vencimientos y saldos.',bg='#f5f6f8',fg='#68707c',font=('Poppins',9),anchor='w').grid(row=1,column=0,sticky='ew',padx=20,pady=(0,7))
        c=tk.Frame(self,bg='#f5f6f8');c.grid(row=1,column=0,sticky='nsew',padx=14,pady=(4,12));c.grid_rowconfigure(1,weight=1);c.grid_columnconfigure(0,weight=4,minsize=480);c.grid_columnconfigure(1,weight=1,minsize=235)
        f=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');f.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,10));self.form_frame=f
        for col in range(6):f.grid_columnconfigure(col,weight=1,uniform='prestamo')
        ctk.CTkLabel(f,text='Datos del préstamo',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,columnspan=6,sticky='w',padx=14,pady=(10,6))
        self.beneficiario=self._campo_prestamo('Beneficiario',0,2);self.concepto=self._campo_prestamo('Concepto',2,2);self.monto=self._campo_prestamo('Monto',4);self.pagado=self._campo_prestamo('Pago inicial / abono',5)
        self.vencimiento=self._campo_prestamo('Vencimiento YYYY-MM-DD',0,2,row=2,pady=(8,12));self.notas=self._campo_prestamo('Notas',2,2,row=2,pady=(8,12))
        self.estado=ctk.CTkComboBox(f,values=['Activo','Pagado','Vencido','Cancelado'],height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',button_color='#8f070c',button_hover_color='#6f0509',font=ctk.CTkFont(family='Poppins',size=9));self.estado.set('Activo');self.estado.grid(row=2,column=4,sticky='ew',padx=6,pady=(8,12))
        ctk.CTkButton(f,text='Registrar',command=self.registrar_prestamo,height=34,corner_radius=8,fg_color='#8f070c',hover_color='#6f0509',font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=2,column=5,sticky='ew',padx=(6,14),pady=(8,12))
        lista=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');lista.grid(row=1,column=0,sticky='nsew',padx=(0,10));lista.grid_rowconfigure(2,weight=1);lista.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(lista,text='Lista de préstamos',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=14,pady=(10,5));self.busqueda=ctk.CTkEntry(lista,placeholder_text='Buscar beneficiario, concepto, fecha, vencimiento o estado',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#f7f8fa',font=ctk.CTkFont(family='Poppins',size=9));self.busqueda.grid(row=1,column=0,sticky='ew',padx=14,pady=(0,10));self.busqueda.bind('<KeyRelease>',self.filtrar_prestamos)
        tf=tk.Frame(lista,bg='#fff');tf.grid(row=2,column=0,sticky='nsew',padx=12,pady=(0,12));tf.grid_rowconfigure(0,weight=1);tf.grid_columnconfigure(0,weight=1);style=ttk.Style();style.configure('Prestamos.Treeview',background='#fff',fieldbackground='#fff',foreground='#20242a',rowheight=27,borderwidth=0,font=('Poppins',9));style.configure('Prestamos.Treeview.Heading',background='#f0f1f3',foreground='#20242a',font=('Poppins',9,'bold'),relief='flat')
        cols=('ID','Beneficiario','Concepto','Monto','Pagado','Saldo','Fecha','Vence','Estado');self.tree=ttk.Treeview(tf,columns=cols,show='headings',style='Prestamos.Treeview');widths={'ID':45,'Beneficiario':150,'Concepto':150,'Monto':90,'Pagado':90,'Saldo':90,'Fecha':95,'Vence':95,'Estado':90}
        for col in cols:self.tree.heading(col,text=col);self.tree.column(col,width=widths[col],anchor='w' if col in ('Beneficiario','Concepto') else 'center',stretch=col!='ID')
        sy=ttk.Scrollbar(tf,orient='vertical',command=self.tree.yview);sx=ttk.Scrollbar(tf,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);self.tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');self.tree.bind('<<TreeviewSelect>>',self.seleccionar_prestamo)
        r=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');r.grid(row=1,column=1,sticky='nsew');r.grid_columnconfigure(0,weight=1);ctk.CTkLabel(r,text='Resumen',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=16,pady=(14,8))
        self.metricas={};
        for row,(titulo,valor) in enumerate((('Prestamos','0'),('Saldo pendiente','$ 0.00'),('Pagado','$ 0.00')),1):lab=tk.Label(r,text=f'{titulo}\n{valor}',bg='#fff',fg='#8f070c' if row==1 else '#20242a',font=('Poppins',11,'bold'),justify='left',anchor='w');lab.grid(row=row,column=0,sticky='ew',padx=16,pady=5);self.metricas[titulo]=lab
        ctk.CTkButton(r,text='Registrar abono',command=self.registrar_abono,height=34,corner_radius=8,fg_color='#8f070c',hover_color='#6f0509',font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=4,column=0,sticky='ew',padx=16,pady=(16,8));ctk.CTkButton(r,text='Actualizar lista',command=self.cargar_prestamos,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a').grid(row=5,column=0,sticky='ew',padx=16,pady=(0,8));ctk.CTkButton(r,text='Limpiar campos',command=self.limpiar_campos,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a').grid(row=6,column=0,sticky='ew',padx=16,pady=(0,16))

    def _campo_prestamo(self,placeholder,column,span=1,row=1,pady=(0,6)):
        e=ctk.CTkEntry(self.form_frame,placeholder_text=placeholder,height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',font=ctk.CTkFont(family='Poppins',size=9));e.grid(row=row,column=column,columnspan=span,sticky='ew',padx=(14 if column==0 else 6,14 if column+span==6 else 6),pady=pady);return e
    def filtrar_prestamos(self,_event=None):
        t=self.busqueda.get().strip().lower();conn=self.conectar();cur=conn.cursor();cur.execute("""SELECT id,beneficiario,COALESCE(concepto,''),monto,pagado,saldo,fecha,COALESCE(vencimiento,''),estado FROM prestamos WHERE ?='' OR LOWER(COALESCE(beneficiario,'')) LIKE ? OR LOWER(COALESCE(concepto,'')) LIKE ? OR LOWER(COALESCE(fecha,'')) LIKE ? OR LOWER(COALESCE(vencimiento,'')) LIKE ? OR LOWER(COALESCE(estado,'')) LIKE ? ORDER BY id DESC""",(t,*(f'%{t}%',)*5));rows=cur.fetchall();conn.close();self.tree.delete(*self.tree.get_children());[self.tree.insert('', 'end', values=(x[0],x[1],x[2],f'$ {x[3]:.2f}',f'$ {x[4]:.2f}',f'$ {x[5]:.2f}',x[6],x[7] or '-',x[8])) for x in rows];self.actualizar_metricas(rows)

    def registrar_prestamo(self):
        beneficiario = self.beneficiario.get().strip()
        concepto = self.concepto.get().strip()
        vencimiento = self.vencimiento.get().strip()
        estado = self.estado.get().strip() or "Activo"
        notas = self.notas.get().strip()
        try:
            monto = float(self.monto.get().strip())
            pagado = float(self.pagado.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Datos invalidos", "Monto y pago inicial deben ser numericos.")
            return
        if not beneficiario or monto <= 0 or pagado < 0:
            messagebox.showwarning("Campos incompletos", "Beneficiario y monto mayor a cero son obligatorios.")
            return
        saldo = max(monto - pagado, 0)
        if saldo <= 0:
            estado = "Pagado"
        fecha = datetime.now().strftime("%Y-%m-%d")
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO prestamos (beneficiario, concepto, monto, pagado, saldo, fecha, vencimiento, estado, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (beneficiario, concepto, monto, pagado, saldo, fecha, vencimiento, estado, notas))
        prestamo_id = cur.lastrowid
        if pagado > 0:
            cur.execute("INSERT INTO abonos_prestamos (prestamo_id, monto, fecha, nota) VALUES (?, ?, ?, ?)",
                        (prestamo_id, pagado, fecha, "Pago inicial"))
        conn.commit()
        conn.close()
        self.limpiar_campos()
        self.cargar_prestamos()
        messagebox.showinfo("Prestamo registrado", "El prestamo se guardo correctamente.")

    def registrar_abono(self):
        if not self.prestamo_seleccionado:
            messagebox.showwarning("Seleccion requerida", "Selecciona un prestamo para abonar.")
            return
        try:
            monto = float(self.pagado.get().strip())
        except ValueError:
            messagebox.showerror("Monto invalido", "Escribe el abono en el campo Pago inicial.")
            return
        if monto <= 0:
            messagebox.showerror("Monto invalido", "El abono debe ser mayor a cero.")
            return
        fecha = datetime.now().strftime("%Y-%m-%d")
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute("SELECT pagado, saldo FROM prestamos WHERE id = ?", (self.prestamo_seleccionado,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        pagado_actual, saldo_actual = row
        nuevo_saldo = max((saldo_actual or 0) - monto, 0)
        nuevo_pagado = (pagado_actual or 0) + monto
        estado = "Pagado" if nuevo_saldo <= 0 else "Activo"
        cur.execute("UPDATE prestamos SET pagado = ?, saldo = ?, estado = ? WHERE id = ?",
                    (nuevo_pagado, nuevo_saldo, estado, self.prestamo_seleccionado))
        cur.execute("INSERT INTO abonos_prestamos (prestamo_id, monto, fecha, nota) VALUES (?, ?, ?, ?)",
                    (self.prestamo_seleccionado, monto, fecha, "Abono"))
        conn.commit()
        conn.close()
        self.limpiar_campos()
        self.cargar_prestamos()
        messagebox.showinfo("Abono registrado", "El abono se aplico correctamente.")

    def cargar_prestamos(self):
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, beneficiario, COALESCE(concepto, ''), monto, pagado, saldo, fecha,
                   COALESCE(vencimiento, ''), estado
            FROM prestamos
            ORDER BY id DESC
        ''')
        rows = cur.fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            id_, beneficiario, concepto, monto, pagado, saldo, fecha, vencimiento, estado = row
            self.tree.insert("", "end", values=(id_, beneficiario, concepto, f"$ {monto:.2f}",
                                                f"$ {pagado:.2f}", f"$ {saldo:.2f}",
                                                fecha, vencimiento or "-", estado))
        self.actualizar_metricas(rows)

    def actualizar_metricas(self, rows):
        self.metricas["Prestamos"].configure(text=f"Préstamos\n{len(rows)}")
        self.metricas["Saldo pendiente"].configure(text=f"Saldo pendiente\n$ {sum(float(r[5] or 0) for r in rows):.2f}")
        self.metricas["Pagado"].configure(text=f"Pagado\n$ {sum(float(r[4] or 0) for r in rows):.2f}")

    def seleccionar_prestamo(self, _event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], "values")
        self.prestamo_seleccionado = valores[0]
        self.limpiar_campos(mantener_seleccion=True)
        self.beneficiario.insert(0, valores[1])
        self.concepto.insert(0, valores[2])
        self.monto.insert(0, str(valores[3]).replace("$", "").strip())
        self.vencimiento.insert(0, "" if valores[7] == "-" else valores[7])
        self.estado.set(valores[8])

    def limpiar_campos(self, mantener_seleccion=False):
        for entry in (self.beneficiario, self.concepto, self.monto, self.pagado, self.vencimiento, self.notas):
            entry.delete(0, tk.END)
        self.estado.set("Activo")
        if not mantener_seleccion:
            self.prestamo_seleccionado = None

