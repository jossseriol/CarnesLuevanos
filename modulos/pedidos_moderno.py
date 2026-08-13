import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from modulos.utils.estilos_modernos import estilos
from datetime import datetime

# Configurar CustomTkinter
ctk.set_appearance_mode("light")

class PedidosModerno(tk.Frame):
    
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.crear_tablas()
        self.widgets()
        # Cargar datos iniciales si las funciones existen
        if hasattr(self, 'cargar_pedidos'):
            self.cargar_pedidos()
        if hasattr(self, 'cargar_proveedores'):
            self.cargar_proveedores()
    
    def actualizar_moneda(self, nueva_moneda):
        """Actualizar precios cuando cambia la moneda"""
        try:
            # Recargar pedidos con nueva moneda
            self.cargar_pedidos()
            print(f"Módulo Pedidos actualizado a moneda: {nueva_moneda}")
        except Exception as e:
            print(f"Error al actualizar moneda en Pedidos: {e}")
        
    def crear_tablas(self):
        """Crear tablas de pedidos y detalles si no existen"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Tabla de pedidos a proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pedidos_proveedor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proveedor_nombre TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    estado TEXT DEFAULT 'Pendiente',
                    total REAL DEFAULT 0.0,
                    observaciones TEXT
                )
            ''')
            
            # Tabla de detalles de pedidos (productos solicitados)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pedidos_detalle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER,
                    producto_codigo TEXT NOT NULL,
                    producto_nombre TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL DEFAULT 0.0,
                    subtotal REAL DEFAULT 0.0,
                    FOREIGN KEY (pedido_id) REFERENCES pedidos_proveedor (id)
                )
            ''')
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al crear tablas: {e}")
        
    def widgets(self):
        # Frame principal de formulario
        form_frame = tk.LabelFrame(self, text="📦 Pedidos a Proveedores", 
                                  font=('Poppins', 16, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        form_frame.place(x=20, y=20, width=320, height=720)

        # Título del formulario
        title_label = tk.Label(form_frame, text="📝 Pedido de Reposición", 
                              font=('Poppins', 14, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['secondary'])
        title_label.place(x=10, y=10)

        # Campo Proveedor
        tk.Label(form_frame, text="🏢 Proveedor:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=50)
        
        self.proveedor_entry = tk.Entry(form_frame, font=('Poppins', 11), relief='solid', bd=1)
        self.proveedor_entry.place(x=10, y=80, width=290, height=35)

        # Campo Estado
        tk.Label(form_frame, text="📊 Estado:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=130)
        
        self.estado_combo = ttk.Combobox(form_frame, font=('Poppins', 11), 
                                        values=["Pendiente", "En Proceso", "Completado", "Cancelado"],
                                        state="readonly")
        self.estado_combo.set("Pendiente")
        self.estado_combo.place(x=10, y=160, width=290, height=35)

        # Campo Producto a Pedir
        tk.Label(form_frame, text="📦 Producto:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=210)
        
        self.producto_combo = ttk.Combobox(form_frame, font=('Poppins', 11), state="readonly")
        self.producto_combo.place(x=10, y=240, width=290, height=35)
        self.cargar_productos()
        
        # Campo Cantidad
        tk.Label(form_frame, text="🔢 Cantidad:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=290)
        
        self.cantidad = tk.Entry(form_frame, font=('Poppins', 12), relief='solid', bd=1)
        self.cantidad.place(x=10, y=320, width=140, height=35)
        
        # Campo Precio Unitario
        tk.Label(form_frame, text="💰 Precio:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=160, y=290)
        
        self.precio = tk.Entry(form_frame, font=('Poppins', 12), relief='solid', bd=1)
        self.precio.place(x=160, y=320, width=140, height=35)

        # Campo Observaciones
        tk.Label(form_frame, text="📝 Observaciones:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white'],
                fg=estilos.COLORS['dark']).place(x=10, y=370)
        
        self.observaciones = tk.Text(form_frame, font=('Poppins', 10), 
                                   relief='solid', bd=1, wrap='word')
        self.observaciones.place(x=10, y=400, width=290, height=60)

        # Botones modernos
        btn_crear = ctk.CTkButton(
            form_frame, 
            text="➕ Crear Pedido", 
            command=self.crear_pedido,
            width=290,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
            fg_color=estilos.COLORS['success'],
            hover_color="#8f070c"
        )
        btn_crear.place(x=10, y=480)

        btn_modificar = ctk.CTkButton(
            form_frame, 
            text="✏️ Modificar Estado", 
            command=self.modificar_pedido,
            width=290,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
            fg_color=estilos.COLORS['warning'],
            hover_color="#d7b56d"
        )
        btn_modificar.place(x=10, y=540)

        btn_recibir = ctk.CTkButton(
            form_frame, 
            text="📥 Recibir Pedido", 
            command=self.recibir_pedido,
            width=290,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
            fg_color=estilos.COLORS['info'],
            hover_color="#b30d12"
        )
        btn_recibir.place(x=10, y=600)
        
        # Etiqueta de estadísticas dentro del form_frame
        self.stats_label = tk.Label(form_frame, text="Total pedidos: 0", 
                                   font=('Poppins', 10, 'bold'), 
                                   bg=estilos.COLORS['white'],
                                   fg=estilos.COLORS['primary'])
        self.stats_label.place(x=10, y=660)

        # Frame para la tabla
        table_frame = tk.LabelFrame(self, text="📋 Lista de Pedidos", 
                                   font=('Poppins', 16, 'bold'), 
                                   bg=estilos.COLORS['white'],
                                   fg=estilos.COLORS['primary'])
        table_frame.place(x=360, y=20, width=860, height=720)

        # Configurar Treeview
        style = ttk.Style()
        style.theme_use('clam')
        
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
                                columns=("ID", "Cliente", "Fecha", "Estado", "Total", "Observaciones"), 
                                show="headings",
                                height=30)

        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # Configurar encabezados
        self.tree.heading("ID", text="🆔 ID")
        self.tree.heading("Cliente", text="🏢 Proveedor")
        self.tree.heading("Fecha", text="📅 Fecha")
        self.tree.heading("Estado", text="📊 Estado")
        self.tree.heading("Total", text="💰 Total")
        self.tree.heading("Observaciones", text="📝 Observaciones")

        # Configurar columnas
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Cliente", width=150, anchor="w")
        self.tree.column("Fecha", width=120, anchor="center")
        self.tree.column("Estado", width=100, anchor="center")
        self.tree.column("Total", width=100, anchor="e")
        self.tree.column("Observaciones", width=200, anchor="w")

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    def widgets(self):
        self.configure(bg='#f5f6f8');self.grid_rowconfigure(1,weight=1);self.grid_columnconfigure(0,weight=1)
        header=tk.Frame(self,bg='#f5f6f8',height=54);header.grid(row=0,column=0,sticky='ew');header.grid_columnconfigure(0,weight=1)
        tk.Label(header,text='Módulo de Pedidos',bg='#f5f6f8',fg='#20242a',font=('Poppins',17,'bold'),anchor='w').grid(row=0,column=0,sticky='ew',padx=18,pady=(8,0))
        tk.Label(header,text='Solicitudes a proveedores, recepción y seguimiento.',bg='#f5f6f8',fg='#68707c',font=('Poppins',9),anchor='w').grid(row=1,column=0,sticky='ew',padx=20,pady=(0,7))
        content=tk.Frame(self,bg='#f5f6f8');content.grid(row=1,column=0,sticky='nsew',padx=14,pady=(4,12));content.grid_rowconfigure(1,weight=1);content.grid_columnconfigure(0,weight=4,minsize=480);content.grid_columnconfigure(1,weight=1,minsize=235)
        form=ctk.CTkFrame(content,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');form.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,10))
        for col in range(6):form.grid_columnconfigure(col,weight=1,uniform='pedido')
        ctk.CTkLabel(form,text='Datos del pedido',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,columnspan=6,sticky='w',padx=14,pady=(10,6))
        self.proveedor_entry=self._entry_pedido(form,'Proveedor',0,2)
        self.estado_combo=ttk.Combobox(form,values=['Pendiente','En Proceso','Completado','Cancelado'],state='readonly',font=('Poppins',9));self.estado_combo.set('Pendiente');self.estado_combo.grid(row=1,column=2,sticky='ew',padx=6,pady=(0,6),ipady=5)
        self.producto_combo=ttk.Combobox(form,state='readonly',font=('Poppins',9));self.producto_combo.grid(row=1,column=3,sticky='ew',padx=6,pady=(0,6),ipady=5)
        self.cantidad=self._entry_pedido(form,'Cantidad',4);self.precio=self._entry_pedido(form,'Precio unitario',5)
        self.observaciones=tk.Text(form,font=('Poppins',9),height=2,relief='flat',bd=0,highlightthickness=1,highlightbackground='#e3e6ea',highlightcolor='#8f070c');self.observaciones.grid(row=2,column=0,columnspan=3,sticky='ew',padx=(14,6),pady=(8,12))
        ctk.CTkButton(form,text='Crear pedido',command=self.crear_pedido,height=34,corner_radius=8,fg_color='#8f070c',hover_color='#6f0509',font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=2,column=3,sticky='ew',padx=6,pady=(8,12))
        ctk.CTkButton(form,text='Modificar',command=self.modificar_pedido,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=2,column=4,sticky='ew',padx=6,pady=(8,12))
        ctk.CTkButton(form,text='Limpiar',command=self.limpiar_campos,height=34,corner_radius=8,fg_color='#eef0f2',hover_color='#dfe2e6',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=2,column=5,sticky='ew',padx=(6,14),pady=(8,12))
        lista=ctk.CTkFrame(content,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');lista.grid(row=1,column=0,sticky='nsew',padx=(0,10));lista.grid_rowconfigure(2,weight=1);lista.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(lista,text='Lista de pedidos',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=14,pady=(10,5))
        self.busqueda=ctk.CTkEntry(lista,placeholder_text='Buscar proveedor, fecha, estado u observaciones',height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#f7f8fa',font=ctk.CTkFont(family='Poppins',size=9));self.busqueda.grid(row=1,column=0,sticky='ew',padx=14,pady=(0,10));self.busqueda.bind('<KeyRelease>',self.filtrar_pedidos)
        tf=tk.Frame(lista,bg='#fff');tf.grid(row=2,column=0,sticky='nsew',padx=12,pady=(0,12));tf.grid_rowconfigure(0,weight=1);tf.grid_columnconfigure(0,weight=1)
        style=ttk.Style();style.configure('Pedidos.Treeview',background='#fff',fieldbackground='#fff',foreground='#20242a',rowheight=27,borderwidth=0,font=('Poppins',9));style.configure('Pedidos.Treeview.Heading',background='#f0f1f3',foreground='#20242a',font=('Poppins',9,'bold'),relief='flat');style.map('Pedidos.Treeview',background=[('selected','#f6dede')],foreground=[('selected','#20242a')])
        cols=('ID','Cliente','Fecha','Estado','Total','Observaciones');self.tree=ttk.Treeview(tf,columns=cols,show='headings',style='Pedidos.Treeview');widths={'ID':50,'Cliente':170,'Fecha':105,'Estado':105,'Total':100,'Observaciones':230};titles={'ID':'ID','Cliente':'Proveedor','Fecha':'Fecha','Estado':'Estado','Total':'Total','Observaciones':'Observaciones'}
        for col in cols:self.tree.heading(col,text=titles[col]);self.tree.column(col,width=widths[col],anchor='w' if col in ('Cliente','Observaciones') else 'center',stretch=col!='ID')
        sy=ttk.Scrollbar(tf,orient='vertical',command=self.tree.yview);sx=ttk.Scrollbar(tf,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);self.tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');self.tree.bind('<<TreeviewSelect>>',self.on_select)
        resumen=ctk.CTkFrame(content,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');resumen.grid(row=1,column=1,sticky='nsew');resumen.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(resumen,text='Resumen',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=16,pady=(14,8))
        self.stats_label=tk.Label(resumen,text='Total pedidos: 0',bg='#fff',fg='#8f070c',font=('Poppins',13,'bold'),anchor='w');self.stats_label.grid(row=1,column=0,sticky='ew',padx=16,pady=(4,16))
        tk.Label(resumen,text='Selecciona un pedido para modificarlo o marcarlo como recibido.',bg='#fff',fg='#68707c',font=('Poppins',8),justify='left',wraplength=190,anchor='w').grid(row=2,column=0,sticky='ew',padx=16,pady=(0,18))
        for row,(text,cmd,color,fg) in enumerate((('Recibir pedido',self.recibir_pedido,'#8f070c','#fff'),('Modificar seleccionado',self.modificar_pedido,'#eef0f2','#20242a'),('Actualizar lista',self.cargar_registros,'#eef0f2','#20242a')),3):ctk.CTkButton(resumen,text=text,command=cmd,height=34,corner_radius=8,fg_color=color,hover_color='#6f0509' if color=='#8f070c' else '#dfe2e6',text_color=fg,font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=row,column=0,sticky='ew',padx=16,pady=(0,8 if row<5 else 16))

    def _entry_pedido(self,parent,placeholder,column,span=1):
        e=ctk.CTkEntry(parent,placeholder_text=placeholder,height=34,corner_radius=8,border_color='#e3e6ea',fg_color='#fff',font=ctk.CTkFont(family='Poppins',size=9));e.grid(row=1,column=column,columnspan=span,sticky='ew',padx=(14 if column==0 else 6,14 if column+span==6 else 6),pady=(0,6));return e

    def filtrar_pedidos(self,_event=None):
        texto=self.busqueda.get().strip().lower();conn=sqlite3.connect('database.db');cur=conn.cursor();cur.execute("""SELECT id,proveedor_nombre,fecha,estado,total,COALESCE(observaciones,'') FROM pedidos_proveedor WHERE ?='' OR LOWER(COALESCE(proveedor_nombre,'')) LIKE ? OR LOWER(COALESCE(fecha,'')) LIKE ? OR LOWER(COALESCE(estado,'')) LIKE ? OR LOWER(COALESCE(observaciones,'')) LIKE ? ORDER BY id DESC""",(texto,*(f'%{texto}%',)*4));rows=cur.fetchall();conn.close();self.limpiar_treeview();[self.tree.insert('', 'end', values=(r[0],r[1],r[2],r[3],f'${float(r[4] or 0):,.2f}',r[5])) for r in rows];self.stats_label.config(text=f'Resultados: {len(rows)}')

    def cargar_productos(self):
        """Cargar productos en el combobox"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nombre FROM productos ORDER BY nombre")
            productos = cursor.fetchall()
            
            producto_list = [f"{producto[0]} - {producto[1]}" for producto in productos]
            self.producto_combo['values'] = producto_list
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar productos: {e}")

    def crear_pedido(self):
        """Crear un nuevo pedido a proveedor"""
        if not self.proveedor_entry.get().strip():
            messagebox.showerror("❌ Error", "Debe ingresar el nombre del proveedor")
            return
        
        if not self.producto_combo.get():
            messagebox.showerror("❌ Error", "Debe seleccionar un producto")
            return
            
        if not self.cantidad.get().strip() or not self.precio.get().strip():
            messagebox.showerror("❌ Error", "Debe ingresar cantidad y precio")
            return

        try:
            # Extraer información del producto
            producto_info = self.producto_combo.get()
            producto_codigo = producto_info.split(' - ')[0]
            producto_nombre = producto_info.split(' - ')[1]
            
            proveedor_nombre = self.proveedor_entry.get().strip()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            estado = self.estado_combo.get()
            cantidad = int(self.cantidad.get())
            precio_unitario = float(self.precio.get())
            subtotal = cantidad * precio_unitario
            observaciones = self.observaciones.get("1.0", "end-1c")

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Crear pedido principal
            cursor.execute("""INSERT INTO pedidos_proveedor (proveedor_nombre, fecha, estado, total, observaciones) 
                            VALUES (?,?,?,?,?)""", 
                          (proveedor_nombre, fecha, estado, subtotal, observaciones))
            
            pedido_id = cursor.lastrowid
            
            # Crear detalle del pedido
            cursor.execute("""INSERT INTO pedidos_detalle (pedido_id, producto_codigo, producto_nombre, 
                            cantidad, precio_unitario, subtotal) VALUES (?,?,?,?,?,?)""", 
                          (pedido_id, producto_codigo, producto_nombre, cantidad, precio_unitario, subtotal))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✅ Éxito", f"Pedido creado correctamente\nTotal: ${subtotal:.2f}")
            self.limpiar_campos()
            self.limpiar_treeview()
            self.cargar_registros()

        except ValueError:
            messagebox.showerror("❌ Error", "Cantidad y precio deben ser números válidos")
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al crear pedido: {e}")

    def cargar_registros(self):
        """Cargar todos los pedidos"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pedidos_proveedor ORDER BY fecha DESC")
            rows = cursor.fetchall()
            
            for row in rows:
                # Formatear el total como moneda
                total_formateado = f"${row[4]:.2f}"
                row_formateada = list(row)
                row_formateada[4] = total_formateado
                self.tree.insert("", "end", values=row_formateada)
            
            if hasattr(self, 'stats_label'):
                self.stats_label.config(text=f"Total pedidos: {len(rows)}")
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar pedidos: {e}")

    def limpiar_treeview(self):
        """Limpiar el Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def limpiar_campos(self):
        """Limpiar todos los campos"""
        self.proveedor_entry.delete(0, 'end')
        self.producto_combo.set("")
        self.estado_combo.set("Pendiente")
        self.cantidad.delete(0, 'end')
        self.precio.delete(0, 'end')
        self.observaciones.delete("1.0", 'end')

    def on_select(self, event):
        """Manejar selección en el Treeview"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            
            if len(values) >= 6:
                # Llenar campos con datos del pedido seleccionado
                self.proveedor_entry.delete(0, 'end')
                self.proveedor_entry.insert(0, values[1])  # Proveedor
                self.estado_combo.set(values[3])  # Estado
                self.observaciones.delete("1.0", 'end')
                self.observaciones.insert("1.0", values[5])  # Observaciones
                
                # Cargar detalles del pedido
                self.cargar_detalle_pedido(values[0])  # ID del pedido

    def modificar_pedido(self):
        """Modificar estado del pedido seleccionado"""
        if not self.tree.selection():
            messagebox.showerror("❌ Error", "Seleccione un pedido para modificar")
            return

        try:
            item = self.tree.selection()[0]
            pedido_id = self.tree.item(item, "values")[0]
            nuevo_estado = self.estado_combo.get()
            observaciones = self.observaciones.get("1.0", "end-1c")

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""UPDATE pedidos_proveedor SET estado=?, observaciones=? WHERE id=?""", 
                          (nuevo_estado, observaciones, pedido_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✅ Éxito", f"Estado del pedido actualizado a: {nuevo_estado}")
            self.limpiar_campos()
            self.limpiar_treeview()
            self.cargar_registros()

        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al modificar pedido: {e}")

    def recibir_pedido(self):
        """Recibir pedido y actualizar inventario"""
        if not self.tree.selection():
            messagebox.showerror("❌ Error", "Seleccione un pedido para recibir")
            return

        item = self.tree.selection()[0]
        pedido_id = self.tree.item(item, "values")[0]
        proveedor_nombre = self.tree.item(item, "values")[1]
        estado_actual = self.tree.item(item, "values")[3]
        
        if estado_actual == "Completado":
            messagebox.showwarning("⚠️ Advertencia", "Este pedido ya fue recibido")
            return
        
        respuesta = messagebox.askyesno("📥 Confirmar Recepción", 
                                      f"¿Marcar como recibido el pedido del proveedor '{proveedor_nombre}'?\n\nEsto actualizará el inventario automáticamente.")
        
        if respuesta:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                
                # Obtener detalles del pedido
                cursor.execute("SELECT producto_codigo, cantidad FROM pedidos_detalle WHERE pedido_id=?", (pedido_id,))
                detalles = cursor.fetchall()
                
                # Actualizar inventario para cada producto
                for detalle in detalles:
                    producto_codigo, cantidad = detalle
                    cursor.execute("""UPDATE productos SET stock = stock + ? WHERE codigo = ?""", 
                                 (cantidad, producto_codigo))
                
                # Marcar pedido como completado
                cursor.execute("UPDATE pedidos_proveedor SET estado='Completado' WHERE id=?", (pedido_id,))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("✅ Éxito", f"Pedido recibido correctamente\nInventario actualizado para {len(detalles)} producto(s)")
                self.limpiar_campos()
                self.limpiar_treeview()
                self.cargar_registros()
                
            except sqlite3.Error as e:
                messagebox.showerror("❌ Error", f"Error al recibir pedido: {e}")
    
    def cargar_detalle_pedido(self, pedido_id):
        """Cargar el primer producto del pedido en el formulario"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""SELECT producto_codigo, producto_nombre, cantidad, precio_unitario 
                            FROM pedidos_detalle WHERE pedido_id=? LIMIT 1""", (pedido_id,))
            detalle = cursor.fetchone()
            
            if detalle:
                producto_codigo, producto_nombre, cantidad, precio_unitario = detalle
                # Buscar el producto en el combo
                producto_texto = f"{producto_codigo} - {producto_nombre}"
                for producto in self.producto_combo['values']:
                    if producto_codigo in producto:
                        self.producto_combo.set(producto)
                        break
                
                self.cantidad.delete(0, 'end')
                self.cantidad.insert(0, str(cantidad))
                self.precio.delete(0, 'end')
                self.precio.insert(0, str(precio_unitario))
            
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al cargar detalle: {e}")


