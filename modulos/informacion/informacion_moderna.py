import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from modulos.utils.estilos_modernos import estilos
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import webbrowser

# Configurar CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class InformacionModerna(tk.Frame):
    
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.widgets()
    
    def actualizar_moneda(self, nueva_moneda):
        """Actualizar estadísticas cuando cambia la moneda"""
        try:
            self._actualizar_centro_info()
            print(f"Módulo Información actualizado a moneda: {nueva_moneda}")
        except Exception as e:
            print(f"Error al actualizar moneda en Información: {e}")
        
    def widgets(self):
        self.configure(bg='#f5f6f8')
        self.info_scroll = ctk.CTkScrollableFrame(
            self, fg_color='#f5f6f8', bg_color='#f5f6f8', corner_radius=0,
            scrollbar_button_color='#dfe2e6',
            scrollbar_button_hover_color='#cfd5dc')
        self.info_scroll.pack(fill='both', expand=True)

        encabezado = ctk.CTkFrame(
            self.info_scroll, height=112, fg_color='#ffffff', corner_radius=14,
            border_width=1, border_color=estilos.COLORS['border'])
        encabezado.pack(fill='x', padx=20, pady=(18, 12)); encabezado.pack_propagate(False)
        ctk.CTkLabel(encabezado, text='Centro de Información',
                     font=ctk.CTkFont('Poppins', 22, 'bold'),
                     text_color=estilos.COLORS['wine']).place(x=24, y=18)
        ctk.CTkLabel(encabezado, text='Indicadores, herramientas y accesos administrativos del sistema',
                     font=ctk.CTkFont('Poppins', 11), text_color=estilos.COLORS['gray']).place(x=24, y=56)
        self.info_actualizacion = ctk.CTkLabel(
            encabezado, text='', font=ctk.CTkFont('Poppins', 9, 'bold'),
            text_color='#23834a')
        self.info_actualizacion.place(relx=1, x=-24, y=24, anchor='ne')

        self.info_cards_host = ctk.CTkFrame(self.info_scroll, fg_color='transparent')
        self.info_cards_host.pack(fill='x', padx=14, pady=(0, 20))
        self.info_cards = []
        self.info_values = {}
        tarjetas = (
            ('Reportes de ventas', '▥', 'Genera documentos con la actividad comercial registrada.',
             'Reportes disponibles', 'Generar reporte', self.generar_reporte, '#8f070c'),
            ('Estado operativo', '◫', 'Consulta productos, clientes y pedidos registrados.',
             'Cargando indicadores…', 'Actualizar datos', self._actualizar_centro_info, '#2563eb'),
            ('Inventario', '◇', 'Revisa existencias y productos que necesitan atención.',
             'Cargando existencias…', 'Abrir inventario', lambda: self._abrir_area('Inventario'), '#0f766e'),
            ('Historial del sistema', '◷', 'Audita movimientos y actividad reciente del programa.',
             'Actividad disponible', 'Ver historial', self.ver_historial_completo, '#7c3aed'),
            ('Configuración', '⚙', 'Administra empresa, seguridad, usuarios y preferencias.',
             'Acceso administrativo', 'Abrir configuración', self.abrir_configuracion, '#475569'),
            ('Acerca del sistema', 'i', 'Consulta versión, componentes y características instaladas.',
             'Carnes Luévanos', 'Ver información', self.mostrar_info_detallada, '#b7791f'),
        )
        for indice, datos in enumerate(tarjetas):
            self._crear_tarjeta_adaptable(indice, *datos)
        self.bind('<Configure>', self._programar_layout_info, add='+')
        self.after(80, self._ajustar_layout_info)
        for delay in (0, 200, 600):
            self.after(delay, self._aplicar_modo_claro_informacion)
        self._actualizar_centro_info()

    def _aplicar_modo_claro_informacion(self):
        """Mantiene claro el fondo exterior del centro de informacion."""
        self.configure(bg='#f5f6f8')
        try:
            self.info_scroll.configure(
                fg_color='#f5f6f8',
                bg_color='#f5f6f8',
                scrollbar_button_color='#dfe2e6',
                scrollbar_button_hover_color='#cfd5dc',
            )
        except Exception:
            pass
        try:
            self.info_cards_host.configure(fg_color='transparent', bg_color='#f5f6f8')
        except Exception:
            pass

    def _crear_tarjeta_adaptable(self, indice, titulo, icono, descripcion, valor, boton, accion, color):
        card = ctk.CTkFrame(
            self.info_cards_host, height=224, fg_color='#ffffff', corner_radius=14,
            border_width=1, border_color=estilos.COLORS['border'])
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=icono, width=42, height=42, corner_radius=12,
                     fg_color=color, text_color='#ffffff',
                     font=ctk.CTkFont('Poppins', 18, 'bold')).place(x=18, y=18)
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont('Poppins', 14, 'bold'),
                     text_color=estilos.COLORS['dark']).place(x=72, y=19)
        ctk.CTkLabel(card, text=descripcion, wraplength=250, justify='left', anchor='w',
                     font=ctk.CTkFont('Poppins', 10), text_color=estilos.COLORS['gray']).place(x=72, y=45)
        valor_label = ctk.CTkLabel(card, text=valor, justify='left', anchor='w',
                                   font=ctk.CTkFont('Poppins', 11, 'bold'), text_color=color)
        valor_label.place(x=20, y=115)
        ctk.CTkButton(card, text=boton, command=accion, height=36, corner_radius=9,
                      fg_color=color, hover_color=estilos.COLORS['primary_dark1'],
                      font=ctk.CTkFont('Poppins', 10, 'bold')).place(
                          relx=.5, rely=1, y=-18, anchor='s', relwidth=.88)
        self.info_cards.append(card)
        self.info_values[indice] = valor_label

    def _programar_layout_info(self, event=None):
        if event is not None and event.widget is not self:
            return
        if hasattr(self, '_info_layout_after') and self._info_layout_after:
            self.after_cancel(self._info_layout_after)
        self._info_layout_after = self.after(60, self._ajustar_layout_info)

    def _ajustar_layout_info(self):
        self._info_layout_after = None
        ancho = max(360, self.winfo_width())
        columnas = 3 if ancho >= 1120 else 2 if ancho >= 720 else 1
        for columna in range(3):
            self.info_cards_host.grid_columnconfigure(columna, weight=1 if columna < columnas else 0,
                                                       uniform='info_cards' if columna < columnas else '')
        for indice, card in enumerate(self.info_cards):
            card.grid_forget()
            card.grid(row=indice // columnas, column=indice % columnas,
                      sticky='nsew', padx=6, pady=7)

    def _actualizar_centro_info(self):
        try:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            productos = cur.execute('SELECT COUNT(*) FROM articulos').fetchone()[0]
            clientes = cur.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
            pedidos = cur.execute("SELECT COUNT(*) FROM pedidos_proveedor WHERE LOWER(COALESCE(estado,'')) != 'recibido'").fetchone()[0]
            bajos = cur.execute('SELECT COUNT(*) FROM articulos WHERE COALESCE(stock,0) <= 5').fetchone()[0]
            conn.close()
            self.info_values[1].configure(text=f'{productos} productos · {clientes} clientes · {pedidos} pedidos')
            self.info_values[2].configure(text=f'{bajos} productos con existencia baja')
            self.info_actualizacion.configure(text=datetime.now().strftime('Actualizado %d/%m/%Y · %I:%M %p'))
        except Exception:
            self.info_values[1].configure(text='Indicadores temporalmente no disponibles')

    def _abrir_area(self, nombre):
        actual = self.master
        while actual is not None:
            comando = getattr(actual, nombre, None)
            if callable(comando):
                comando()
                return
            actual = getattr(actual, 'master', None)

    def crear_card_reporte(self, parent, x, y):
        """Crear card de reportes"""
        card = tk.LabelFrame(parent, text="📈 Reportes de Ventas", 
                            font=('Poppins', 14, 'bold'), 
                            bg=estilos.COLORS['white'],
                            fg=estilos.COLORS['primary'],
                            relief='solid', bd=1)
        card.place(x=x, y=y, width=350, height=250)
        
        # Icono grande (tamaño optimizado para que no lo tape el texto)
        icon_label = tk.Label(card, text="📊", font=('Poppins', 56), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['success'])
        icon_label.place(x=145, y=15)
        
        # Descripción (más separado del ícono)
        desc_label = tk.Label(card, text="Generar reportes detallados\nde ventas y transacciones", 
                             font=('Poppins', 11), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['dark'],
                             justify='center')
        desc_label.place(x=75, y=120)
        
        # Botón moderno
        btn_reporte = ctk.CTkButton(
            card, 
            text="📊 Generar Reporte", 
            command=self.generar_reporte,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['success'],
            hover_color="#8f070c"
        )
        btn_reporte.place(x=25, y=180)

    def crear_card_estadisticas(self, parent, x, y):
        """Crear card de estadísticas"""
        card = tk.LabelFrame(parent, text="📊 Estadísticas del Sistema", 
                            font=('Poppins', 14, 'bold'), 
                            bg=estilos.COLORS['white'],
                            fg=estilos.COLORS['primary'],
                            relief='solid', bd=1)
        card.place(x=x, y=y, width=350, height=250)
        
        # Icono grande (tamaño optimizado para que no lo tape el texto)
        icon_label = tk.Label(card, text="📈", font=('Poppins', 56), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['info'])
        icon_label.place(x=145, y=15)
        
        # Estadísticas en tiempo real (más separado del ícono)
        self.stats_frame = tk.Frame(card, bg=estilos.COLORS['white'])
        self.stats_frame.place(x=25, y=120, width=300, height=70)
        
        self.cargar_estadisticas()
        
        # Botón moderno
        btn_stats = ctk.CTkButton(
            card, 
            text="🔄 Actualizar Stats", 
            command=self.actualizar_estadisticas,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['info'],
            hover_color="#b30d12"
        )
        btn_stats.place(x=25, y=180)

    def crear_card_info_sistema(self, parent, x, y):
        """Crear card de información del sistema"""
        card = tk.LabelFrame(parent, text="ℹ️ Información del Sistema", 
                            font=('Poppins', 14, 'bold'), 
                            bg=estilos.COLORS['white'],
                            fg=estilos.COLORS['primary'],
                            relief='solid', bd=1)
        card.place(x=x, y=y, width=350, height=250)
        
        # Icono grande (tamaño optimizado para que no lo tape el texto)
        icon_label = tk.Label(card, text="💻", font=('Poppins', 56), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['accent'])
        icon_label.place(x=145, y=15)
        
        # Información del sistema (texto simplificado)
        info_text = f"""Sistema de Punto de Venta
Versión: 2.0 Moderna
Fecha: {datetime.now().strftime('%Y-%m-%d')}"""
        
        info_label = tk.Label(card, text=info_text, 
                             font=('Poppins', 10), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['dark'],
                             justify='center')
        info_label.place(x=75, y=120)
        
        # Botón moderno
        btn_info = ctk.CTkButton(
            card, 
            text="ℹ️ Más Información", 
            command=self.mostrar_info_detallada,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['accent'],
            hover_color="#8f070c"
        )
        btn_info.place(x=25, y=180)

    def crear_card_inventario(self, parent, x, y):
        """Crear card de resumen de inventario"""
        card = tk.LabelFrame(parent, text="📦 Resumen de Inventario", 
                            font=('Poppins', 14, 'bold'), 
                            bg=estilos.COLORS['white'],
                            fg=estilos.COLORS['primary'],
                            relief='solid', bd=1)
        card.place(x=x, y=y, width=350, height=250)
        
        # Icono grande (tamaño optimizado para que no lo tape el texto)
        icon_label = tk.Label(card, text="📦", font=('Poppins', 56), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['warning'])
        icon_label.place(x=145, y=15)
        
        # Frame para estadísticas de inventario (más separado del ícono)
        self.inventario_frame = tk.Frame(card, bg=estilos.COLORS['white'])
        self.inventario_frame.place(x=25, y=120, width=300, height=70)
        
        self.cargar_resumen_inventario()
        
        # Botón moderno
        btn_inventario = ctk.CTkButton(
            card, 
            text="📦 Ver Inventario", 
            command=self.ver_inventario_detallado,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['warning'],
            hover_color="#d7b56d"
        )
        btn_inventario.place(x=25, y=180)

    def crear_card_actividad(self, parent, x, y):
        """Crear card de actividad reciente"""
        card = tk.LabelFrame(parent, text="🕒 Actividad Reciente", 
                            font=('Poppins', 14, 'bold'), 
                            bg=estilos.COLORS['white'],
                            fg=estilos.COLORS['primary'],
                            relief='solid', bd=1)
        card.place(x=x, y=y, width=350, height=250)
        
        # Icono grande (tamaño optimizado para que no lo tape el texto)
        icon_label = tk.Label(card, text="📋", font=('Poppins', 56), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['secondary'])
        icon_label.place(x=145, y=15)
        
        # Frame para actividad reciente (más separado del ícono)
        self.actividad_frame = tk.Frame(card, bg=estilos.COLORS['white'])
        self.actividad_frame.place(x=25, y=120, width=300, height=70)
        
        self.cargar_actividad_reciente()
        
        # Botón moderno
        btn_actividad = ctk.CTkButton(
            card, 
            text="📋 Ver Historial", 
            command=self.ver_historial_completo,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['secondary'],
            hover_color="#8f070c"
        )
        btn_actividad.place(x=25, y=180)

    def crear_card_configuracion(self, parent, x, y):
        """Crear card de configuración"""
        card = tk.LabelFrame(parent, text="⚙️ Configuración", 
                            font=('Poppins', 14, 'bold'), 
                            bg=estilos.COLORS['white'],
                            fg=estilos.COLORS['primary'],
                            relief='solid', bd=1)
        card.place(x=x, y=y, width=350, height=250)
        
        # Icono grande (tamaño optimizado para que no lo tape el texto)
        icon_label = tk.Label(card, text="⚙️", font=('Poppins', 56), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['gray'])
        icon_label.place(x=145, y=15)
        
        # Descripción (más separado del ícono)
        desc_label = tk.Label(card, text="Configurar parámetros\ndel sistema y preferencias", 
                             font=('Poppins', 11), 
                             bg=estilos.COLORS['white'],
                             fg=estilos.COLORS['dark'],
                             justify='center')
        desc_label.place(x=75, y=120)
        
        # Botón moderno
        btn_config = ctk.CTkButton(
            card, 
            text="⚙️ Configuración", 
            command=self.abrir_configuracion,
            width=300,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold"),
            fg_color=estilos.COLORS['gray'],
            hover_color="#5a4b48"
        )
        btn_config.place(x=25, y=180)

    def cargar_estadisticas(self):
        """Cargar estadísticas del sistema"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Contar productos
            cursor.execute("SELECT COUNT(*) FROM productos")
            total_productos = cursor.fetchone()[0]
            
            # Contar clientes
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            
            # Contar pedidos
            cursor.execute("SELECT COUNT(*) FROM pedidos_proveedor")
            total_pedidos = cursor.fetchone()[0]
            
            conn.close()
            
            # Mostrar estadísticas
            stats_text = f"📦 Productos: {total_productos}\n👥 Clientes: {total_clientes}\n📋 Pedidos: {total_pedidos}"
            
            stats_label = tk.Label(self.stats_frame, text=stats_text, 
                                  font=('Poppins', 10, 'bold'), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['dark'],
                                  justify='left')
            stats_label.place(x=0, y=0)
            
        except sqlite3.Error as e:
            error_label = tk.Label(self.stats_frame, text="Error al cargar estadísticas", 
                                  font=('Poppins', 10), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['danger'])
            error_label.place(x=0, y=0)

    def cargar_resumen_inventario(self):
        """Cargar resumen del inventario"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Stock total
            cursor.execute("SELECT SUM(stock) FROM productos")
            stock_total = cursor.fetchone()[0] or 0
            
            # Productos con stock bajo (menos de 10)
            cursor.execute("SELECT COUNT(*) FROM productos WHERE stock < 10")
            stock_bajo = cursor.fetchone()[0]
            
            conn.close()
            
            # Mostrar resumen
            resumen_text = f"📊 Stock Total: {stock_total}\n⚠️ Stock Bajo: {stock_bajo} productos"
            
            resumen_label = tk.Label(self.inventario_frame, text=resumen_text, 
                                    font=('Poppins', 10, 'bold'), 
                                    bg=estilos.COLORS['white'],
                                    fg=estilos.COLORS['dark'],
                                    justify='left')
            resumen_label.place(x=0, y=0)
            
        except sqlite3.Error as e:
            error_label = tk.Label(self.inventario_frame, text="Error al cargar inventario", 
                                  font=('Poppins', 10), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['danger'])
            error_label.place(x=0, y=0)

    def cargar_actividad_reciente(self):
        """Cargar actividad reciente"""
        actividad_text = f"🕒 Última actualización:\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n✅ Sistema operativo"
        
        actividad_label = tk.Label(self.actividad_frame, text=actividad_text, 
                                  font=('Poppins', 10), 
                                  bg=estilos.COLORS['white'],
                                  fg=estilos.COLORS['dark'],
                                  justify='left')
        actividad_label.place(x=0, y=0)

    # Funciones de los botones
    def generar_reporte(self):
        """Generar reporte de ventas"""
        try:
            from modulos.reportes.generador_reportes import GeneradorReportes
            generador = GeneradorReportes(self)
            generador.abrir_ventana_reportes()
        except ImportError as e:
            messagebox.showerror("❌ Error", f"Error al cargar módulo de reportes: {e}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al abrir reportes: {e}")

    def actualizar_estadisticas(self):
        """Actualizar estadísticas"""
        # Limpiar frame
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Recargar estadísticas
        self.cargar_estadisticas()
        messagebox.showinfo("🔄 Actualizado", "Estadísticas actualizadas correctamente")

    def mostrar_info_detallada(self):
        """Mostrar información detallada del sistema"""
        info_detallada = f"""
🖥️ Sistema Administrativo Carnes Luévanos 

📋 Información Técnica:
• Versión: 1.0 C-LAdmin
• Tecnología: Python 3.0 + Tkinter + CustomTkinter
• Base de datos: SQLite con API local para móvil
• Interfaz: Escritorio moderno con conexión local/cloud

✨ Características:
• Gestión de inventario
• Registro de clientes
• Pedidos a proveedores
• Interfaz moderna y clara
• Actualización automática de stock

👨‍💻 Desarrollado por Alpha Systems Company
📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        messagebox.showinfo("ℹ️ Información del Sistema", info_detallada)

    def ver_inventario_detallado(self):
        """Ver inventario detallado"""
        messagebox.showinfo("📦 Inventario", "Para ver el inventario detallado,\nnavega a la sección 'Inventario' en el menú principal.")

    def ver_historial_completo(self):
        """Ver historial completo"""
        try:
            from modulos.historial.gestor_historial import GestorHistorial
            gestor = GestorHistorial(self)
            gestor.abrir_ventana_historial()
        except ImportError as e:
            messagebox.showerror("❌ Error", f"Error al cargar módulo de historial: {e}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al abrir historial: {e}")

    def abrir_configuracion(self):
        """Abrir configuracion"""
        self._abrir_area('Configuracion')





