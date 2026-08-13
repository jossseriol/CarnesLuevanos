import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import customtkinter as ctk

from modulos.utils.estilos_modernos import estilos


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class NominasModerno(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.nomina_seleccionada = None
        self.crear_tabla()
        self.widgets()
        self.cargar_nominas()

    def conectar(self):
        return sqlite3.connect('database.db')

    def crear_tabla(self):
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS nominas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado TEXT NOT NULL,
                puesto TEXT,
                periodo TEXT NOT NULL,
                sueldo REAL NOT NULL,
                bonos REAL DEFAULT 0,
                deducciones REAL DEFAULT 0,
                neto REAL NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT NOT NULL,
                notas TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def widgets(self):
        self.crear_header()
        self.crear_formulario()
        self.crear_metricas()
        self.crear_tabla_visual()

    def crear_header(self):
        header = tk.Frame(self, bg=estilos.COLORS['bg_primary'])
        header.place(x=20, y=15, width=1320, height=70)
        tk.Label(header, text="Modulo de Nominas", font=('Poppins', 24, 'bold'),
                 bg=estilos.COLORS['bg_primary'], fg=estilos.COLORS['primary2']).place(x=0, y=0)
        tk.Label(header, text="Registra pagos de empleados, bonos, deducciones y estado de nomina.",
                 font=('Poppins', 11), bg=estilos.COLORS['bg_primary'],
                 fg=estilos.COLORS['dark_gray']).place(x=3, y=42)

    def crear_formulario(self):
        self.form_frame = ctk.CTkFrame(self, width=350, height=610, corner_radius=18,
                                       fg_color=estilos.COLORS['white'], border_width=1,
                                       border_color=estilos.COLORS['border'])
        self.form_frame.place(x=20, y=100)
        ctk.CTkLabel(self.form_frame, text="Nueva nomina",
                     font=ctk.CTkFont(family="Poppins", size=20, weight="bold"),
                     text_color=estilos.COLORS['primary2']).place(x=22, y=18)

        self.empleado = self.crear_entry("Empleado", 74)
        self.puesto = self.crear_entry("Puesto", 132)
        self.periodo = self.crear_entry("Periodo, ej. 2026-07 semana 1", 190)
        self.sueldo = self.crear_entry("Sueldo base", 248)
        self.bonos = self.crear_entry("Bonos", 306)
        self.deducciones = self.crear_entry("Deducciones", 364)
        self.estado = ctk.CTkComboBox(self.form_frame, values=["Pendiente", "Pagada", "Cancelada"],
                                      width=306, height=38, corner_radius=10,
                                      border_color=estilos.COLORS['border'],
                                      fg_color=estilos.COLORS['white'],
                                      button_color=estilos.COLORS['primary2'],
                                      button_hover_color=estilos.COLORS['secondary1'])
        self.estado.set("Pendiente")
        self.estado.place(x=22, y=422)
        self.notas = self.crear_entry("Notas", 480)

        ctk.CTkButton(self.form_frame, text="Registrar nomina", command=self.registrar_nomina,
                      width=146, height=42, corner_radius=12,
                      fg_color=estilos.COLORS['primary2'],
                      hover_color=estilos.COLORS['secondary1'],
                      font=ctk.CTkFont(family="Poppins", size=12, weight="bold")).place(x=22, y=542)
        ctk.CTkButton(self.form_frame, text="Limpiar", command=self.limpiar_campos,
                      width=146, height=42, corner_radius=12,
                      fg_color=estilos.COLORS['dark_gray'],
                      hover_color=estilos.COLORS['gray'],
                      font=ctk.CTkFont(family="Poppins", size=12, weight="bold")).place(x=182, y=542)

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
            ("Nominas", "0", estilos.COLORS['primary2']),
            ("Total neto", "$ 0.00", estilos.COLORS['success']),
            ("Pendientes", "0", estilos.COLORS['warning']),
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

    def crear_tabla_visual(self):
        table_frame = ctk.CTkFrame(self, width=885, height=500, corner_radius=16,
                                   fg_color=estilos.COLORS['white'], border_width=1,
                                   border_color=estilos.COLORS['border'])
        table_frame.place(x=395, y=220)
        columns = ("ID", "Empleado", "Puesto", "Periodo", "Sueldo", "Bonos", "Deducciones", "Neto", "Estado")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.place(x=15, y=15, width=835, height=450)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.place(x=852, y=15, height=450)
        self.tree.configure(yscrollcommand=scroll.set)
        widths = {"ID": 45, "Empleado": 150, "Puesto": 120, "Periodo": 130, "Sueldo": 90,
                  "Bonos": 90, "Deducciones": 95, "Neto": 95, "Estado": 90}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_nomina)

    def widgets(self):
        self.configure(bg='#f5f6f8');self.grid_rowconfigure(1,weight=1);self.grid_columnconfigure(0,weight=1)
        h=tk.Frame(self,bg='#f5f6f8');h.grid(row=0,column=0,sticky='ew');h.grid_columnconfigure(0,weight=1);tk.Label(h,text='Módulo de Nóminas',bg='#f5f6f8',fg='#20242a',font=('Poppins',17,'bold'),anchor='w').grid(row=0,column=0,sticky='ew',padx=18,pady=(8,0));tk.Label(h,text='Pagos, bonos, deducciones y estado de nómina.',bg='#f5f6f8',fg='#68707c',font=('Poppins',9),anchor='w').grid(row=1,column=0,sticky='ew',padx=20,pady=(0,7))
        c=tk.Frame(self,bg='#f5f6f8');c.grid(row=1,column=0,sticky='nsew',padx=14,pady=(4,12));c.grid_rowconfigure(1,weight=1);c.grid_columnconfigure(0,weight=4,minsize=480);c.grid_columnconfigure(1,weight=1,minsize=235)
        f=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');f.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,10));self.form_frame=f
        for col in range(6):f.grid_columnconfigure(col,weight=1,uniform='nomina')
        ctk.CTkLabel(f,text='Datos de nómina',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,columnspan=6,sticky='w',padx=14,pady=(10,6))
        self.empleado=self._campo_nomina('Empleado',0,2);self.puesto=self._campo_nomina('Puesto',2);self.periodo=self._campo_nomina('Periodo',3);self.sueldo=self._campo_nomina('Sueldo base',4);self.bonos=self._campo_nomina('Bonos',5)
        self.deducciones=self._campo_nomina('Deducciones',0,row=2,pady=(8,12));self.notas=self._campo_nomina('Notas',1,2,row=2,pady=(8,12));self.estado=ctk.CTkComboBox(f,values=['Pendiente','Pagada','Cancelada'],height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',text_color='#20242a',dropdown_fg_color='#fff',dropdown_text_color='#20242a',dropdown_hover_color='#f6dede',button_color='#8f070c',button_hover_color='#6f0509',font=ctk.CTkFont(family='Poppins',size=9));self.estado.set('Pendiente');self.estado.grid(row=2,column=3,sticky='ew',padx=6,pady=(8,12))
        ctk.CTkButton(f,text='Registrar nómina',command=self.registrar_nomina,height=34,corner_radius=8,fg_color='#8f070c',hover_color='#6f0509',font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=2,column=4,sticky='ew',padx=6,pady=(8,12));ctk.CTkButton(f,text='Limpiar',command=self.limpiar_campos,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a').grid(row=2,column=5,sticky='ew',padx=(6,14),pady=(8,12))
        lista=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');lista.grid(row=1,column=0,sticky='nsew',padx=(0,10));lista.grid_rowconfigure(2,weight=1);lista.grid_columnconfigure(0,weight=1);ctk.CTkLabel(lista,text='Historial de nóminas',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=14,pady=(10,5));self.busqueda=ctk.CTkEntry(lista,placeholder_text='Buscar empleado, puesto, periodo o estado',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#f7f8fa',text_color='#20242a',placeholder_text_color='#68707c',font=ctk.CTkFont(family='Poppins',size=9));self.busqueda.grid(row=1,column=0,sticky='ew',padx=14,pady=(0,10));self.busqueda.bind('<KeyRelease>',self.filtrar_nominas)
        tf=tk.Frame(lista,bg='#fff');tf.grid(row=2,column=0,sticky='nsew',padx=12,pady=(0,12));tf.grid_rowconfigure(0,weight=1);tf.grid_columnconfigure(0,weight=1);style=ttk.Style();style.configure('Nominas.Treeview',background='#fff',fieldbackground='#fff',foreground='#20242a',rowheight=27,borderwidth=0,font=('Poppins',9));style.configure('Nominas.Treeview.Heading',background='#f0f1f3',foreground='#20242a',font=('Poppins',9,'bold'),relief='flat')
        cols=('ID','Empleado','Puesto','Periodo','Sueldo','Bonos','Deducciones','Neto','Estado');self.tree=ttk.Treeview(tf,columns=cols,show='headings',style='Nominas.Treeview');widths={'ID':45,'Empleado':150,'Puesto':120,'Periodo':130,'Sueldo':90,'Bonos':90,'Deducciones':95,'Neto':95,'Estado':90}
        for col in cols:self.tree.heading(col,text=col);self.tree.column(col,width=widths[col],anchor='w' if col in ('Empleado','Puesto','Periodo') else 'center',stretch=col!='ID')
        sy=ttk.Scrollbar(tf,orient='vertical',command=self.tree.yview);sx=ttk.Scrollbar(tf,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);self.tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');self.tree.bind('<<TreeviewSelect>>',self.seleccionar_nomina)
        r=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');r.grid(row=1,column=1,sticky='nsew');r.grid_columnconfigure(0,weight=1);ctk.CTkLabel(r,text='Resumen',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=16,pady=(14,8));self.metricas={}
        for row,(titulo,valor) in enumerate((('Nominas','0'),('Total neto','$ 0.00'),('Pendientes','0')),1):lab=tk.Label(r,text=f'{titulo}\n{valor}',bg='#fff',fg='#8f070c' if row==1 else '#20242a',font=('Poppins',11,'bold'),justify='left',anchor='w');lab.grid(row=row,column=0,sticky='ew',padx=16,pady=5);self.metricas[titulo]=lab
        ctk.CTkButton(r,text='Actualizar lista',command=self.cargar_nominas,height=34,corner_radius=8,fg_color='#8f070c',hover_color='#6f0509').grid(row=4,column=0,sticky='ew',padx=16,pady=(16,8));ctk.CTkButton(r,text='Limpiar campos',command=self.limpiar_campos,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a').grid(row=5,column=0,sticky='ew',padx=16,pady=(0,16))

    def _campo_nomina(self,placeholder,column,span=1,row=1,pady=(0,6)):
        e=ctk.CTkEntry(self.form_frame,placeholder_text=placeholder,height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',text_color='#20242a',placeholder_text_color='#68707c',font=ctk.CTkFont(family='Poppins',size=9));e.grid(row=row,column=column,columnspan=span,sticky='ew',padx=(14 if column==0 else 6,14 if column+span==6 else 6),pady=pady);return e
    def filtrar_nominas(self,_event=None):
        t=self.busqueda.get().strip().lower();conn=self.conectar();cur=conn.cursor();cur.execute("""SELECT id,empleado,COALESCE(puesto,''),periodo,sueldo,bonos,deducciones,neto,estado FROM nominas WHERE ?='' OR LOWER(COALESCE(empleado,'')) LIKE ? OR LOWER(COALESCE(puesto,'')) LIKE ? OR LOWER(COALESCE(periodo,'')) LIKE ? OR LOWER(COALESCE(estado,'')) LIKE ? ORDER BY id DESC""",(t,*(f'%{t}%',)*4));rows=cur.fetchall();conn.close();self.tree.delete(*self.tree.get_children());[self.tree.insert('', 'end', values=(x[0],x[1],x[2],x[3],f'$ {x[4]:.2f}',f'$ {x[5]:.2f}',f'$ {x[6]:.2f}',f'$ {x[7]:.2f}',x[8])) for x in rows];self.actualizar_metricas(rows)

    def registrar_nomina(self):
        empleado = self.empleado.get().strip()
        puesto = self.puesto.get().strip()
        periodo = self.periodo.get().strip()
        estado = self.estado.get().strip() or "Pendiente"
        notas = self.notas.get().strip()
        try:
            sueldo = float(self.sueldo.get().strip())
            bonos = float(self.bonos.get().strip() or 0)
            deducciones = float(self.deducciones.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Datos invalidos", "Sueldo, bonos y deducciones deben ser numericos.")
            return
        if not empleado or not periodo or sueldo <= 0 or bonos < 0 or deducciones < 0:
            messagebox.showwarning("Campos incompletos", "Empleado, periodo y sueldo mayor a cero son obligatorios.")
            return
        neto = sueldo + bonos - deducciones
        fecha = datetime.now().strftime("%Y-%m-%d")
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO nominas (empleado, puesto, periodo, sueldo, bonos, deducciones, neto, fecha, estado, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (empleado, puesto, periodo, sueldo, bonos, deducciones, neto, fecha, estado, notas))
        conn.commit()
        conn.close()
        self.limpiar_campos()
        self.cargar_nominas()
        messagebox.showinfo("Nomina registrada", "La nomina se guardo correctamente.")

    def cargar_nominas(self):
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, empleado, COALESCE(puesto, ''), periodo, sueldo, bonos, deducciones, neto, estado
            FROM nominas
            ORDER BY id DESC
        ''')
        rows = cur.fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            id_, empleado, puesto, periodo, sueldo, bonos, deducciones, neto, estado = row
            self.tree.insert("", "end", values=(id_, empleado, puesto, periodo,
                                                f"$ {sueldo:.2f}", f"$ {bonos:.2f}",
                                                f"$ {deducciones:.2f}", f"$ {neto:.2f}", estado))
        self.actualizar_metricas(rows)

    def actualizar_metricas(self, rows):
        self.metricas["Nominas"].configure(text=f"Nóminas\n{len(rows)}")
        self.metricas["Total neto"].configure(text=f"Total neto\n$ {sum(float(r[7] or 0) for r in rows):.2f}")
        self.metricas["Pendientes"].configure(text=f"Pendientes\n{sum(1 for r in rows if str(r[8]).lower() != 'pagada')}")

    def seleccionar_nomina(self, _event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], "values")
        self.nomina_seleccionada = valores[0]
        self.limpiar_campos(mantener_seleccion=True)
        self.empleado.insert(0, valores[1])
        self.puesto.insert(0, valores[2])
        self.periodo.insert(0, valores[3])
        self.sueldo.insert(0, str(valores[4]).replace("$", "").strip())
        self.bonos.insert(0, str(valores[5]).replace("$", "").strip())
        self.deducciones.insert(0, str(valores[6]).replace("$", "").strip())
        self.estado.set(valores[8])

    def limpiar_campos(self, mantener_seleccion=False):
        for entry in (self.empleado, self.puesto, self.periodo, self.sueldo, self.bonos, self.deducciones, self.notas):
            entry.delete(0, tk.END)
        self.estado.set("Pendiente")
        if not mantener_seleccion:
            self.nomina_seleccionada = None

