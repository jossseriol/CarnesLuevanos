import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from modulos.utils.estilos_modernos import estilos
import sqlite3
from datetime import datetime, timedelta

# Configurar CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class GestorHistorial:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.crear_tabla_historial()
        
    def crear_tabla_historial(self):
        """Crear tabla de historial si no existe"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_actividades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    usuario TEXT DEFAULT 'Sistema',
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    descripcion TEXT,
                    detalles TEXT,
                    tipo TEXT DEFAULT 'INFO'
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al crear tabla de historial: {e}")
    
    @staticmethod
    def registrar_actividad(modulo, accion, descripcion="", detalles="", usuario="Sistema", tipo="INFO"):
        """Registrar una actividad en el historial"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            fecha = datetime.now().strftime('%Y-%m-%d')
            hora = datetime.now().strftime('%H:%M:%S')
            
            cursor.execute('''
                INSERT INTO historial_actividades 
                (fecha, hora, usuario, modulo, accion, descripcion, detalles, tipo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fecha, hora, usuario, modulo, accion, descripcion, detalles, tipo))
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al registrar actividad: {e}")
    
    def abrir_ventana_historial(self):
        """Abrir ventana principal de historial"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("📋 Historial de Actividades")
        self.window.geometry("1200x800+200+50")
        self.window.configure(bg=estilos.COLORS['bg_primary'])
        self.window.resizable(True, True)
        self.window.grab_set()
        self.window.focus_set()
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg=estilos.COLORS['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="📋 Historial de Actividades del Sistema", 
                              font=('Poppins', 20, 'bold'), 
                              bg=estilos.COLORS['bg_primary'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=(0, 20))
        
        # Frame de filtros
        filters_frame = tk.LabelFrame(main_frame, text="🔍 Filtros de Búsqueda", 
                                     font=('Poppins', 14, 'bold'), 
                                     bg=estilos.COLORS['white'],
                                     fg=estilos.COLORS['primary'])
        filters_frame.pack(fill='x', pady=(0, 20))
        
        # Primera fila de filtros
        filter_row1 = tk.Frame(filters_frame, bg=estilos.COLORS['white'])
        filter_row1.pack(fill='x', padx=10, pady=10)
        
        # Filtro por fecha
        tk.Label(filter_row1, text="📅 Fecha:", 
                font=('Poppins', 11, 'bold'), 
                bg=estilos.COLORS['white']).pack(side='left', padx=(0, 5))
        
        self.fecha_filtro = tk.Entry(filter_row1, font=('Poppins', 10), width=12)
        self.fecha_filtro.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.fecha_filtro.pack(side='left', padx=(0, 20))
        
        # Filtro por módulo
        tk.Label(filter_row1, text="📦 Módulo:", 
                font=('Poppins', 11, 'bold'), 
                bg=estilos.COLORS['white']).pack(side='left', padx=(0, 5))
        
        self.modulo_filtro = ttk.Combobox(filter_row1, font=('Poppins', 10), 
                                         values=["Todos", "Ventas", "Inventario", "Clientes", 
                                                "Pedidos", "Proveedores", "Sistema", "Login"], 
                                         state="readonly", width=15)
        self.modulo_filtro.set("Todos")
        self.modulo_filtro.pack(side='left', padx=(0, 20))
        
        # Filtro por tipo
        tk.Label(filter_row1, text="⚠️ Tipo:", 
                font=('Poppins', 11, 'bold'), 
                bg=estilos.COLORS['white']).pack(side='left', padx=(0, 5))
        
        self.tipo_filtro = ttk.Combobox(filter_row1, font=('Poppins', 10), 
                                       values=["Todos", "INFO", "SUCCESS", "WARNING", "ERROR"], 
                                       state="readonly", width=12)
        self.tipo_filtro.set("Todos")
        self.tipo_filtro.pack(side='left', padx=(0, 20))
        
        # Botones de filtro
        btn_filtrar = ctk.CTkButton(filter_row1, text="🔍 Filtrar", 
                                   command=self.aplicar_filtros,
                                   width=100, height=35,
                                   font=ctk.CTkFont(family="Poppins", size=11, weight="bold"),
                                   fg_color=estilos.COLORS['primary'])
        btn_filtrar.pack(side='left', padx=5)
        
        btn_limpiar = ctk.CTkButton(filter_row1, text="🗑️ Limpiar", 
                                   command=self.limpiar_filtros,
                                   width=100, height=35,
                                   font=ctk.CTkFont(family="Poppins", size=11, weight="bold"),
                                   fg_color=estilos.COLORS['secondary'])
        btn_limpiar.pack(side='left', padx=5)
        
        btn_exportar = ctk.CTkButton(filter_row1, text="📄 Exportar", 
                                    command=self.exportar_historial,
                                    width=100, height=35,
                                    font=ctk.CTkFont(family="Poppins", size=11, weight="bold"),
                                    fg_color=estilos.COLORS['warning'])
        btn_exportar.pack(side='left', padx=5)
        
        # Frame de la tabla
        table_frame = tk.LabelFrame(main_frame, text="📊 Registro de Actividades", 
                                   font=('Poppins', 14, 'bold'), 
                                   bg=estilos.COLORS['white'],
                                   fg=estilos.COLORS['primary'])
        table_frame.pack(fill='both', expand=True)
        
        # Configurar Treeview
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Historial.Treeview",
                       background=estilos.COLORS['white'],
                       foreground=estilos.COLORS['dark'],
                       fieldbackground=estilos.COLORS['white'],
                       font=('Poppins', 9))
        
        style.configure("Historial.Treeview.Heading",
                       background=estilos.COLORS['primary'],
                       foreground='white',
                       font=('Poppins', 10, 'bold'))
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient='vertical')
        scrollbar_y.pack(side='right', fill='y')
        
        scrollbar_x = ttk.Scrollbar(table_frame, orient='horizontal')
        scrollbar_x.pack(side='bottom', fill='x')
        
        # Treeview
        self.tree = ttk.Treeview(table_frame, 
                                style="Historial.Treeview",
                                yscrollcommand=scrollbar_y.set, 
                                xscrollcommand=scrollbar_x.set,
                                columns=("ID", "Fecha", "Hora", "Usuario", "Modulo", "Accion", "Descripcion", "Tipo"), 
                                show="headings",
                                height=25)
        
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Configurar encabezados
        self.tree.heading("ID", text="🆔 ID")
        self.tree.heading("Fecha", text="📅 Fecha")
        self.tree.heading("Hora", text="🕐 Hora")
        self.tree.heading("Usuario", text="👤 Usuario")
        self.tree.heading("Modulo", text="📦 Módulo")
        self.tree.heading("Accion", text="⚡ Acción")
        self.tree.heading("Descripcion", text="📝 Descripción")
        self.tree.heading("Tipo", text="⚠️ Tipo")
        
        # Configurar columnas
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Fecha", width=100, anchor="center")
        self.tree.column("Hora", width=80, anchor="center")
        self.tree.column("Usuario", width=100, anchor="center")
        self.tree.column("Modulo", width=100, anchor="center")
        self.tree.column("Accion", width=120, anchor="w")
        self.tree.column("Descripcion", width=300, anchor="w")
        self.tree.column("Tipo", width=80, anchor="center")
        
        # Bind para doble click
        self.tree.bind('<Double-1>', self.ver_detalles)
        
        # Frame de estadísticas
        stats_frame = tk.Frame(main_frame, bg=estilos.COLORS['white'], relief='solid', bd=1)
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.stats_label = tk.Label(stats_frame, text="📊 Cargando estadísticas...", 
                                   font=('Poppins', 10, 'bold'), 
                                   bg=estilos.COLORS['white'],
                                   fg=estilos.COLORS['primary'])
        self.stats_label.pack(pady=10)
        
        # Cargar datos iniciales
        self.cargar_historial()
        
        # Registrar que se abrió el historial
        self.registrar_actividad("Historial", "Ver Historial", "Usuario consultó el historial de actividades")
    
    def cargar_historial(self, filtros=None):
        """Cargar historial con filtros opcionales"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Construir query con filtros
            query = "SELECT * FROM historial_actividades WHERE 1=1"
            params = []
            
            if filtros:
                if filtros.get('fecha'):
                    query += " AND fecha = ?"
                    params.append(filtros['fecha'])
                
                if filtros.get('modulo') and filtros['modulo'] != 'Todos':
                    query += " AND modulo = ?"
                    params.append(filtros['modulo'])
                
                if filtros.get('tipo') and filtros['tipo'] != 'Todos':
                    query += " AND tipo = ?"
                    params.append(filtros['tipo'])
            
            query += " ORDER BY fecha DESC, hora DESC LIMIT 1000"
            
            cursor.execute(query, params)
            actividades = cursor.fetchall()
            
            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Cargar datos
            for actividad in actividades:
                # Agregar emoji según el tipo
                tipo_emoji = {
                    'INFO': '💡',
                    'SUCCESS': '✅',
                    'WARNING': '⚠️',
                    'ERROR': '❌'
                }.get(actividad[8], '💡')
                
                # Formatear datos
                valores = (
                    actividad[0],  # ID
                    actividad[1],  # Fecha
                    actividad[2],  # Hora
                    actividad[3],  # Usuario
                    actividad[4],  # Módulo
                    actividad[5],  # Acción
                    actividad[6][:50] + "..." if len(str(actividad[6])) > 50 else actividad[6],  # Descripción
                    f"{tipo_emoji} {actividad[8]}"  # Tipo con emoji
                )
                
                self.tree.insert("", "end", values=valores)
            
            # Actualizar estadísticas
            self.actualizar_estadisticas(len(actividades))
            
            conn.close()
            
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al cargar historial: {e}")
    
    def aplicar_filtros(self):
        """Aplicar filtros seleccionados"""
        filtros = {
            'fecha': self.fecha_filtro.get().strip() if self.fecha_filtro.get().strip() else None,
            'modulo': self.modulo_filtro.get(),
            'tipo': self.tipo_filtro.get()
        }
        
        self.cargar_historial(filtros)
        self.registrar_actividad("Historial", "Filtrar", f"Aplicados filtros: {filtros}")
    
    def limpiar_filtros(self):
        """Limpiar todos los filtros"""
        self.fecha_filtro.delete(0, 'end')
        self.fecha_filtro.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.modulo_filtro.set("Todos")
        self.tipo_filtro.set("Todos")
        self.cargar_historial()
    
    def ver_detalles(self, event):
        """Ver detalles completos de una actividad"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        valores = self.tree.item(item, "values")
        
        if not valores:
            return
        
        # Obtener detalles completos de la base de datos
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM historial_actividades WHERE id = ?", (valores[0],))
            actividad = cursor.fetchone()
            conn.close()
            
            if actividad:
                self.mostrar_ventana_detalles(actividad)
                
        except sqlite3.Error as e:
            messagebox.showerror("❌ Error", f"Error al obtener detalles: {e}")
    
    def mostrar_ventana_detalles(self, actividad):
        """Mostrar ventana con detalles completos"""
        detalle_window = tk.Toplevel(self.window)
        detalle_window.title("🔍 Detalles de Actividad")
        detalle_window.geometry("600x500+400+200")
        detalle_window.configure(bg=estilos.COLORS['white'])
        detalle_window.resizable(False, False)
        detalle_window.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(detalle_window, bg=estilos.COLORS['white'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="🔍 Detalles de la Actividad", 
                              font=('Poppins', 16, 'bold'), 
                              bg=estilos.COLORS['white'],
                              fg=estilos.COLORS['primary'])
        title_label.pack(pady=(0, 20))
        
        # Información básica
        info_frame = tk.LabelFrame(main_frame, text="📋 Información Básica", 
                                  font=('Poppins', 12, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        info_frame.pack(fill='x', pady=(0, 15))
        
        # Crear etiquetas de información
        info_data = [
            ("🆔 ID:", str(actividad[0])),
            ("📅 Fecha:", actividad[1]),
            ("🕐 Hora:", actividad[2]),
            ("👤 Usuario:", actividad[3]),
            ("📦 Módulo:", actividad[4]),
            ("⚡ Acción:", actividad[5]),
            ("⚠️ Tipo:", actividad[8])
        ]
        
        for i, (label, value) in enumerate(info_data):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(info_frame, text=label, font=('Poppins', 10, 'bold'), 
                    bg=estilos.COLORS['white']).grid(row=row, column=col, sticky='w', padx=10, pady=5)
            tk.Label(info_frame, text=value, font=('Poppins', 10), 
                    bg=estilos.COLORS['white']).grid(row=row, column=col+1, sticky='w', padx=10, pady=5)
        
        # Descripción
        desc_frame = tk.LabelFrame(main_frame, text="📝 Descripción", 
                                  font=('Poppins', 12, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['primary'])
        desc_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        desc_text = tk.Text(desc_frame, font=('Poppins', 10), 
                           bg=estilos.COLORS['light'], wrap='word', height=6)
        desc_text.pack(fill='both', expand=True, padx=10, pady=10)
        desc_text.insert('1.0', actividad[6] or "Sin descripción")
        desc_text.config(state='disabled')
        
        # Detalles técnicos
        if actividad[7]:  # Si hay detalles
            details_frame = tk.LabelFrame(main_frame, text="🔧 Detalles Técnicos", 
                                         font=('Poppins', 12, 'bold'), 
                                         bg=estilos.COLORS['white'],
                                         fg=estilos.COLORS['primary'])
            details_frame.pack(fill='both', expand=True)
            
            details_text = tk.Text(details_frame, font=('Consolas', 9), 
                                  bg=estilos.COLORS['light'], wrap='word', height=4)
            details_text.pack(fill='both', expand=True, padx=10, pady=10)
            details_text.insert('1.0', actividad[7])
            details_text.config(state='disabled')
        
        # Botón cerrar
        btn_cerrar = ctk.CTkButton(main_frame, text="❌ Cerrar", 
                                  command=detalle_window.destroy,
                                  width=100, height=35,
                                  font=ctk.CTkFont(family="Poppins", size=11, weight="bold"),
                                  fg_color=estilos.COLORS['secondary'])
        btn_cerrar.pack(pady=10)
    
    def actualizar_estadisticas(self, total_registros):
        """Actualizar estadísticas del historial"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Contar por tipo
            cursor.execute("SELECT tipo, COUNT(*) FROM historial_actividades GROUP BY tipo")
            tipos = dict(cursor.fetchall())
            
            # Contar por módulo (últimos 7 días)
            fecha_limite = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute("SELECT modulo, COUNT(*) FROM historial_actividades WHERE fecha >= ? GROUP BY modulo", (fecha_limite,))
            modulos = dict(cursor.fetchall())
            
            conn.close()
            
            # Formatear estadísticas
            stats_text = f"📊 Mostrando {total_registros} registros | "
            stats_text += f"✅ Éxitos: {tipos.get('SUCCESS', 0)} | "
            stats_text += f"⚠️ Advertencias: {tipos.get('WARNING', 0)} | "
            stats_text += f"❌ Errores: {tipos.get('ERROR', 0)} | "
            stats_text += f"💡 Info: {tipos.get('INFO', 0)}"
            
            self.stats_label.config(text=stats_text)
            
        except sqlite3.Error as e:
            self.stats_label.config(text=f"❌ Error al cargar estadísticas: {e}")
    
    def exportar_historial(self):
        """Exportar historial a archivo"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                title="Exportar Historial"
            )
            
            if filename:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM historial_actividades ORDER BY fecha DESC, hora DESC")
                actividades = cursor.fetchall()
                
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write("HISTORIAL DE ACTIVIDADES DEL SISTEMA\n")
                    file.write("=" * 80 + "\n")
                    file.write(f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    file.write(f"Total de registros: {len(actividades)}\n\n")
                    
                    for actividad in actividades:
                        file.write(f"ID: {actividad[0]}\n")
                        file.write(f"Fecha/Hora: {actividad[1]} {actividad[2]}\n")
                        file.write(f"Usuario: {actividad[3]}\n")
                        file.write(f"Módulo: {actividad[4]}\n")
                        file.write(f"Acción: {actividad[5]}\n")
                        file.write(f"Tipo: {actividad[8]}\n")
                        file.write(f"Descripción: {actividad[6]}\n")
                        if actividad[7]:
                            file.write(f"Detalles: {actividad[7]}\n")
                        file.write("-" * 80 + "\n\n")
                
                conn.close()
                messagebox.showinfo("✅ Éxito", f"Historial exportado a:\n{filename}")
                self.registrar_actividad("Historial", "Exportar", f"Historial exportado a {filename}")
                
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al exportar: {e}")

# Función para registrar actividades desde otros módulos
def registrar_actividad(modulo, accion, descripcion="", detalles="", usuario="Sistema", tipo="INFO"):
    """Función global para registrar actividades"""
    GestorHistorial.registrar_actividad(modulo, accion, descripcion, detalles, usuario, tipo)



