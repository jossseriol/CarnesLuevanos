from tkinter import *
from tkinter import ttk
from data.models import crear_base_de_datos
from PIL import Image, ImageTk

from login_simple import mostrar_login_simple, aplicar_barra_titulo_personalizada
from modulos.utils.utils import resource_path
from modulos.utils.estilos_modernos import estilos
from modulos.utils.font_loader import registrar_fuentes

import sys
import os
import threading

_API_LOCAL_INICIADA = False


def obtener_area_trabajo(root):
    """Obtiene el área física útil del monitor, excluyendo la barra de tareas."""
    if os.name == 'nt':
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ('left', ctypes.c_long), ('top', ctypes.c_long),
                    ('right', ctypes.c_long), ('bottom', ctypes.c_long),
                ]

            rect = RECT()
            if ctypes.windll.user32.SystemParametersInfoW(
                    48, 0, ctypes.byref(rect), 0):
                return (
                    rect.left, rect.top,
                    rect.right - rect.left, rect.bottom - rect.top,
                )
        except Exception:
            pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def iniciar_api_local_global():
    """Levantar la API local una sola vez para Android/iOS."""
    global _API_LOCAL_INICIADA
    if _API_LOCAL_INICIADA:
        return
    _API_LOCAL_INICIADA = True

    def run_api():
        try:
            project_root = os.path.dirname(os.path.abspath(__file__))
            database_path = os.path.join(project_root, "database.db")
            os.environ["DATABASE_PATH"] = database_path
            os.environ.setdefault("DATABASE_SEED_PATH", database_path)
            import uvicorn
            from api.main import app as api_app
            config = uvicorn.Config(
                api_app,
                host="0.0.0.0",
                port=8000,
                log_level="warning",
                access_log=False,
                log_config=None,
            )
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            try:
                from pathlib import Path
                log_path = Path(sys.executable).resolve().parent / "api_error.log"
                log_path.write_text(str(e), encoding="utf-8")
            except Exception:
                pass
            print(f"No se pudo iniciar la API local: {e}")

    threading.Thread(target=run_api, daemon=True).start()


class Manager(Tk):
    def __init__(self, usuario_actual=None, *args, **kwargs):
        registrar_fuentes()
        super().__init__(*args, **kwargs)
        # El login CTk activa el escalado DPI de Windows (125 % en el equipo
        # objetivo). Normalizamos el factor de usuario para que las medidas
        # del diseño sigan siendo píxeles reales y no se escalen dos veces.
        try:
            import ctypes
            import customtkinter as ctk

            dpi = int(ctypes.windll.user32.GetDpiForSystem())
            factor = 96.0 / max(96, dpi)
            ctk.set_widget_scaling(factor)
            ctk.set_window_scaling(factor)
            self.ctk_scale_normalizada = factor
        except Exception:
            self.ctk_scale_normalizada = 1.0
        # Escala tipográfica más compacta para aprovechar mejor el espacio.
        try:
            escala_actual = float(self.tk.call('tk', 'scaling'))
            self.tk.call('tk', 'scaling', max(0.85, escala_actual * 0.88))
            self.option_add('*Font', ('Poppins', 9))
        except Exception:
            pass
        self.usuario_actual = usuario_actual
        from login_simple import obtener_sesion_actual
        self.session_id = obtener_sesion_actual()
        self.title("Sistema administrativo | Carnes Luévanos")
        # Aprovecha toda el área útil del monitor. En el equipo objetivo esto
        # permite trabajar a 1920 px de ancho sin el antiguo límite de 1680.
        x, y, win_w, win_h = obtener_area_trabajo(self)
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(1100, 700)
        self.update_idletasks()
        self.barra_titulo = aplicar_barra_titulo_personalizada(
            self,
            texto='Sistema administrativo | Carnes Luévanos',
            permitir_maximizar=True,
            cerrar_callback=self.confirmar_cierre_programa,
        )
        
        # Aplicar colores modernos de fondo
        self.configure(bg=estilos.COLORS['bg_primary'])
        
        # Icono de la aplicación
        try:
            icon_path = resource_path("media/icons/logo_luevanos.ico")  
            self.iconbitmap(icon_path)
        except:
            pass  # Si no encuentra el icono, continúa sin error

        from container import Container

        # Container principal con estilos modernos
        container = Frame(self, bg=estilos.COLORS['bg_primary'])
        container.pack(side=TOP, fill=BOTH, expand=True, pady=(34, 0))
        container.configure(width=win_w, height=win_h - 34)
        
        # Crear solo el container principal
        self.container_frame = Container(container, self, usuario_actual=self.usuario_actual)
        self.container_frame.pack(fill=BOTH, expand=True)
        self.barra_titulo.lift()
        self.after(120, self._mostrar_dashboard_al_frente)
        self.protocol("WM_DELETE_WINDOW", self.confirmar_cierre_programa)
        self.bind_all('<KeyPress>', self._registrar_actividad, add='+')
        self.bind_all('<Button>', self._registrar_actividad, add='+')
        self.after(30_000, self._vigilar_sesion)
        self.iniciar_api_local()
        
        # El contenedor inicia en el primer modulo permitido del usuario.
        
        # Configurar tema y estilos modernos
        self.configurar_estilos_modernos()

        crear_base_de_datos()


    def _mostrar_dashboard_al_frente(self):
        """Muestra el dashboard al cambiar desde el login sin dejarlo siempre arriba."""
        try:
            self.container_frame.Inicio()
            self.attributes('-topmost', True)
            self.lift()
            self.focus_force()
            self.after(500, lambda: self.attributes('-topmost', False))
        except TclError:
            pass



    def iniciar_api_local(self):
        iniciar_api_local_global()

    def _registrar_actividad(self, _event=None):
        if self.session_id:
            from modulos.auth.seguridad import touch_session
            touch_session(self.session_id)

    def _vigilar_sesion(self):
        if self.session_id:
            from modulos.auth.seguridad import touch_session
            if not touch_session(self.session_id):
                from tkinter import messagebox
                messagebox.showwarning('Sesión finalizada', 'La sesión se cerró por inactividad o vencimiento.')
                self.destroy()
                os.execl(sys.executable, sys.executable, *sys.argv)
                return
        self.after(30_000, self._vigilar_sesion)

    def confirmar_cierre_programa(self):
        """Preguntar si se desean guardar cambios antes de cerrar."""
        def guardar_y_cerrar():
            try:
                from tkinter import messagebox
                messagebox.showinfo("Cambios guardados", "Tus cambios se guardaron correctamente.")
            finally:
                if self.session_id:
                    from modulos.auth.seguridad import close_session
                    close_session(self.session_id, 'programa cerrado')
                self.destroy()

        try:
            self.container_frame.mostrar_alert_dialog(
                "Guardar cambios",
                "Deseas guardar tus cambios antes de cerrar el programa?",
                "Guardar y cerrar",
                "Cancelar",
                guardar_y_cerrar,
            )
        except Exception:
            from tkinter import messagebox
            if messagebox.askyesno("Guardar cambios", "Deseas guardar tus cambios antes de cerrar el programa?"):
                guardar_y_cerrar()

    def configurar_estilos_modernos(self):
        """Configurar todos los estilos modernos de la aplicación"""
        try:
            from ttkthemes import ThemedStyle
            self.style = ThemedStyle(self)
            self.style.set_theme("arc")  # Tema base moderno
        except ImportError:
            # Si no está disponible ttkthemes, usar ttk.Style normal
            self.style = ttk.Style()
            self.style.theme_use("clam")
        
        # Configurar estilos personalizados usando nuestro sistema
        # Labels modernos
        self.style.configure('Modern.TLabel', 
                           background=estilos.COLORS['bg_primary'],
                           foreground=estilos.COLORS['primary'],
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['base']))
        
        self.style.configure('Title.TLabel',
                           background=estilos.COLORS['bg_primary'],
                           foreground=estilos.COLORS['primary'],
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['2xl']) + ' bold')
        
        # Botones modernos
        self.style.configure('Modern.TButton',
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['base']) + ' bold',
                           padding=(15, 8))
        
        # Entries modernos
        self.style.configure('Modern.TEntry',
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['base']),
                           fieldbackground=estilos.COLORS['white'],
                           borderwidth=1,
                           relief='solid')
        
        # Combobox modernos
        self.style.configure('Modern.TCombobox',
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['base']),
                           fieldbackground=estilos.COLORS['white'],
                           borderwidth=1,
                           relief='solid')
        
        # Treeview moderno
        self.style.configure('Modern.Treeview',
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['base']),
                           background=estilos.COLORS['white'],
                           foreground=estilos.COLORS['dark'],
                           fieldbackground=estilos.COLORS['white'])
        
        self.style.configure('Modern.Treeview.Heading',
                           font=estilos.FONTS['primary'] + ' ' + str(estilos.FONTS['sizes']['base']) + ' bold',
                           background=estilos.COLORS['primary'],
                           foreground=estilos.COLORS['white'])

def main():
    """Función principal que maneja el flujo de login y aplicación"""
    registrar_fuentes()
    # Crear base de datos primero
    crear_base_de_datos()
    iniciar_api_local_global()

    # Mostrar login primero
    usuario_actual = mostrar_login_simple()
    if usuario_actual:
        # Si el login fue exitoso, abrir la aplicacion principal
        app = Manager(usuario_actual=usuario_actual)
        app.mainloop()
    else:
        # Si se cancelo el login, salir
        print("Login cancelado. Cerrando aplicacion...")

    
if __name__ == "__main__":
    main()















