import sqlite3
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
from modulos.utils.utils import generar_qr_producto
from modulos.utils.estilos_modernos import estilos
import threading
import sys
import os

# Configurar CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class InventarioSimple(tk.Frame):
    
    def __init__(self, padre):
        super().__init__(padre)
        self.configure(bg=estilos.COLORS['bg_primary'])
        self.widgets()
        self.articulos_combobox()
        self.cargar_articulos()
        self.timer_articulos = None
        
        self.image_folder = 'media/img/img_productos'
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
    
    def actualizar_moneda(self, nueva_moneda):
        """Actualizar precios cuando cambia la moneda"""
        try:
            # Recargar artículos con nueva moneda
            self.cargar_articulos()
            print(f"Módulo Inventario actualizado a moneda: {nueva_moneda}")
        except Exception as e:
            print(f"Error al actualizar moneda en Inventario: {e}")
        
    def widgets(self):
        # Frame principal de artículos (ancho optimizado para 4 columnas)
        canvas_articulos = tk.LabelFrame(self, text="📦 Inventario de Productos", 
                                        font=('Poppins', 15, 'bold'), 
                                        bg=estilos.COLORS['white'])
        canvas_articulos.place(x=300, y=10, width=1100, height=740)
        
        # Canvas scrollable con configuración mejorada
        self.canvas = tk.Canvas(canvas_articulos, bg=estilos.COLORS['white'], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(canvas_articulos, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=estilos.COLORS['white'])
        
        # Configurar el scroll correctamente
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Crear ventana en el canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Configurar eventos de scroll con mouse
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        # Bind eventos de mouse
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Configurar el ancho del frame interno
        def configure_scroll_region(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Ajustar el ancho del frame interno al ancho del canvas
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.canvas.bind('<Configure>', configure_scroll_region)
        
        # Empaquetar elementos
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Frame de búsqueda
        search_frame = tk.LabelFrame(self, text="🔍 Buscar", 
                                   font=('Poppins', 14, 'bold'), 
                                   bg=estilos.COLORS['white'])
        search_frame.place(x=5, y=10, width=280, height=80)
        
        self.comboboxbuscar = ttk.Combobox(search_frame, font=('Poppins', 12))
        self.comboboxbuscar.place(x=5, y=5, width=260, height=40)
        self.comboboxbuscar.bind('<<ComboboxSelected>>', self.on_combobox_select)
        self.comboboxbuscar.bind('<KeyRelease>', self.filtrar_articulos)
        
        # Frame de información
        info_frame = tk.LabelFrame(self, text='📋 Información del Producto', 
                                 font=('Poppins', 12, 'bold'), 
                                 bg=estilos.COLORS['white'])
        info_frame.place(x=10, y=95, width=280, height=240)
        
        self.label1 = tk.Label(info_frame, text='Artículo: --', 
                              font=('Poppins', 12, 'bold'), 
                              bg=estilos.COLORS['white'], 
                              wraplength=250, anchor='w')
        self.label1.place(x=5, y=5)
        
        self.label2 = tk.Label(info_frame, text='Precio: --', 
                              font=('Poppins', 12, 'bold'), 
                              bg=estilos.COLORS['white'])
        self.label2.place(x=5, y=40)
        
        self.label3 = tk.Label(info_frame, text='Código: --', 
                              font=('Poppins', 12, 'bold'), 
                              bg=estilos.COLORS['white'])
        self.label3.place(x=5, y=75)
        
        self.label4 = tk.Label(info_frame, text='Stock: --', 
                              font=('Poppins', 12, 'bold'), 
                              bg=estilos.COLORS['white'])
        self.label4.place(x=5, y=110)
        
        self.label5 = tk.Label(info_frame, text='Estado: --', 
                              font=('Poppins', 12, 'bold'), 
                              bg=estilos.COLORS['white'])
        self.label5.place(x=5, y=145)
        
        # Frame de botones con CustomTkinter
        buttons_frame = tk.LabelFrame(self, text="⚙️ Opciones", 
                                    font=('Poppins', 14, 'bold'), 
                                    bg=estilos.COLORS['white'])
        buttons_frame.place(x=10, y=350, width=280, height=250)
        
        # Botones modernos
        btn1 = ctk.CTkButton(
            buttons_frame, 
            text="➕ Agregar Producto", 
            command=self.agregar_articulo,
            width=240,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['success'],
            hover_color="#8f070c"
        )
        btn1.place(x=20, y=20)
        
        btn2 = ctk.CTkButton(
            buttons_frame, 
            text="✏️ Editar Producto", 
            command=self.editar_articulo,
            width=240,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['warning'],
            hover_color="#d7b56d"
        )
        btn2.place(x=20, y=80)

        btn3 = ctk.CTkButton(
            buttons_frame, 
            text="🏷️ Imprimir Etiqueta", 
            command=self.imprimir_etiqueta,
            width=240,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['secondary'],
            hover_color="#5a4b48"
        )
        btn3.place(x=20, y=140)
    
    def widgets(self):
        self.configure(bg='#f5f6f8');self.grid_rowconfigure(1,weight=1);self.grid_columnconfigure(0,weight=1)
        h=tk.Frame(self,bg='#f5f6f8');h.grid(row=0,column=0,sticky='ew');h.grid_columnconfigure(0,weight=1);tk.Label(h,text='Módulo de Inventario',bg='#f5f6f8',fg='#20242a',font=('Poppins',17,'bold'),anchor='w').grid(row=0,column=0,sticky='ew',padx=18,pady=(8,0));tk.Label(h,text='Productos, existencias, precios y etiquetas.',bg='#f5f6f8',fg='#68707c',font=('Poppins',9),anchor='w').grid(row=1,column=0,sticky='ew',padx=20,pady=(0,7))
        c=tk.Frame(self,bg='#f5f6f8');c.grid(row=1,column=0,sticky='nsew',padx=14,pady=(4,12));c.grid_rowconfigure(0,weight=1);c.grid_columnconfigure(0,weight=4,minsize=480);c.grid_columnconfigure(1,weight=1,minsize=235)
        lista=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');lista.grid(row=0,column=0,sticky='nsew',padx=(0,10));lista.grid_rowconfigure(2,weight=1);lista.grid_columnconfigure(0,weight=1);ctk.CTkLabel(lista,text='Catálogo de productos',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=14,pady=(10,5))
        self.comboboxbuscar=ttk.Combobox(lista,font=('Poppins',9));self.comboboxbuscar.grid(row=1,column=0,sticky='ew',padx=14,pady=(0,10),ipady=5);self.comboboxbuscar.bind('<<ComboboxSelected>>',self.on_combobox_select);self.comboboxbuscar.bind('<KeyRelease>',self.filtrar_articulos)
        cf=tk.Frame(lista,bg='#fff');cf.grid(row=2,column=0,sticky='nsew',padx=8,pady=(0,10));cf.grid_rowconfigure(0,weight=1);cf.grid_columnconfigure(0,weight=1)
        self.canvas=tk.Canvas(cf,bg='#fff',highlightthickness=0);self.scrollbar=tk.Scrollbar(cf,orient='vertical',command=self.canvas.yview);self.scrollable_frame=tk.Frame(self.canvas,bg='#fff');self.canvas_window=self.canvas.create_window((0,0),window=self.scrollable_frame,anchor='nw');self.canvas.configure(yscrollcommand=self.scrollbar.set);self.canvas.grid(row=0,column=0,sticky='nsew');self.scrollbar.grid(row=0,column=1,sticky='ns');self.scrollable_frame.bind('<Configure>',lambda _e:self.canvas.configure(scrollregion=self.canvas.bbox('all')));self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfig(self.canvas_window,width=e.width))
        side=ctk.CTkFrame(c,fg_color='#fff',corner_radius=12,border_width=1,border_color='#e3e6ea');side.grid(row=0,column=1,sticky='nsew');side.grid_columnconfigure(0,weight=1);ctk.CTkLabel(side,text='Producto seleccionado',fg_color='transparent',bg_color='#fff',text_color='#20242a',font=ctk.CTkFont(family='Poppins',size=11,weight='bold')).grid(row=0,column=0,sticky='w',padx=16,pady=(14,10))
        self.label1=self._info_inventario(side,'Artículo: --',1);self.label2=self._info_inventario(side,'Precio: --',2);self.label3=self._info_inventario(side,'Código: --',3);self.label4=self._info_inventario(side,'Stock: --',4);self.label5=self._info_inventario(side,'Estado: --',5)
        for row,(text,cmd,color,fg) in enumerate((('Agregar producto',self.agregar_articulo,'#8f070c','#fff'),('Editar producto',self.editar_articulo,'#eef0f2','#20242a'),('Imprimir etiqueta',self.imprimir_etiqueta,'#eef0f2','#20242a'),('Actualizar catálogo',self.cargar_articulos,'#eef0f2','#20242a')),6):ctk.CTkButton(side,text=text,command=cmd,height=34,corner_radius=8,fg_color=color,hover_color='#6f0509' if color=='#8f070c' else '#dfe2e6',text_color=fg,font=ctk.CTkFont(family='Poppins',size=9,weight='bold')).grid(row=row,column=0,sticky='ew',padx=16,pady=(12 if row==6 else 0,8))
        def wheel(e):self.canvas.yview_scroll(int(-1*(e.delta/120)),'units')
        self.canvas.bind('<Enter>',lambda _e:self.canvas.bind_all('<MouseWheel>',wheel));self.canvas.bind('<Leave>',lambda _e:self.canvas.unbind_all('<MouseWheel>'))
        for delay in (0, 200, 600):
            self.after(delay, self._aplicar_modo_claro_inventario)

    def _info_inventario(self,parent,text,row):
        label=tk.Label(parent,text=text,bg='#fff',fg='#20242a',font=('Poppins',9,'bold'),anchor='w',wraplength=195);label.grid(row=row,column=0,sticky='ew',padx=16,pady=5);return label

    def _aplicar_modo_claro_inventario(self):
        """Mantiene claro el área del catálogo en modo claro."""
        for widget in (getattr(self, 'canvas', None), getattr(self, 'scrollable_frame', None)):
            if widget is not None:
                try:
                    widget.configure(bg='#ffffff')
                except Exception:
                    pass

    def articulos_combobox(self):
        try:
            self.conn = sqlite3.connect('database.db')
            self.cur = self.conn.cursor()
            self.cur.execute("SELECT articulo FROM articulos WHERE estado = 'activo'")
            self.articulos = [row[0] for row in self.cur.fetchall()]
            self.comboboxbuscar['values'] = self.articulos
        except sqlite3.Error as e:
            print(f"Error cargando artículos para combobox: {e}")
            self.articulos = []
    
    def agregar_articulo(self):
        """Ventana para agregar un nuevo producto"""
        top = tk.Toplevel(self)
        top.title("➕ Agregar Nuevo Producto")
        top.geometry("700x500+200+50")
        top.configure(bg=estilos.COLORS['white'])
        top.resizable(False, False)
        
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()
        
        # Título
        title_label = tk.Label(top, text="➕ Agregar Nuevo Producto", 
                              font=('Poppins', 16, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=15)
        
        # Frame principal
        main_frame = tk.Frame(top, bg=estilos.COLORS['white'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Campos de entrada
        tk.Label(main_frame, text="Código de Barras:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=20)
        entry_codigo = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_codigo.place(x=180, y=20)
        
        tk.Label(main_frame, text="Nombre del Artículo:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=60)
        entry_articulo = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_articulo.place(x=180, y=60)
        
        tk.Label(main_frame, text="Precio de Venta:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=100)
        entry_precio = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_precio.place(x=180, y=100)
        
        tk.Label(main_frame, text="Costo del Producto:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=140)
        entry_costo = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_costo.place(x=180, y=140)
        
        tk.Label(main_frame, text="Stock Inicial:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=180)
        entry_stock = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_stock.place(x=180, y=180)
        
        # Frame para imagen
        self.frameimg = tk.Frame(main_frame, bg='lightgray', relief='solid', bd=1)
        self.frameimg.place(x=480, y=30, width=180, height=180)
        
        img_placeholder = tk.Label(self.frameimg, text="📷\nImagen del\nProducto", 
                                  font=('Poppins', 12), bg='lightgray')
        img_placeholder.pack(expand=True)
        
        # Botón para cargar imagen
        btn_imagen = ctk.CTkButton(main_frame, text='📁 Cargar Imagen', 
                                  font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                  command=self.load_image, width=180, height=35)
        btn_imagen.place(x=480, y=230)
        
        def guardar():
            codigo = entry_codigo.get().strip()
            articulo = entry_articulo.get().strip()
            precio = entry_precio.get().strip()
            costo = entry_costo.get().strip()
            stock = entry_stock.get().strip()
            
            # Validaciones
            if not all([codigo, articulo, precio, costo, stock]):
                messagebox.showerror("❌ Error", "Todos los campos deben ser completados")
                return
            
            try:
                precio_float = float(precio)
                costo_float = float(costo)
                stock_int = int(stock)
                
                if precio_float <= 0 or costo_float <= 0 or stock_int < 0:
                    messagebox.showerror("❌ Error", "Los valores deben ser positivos")
                    return
                    
            except ValueError:
                messagebox.showerror("❌ Error", "Precio, costo y stock deben ser números válidos")
                return
            
            # Verificar si el código ya existe
            try:
                self.cur.execute("SELECT codigo FROM articulos WHERE codigo = ?", (codigo,))
                if self.cur.fetchone():
                    messagebox.showerror("❌ Error", f"El código '{codigo}' ya existe")
                    return
            except sqlite3.Error:
                pass
            
            # Imagen por defecto si no se cargó una
            imagen_path = getattr(self, 'image_path', 'media/icons/img_default.png')
            
            try:
                # Insertar el nuevo producto
                self.cur.execute("""INSERT INTO articulos 
                               (codigo, articulo, precio, costo, stock, estado, imagen_path) 
                               VALUES (?, ?, ?, ?, ?, 'activo', ?)""", 
                               (codigo, articulo, precio_float, costo_float, stock_int, imagen_path))
                self.conn.commit()
                
                messagebox.showinfo('✅ Éxito', f'Producto "{articulo}" agregado correctamente')
                top.destroy()
                
                # Recargar la vista
                self.cargar_articulos()
                self.articulos_combobox()
                
            except sqlite3.Error as e:
                print(f'Error al agregar producto: {e}')
                messagebox.showerror("❌ Error", f"Error al agregar producto: {e}")
        
        # Frame para botones (más arriba)
        btn_frame = tk.Frame(main_frame, bg=estilos.COLORS['white'])
        btn_frame.place(x=50, y=320, width=400, height=60)
        
        # Botones
        btn_guardar = ctk.CTkButton(btn_frame, text='💾 Guardar Producto', 
                                   font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                   command=guardar, width=180, height=40,
                                   fg_color=estilos.COLORS['success'],
                                   hover_color="#8f070c")
        btn_guardar.pack(side='left', padx=10, pady=10)
        
        btn_cancelar = ctk.CTkButton(btn_frame, text='❌ Cancelar', 
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    command=top.destroy, width=180, height=40,
                                    fg_color=estilos.COLORS['danger'],
                                    hover_color="#c21f28")
        btn_cancelar.pack(side='right', padx=10, pady=10)
    
    def load_image(self):
        """Cargar imagen para el producto"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen del producto",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Abrir y redimensionar la imagen
                image = Image.open(file_path)
                image = image.resize((180, 180), Image.LANCZOS)
                
                # Guardar la imagen en la carpeta del proyecto
                image_name = os.path.basename(file_path)
                image_save_path = os.path.join(self.image_folder, image_name)
                image.save(image_save_path)
                
                # Mostrar la imagen en el frame
                self.image_tk = ImageTk.PhotoImage(image)
                self.image_path = image_save_path
                
                # Limpiar el frame y mostrar la nueva imagen
                for widget in self.frameimg.winfo_children():
                    widget.destroy()
                
                image_label = tk.Label(self.frameimg, image=self.image_tk, bg='lightgray')
                image_label.pack(expand=True, fill='both')
                
                messagebox.showinfo("✅ Éxito", "Imagen cargada correctamente")
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error al cargar la imagen: {e}")
    
    def editar_articulo(self):
        """Ventana para editar un producto existente"""
        # Verificar que hay un producto seleccionado
        producto_seleccionado = self.comboboxbuscar.get().strip()
        
        if not producto_seleccionado:
            messagebox.showerror("❌ Error", "Selecciona un producto para editar")
            return
        
        # Obtener datos del producto
        try:
            self.cur.execute("""SELECT codigo, articulo, precio, costo, stock, estado, imagen_path 
                              FROM articulos WHERE articulo=?""", (producto_seleccionado,))
            resultado = self.cur.fetchone()
            
            if not resultado:
                messagebox.showerror("❌ Error", "Producto no encontrado")
                return
                
            codigo_actual, articulo_actual, precio_actual, costo_actual, stock_actual, estado_actual, imagen_actual = resultado
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al obtener datos del producto: {e}")
            return
        
        # Crear ventana de edición
        top = tk.Toplevel(self)
        top.title("✏️ Editar Producto")
        top.geometry("700x500+200+50")
        top.configure(bg=estilos.COLORS['white'])
        top.resizable(False, False)
        
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()
        
        # Título
        title_label = tk.Label(top, text=f"✏️ Editar Producto: {articulo_actual}", 
                              font=('Poppins', 16, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=15)
        
        # Frame principal
        main_frame = tk.Frame(top, bg=estilos.COLORS['white'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Campos de entrada con valores actuales
        tk.Label(main_frame, text="Código de Barras:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=20)
        entry_codigo = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_codigo.place(x=180, y=20)
        entry_codigo.insert(0, codigo_actual)
        
        tk.Label(main_frame, text="Nombre del Artículo:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=60)
        entry_articulo = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_articulo.place(x=180, y=60)
        entry_articulo.insert(0, articulo_actual)
        
        tk.Label(main_frame, text="Precio de Venta:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=100)
        entry_precio = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_precio.place(x=180, y=100)
        entry_precio.insert(0, str(precio_actual))
        
        tk.Label(main_frame, text="Costo del Producto:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=140)
        entry_costo = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_costo.place(x=180, y=140)
        entry_costo.insert(0, str(costo_actual))
        
        tk.Label(main_frame, text="Stock:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=180)
        entry_stock = tk.Entry(main_frame, font=('Poppins', 12), width=30)
        entry_stock.place(x=180, y=180)
        entry_stock.insert(0, str(stock_actual))
        
        tk.Label(main_frame, text="Estado:", 
                font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).place(x=20, y=220)
        
        # Combobox para estado
        from tkinter import ttk
        combo_estado = ttk.Combobox(main_frame, values=["activo", "inactivo"], 
                                   font=('Poppins', 12), state="readonly", width=28)
        combo_estado.place(x=180, y=220)
        combo_estado.set(estado_actual)
        
        # Frame para imagen
        self.frameimg_edit = tk.Frame(main_frame, bg='lightgray', relief='solid', bd=1)
        self.frameimg_edit.place(x=480, y=30, width=180, height=180)
        
        # Mostrar imagen actual si existe
        if imagen_actual and os.path.exists(imagen_actual):
            try:
                image = Image.open(imagen_actual)
                image = image.resize((180, 180), Image.LANCZOS)
                self.current_image_tk = ImageTk.PhotoImage(image)
                self.current_image_path = imagen_actual
                
                image_label = tk.Label(self.frameimg_edit, image=self.current_image_tk, bg='lightgray')
                image_label.pack(expand=True, fill='both')
            except Exception:
                img_placeholder = tk.Label(self.frameimg_edit, text="📷\nImagen\nActual", 
                                          font=('Poppins', 12), bg='lightgray')
                img_placeholder.pack(expand=True)
        else:
            img_placeholder = tk.Label(self.frameimg_edit, text="📷\nSin\nImagen", 
                                      font=('Poppins', 12), bg='lightgray')
            img_placeholder.pack(expand=True)
            self.current_image_path = imagen_actual
        
        # Botón para cambiar imagen
        def cambiar_imagen():
            file_path = filedialog.askopenfilename(
                title="Seleccionar nueva imagen",
                filetypes=[
                    ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if file_path:
                try:
                    # Redimensionar y guardar
                    image = Image.open(file_path)
                    image = image.resize((180, 180), Image.LANCZOS)
                    
                    image_name = os.path.basename(file_path)
                    image_save_path = os.path.join(self.image_folder, image_name)
                    image.save(image_save_path)
                    
                    # Mostrar nueva imagen
                    self.current_image_tk = ImageTk.PhotoImage(image)
                    self.current_image_path = image_save_path
                    
                    # Limpiar y mostrar
                    for widget in self.frameimg_edit.winfo_children():
                        widget.destroy()
                    
                    image_label = tk.Label(self.frameimg_edit, image=self.current_image_tk, bg='lightgray')
                    image_label.pack(expand=True, fill='both')
                    
                    messagebox.showinfo("✅ Éxito", "Imagen actualizada correctamente")
                    
                except Exception as e:
                    messagebox.showerror("❌ Error", f"Error al cargar imagen: {e}")
        
        btn_imagen = ctk.CTkButton(main_frame, text='📁 Cambiar Imagen', 
                                  font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                  command=cambiar_imagen, width=180, height=35)
        btn_imagen.place(x=480, y=230)
        
        def guardar_cambios():
            codigo = entry_codigo.get().strip()
            articulo = entry_articulo.get().strip()
            precio = entry_precio.get().strip()
            costo = entry_costo.get().strip()
            stock = entry_stock.get().strip()
            estado = combo_estado.get()
            
            # Validaciones
            if not all([codigo, articulo, precio, costo, stock, estado]):
                messagebox.showerror("❌ Error", "Todos los campos deben ser completados")
                return
            
            try:
                precio_float = float(precio)
                costo_float = float(costo)
                stock_int = int(stock)
                
                if precio_float <= 0 or costo_float <= 0 or stock_int < 0:
                    messagebox.showerror("❌ Error", "Los valores deben ser positivos")
                    return
                    
            except ValueError:
                messagebox.showerror("❌ Error", "Precio, costo y stock deben ser números válidos")
                return
            
            # Verificar si el código cambió y ya existe
            if codigo != codigo_actual:
                try:
                    self.cur.execute("SELECT codigo FROM articulos WHERE codigo = ? AND articulo != ?", 
                                   (codigo, producto_seleccionado))
                    if self.cur.fetchone():
                        messagebox.showerror("❌ Error", f"El código '{codigo}' ya existe en otro producto")
                        return
                except sqlite3.Error:
                    pass
            
            # Usar imagen actual si no se cambió
            imagen_path = getattr(self, 'current_image_path', imagen_actual)
            
            try:
                # Actualizar el producto
                self.cur.execute("""UPDATE articulos 
                               SET codigo=?, articulo=?, precio=?, costo=?, stock=?, estado=?, imagen_path=?
                               WHERE articulo=?""", 
                               (codigo, articulo, precio_float, costo_float, stock_int, estado, imagen_path, producto_seleccionado))
                self.conn.commit()
                
                messagebox.showinfo('✅ Éxito', f'Producto "{articulo}" actualizado correctamente')
                top.destroy()
                
                # Recargar la vista
                self.cargar_articulos()
                self.articulos_combobox()
                
                # Seleccionar el producto editado
                self.comboboxbuscar.set(articulo)
                self.actualizar_label()
                
            except sqlite3.Error as e:
                print(f'Error al actualizar producto: {e}')
                messagebox.showerror("❌ Error", f"Error al actualizar producto: {e}")
        
        def eliminar_producto():
            respuesta = messagebox.askyesno("⚠️ Confirmar Eliminación", 
                                          f"¿Estás seguro de que quieres eliminar el producto '{articulo_actual}'?\n\nEsta acción no se puede deshacer.")
            
            if respuesta:
                try:
                    self.cur.execute("DELETE FROM articulos WHERE articulo=?", (producto_seleccionado,))
                    self.conn.commit()
                    
                    messagebox.showinfo('✅ Éxito', f'Producto "{articulo_actual}" eliminado correctamente')
                    top.destroy()
                    
                    # Recargar la vista
                    self.cargar_articulos()
                    self.articulos_combobox()
                    
                    # Limpiar selección
                    self.comboboxbuscar.set("")
                    self.label1.config(text="📦 Artículo: --")
                    self.label2.config(text="💰 Precio: --")
                    self.label3.config(text="🏷️ Código: --")
                    self.label4.config(text="📊 Stock: --")
                    self.label5.config(text="❌ Estado: --")
                    
                except sqlite3.Error as e:
                    print(f'Error al eliminar producto: {e}')
                    messagebox.showerror("❌ Error", f"Error al eliminar producto: {e}")
        
        # Frame para botones
        btn_frame = tk.Frame(main_frame, bg=estilos.COLORS['white'])
        btn_frame.place(x=20, y=320, width=640, height=60)
        
        # Botones
        btn_guardar = ctk.CTkButton(btn_frame, text='💾 Guardar Cambios', 
                                   font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                   command=guardar_cambios, width=150, height=40,
                                   fg_color=estilos.COLORS['success'],
                                   hover_color="#8f070c")
        btn_guardar.pack(side='left', padx=10, pady=10)
        
        btn_eliminar = ctk.CTkButton(btn_frame, text='🗑️ Eliminar', 
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    command=eliminar_producto, width=150, height=40,
                                    fg_color="#c21f28",
                                    hover_color="#8f070c")
        btn_eliminar.pack(side='left', padx=10, pady=10)
        
        btn_cancelar = ctk.CTkButton(btn_frame, text='❌ Cancelar', 
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    command=top.destroy, width=150, height=40,
                                    fg_color=estilos.COLORS['secondary'],
                                    hover_color="#5a4b48")
        btn_cancelar.pack(side='right', padx=10, pady=10)
    
    def imprimir_etiqueta(self):
        """Modal para imprimir etiqueta con código de barras y precio"""
        # Verificar que hay un producto seleccionado
        producto_seleccionado = self.comboboxbuscar.get().strip()
        
        if not producto_seleccionado:
            messagebox.showerror("❌ Error", "Selecciona un producto para imprimir su etiqueta")
            return
        
        # Obtener datos del producto
        try:
            self.cur.execute("""SELECT codigo, articulo, precio, imagen_path 
                              FROM articulos WHERE articulo=?""", (producto_seleccionado,))
            resultado = self.cur.fetchone()
            
            if not resultado:
                messagebox.showerror("❌ Error", "Producto no encontrado")
                return
                
            codigo, articulo, precio, imagen_path = resultado
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al obtener datos del producto: {e}")
            return
        
        # Crear ventana modal para etiqueta (más alto)
        top = tk.Toplevel(self)
        top.title("🏷️ Imprimir Etiqueta")
        top.geometry("600x650+300+50")
        top.configure(bg=estilos.COLORS['white'])
        top.resizable(False, False)
        
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()
        
        # Título
        title_label = tk.Label(top, text="🏷️ Vista Previa de Etiqueta", 
                              font=('Poppins', 18, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=20)
        
        # Frame principal para la etiqueta
        etiqueta_frame = tk.Frame(top, bg='white', relief='solid', bd=2)
        etiqueta_frame.pack(pady=20, padx=50)
        
        # Simular etiqueta térmica (58mm de ancho típico) - Más grande
        etiqueta_canvas = tk.Canvas(etiqueta_frame, width=400, height=250, bg='white', highlightthickness=1, highlightbackground='black')
        etiqueta_canvas.pack(padx=15, pady=15)
        
        # Generar código de barras visual (simulado)
        def generar_codigo_barras_visual(canvas, codigo, x, y, width=200, height=40):
            """Genera una representación visual del código de barras"""
            # Limpiar área
            canvas.create_rectangle(x, y, x + width, y + height, fill='white', outline='white')
            
            # Crear barras simuladas del código de barras
            import random
            random.seed(hash(codigo))  # Seed basado en el código para consistencia
            
            bar_width = 2
            current_x = x + 10
            
            for i in range(0, len(codigo) * 3):  # Múltiples barras por dígito
                if random.choice([True, False]):  # Barra negra o espacio
                    canvas.create_rectangle(current_x, y + 5, current_x + bar_width, y + height - 5, 
                                          fill='black', outline='black')
                current_x += bar_width
                if current_x > x + width - 20:
                    break
        
        # Dibujar contenido de la etiqueta (ajustado para canvas más grande)
        # Nombre del producto (centrado, en negrita)
        etiqueta_canvas.create_text(200, 40, text=articulo, 
                                   font=('Montserrat', 14, 'bold'), 
                                   fill='black', anchor='center', width=360)
        
        # Código de barras visual (más grande y centrado)
        generar_codigo_barras_visual(etiqueta_canvas, codigo, 100, 80, width=240, height=50)
        
        # Código numérico debajo del código de barras
        etiqueta_canvas.create_text(200, 150, text=codigo, 
                                   font=('Montserrat', 12), 
                                   fill='black', anchor='center')
        
        # Precio (grande y destacado)
        etiqueta_canvas.create_text(200, 200, text=f"${precio:.2f}", 
                                   font=('Montserrat', 20, 'bold'), 
                                   fill='black', anchor='center')
        
        # Información adicional
        info_frame = tk.Frame(top, bg=estilos.COLORS['white'])
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text=f"📦 Producto: {articulo}", 
                font=('Poppins', 12), bg=estilos.COLORS['white']).pack(anchor='w', padx=20)
        tk.Label(info_frame, text=f"🏷️ Código: {codigo}", 
                font=('Poppins', 12), bg=estilos.COLORS['white']).pack(anchor='w', padx=20)
        tk.Label(info_frame, text=f"💰 Precio: ${precio:.2f}", 
                font=('Poppins', 12), bg=estilos.COLORS['white']).pack(anchor='w', padx=20)
        
        # Configuración de impresión
        config_frame = tk.LabelFrame(top, text="⚙️ Configuración de Impresión", 
                                   font=('Poppins', 12, 'bold'), 
                                   bg=estilos.COLORS['white'])
        config_frame.pack(pady=10, padx=50, fill='x')
        
        # Cantidad de etiquetas
        tk.Label(config_frame, text="Cantidad de etiquetas:", 
                font=('Poppins', 11), bg=estilos.COLORS['white']).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        cantidad_var = tk.StringVar(value="1")
        cantidad_entry = tk.Entry(config_frame, textvariable=cantidad_var, 
                                font=('Poppins', 11), width=10)
        cantidad_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Tamaño de etiqueta
        tk.Label(config_frame, text="Tamaño de etiqueta:", 
                font=('Poppins', 11), bg=estilos.COLORS['white']).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        from tkinter import ttk
        tamaño_combo = ttk.Combobox(config_frame, values=["58mm x 40mm", "58mm x 60mm", "80mm x 40mm"], 
                                   font=('Poppins', 11), state="readonly", width=15)
        tamaño_combo.grid(row=1, column=1, padx=10, pady=5)
        tamaño_combo.set("58mm x 40mm")
        
        def enviar_a_impresora():
            """Función para enviar etiqueta a impresora térmica"""
            try:
                cantidad = int(cantidad_var.get())
                if cantidad <= 0:
                    messagebox.showerror("❌ Error", "La cantidad debe ser mayor a 0")
                    return
                    
                tamaño = tamaño_combo.get()
                
                # Aquí iría la lógica real de impresión térmica
                # Por ahora simulamos el proceso
                
                # Crear contenido de la etiqueta para impresión
                etiqueta_content = f"""
╔══════════════════════════════════════╗
║            ETIQUETA PRODUCTO         ║
╠══════════════════════════════════════╣
║                                      ║
║  {articulo[:30].center(30)}          ║
║                                      ║
║  ████ ██ █ ██ █ ██ ████ █ ██ ████    ║
║  ████ ██ █ ██ █ ██ ████ █ ██ ████    ║
║  ████ ██ █ ██ █ ██ ████ █ ██ ████    ║
║                                      ║
║           {codigo.center(20)}        ║
║                                      ║
║              ${precio:.2f}           ║
║                                      ║
╚══════════════════════════════════════╝
                """
                
                # Simulación de impresión
                import time
                
                # Mostrar progreso
                progress_window = tk.Toplevel(top)
                progress_window.title("🖨️ Imprimiendo...")
                progress_window.geometry("300x150+400+200")
                progress_window.configure(bg=estilos.COLORS['white'])
                progress_window.resizable(False, False)
                progress_window.transient(top)
                progress_window.grab_set()
                
                tk.Label(progress_window, text="🖨️ Enviando a impresora térmica...", 
                        font=('Poppins', 12, 'bold'), 
                        bg=estilos.COLORS['white']).pack(pady=20)
                
                progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
                progress_bar.pack(pady=10, padx=20, fill='x')
                progress_bar.start()
                
                status_label = tk.Label(progress_window, text=f"Imprimiendo {cantidad} etiqueta(s)...", 
                                      font=('Poppins', 10), 
                                      bg=estilos.COLORS['white'])
                status_label.pack(pady=10)
                
                progress_window.update()
                
                # Simular tiempo de impresión
                for i in range(cantidad):
                    time.sleep(1)  # Simular tiempo de impresión por etiqueta
                    status_label.config(text=f"Imprimiendo etiqueta {i+1} de {cantidad}...")
                    progress_window.update()
                
                progress_bar.stop()
                progress_window.destroy()
                
                # Aquí iría el código real para impresora térmica:
                # import win32print
                # printer_name = win32print.GetDefaultPrinter()
                # hPrinter = win32print.OpenPrinter(printer_name)
                # win32print.StartDocPrinter(hPrinter, 1, ("Etiqueta", None, "RAW"))
                # win32print.StartPagePrinter(hPrinter)
                # win32print.WritePrinter(hPrinter, etiqueta_content.encode())
                # win32print.EndPagePrinter(hPrinter)
                # win32print.EndDocPrinter(hPrinter)
                # win32print.ClosePrinter(hPrinter)
                
                messagebox.showinfo("✅ Éxito", 
                                  f"Se enviaron {cantidad} etiqueta(s) a la impresora térmica.\n\n"
                                  f"Producto: {articulo}\n"
                                  f"Código: {codigo}\n"
                                  f"Precio: ${precio:.2f}\n"
                                  f"Tamaño: {tamaño}")
                
                top.destroy()
                
            except ValueError:
                messagebox.showerror("❌ Error", "La cantidad debe ser un número válido")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error al imprimir: {e}")
        
        # Frame para botones
        btn_frame = tk.Frame(top, bg=estilos.COLORS['white'])
        btn_frame.pack(pady=20)
        
        # Botones
        btn_imprimir = ctk.CTkButton(btn_frame, text='🖨️ Imprimir Etiqueta', 
                                   font=ctk.CTkFont(family="Poppins", size=14, weight="bold"),
                                   command=enviar_a_impresora, width=200, height=45,
                                   fg_color=estilos.COLORS['success'],
                                   hover_color="#8f070c")
        btn_imprimir.pack(side='left', padx=10)
        
        btn_cancelar = ctk.CTkButton(btn_frame, text='❌ Cancelar', 
                                    font=ctk.CTkFont(family="Poppins", size=14, weight="bold"),
                                    command=top.destroy, width=150, height=45,
                                    fg_color=estilos.COLORS['danger'],
                                    hover_color="#c21f28")
        btn_cancelar.pack(side='right', padx=10)
    
    def cargar_articulos(self, filtro=None):
        self.after(0, self._cargar_articulos, filtro)
    
    def _cargar_articulos(self, filtro=None):
        self._aplicar_modo_claro_inventario()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        try:
            query = "SELECT codigo, articulo, precio, imagen_path FROM articulos WHERE estado = 'activo'"
            params = []
            
            if filtro:
                query += " AND articulo LIKE ?"
                params.append(f'%{filtro}%')
                
            self.cur.execute(query, params)
            articulos = self.cur.fetchall()
            
            self.row = 0
            self.column = 0
            self.update_idletasks()
            ancho_catalogo = max(210, self.canvas.winfo_width())
            self._columnas_catalogo = max(1, int(ancho_catalogo / 210))
            
            for codigo, articulo, precio, image_path in articulos:
                self.mostrar_articulo(codigo, articulo, precio, image_path)
                
        except sqlite3.Error as e:
            print(f"Error cargando artículos: {e}")
            # Mostrar mensaje de error en el canvas
            error_label = tk.Label(self.scrollable_frame, 
                                 text=f"❌ Error cargando productos: {e}",
                                 font=('Poppins', 12, 'bold'),
                                 fg='red', bg=estilos.COLORS['white'])
            error_label.pack(pady=20)
    
    def mostrar_articulo(self, codigo, articulo, precio, image_path):
        # Tarjeta compacta con las cuatro esquinas redondeadas.
        article_frame = ctk.CTkFrame(
            self.scrollable_frame, width=190, height=220,
            corner_radius=14, fg_color='#ffffff',
            border_width=1, border_color='#e3e6ea'
        )
        article_frame.grid(row=self.row, column=self.column, padx=8, pady=8, sticky="nsew")
        article_frame.grid_propagate(False)
        
        # Imagen del producto (mucho más grande) - Clickeable
        if image_path and os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                image = image.resize((150, 120), Image.LANCZOS)
                imagen = ImageTk.PhotoImage(image)
                image_label = tk.Label(article_frame, image=imagen, bg='white', cursor='hand2')
                image_label.image = imagen
                image_label.pack(pady=(8, 4))
                # Hacer clickeable la imagen
                image_label.bind("<Button-1>", lambda e: self.seleccionar_producto(articulo))
            except Exception:
                placeholder = tk.Label(article_frame, text="📷", 
                                     font=('Poppins', 38), bg='white', cursor='hand2')
                placeholder.pack(pady=(28, 24))
                # Hacer clickeable el placeholder
                placeholder.bind("<Button-1>", lambda e: self.seleccionar_producto(articulo))
        else:
            placeholder = tk.Label(article_frame, text="📷", 
                                 font=('Poppins', 38), bg='white', cursor='hand2')
            placeholder.pack(pady=(28, 24))
            # Hacer clickeable el placeholder
            placeholder.bind("<Button-1>", lambda e: self.seleccionar_producto(articulo))
        
        # Información del producto
        name_label = tk.Label(article_frame, text=articulo, bg='white', anchor='w', 
                            wraplength=170, font=('Poppins', 9, 'bold'))
        name_label.pack(side="top", fill='x', padx=10)
        
        # Formatear precio según configuración de moneda
        try:
            from modulos.configuracion.gestor_configuracion import formatear_precio
            precio_formateado = formatear_precio(precio)
        except:
            precio_formateado = f'${precio:.2f}'
        
        precio_label = tk.Label(article_frame, text=f'💰 {precio_formateado}', bg='white', 
                              anchor='w', font=('Poppins', 8, 'bold'), fg=estilos.COLORS['success'])
        precio_label.pack(side="top", fill='x', padx=10)
        
        codigo_label = tk.Label(article_frame, text=f'🏷️ {codigo}', bg='white', 
                              anchor='w', font=('Poppins', 8), fg=estilos.COLORS['secondary'])
        codigo_label.pack(side="bottom", fill='x', padx=10, pady=(2, 7))
        
        self.column += 1
        columnas = getattr(self, '_columnas_catalogo', 1)
        if self.column >= columnas:
            self.column = 0 
            self.row += 1
    
    def seleccionar_producto(self, articulo):
        """Seleccionar producto al hacer click en la imagen"""
        # Actualizar el combobox con el producto seleccionado
        self.comboboxbuscar.set(articulo)
        # Actualizar la información del producto
        self.actualizar_label()
    
    def on_combobox_select(self, event):
        self.actualizar_label()
        
    def actualizar_label(self, event=None):
        articulo_seleccionado = self.comboboxbuscar.get()
        
        try:
            self.cur.execute("""SELECT codigo, articulo, precio, costo, stock, estado 
                              FROM articulos WHERE articulo=?""", (articulo_seleccionado,))
            resultado = self.cur.fetchone()
            
            if resultado:
                codigo, articulo, precio, costo, stock, estado = resultado
                
                self.label1.config(text=f'📦 Artículo: {articulo}')
                self.label2.config(text=f'💰 Precio: ${precio:.2f}')
                self.label3.config(text=f'🏷️ Código: {codigo}')
                self.label4.config(text=f'📊 Stock: {stock} unidades')
                
                if estado.lower() == "activo":
                    self.label5.config(text=f'✅ Estado: {estado}', fg='#23834a')
                else:
                    self.label5.config(text=f'❌ Estado: {estado}', fg='#c21f28')
            else:
                self.label1.config(text="📦 Artículo: No encontrado")
                self.label2.config(text="💰 Precio: --")
                self.label3.config(text="🏷️ Código: --")
                self.label4.config(text="📊 Stock: --")
                self.label5.config(text="❌ Estado: --")
                
        except sqlite3.Error as e:
            print("Error al obtener datos del artículo:", e)
            messagebox.showerror("❌ Error", "Error al obtener los datos del artículo")
    
    def filtrar_articulos(self, event): 
        if self.timer_articulos:
            self.timer_articulos.cancel()
        self.timer_articulos = threading.Timer(0.5, self._filter_articulos)   
        self.timer_articulos.start()
    
    def _filter_articulos(self):
        typed = self.comboboxbuscar.get()
        
        if typed == '':
            data = self.articulos
        else:
            data = [item for item in self.articulos if typed.lower() in item.lower()]
        
        if data:
            self.comboboxbuscar['values'] = data
            self.comboboxbuscar.event_generate('<Down>')
        else:
            self.comboboxbuscar['values'] = ['No se encontraron resultados']
            self.comboboxbuscar.event_generate('<Down>')
            
        self.cargar_articulos(filtro=typed)



