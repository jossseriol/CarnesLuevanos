import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from modulos.utils.estilos_modernos import estilos
import sqlite3
import hashlib
import os
import shutil
import uuid
from PIL import Image
from datetime import datetime
from modulos.auth.permisos import (
    MODULOS_SISTEMA,
    SUPERUSER_USERNAME,
    asegurar_tablas_permisos,
    guardar_permisos_usuario,
    obtener_permisos_usuario,
    permisos_por_defecto,
)

# Configurar CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class GestorConfiguracion:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.modo_edicion = False
        self.usuario_editando_id = None
        self.crear_tablas_configuracion()
        
    def crear_tablas_configuracion(self):
        """Crear tablas de configuración"""
        try:
            asegurar_tablas_permisos()
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            columnas_usuario = {fila[1] for fila in cursor.execute("PRAGMA table_info(usuarios)").fetchall()}
            if 'foto_perfil' not in columnas_usuario:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil TEXT")
            
            # Tabla de configuración del sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT UNIQUE NOT NULL,
                    valor TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insertar configuraciones por defecto
            configuraciones_default = [
                ('moneda_principal', 'USD', 'Moneda principal del sistema (USD/VES)'),
                ('tasa_cambio', '36.50', 'Tasa de cambio USD a VES'),
                ('simbolo_ves', 'Bs.', 'Símbolo para Bolívares'),
                ('simbolo_usd', '$', 'Símbolo para Dólares'),
                ('mostrar_ambas_monedas', '1', 'Mostrar precios en ambas monedas (1=Sí, 0=No)'),
                ('nombre_empresa', 'Carnes Luévanos', 'Administración'),
                ('direccion_empresa', 'Gomez Palacio, Durango', 'Dirección de la empresa'),
                ('telefono_empresa', '+52(87) 1503-4671', 'Teléfono de la empresa'),
                ('rif_empresa', 'J-00000000-0', 'RIF de la empresa'),
                ('iva_porcentaje', '16', 'Porcentaje de IVA aplicado en ventas')
            ]
            
            for clave, valor, descripcion in configuraciones_default:
                cursor.execute('''
                    INSERT OR IGNORE INTO configuracion_sistema (clave, valor, descripcion)
                    VALUES (?, ?, ?)
                ''', (clave, valor, descripcion))
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al crear tablas de configuración: {e}")
    
    def abrir_ventana_configuracion(self):
        """Abrir ventana principal de configuración"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ Configuración del Sistema")
        self.window.geometry("1000x700+250+50")
        self.window.configure(bg=estilos.COLORS['bg_primary'])
        self.window.resizable(True, True)
        self.window.grab_set()
        self.window.focus_set()
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Pestaña 1: Usuarios
        self.crear_pestaña_usuarios(notebook)
        
        # Pestaña 2: Monedas
        self.crear_pestaña_monedas(notebook)

        # Pestana 3: IVA
        self.crear_pestana_impuestos(notebook)
        
        # Pestana 4: Empresa
        self.crear_pestaña_empresa(notebook)
    
    def crear_pestaña_usuarios(self, notebook):
        """Crear pestaña de gestión de usuarios"""
        frame_usuarios = tk.Frame(notebook, bg=estilos.COLORS['bg_primary'])
        notebook.add(frame_usuarios, text="👥 Usuarios")
        
        # Título
        title_label = tk.Label(frame_usuarios, text="👥 Gestión de Usuarios", 
                              font=('Poppins', 18, 'bold'), 
                              bg=estilos.COLORS['bg_primary'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=(20, 30))
        
        # Frame principal dividido
        main_frame = tk.Frame(frame_usuarios, bg=estilos.COLORS['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=20)
        
        # Frame izquierdo - Formulario
        self.form_frame_label = tk.LabelFrame(main_frame, text="➕ Nuevo Usuario", 
                                  font=('Poppins', 14, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        self.form_frame_label.pack(side='left', fill='y', padx=(0, 10), pady=10)
        
        # Campos del formulario
        tk.Label(self.form_frame_label, text="👤 Usuario:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.nuevo_usuario = tk.Entry(self.form_frame_label, font=('Poppins', 11), width=20)
        self.nuevo_usuario.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(self.form_frame_label, text="🔒 Contraseña:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.nueva_password = tk.Entry(self.form_frame_label, font=('Poppins', 11), width=20, show="*")
        self.nueva_password.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(self.form_frame_label, text="📝 Nombre:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.nuevo_nombre = tk.Entry(self.form_frame_label, font=('Poppins', 11), width=20)
        self.nuevo_nombre.grid(row=2, column=1, padx=10, pady=5)

        permisos_frame = tk.LabelFrame(
            self.form_frame_label,
            text="Permisos por modulo",
            font=('Poppins', 10, 'bold'),
            bg=estilos.COLORS['white'],
            fg=estilos.COLORS['primary']
        )
        permisos_frame.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=(12, 5))
        self.perm_vars = {}
        for idx, (clave, nombre_modulo) in enumerate(MODULOS_SISTEMA):
            var = tk.BooleanVar(value=(clave == 'informacion'))
            chk = tk.Checkbutton(
                permisos_frame,
                text=nombre_modulo,
                variable=var,
                bg=estilos.COLORS['white'],
                font=('Poppins', 9),
                anchor='w'
            )
            chk.grid(row=idx // 2, column=idx % 2, sticky='w', padx=8, pady=3)
            self.perm_vars[clave] = var
        
        # Frame para botones
        buttons_form_frame = tk.Frame(self.form_frame_label, bg=estilos.COLORS['white'])
        buttons_form_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Botones
        self.btn_crear_guardar = ctk.CTkButton(buttons_form_frame, text="➕ Crear Usuario", 
                                 command=self.crear_o_actualizar_usuario,
                                 width=180, height=40,
                                 font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                 fg_color=estilos.COLORS['success'])
        self.btn_crear_guardar.pack(side='left', padx=5)
        
        self.btn_cancelar = ctk.CTkButton(buttons_form_frame, text="❌ Cancelar", 
                                 command=self.cancelar_edicion,
                                 width=100, height=40,
                                 font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                 fg_color=estilos.COLORS['danger'])
        self.btn_cancelar.pack(side='left', padx=5)
        self.btn_cancelar.pack_forget()  # Ocultar inicialmente
        
        # Frame derecho - Lista de usuarios
        list_frame = tk.LabelFrame(main_frame, text="📋 Usuarios Registrados", 
                                  font=('Poppins', 14, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        list_frame.pack(side='right', fill='both', expand=True, padx=(10, 0), pady=10)
        
        # Treeview para usuarios
        self.tree_usuarios = ttk.Treeview(list_frame, 
                                         columns=("ID", "Usuario", "Nombre"), 
                                         show="headings", height=15)
        self.tree_usuarios.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree_usuarios.heading("ID", text="ID")
        self.tree_usuarios.heading("Usuario", text="Usuario")
        self.tree_usuarios.heading("Nombre", text="Nombre")
        
        self.tree_usuarios.column("ID", width=50, anchor="center")
        self.tree_usuarios.column("Usuario", width=150, anchor="w")
        self.tree_usuarios.column("Nombre", width=200, anchor="w")
        
        # Frame para botones de acción
        buttons_list_frame = tk.Frame(list_frame, bg=estilos.COLORS['white'])
        buttons_list_frame.pack(pady=10)
        
        # Botón editar
        btn_editar = ctk.CTkButton(buttons_list_frame, text="✏️ Editar Usuario", 
                                    command=self.editar_usuario,
                                    width=180, height=40,
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    fg_color=estilos.COLORS['info'])
        btn_editar.pack(side='left', padx=5)
        
        # Botón eliminar
        btn_eliminar = ctk.CTkButton(buttons_list_frame, text="🗑️ Eliminar Usuario", 
                                    command=self.eliminar_usuario,
                                    width=180, height=40,
                                    font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
                                    fg_color=estilos.COLORS['danger'])
        btn_eliminar.pack(side='left', padx=5)
        
        # Permitir doble clic para editar
        self.tree_usuarios.bind('<Double-1>', lambda e: self.editar_usuario())
        
        self.cargar_usuarios()
    
    def crear_pestaña_monedas(self, notebook):
        """Crear pestaña de configuración de monedas"""
        frame_monedas = tk.Frame(notebook, bg=estilos.COLORS['bg_primary'])
        notebook.add(frame_monedas, text="💰 Monedas")
        
        # Título
        title_label = tk.Label(frame_monedas, text="💰 Configuración de Monedas", 
                              font=('Poppins', 18, 'bold'), 
                              bg=estilos.COLORS['bg_primary'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=(20, 30))
        
        # Frame principal
        main_frame = tk.Frame(frame_monedas, bg=estilos.COLORS['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=40)
        
        # Configuración de moneda principal
        moneda_frame = tk.LabelFrame(main_frame, text="🏦 Moneda Principal", 
                                    font=('Poppins', 14, 'bold'), 
                                    bg=estilos.COLORS['white'],
                                    fg=estilos.COLORS['primary'])
        moneda_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(moneda_frame, text="💵 Moneda Principal:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=0, column=0, sticky='w', padx=20, pady=15)
        
        self.moneda_principal = ttk.Combobox(moneda_frame, font=('Poppins', 11), 
                                           values=["USD", "VES"], state="readonly", width=10)
        self.moneda_principal.grid(row=0, column=1, padx=20, pady=15)
        
        # Tasa de cambio
        tasa_frame = tk.LabelFrame(main_frame, text="📈 Tasa de Cambio", 
                                  font=('Poppins', 14, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        tasa_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(tasa_frame, text="💱 1 USD = ", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=0, column=0, sticky='w', padx=20, pady=15)
        
        self.tasa_cambio = tk.Entry(tasa_frame, font=('Poppins', 11), width=15)
        self.tasa_cambio.grid(row=0, column=1, padx=5, pady=15)
        
        # Bind para actualizar vista previa automáticamente
        self.tasa_cambio.bind('<KeyRelease>', lambda e: self.actualizar_preview())
        self.moneda_principal.bind('<<ComboboxSelected>>', lambda e: self.actualizar_preview())
        
        tk.Label(tasa_frame, text="Bs.", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=0, column=2, sticky='w', padx=5, pady=15)
        
        # Switch para mostrar ambas monedas
        switch_frame = tk.LabelFrame(main_frame, text="🔄 Opciones de Visualización", 
                                    font=('Poppins', 14, 'bold'), 
                                    bg=estilos.COLORS['white'],
                                    fg=estilos.COLORS['primary'])
        switch_frame.pack(fill='x', pady=(0, 20))
        
        self.mostrar_ambas = tk.BooleanVar()
        switch_check = tk.Checkbutton(switch_frame, text="Mostrar precios en ambas monedas", 
                                     variable=self.mostrar_ambas,
                                     font=('Poppins', 12), 
                                     bg=estilos.COLORS['white'],
                                     command=self.actualizar_preview)
        switch_check.pack(padx=20, pady=15, anchor='w')
        
        # Botones de acción
        buttons_frame = tk.Frame(main_frame, bg=estilos.COLORS['bg_primary'])
        buttons_frame.pack(fill='x', pady=20)
        
        btn_guardar = ctk.CTkButton(buttons_frame, text="💾 Guardar Configuración", 
                                   command=self.guardar_configuracion_monedas,
                                   width=200, height=45,
                                   font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
                                   fg_color=estilos.COLORS['success'])
        btn_guardar.pack(side='left', padx=10)
        
        btn_actualizar_tasa = ctk.CTkButton(buttons_frame, text="💱 Ingresar Tasa del Día", 
                                           command=self.ingresar_tasa_dia,
                                           width=200, height=45,
                                           font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
                                           fg_color=estilos.COLORS['info'])
        btn_actualizar_tasa.pack(side='left', padx=10)
        
        # Vista previa de conversión
        preview_frame = tk.LabelFrame(main_frame, text="👁️ Vista Previa", 
                                     font=('Poppins', 14, 'bold'), 
                                     bg=estilos.COLORS['white'],
                                     fg=estilos.COLORS['primary'])
        preview_frame.pack(fill='x')
        
        self.preview_label = tk.Label(preview_frame, text="Ejemplo: $10.00 = Bs. 365.00", 
                                     font=('Poppins', 12), 
                                     bg=estilos.COLORS['white'],
                                     fg=estilos.COLORS['dark'])
        self.preview_label.pack(pady=15)
        
        self.cargar_configuracion_monedas()
    
    def crear_pestana_impuestos(self, notebook):
        """Crear pestana para configurar impuestos."""
        frame_impuestos = tk.Frame(notebook, bg=estilos.COLORS['bg_primary'])
        notebook.add(frame_impuestos, text="IVA")

        title_label = tk.Label(frame_impuestos, text="Configuracion de IVA", font=('Poppins', 18, 'bold'), bg=estilos.COLORS['bg_primary'], fg=estilos.COLORS['primary'])
        title_label.pack(pady=(20, 30))

        main_frame = tk.LabelFrame(frame_impuestos, text="Porcentaje de IVA para ventas", font=('Poppins', 14, 'bold'), bg=estilos.COLORS['white'], fg=estilos.COLORS['primary'])
        main_frame.pack(fill='x', padx=40, pady=20)

        tk.Label(main_frame, text="IVA (%):", font=('Poppins', 12, 'bold'), bg=estilos.COLORS['white']).grid(row=0, column=0, sticky='w', padx=20, pady=20)
        self.iva_porcentaje = tk.Entry(main_frame, font=('Poppins', 12), width=12)
        self.iva_porcentaje.grid(row=0, column=1, sticky='w', padx=10, pady=20)

        tk.Label(main_frame, text="Ejemplo: escribe 16 para aplicar IVA del 16%.", font=('Poppins', 10), bg=estilos.COLORS['white'], fg=estilos.COLORS['gray']).grid(row=1, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 20))

        self.preview_iva = tk.Label(main_frame, text="", font=('Poppins', 11, 'bold'), bg=estilos.COLORS['white'], fg=estilos.COLORS['dark'])
        self.preview_iva.grid(row=2, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 20))
        self.iva_porcentaje.bind('<KeyRelease>', lambda e: self.actualizar_preview_iva())

        btn_guardar = ctk.CTkButton(main_frame, text="Guardar IVA", command=self.guardar_configuracion_iva, width=180, height=42, font=ctk.CTkFont(family="Poppins", size=12, weight="bold"), fg_color=estilos.COLORS['success'])
        btn_guardar.grid(row=3, column=0, columnspan=2, pady=(0, 25))
        self.cargar_configuracion_iva()

    def cargar_configuracion_iva(self):
        """Cargar porcentaje de IVA guardado."""
        try:
            iva = obtener_configuracion('iva_porcentaje', '16')
            self.iva_porcentaje.delete(0, 'end')
            self.iva_porcentaje.insert(0, iva)
            self.actualizar_preview_iva()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar IVA: {e}")

    def guardar_configuracion_iva(self):
        """Guardar porcentaje de IVA."""
        try:
            iva = float(self.iva_porcentaje.get().strip().replace(',', '.'))
            if iva < 0 or iva > 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingrese un porcentaje de IVA valido entre 0 y 100.")
            return

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO configuracion_sistema
                (clave, valor, descripcion, fecha_modificacion)
                VALUES (?, ?, ?, ?)
            """, ('iva_porcentaje', f"{iva:g}", 'Porcentaje de IVA aplicado en ventas', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            self.actualizar_preview_iva()
            self.notificar_cambio_iva()
            messagebox.showinfo("Exito", f"IVA guardado correctamente: {iva:g}%")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al guardar IVA: {e}")

    def notificar_cambio_iva(self):
        """Avisar a Ventas que recalcule totales con el IVA actualizado."""
        try:
            from modulos.ventas.ventas_moderna import VentasModerna
            frames = getattr(self.parent, 'frames', {})
            ventas = frames.get(VentasModerna)
            if ventas is not None and hasattr(ventas, 'refrescar_iva'):
                ventas.refrescar_iva()
        except Exception:
            pass

    def actualizar_preview_iva(self):
        """Actualizar vista previa del IVA."""
        try:
            iva = float(self.iva_porcentaje.get().strip().replace(',', '.'))
            subtotal = 100.0
            impuesto = subtotal * (iva / 100)
            total = subtotal + impuesto
            self.preview_iva.config(text=f"Ejemplo: $100.00 + IVA {iva:g}% (${impuesto:,.2f}) = ${total:,.2f}")
        except Exception:
            self.preview_iva.config(text="Ingrese un porcentaje valido para ver la vista previa.")

    def crear_pestaña_empresa(self, notebook):
        """Crear pestaña de información de la empresa"""
        frame_empresa = tk.Frame(notebook, bg=estilos.COLORS['bg_primary'])
        notebook.add(frame_empresa, text="🏢 Empresa")
        
        # Título
        title_label = tk.Label(frame_empresa, text="🏢 Información de la Empresa", 
                              font=('Poppins', 18, 'bold'), 
                              bg=estilos.COLORS['bg_primary'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=(20, 30))
        
        # Frame principal
        main_frame = tk.LabelFrame(frame_empresa, text="📋 Datos de la Empresa", 
                                  font=('Poppins', 14, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        main_frame.pack(fill='both', expand=True, padx=40, pady=20)
        
        # Campos de la empresa
        tk.Label(main_frame, text="🏢 Nombre:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=0, column=0, sticky='w', padx=20, pady=15)
        self.nombre_empresa = tk.Entry(main_frame, font=('Poppins', 11), width=40)
        self.nombre_empresa.grid(row=0, column=1, padx=20, pady=15)
        
        tk.Label(main_frame, text="📍 Dirección:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=1, column=0, sticky='w', padx=20, pady=15)
        self.direccion_empresa = tk.Entry(main_frame, font=('Poppins', 11), width=40)
        self.direccion_empresa.grid(row=1, column=1, padx=20, pady=15)
        
        tk.Label(main_frame, text="📞 Teléfono:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=2, column=0, sticky='w', padx=20, pady=15)
        self.telefono_empresa = tk.Entry(main_frame, font=('Poppins', 11), width=40)
        self.telefono_empresa.grid(row=2, column=1, padx=20, pady=15)
        
        tk.Label(main_frame, text="🏢 RFC:", font=('Poppins', 12, 'bold'), 
                bg=estilos.COLORS['white']).grid(row=3, column=0, sticky='w', padx=20, pady=15)
        self.rif_empresa = tk.Entry(main_frame, font=('Poppins', 11), width=40)
        self.rif_empresa.grid(row=3, column=1, padx=20, pady=15)
        
        # Botón guardar
        btn_guardar_empresa = ctk.CTkButton(main_frame, text="💾 Guardar Información", 
                                           command=self.guardar_info_empresa,
                                           width=250, height=45,
                                           font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
                                           fg_color=estilos.COLORS['success'])
        btn_guardar_empresa.grid(row=4, column=0, columnspan=2, pady=30)
        
        self.cargar_info_empresa()
    
    # Funciones de usuarios
    def crear_o_actualizar_usuario(self):
        """Crear nuevo usuario o actualizar usuario existente"""
        usuario = self.nuevo_usuario.get().strip()
        password = self.nueva_password.get().strip()
        nombre = self.nuevo_nombre.get().strip()
        
        if not usuario:
            messagebox.showerror("❌ Error", "El campo Usuario es requerido")
            return
        
        if not self.modo_edicion and not password:
            messagebox.showerror("❌ Error", "El campo Contraseña es requerido para nuevos usuarios")
            return
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            if self.modo_edicion:
                # Modo edición: actualizar usuario existente
                if self.usuario_editando_id is None:
                    messagebox.showerror("❌ Error", "Error: No se ha seleccionado un usuario para editar")
                    conn.close()
                    return
                
                # Verificar si el nuevo nombre de usuario ya existe (y no es el mismo usuario)
                cursor.execute("SELECT id, username FROM usuarios WHERE username = ?", (usuario,))
                usuario_existente = cursor.fetchone()
                if usuario_existente and usuario_existente[0] != self.usuario_editando_id:
                    messagebox.showerror("❌ Error", "El nombre de usuario ya existe")
                    conn.close()
                    return
                
                # Obtener el nombre de usuario actual antes de cambiar
                cursor.execute("SELECT username FROM usuarios WHERE id = ?", (self.usuario_editando_id,))
                usuario_actual = cursor.fetchone()
                es_admin = usuario_actual and usuario_actual[0] in ('admin', SUPERUSER_USERNAME)
                
                # Actualizar usuario
                if password:
                    # Si se ingresó una nueva contraseña, actualizarla
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    cursor.execute("UPDATE usuarios SET username = ?, password = ?, nombre = ? WHERE id = ?", 
                                  (usuario, password_hash, nombre or usuario, self.usuario_editando_id))
                else:
                    # Si no se ingresó contraseña, solo actualizar el nombre de usuario
                    cursor.execute("UPDATE usuarios SET username = ?, nombre = ? WHERE id = ?", 
                                  (usuario, nombre or usuario, self.usuario_editando_id))
                
                # Advertencia especial si se cambió el admin
                if es_admin:
                    mensaje_extra = "\n\n⚠️ IMPORTANTE: Se han modificado las credenciales del usuario administrador."
                    if password:
                        mensaje_extra += "\n🔒 La nueva contraseña ha sido actualizada."
                else:
                    mensaje_extra = ""
                
                permisos = {clave: var.get() for clave, var in self.perm_vars.items()}
                if usuario == SUPERUSER_USERNAME:
                    permisos = {clave: True for clave, _nombre in MODULOS_SISTEMA}
                conn.commit()
                conn.close()
                guardar_permisos_usuario(self.usuario_editando_id, permisos)
                
                mensaje_exito = f"Usuario '{usuario}' actualizado correctamente"
                if es_admin:
                    mensaje_exito += mensaje_extra
                messagebox.showinfo("✅ Éxito", mensaje_exito)
                
            else:
                # Modo creación: crear nuevo usuario
                if not password:
                    messagebox.showerror("❌ Error", "El campo Contraseña es requerido")
                    conn.close()
                    return
                
                # Verificar si el usuario ya existe
                cursor.execute("SELECT username FROM usuarios WHERE username = ?", (usuario,))
                if cursor.fetchone():
                    messagebox.showerror("❌ Error", "El usuario ya existe")
                    conn.close()
                    return
                
                # Hash de la contraseña
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Insertar usuario
                cursor.execute("INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, 'usuario')", 
                              (usuario, password_hash, nombre or usuario))
                self.usuario_editando_id = cursor.lastrowid
                permisos = {clave: var.get() for clave, var in self.perm_vars.items()}
                conn.commit()
                conn.close()
                guardar_permisos_usuario(self.usuario_editando_id, permisos)
                
                messagebox.showinfo("✅ Éxito", f"Usuario '{usuario}' creado correctamente")
            
            # Limpiar campos y salir del modo edición
            self.cancelar_edicion()
            
            # Recargar lista
            self.cargar_usuarios()
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al {'actualizar' if self.modo_edicion else 'crear'} usuario: {e}")
    
    def editar_usuario(self):
        """Cargar datos del usuario seleccionado para editar"""
        selection = self.tree_usuarios.selection()
        if not selection:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un usuario para editar")
            return
        
        item = selection[0]
        valores = self.tree_usuarios.item(item, "values")
        usuario_id = int(valores[0])
        username = valores[1]
        
        # Advertencia especial si es el usuario admin
        if username in ('admin', SUPERUSER_USERNAME):
            respuesta = messagebox.askyesno(
                "⚠️ Advertencia de Seguridad",
                "Está intentando editar el usuario administrador.\n\n"
                "⚠️ IMPORTANTE:\n"
                "• Asegúrese de recordar la nueva contraseña.\n"
                "• Si olvida la contraseña, no podrá acceder al sistema.\n"
                "• Se recomienda crear un usuario alternativo antes de cambiar el admin.\n\n"
                "¿Desea continuar con la edición del usuario administrador?",
                icon='warning'
            )
            if not respuesta:
                return
        
        try:
            # Obtener datos del usuario
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, COALESCE(nombre, username) FROM usuarios WHERE id = ?", (usuario_id,))
            usuario_data = cursor.fetchone()
            conn.close()
            
            if not usuario_data:
                messagebox.showerror("❌ Error", "Usuario no encontrado")
                return
            
            # Activar modo edición
            self.modo_edicion = True
            self.usuario_editando_id = usuario_id
            
            # Cargar datos en el formulario
            self.nuevo_usuario.delete(0, 'end')
            self.nuevo_usuario.insert(0, usuario_data[1])
            
            self.nueva_password.delete(0, 'end')
            self.nueva_password.insert(0, "")  # Dejar vacío para no mostrar contraseña
            
            self.nuevo_nombre.delete(0, 'end')
            self.nuevo_nombre.insert(0, usuario_data[2])
            self.cargar_permisos_en_formulario(usuario_id, usuario_data[1])
            
            # Actualizar interfaz
            if username in ('admin', SUPERUSER_USERNAME):
                self.form_frame_label.config(text="⚠️ Editar Usuario Administrador")
                self.btn_crear_guardar.config(text="💾 Guardar Cambios", fg_color=estilos.COLORS['warning'])
            else:
                self.form_frame_label.config(text="✏️ Editar Usuario")
                self.btn_crear_guardar.config(text="💾 Guardar Cambios", fg_color=estilos.COLORS['info'])
            self.btn_cancelar.pack(side='left', padx=5)
            
            # Seleccionar el campo de usuario
            self.nuevo_usuario.focus()
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar usuario: {e}")
    
    def cancelar_edicion(self):
        """Cancelar modo edición y limpiar formulario"""
        self.modo_edicion = False
        self.usuario_editando_id = None
        
        # Limpiar campos
        self.nuevo_usuario.delete(0, 'end')
        self.nueva_password.delete(0, 'end')
        self.nuevo_nombre.delete(0, 'end')
        self.restaurar_permisos_default()
        
        # Restaurar interfaz
        self.form_frame_label.config(text="➕ Nuevo Usuario")
        self.btn_crear_guardar.config(text="➕ Crear Usuario", fg_color=estilos.COLORS['success'])
        self.btn_cancelar.pack_forget()
        
        # Deseleccionar en el treeview
        for item in self.tree_usuarios.selection():
            self.tree_usuarios.selection_remove(item)
    
    def eliminar_usuario(self):
        """Eliminar usuario seleccionado"""
        selection = self.tree_usuarios.selection()
        if not selection:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un usuario para eliminar")
            return
        
        item = selection[0]
        valores = self.tree_usuarios.item(item, "values")
        usuario_id = valores[0]
        username = valores[1]
        
        if username in ('admin', SUPERUSER_USERNAME):
            messagebox.showerror("❌ Error", "No se puede eliminar el usuario administrador")
            return
        
        respuesta = messagebox.askyesno("⚠️ Confirmar", 
                                      f"¿Eliminar el usuario '{username}'?\n\nEsta acción no se puede deshacer.")
        
        if respuesta:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM permisos_usuario WHERE usuario_id = ?", (usuario_id,))
                cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("✅ Éxito", f"Usuario '{username}' eliminado")
                self.cargar_usuarios()
                
            except sqlite3.Error as e:
                messagebox.showerror("❌ Error", f"Error al eliminar usuario: {e}")
    
    def cargar_usuarios(self):
        """Cargar lista de usuarios"""
        try:
            # Limpiar tabla
            for item in self.tree_usuarios.get_children():
                self.tree_usuarios.delete(item)
            
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, COALESCE(nombre, username) FROM usuarios ORDER BY username")
            usuarios = cursor.fetchall()
            
            for usuario in usuarios:
                # Usar username como nombre si no hay campo nombre
                self.tree_usuarios.insert("", "end", values=(usuario[0], usuario[1], usuario[2]))
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar usuarios: {e}")
    

    def restaurar_permisos_default(self):
        if not hasattr(self, 'perm_vars'):
            return
        defaults = permisos_por_defecto()
        for clave, var in self.perm_vars.items():
            var.set(defaults.get(clave, False))

    def cargar_permisos_en_formulario(self, usuario_id, username):
        if not hasattr(self, 'perm_vars'):
            return
        if username == SUPERUSER_USERNAME:
            for var in self.perm_vars.values():
                var.set(True)
            return
        permisos = obtener_permisos_usuario(usuario_id)
        defaults = permisos_por_defecto()
        for clave, var in self.perm_vars.items():
            var.set(permisos.get(clave, defaults.get(clave, False)))

    # Funciones de monedas
    def cargar_configuracion_monedas(self):
        """Cargar configuración de monedas"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Cargar configuraciones
            cursor.execute("SELECT clave, valor FROM configuracion_sistema WHERE clave IN ('moneda_principal', 'tasa_cambio', 'mostrar_ambas_monedas')")
            configs = dict(cursor.fetchall())
            
            self.moneda_principal.set(configs.get('moneda_principal', 'USD'))
            self.tasa_cambio.delete(0, 'end')
            self.tasa_cambio.insert(0, configs.get('tasa_cambio', '36.50'))
            self.mostrar_ambas.set(configs.get('mostrar_ambas_monedas', '1') == '1')
            
            conn.close()
            self.actualizar_preview()
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar configuración: {e}")
    
    def guardar_configuracion_monedas(self):
        """Guardar configuración de monedas"""
        try:
            tasa = float(self.tasa_cambio.get())
            if tasa <= 0:
                raise ValueError("La tasa debe ser mayor a 0")
        except ValueError:
            messagebox.showerror("❌ Error", "Ingrese una tasa de cambio válida")
            return
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Actualizar configuraciones
            configs = [
                ('moneda_principal', self.moneda_principal.get()),
                ('tasa_cambio', self.tasa_cambio.get()),
                ('mostrar_ambas_monedas', '1' if self.mostrar_ambas.get() else '0')
            ]
            
            for clave, valor in configs:
                cursor.execute('''
                    INSERT OR REPLACE INTO configuracion_sistema 
                    (clave, valor, descripcion, fecha_modificacion) 
                    VALUES (?, ?, ?, ?)
                ''', (clave, valor, f'Configuración de {clave}', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Verificar que se guardó correctamente
            cursor.execute("SELECT valor FROM configuracion_sistema WHERE clave = 'tasa_cambio'")
            tasa_guardada = cursor.fetchone()
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✅ Éxito", f"Configuración guardada correctamente\n\nTasa de cambio: {tasa_guardada[0] if tasa_guardada else 'Error'}")
            self.actualizar_preview()
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al guardar configuración: {e}")
    
    def ingresar_tasa_dia(self):
        """Permitir ingresar manualmente la tasa del día"""
        from tkinter import simpledialog
        
        # Obtener tasa actual
        tasa_actual = self.tasa_cambio.get()
        
        # Solicitar nueva tasa
        nueva_tasa = simpledialog.askfloat(
            "💱 Tasa del Día",
            f"Ingrese la tasa de cambio actual:\n\n" +
            f"Tasa actual: {tasa_actual} Bs. por USD\n\n" +
            f"Nueva tasa (solo números):",
            initialvalue=float(tasa_actual) if tasa_actual else 36.50,
            minvalue=1.0,
            maxvalue=1000.0
        )
        
        if nueva_tasa:
            try:
                # Actualizar el campo
                self.tasa_cambio.delete(0, 'end')
                self.tasa_cambio.insert(0, str(nueva_tasa))
                
                # Actualizar vista previa
                self.actualizar_preview()
                
                messagebox.showinfo("✅ Tasa Actualizada", 
                                   f"Nueva tasa ingresada:\n\n" +
                                   f"💱 1 USD = {nueva_tasa} Bs.\n\n" +
                                   f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n" +
                                   "⚠️ Recuerde guardar la configuración para aplicar los cambios.")
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error al actualizar tasa: {e}")
    
    def actualizar_preview(self):
        """Actualizar vista previa de conversión"""
        try:
            tasa = float(self.tasa_cambio.get())
            ejemplo_usd = 1.00  # Cambiar a 1 USD para que coincida con la interfaz
            ejemplo_ves = ejemplo_usd * tasa
            
            if self.mostrar_ambas.get():
                preview_text = f"Ejemplo: ${ejemplo_usd:.2f} = Bs. {ejemplo_ves:,.2f} (Ambas monedas)"
            else:
                moneda = self.moneda_principal.get()
                if moneda == 'USD':
                    preview_text = f"Ejemplo: ${ejemplo_usd:.2f} (Solo USD)"
                else:
                    preview_text = f"Ejemplo: Bs. {ejemplo_ves:,.2f} (Solo VES)"
            
            self.preview_label.config(text=preview_text)
        except:
            self.preview_label.config(text="Vista previa no disponible")
    
    # Funciones de empresa
    def cargar_info_empresa(self):
        """Cargar información de la empresa"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT clave, valor FROM configuracion_sistema WHERE clave IN ('nombre_empresa', 'direccion_empresa', 'telefono_empresa', 'rif_empresa')")
            configs = dict(cursor.fetchall())
            
            self.nombre_empresa.delete(0, 'end')
            self.nombre_empresa.insert(0, configs.get('nombre_empresa', 'Mi Tienda'))
            
            self.direccion_empresa.delete(0, 'end')
            self.direccion_empresa.insert(0, configs.get('direccion_empresa', 'Caracas, Venezuela'))
            
            self.telefono_empresa.delete(0, 'end')
            self.telefono_empresa.insert(0, configs.get('telefono_empresa', '+58-212-1234567'))
            
            self.rif_empresa.delete(0, 'end')
            self.rif_empresa.insert(0, configs.get('rif_empresa', 'J-00000000-0'))
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar información: {e}")
    
    def guardar_info_empresa(self):
        """Guardar información de la empresa"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            configs = [
                ('nombre_empresa', self.nombre_empresa.get()),
                ('direccion_empresa', self.direccion_empresa.get()),
                ('telefono_empresa', self.telefono_empresa.get()),
                ('rif_empresa', self.rif_empresa.get())
            ]
            
            for clave, valor in configs:
                cursor.execute('''
                    INSERT OR REPLACE INTO configuracion_sistema 
                    (clave, valor, descripcion, fecha_modificacion) 
                    VALUES (?, ?, ?, ?)
                ''', (clave, valor, f'Configuración de {clave}', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✅ Éxito", "Información de la empresa guardada correctamente")
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al guardar información: {e}")

# --- Interfaz compacta y moderna de Configuracion -------------------------
def _config_abrir_moderna(self):
    if self.window is not None and self.window.winfo_exists():
        self.window.lift()
        return
    self.window = ctk.CTkToplevel(self.parent)
    self.window.title("Configuracion del sistema")
    self.window.geometry("1120x720")
    self.window.minsize(900, 620)
    self.window.configure(fg_color="#f5f6f8")
    self.window.transient(self.parent)
    self.window.grab_set()

    cabecera = ctk.CTkFrame(self.window, height=76, corner_radius=0, fg_color="#ffffff")
    cabecera.pack(fill="x")
    cabecera.pack_propagate(False)
    ctk.CTkLabel(cabecera, text="Configuracion", font=ctk.CTkFont("Poppins", 20, "bold"),
                 text_color="#20242a").pack(anchor="w", padx=24, pady=(14, 0))
    ctk.CTkLabel(cabecera, text="Administra usuarios y preferencias del negocio desde un solo lugar",
                 font=ctk.CTkFont("Poppins", 10), text_color="#68707c").pack(anchor="w", padx=24)

    style = ttk.Style(self.window)
    style.configure("Config.TNotebook", background="#f5f6f8", borderwidth=0)
    style.configure("Config.TNotebook.Tab", font=("Poppins", 10, "bold"), padding=(18, 10),
                    background="#e9ebef", foreground="#343941")
    style.map("Config.TNotebook.Tab",
              background=[("selected", "#ffffff"), ("active", "#f5e9e9")],
              foreground=[("selected", "#8f070c"), ("active", "#8f070c")])
    notebook = ttk.Notebook(self.window, style="Config.TNotebook")
    notebook.pack(fill="both", expand=True, padx=20, pady=(14, 20))
    self.crear_pestaña_usuarios(notebook)
    self.crear_pestaña_monedas(notebook)
    self.crear_pestana_impuestos(notebook)
    self.crear_pestaña_empresa(notebook)


def _config_pestana_usuarios_moderna(self, notebook):
    base = ctk.CTkFrame(notebook, fg_color="#f5f6f8", corner_radius=0)
    notebook.add(base, text="Usuarios")
    base.grid_columnconfigure(0, weight=0, minsize=330)
    base.grid_columnconfigure(1, weight=1)
    base.grid_rowconfigure(0, weight=1)

    formulario = ctk.CTkScrollableFrame(base, width=315, fg_color="#ffffff", corner_radius=12,
                                        border_width=1, border_color="#e3e6ea")
    formulario.grid(row=0, column=0, sticky="nsew", padx=(4, 8), pady=10)
    self.form_frame_label = formulario
    self.form_title = ctk.CTkLabel(formulario, text="Nuevo usuario", font=ctk.CTkFont("Poppins", 14, "bold"), text_color="#20242a")
    self.form_title.pack(anchor="w", padx=6, pady=(3, 12))

    self.foto_usuario_path = None
    foto_box = ctk.CTkFrame(formulario, fg_color="#f5f6f8", corner_radius=12, height=116)
    foto_box.pack(fill="x", padx=4, pady=(0, 12)); foto_box.pack_propagate(False)
    self.foto_preview = ctk.CTkLabel(foto_box, text="US", width=62, height=62, corner_radius=31,
                                     fg_color="#8f070c", text_color="white", font=ctk.CTkFont("Poppins", 14, "bold"))
    self.foto_preview.place(x=14, y=27)
    ctk.CTkLabel(foto_box, text="Foto de perfil", font=ctk.CTkFont("Poppins", 10, "bold"), text_color="#20242a").place(x=92, y=24)
    ctk.CTkLabel(foto_box, text="PNG o JPG", font=ctk.CTkFont("Poppins", 8), text_color="#7b828c").place(x=92, y=45)
    ctk.CTkButton(foto_box, text="Seleccionar imagen", command=lambda: _config_seleccionar_foto(self),
                  width=154, height=31, corner_radius=7, fg_color="#ffffff", border_width=1,
                  border_color="#d9dde3", text_color="#505762", hover_color="#eceff3").place(x=92, y=69)

    def campo(etiqueta, show=None):
        ctk.CTkLabel(formulario, text=etiqueta, font=ctk.CTkFont("Poppins", 9, "bold"), text_color="#505762").pack(anchor="w", padx=6)
        entrada = ctk.CTkEntry(formulario, height=34, corner_radius=7, border_color="#d9dde3", show=show,
                               fg_color="#ffffff", text_color="#20242a", font=ctk.CTkFont("Poppins", 10))
        entrada.pack(fill="x", padx=4, pady=(3, 9))
        return entrada
    self.nuevo_usuario = campo("Usuario")
    self.nueva_password = campo("Contraseña", "*")
    self.nuevo_nombre = campo("Nombre completo")

    combos = ctk.CTkFrame(formulario, fg_color="transparent")
    combos.pack(fill="x", padx=4, pady=(0, 10)); combos.grid_columnconfigure((0, 1), weight=1)
    ctk.CTkLabel(combos, text="Rol", font=ctk.CTkFont("Poppins", 9, "bold"), text_color="#505762").grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(combos, text="Estado", font=ctk.CTkFont("Poppins", 9, "bold"), text_color="#505762").grid(row=0, column=1, sticky="w", padx=(6, 0))
    self.nuevo_rol = ctk.CTkComboBox(combos, values=["usuario", "supervisor", "administrador"], height=32, state="readonly")
    self.nuevo_rol.grid(row=1, column=0, sticky="ew", pady=3); self.nuevo_rol.set("usuario")
    self.nuevo_estado = ctk.CTkComboBox(combos, values=["activo", "suspendido", "bloqueado"], height=32, state="readonly")
    self.nuevo_estado.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=3); self.nuevo_estado.set("activo")

    ctk.CTkLabel(formulario, text="Permisos de modulos", font=ctk.CTkFont("Poppins", 9, "bold"), text_color="#505762").pack(anchor="w", padx=6)
    permisos = ctk.CTkFrame(formulario, fg_color="#f5f6f8", corner_radius=8)
    permisos.pack(fill="x", padx=4, pady=(4, 12))
    self.perm_vars = {}
    for i, (clave, nombre) in enumerate(MODULOS_SISTEMA):
        var = tk.BooleanVar(value=(clave == "informacion"))
        ctk.CTkCheckBox(permisos, text=nombre, variable=var, width=130, checkbox_width=17,
                        checkbox_height=17, font=ctk.CTkFont("Poppins", 9), fg_color="#8f070c",
                        hover_color="#71070a", text_color="#343941").grid(row=i // 2, column=i % 2, sticky="w", padx=8, pady=5)
        self.perm_vars[clave] = var

    acciones = ctk.CTkFrame(formulario, fg_color="transparent")
    acciones.pack(fill="x", padx=4, pady=(0, 6))
    self.btn_crear_guardar = ctk.CTkButton(acciones, text="Guardar usuario", command=self.crear_o_actualizar_usuario,
                                           height=36, corner_radius=8, fg_color="#8f070c", hover_color="#71070a")
    self.btn_crear_guardar.pack(side="left", fill="x", expand=True)
    self.btn_cancelar = ctk.CTkButton(acciones, text="Cancelar", command=self.cancelar_edicion,
                                      width=78, height=36, corner_radius=8, fg_color="#e9ebef", hover_color="#dde1e6", text_color="#505762")
    self.btn_cancelar.pack(side="left", padx=(6, 0)); self.btn_cancelar.pack_forget()

    lista = ctk.CTkFrame(base, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#e3e6ea")
    lista.grid(row=0, column=1, sticky="nsew", padx=(8, 4), pady=10)
    cab = ctk.CTkFrame(lista, fg_color="transparent", height=58); cab.pack(fill="x", padx=16, pady=(8, 0)); cab.pack_propagate(False)
    ctk.CTkLabel(cab, text="Usuarios registrados", font=ctk.CTkFont("Poppins", 14, "bold"), text_color="#20242a").pack(side="left")
    ctk.CTkButton(cab, text="Eliminar", command=self.eliminar_usuario, width=82, height=32, fg_color="#ffffff",
                  border_width=1, border_color="#e1b8b9", text_color="#8f070c", hover_color="#fff0f0").pack(side="right")
    ctk.CTkButton(cab, text="Editar", command=self.editar_usuario, width=76, height=32, fg_color="#343941",
                  hover_color="#20242a").pack(side="right", padx=7)
    style = ttk.Style(self.window)
    style.configure("Users.Treeview", rowheight=36, font=("Poppins", 9), borderwidth=0, background="#ffffff", fieldbackground="#ffffff")
    style.configure("Users.Treeview.Heading", font=("Poppins", 9, "bold"), background="#f1f3f5", foreground="#505762")
    self.tree_usuarios = ttk.Treeview(lista, columns=("ID", "Usuario", "Nombre", "Rol", "Estado"), show="headings", style="Users.Treeview")
    for col, ancho in (("ID", 48), ("Usuario", 115), ("Nombre", 190), ("Rol", 105), ("Estado", 90)):
        self.tree_usuarios.heading(col, text=col); self.tree_usuarios.column(col, width=ancho, minwidth=50, anchor="w", stretch=(col == "Nombre"))
    self.tree_usuarios.pack(fill="both", expand=True, padx=16, pady=(0, 16))
    self.tree_usuarios.bind("<Double-1>", lambda _e: self.editar_usuario())
    self.cargar_usuarios()


def _config_seleccionar_foto(self):
    ruta = filedialog.askopenfilename(parent=self.window, title="Seleccionar foto",
                                     filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
    if not ruta:
        return
    self.foto_usuario_path = ruta
    _config_mostrar_foto(self, ruta)


def _config_mostrar_foto(self, ruta):
    try:
        imagen = Image.open(ruta).convert("RGB")
        lado = min(imagen.size); x = (imagen.width - lado) // 2; y = (imagen.height - lado) // 2
        imagen = imagen.crop((x, y, x + lado, y + lado)).resize((62, 62), Image.LANCZOS)
        self._foto_ctk = ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(62, 62))
        self.foto_preview.configure(image=self._foto_ctk, text="")
    except Exception:
        self.foto_preview.configure(image=None, text="US")


def _config_guardar_usuario_moderno(self):
    from modulos.auth.seguridad import hash_password
    usuario, password, nombre = self.nuevo_usuario.get().strip(), self.nueva_password.get().strip(), self.nuevo_nombre.get().strip()
    if not usuario or (not self.modo_edicion and not password):
        messagebox.showwarning("Datos incompletos", "Captura el usuario y la contraseña.", parent=self.window); return
    try:
        conn = sqlite3.connect("database.db"); cur = conn.cursor()
        repetido = cur.execute("SELECT id FROM usuarios WHERE username=?", (usuario,)).fetchone()
        if repetido and (not self.modo_edicion or repetido[0] != self.usuario_editando_id):
            conn.close(); messagebox.showwarning("Usuario existente", "Ese nombre de usuario ya esta registrado.", parent=self.window); return
        rol, estado = self.nuevo_rol.get(), self.nuevo_estado.get()
        if self.modo_edicion:
            uid = self.usuario_editando_id
            if password:
                cur.execute("UPDATE usuarios SET username=?,nombre=?,rol=?,estado=?,password=? WHERE id=?",
                            (usuario, nombre or usuario, rol, estado, hash_password(password), uid))
            else:
                cur.execute("UPDATE usuarios SET username=?,nombre=?,rol=?,estado=? WHERE id=?",
                            (usuario, nombre or usuario, rol, estado, uid))
        else:
            cur.execute("INSERT INTO usuarios(username,password,nombre,rol,estado) VALUES(?,?,?,?,?)",
                        (usuario, hash_password(password), nombre or usuario, rol, estado)); uid = cur.lastrowid
        if self.foto_usuario_path and os.path.isfile(self.foto_usuario_path):
            carpeta = os.path.abspath(os.path.join("media", "perfiles")); os.makedirs(carpeta, exist_ok=True)
            ext = os.path.splitext(self.foto_usuario_path)[1].lower() or ".jpg"
            destino = os.path.join(carpeta, f"usuario_{uid}_{uuid.uuid4().hex[:8]}{ext}")
            if os.path.abspath(self.foto_usuario_path) != os.path.abspath(destino): shutil.copy2(self.foto_usuario_path, destino)
            cur.execute("UPDATE usuarios SET foto_perfil=? WHERE id=?", (destino, uid))
        conn.commit(); conn.close()
        guardar_permisos_usuario(uid, {clave: var.get() for clave, var in self.perm_vars.items()})
        messagebox.showinfo("Usuario guardado", "La cuenta y su imagen se guardaron correctamente.", parent=self.window)
        self.cancelar_edicion(); self.cargar_usuarios()
    except (sqlite3.Error, ValueError, RuntimeError) as exc:
        messagebox.showerror("No se pudo guardar", str(exc), parent=self.window)


def _config_cargar_usuarios_moderno(self):
    for item in self.tree_usuarios.get_children(): self.tree_usuarios.delete(item)
    with sqlite3.connect("database.db") as conn:
        filas = conn.execute("SELECT id,username,COALESCE(nombre,username),COALESCE(rol,'usuario'),COALESCE(estado,'activo') FROM usuarios ORDER BY nombre").fetchall()
    for fila in filas: self.tree_usuarios.insert("", "end", values=fila)


def _config_editar_usuario_moderno(self):
    seleccion = self.tree_usuarios.selection()
    if not seleccion:
        messagebox.showwarning("Selecciona un usuario", "Elige una cuenta de la lista.", parent=self.window); return
    uid = int(self.tree_usuarios.item(seleccion[0], "values")[0])
    with sqlite3.connect("database.db") as conn:
        fila = conn.execute("SELECT username,COALESCE(nombre,username),COALESCE(rol,'usuario'),COALESCE(estado,'activo'),foto_perfil FROM usuarios WHERE id=?", (uid,)).fetchone()
    if not fila: return
    self.modo_edicion = True; self.usuario_editando_id = uid
    for entrada, valor in ((self.nuevo_usuario, fila[0]), (self.nuevo_nombre, fila[1])):
        entrada.delete(0, "end"); entrada.insert(0, valor)
    self.nueva_password.delete(0, "end"); self.nuevo_rol.set(fila[2]); self.nuevo_estado.set(fila[3])
    self.foto_usuario_path = fila[4]
    if fila[4] and os.path.isfile(fila[4]): _config_mostrar_foto(self, fila[4])
    else: self.foto_preview.configure(image=None, text=(fila[1][:2].upper() if fila[1] else "US"))
    self.cargar_permisos_en_formulario(uid, fila[0]); self.form_title.configure(text="Editar usuario")
    self.btn_crear_guardar.configure(text="Guardar cambios"); self.btn_cancelar.pack(side="left", padx=(6, 0))


def _config_cancelar_usuario_moderno(self):
    self.modo_edicion = False; self.usuario_editando_id = None; self.foto_usuario_path = None
    for entrada in (self.nuevo_usuario, self.nueva_password, self.nuevo_nombre): entrada.delete(0, "end")
    self.nuevo_rol.set("usuario"); self.nuevo_estado.set("activo"); self.restaurar_permisos_default()
    self.form_title.configure(text="Nuevo usuario"); self.btn_crear_guardar.configure(text="Guardar usuario")
    self.btn_cancelar.pack_forget(); self.foto_preview.configure(image=None, text="US")
    for item in self.tree_usuarios.selection(): self.tree_usuarios.selection_remove(item)


GestorConfiguracion.abrir_ventana_configuracion = _config_abrir_moderna
GestorConfiguracion.crear_pestaña_usuarios = _config_pestana_usuarios_moderna
GestorConfiguracion.crear_o_actualizar_usuario = _config_guardar_usuario_moderno
GestorConfiguracion.cargar_usuarios = _config_cargar_usuarios_moderno
GestorConfiguracion.editar_usuario = _config_editar_usuario_moderno
GestorConfiguracion.cancelar_edicion = _config_cancelar_usuario_moderno

# Funciones globales para obtener configuración
def obtener_configuracion(clave, default=None):
    """Obtener valor de configuración"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion_sistema WHERE clave = ?", (clave,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else default
    except:
        return default

def formatear_precio(precio, mostrar_ambas=None):
    """Formatear precio según configuración de monedas"""
    try:
        if mostrar_ambas is None:
            mostrar_ambas = obtener_configuracion('mostrar_ambas_monedas', '1') == '1'
        
        moneda_principal = obtener_configuracion('moneda_principal', 'USD')
        tasa_cambio = float(obtener_configuracion('tasa_cambio', '36.50'))
        
        precio_float = float(precio)
        
        if mostrar_ambas:
            if moneda_principal == 'USD':
                precio_ves = precio_float * tasa_cambio
                return f"${precio_float:.2f} (Bs. {precio_ves:,.2f})"
            else:
                precio_usd = precio_float / tasa_cambio
                return f"Bs. {precio_float:,.2f} (${precio_usd:.2f})"
        else:
            if moneda_principal == 'USD':
                return f"${precio_float:.2f}"
            else:
                return f"Bs. {precio_float:,.2f}"
    except:
        return f"${precio:.2f}"




