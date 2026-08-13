import json
import os
import re
import sqlite3
import threading
import base64
import shutil
import uuid
import subprocess
import tempfile
import time
import unicodedata
from io import BytesIO
from datetime import datetime
from tkinter import messagebox, simpledialog, filedialog, ttk

import customtkinter as ctk
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw
from modulos.utils.utils import resource_path


COLOR_VINO = '#8f070c'
COLOR_VINO_OSCURO = '#71070a'


class AsistenteIA:
    """Asistente operativo con herramientas limitadas y auditadas."""

    def __init__(self, app, usuario):
        self.app = app
        self.usuario = usuario or 'Usuario'
        self.historial = []
        self.ventana = None
        self._crear_tabla_auditoria()

    def _abrir_clasico(self):
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.lift()
            return
        self.ventana = ctk.CTkToplevel(self.app)
        self.ventana.title('JELOX · Asistente inteligente')
        self.ventana.geometry('560x700')
        self.ventana.minsize(480, 600)
        self.ventana.configure(fg_color='#f5f6f8')
        self.ventana.transient(self.app.winfo_toplevel())

        header = ctk.CTkFrame(self.ventana, height=96, corner_radius=0, fg_color='#081426')
        header.pack(fill='x'); header.pack_propagate(False)
        try:
            avatar = Image.open(resource_path('media/icons/jelox_v2.png')).convert('RGBA')
            lado = min(avatar.size)
            margen = int(lado * .09)
            avatar = avatar.crop(((avatar.width-lado)//2+margen, (avatar.height-lado)//2+margen,
                                  (avatar.width+lado)//2-margen, (avatar.height+lado)//2-margen)).resize((68,68), Image.LANCZOS)
            mascara = Image.new('L',(68,68),0)
            ImageDraw.Draw(mascara).ellipse((0,0,67,67),fill=255)
            avatar.putalpha(mascara)
            self._avatar_ia = ctk.CTkImage(light_image=avatar, dark_image=avatar, size=(68,68))
        except Exception:
            self._avatar_ia = None
        self.avatar_ring = ctk.CTkFrame(header, width=78, height=78, corner_radius=39,
                                        fg_color='#081426', border_width=3, border_color='#00c8ff')
        self.avatar_ring.place(x=14, y=9)
        ctk.CTkLabel(self.avatar_ring, text='' if self._avatar_ia else 'J', image=self._avatar_ia,
                     width=68, height=68, corner_radius=34, fg_color='#081426',
                     text_color='#00d9ff', font=ctk.CTkFont('Poppins',16,'bold')).place(relx=.5,rely=.5,anchor='center')
        ctk.CTkLabel(header, text='JELOX', font=ctk.CTkFont('Poppins',20,'bold'),
                     text_color='white').place(x=108,y=19)
        self.jelox_status_dot = ctk.CTkLabel(header,text='',width=9,height=9,corner_radius=5,fg_color='#00e6a8')
        self.jelox_status_dot.place(x=109,y=61)
        ctk.CTkLabel(header,text='En línea...',
                     font=ctk.CTkFont('Poppins',11,'bold'),text_color='#75dfff').place(x=126,y=56)
        self._animar_avatar_jelox()

        self.chat = ctk.CTkTextbox(self.ventana, wrap='word', corner_radius=12, border_width=1,
                                   border_color='#e3e6ea', fg_color='white', text_color='#20242a',
                                   font=ctk.CTkFont('Poppins', 10), state='disabled')
        self.chat.pack(fill='both', expand=True, padx=16, pady=(14, 8))

        sugerencias = ctk.CTkFrame(self.ventana, fg_color='transparent')
        sugerencias.pack(fill='x', padx=16)
        for texto in ('Resumen de hoy', 'Productos con poco stock', 'Buscar un cliente'):
            ctk.CTkButton(sugerencias, text=texto, command=lambda t=texto: self.enviar(t), height=29,
                          width=104,
                          corner_radius=14, fg_color='#eceff3', hover_color='#dde2e8', text_color='#505762',
                          font=ctk.CTkFont('Poppins', 8)).pack(side='left', padx=(0, 5))
        ctk.CTkButton(sugerencias, text='Leer nota de venta', command=self.seleccionar_nota_venta,
                      width=126, height=29, corner_radius=14, fg_color=COLOR_VINO, hover_color=COLOR_VINO_OSCURO,
                      text_color='white', font=ctk.CTkFont('Poppins', 8, 'bold')).pack(side='right')

        entrada_box = ctk.CTkFrame(self.ventana, fg_color='white', corner_radius=12, height=62,
                                   border_width=1, border_color='#e3e6ea')
        entrada_box.pack(fill='x', padx=16, pady=(8, 16)); entrada_box.pack_propagate(False)
        self.entrada = ctk.CTkEntry(entrada_box, placeholder_text='Preguntame o pideme una accion...',
                                    border_width=0, fg_color='transparent', height=44,
                                    font=ctk.CTkFont('Poppins', 10))
        self.entrada.pack(side='left', fill='x', expand=True, padx=(12, 4), pady=8)
        self.entrada.bind('<Return>', lambda _e: self.enviar())
        self.boton = ctk.CTkButton(entrada_box, text='Enviar', command=self.enviar, width=78, height=38,
                                   corner_radius=9, fg_color=COLOR_VINO, hover_color=COLOR_VINO_OSCURO)
        self.boton.pack(side='right', padx=8, pady=8)
        self._texto_boton_reposo = 'Enviar'
        self._mensaje('JELOX', f'Hola, {self.usuario}. Soy JELOX, tu robot inteligente. Puedo responder preguntas, consultar el negocio y ayudarte a ejecutar acciones. ¿Que necesitas?')
        self.entrada.focus()
        threading.Thread(target=self._precalentar_modelo, daemon=True).start()

    def abrir(self):
        if self.ventana and self.ventana.winfo_exists():
            self.ventana.deiconify()
            self.ventana.lift()
            self.entrada.focus()
            if hasattr(self.app, 'limpiar_badge_jelox'):
                self.app.limpiar_badge_jelox()
            return

        raiz = self.app.winfo_toplevel()
        raiz.update_idletasks()
        ancho, alto = 410, 620
        x = raiz.winfo_rootx() + max(8, raiz.winfo_width() - ancho - 18)
        y = raiz.winfo_rooty() + max(45, raiz.winfo_height() - alto - 82)
        x = max(8, min(x, raiz.winfo_screenwidth() - ancho - 8))
        y = max(8, min(y, raiz.winfo_screenheight() - alto - 72))
        self._jelox_compact_geometry = f'{ancho}x{alto}+{x}+{y}'
        self._jelox_expanded = False

        self.ventana = ctk.CTkToplevel(self.app)
        self.ventana.withdraw()
        self.ventana.overrideredirect(True)
        self.ventana.geometry(self._jelox_compact_geometry)
        self.ventana.configure(fg_color='#dce8f7')
        self.ventana.transient(raiz)

        sombra = ctk.CTkFrame(self.ventana, fg_color='#78aef4', corner_radius=22)
        sombra.place(x=7, y=8, relwidth=.975, relheight=.98)
        exterior = ctk.CTkFrame(self.ventana, fg_color='#f3f7ff', corner_radius=22,
                                border_width=2, border_color='#00aef0')
        exterior.place(x=3, y=3, relwidth=.973, relheight=.98)

        cabecera = ctk.CTkFrame(exterior, height=68, fg_color='#f7faff', corner_radius=20)
        cabecera.pack(fill='x', padx=1, pady=(1, 0)); cabecera.pack_propagate(False)
        try:
            avatar = Image.open(resource_path('media/icons/jelox_v2.png')).convert('RGBA')
            lado = min(avatar.size); margen = int(lado * .10)
            avatar = avatar.crop(((avatar.width-lado)//2+margen, (avatar.height-lado)//2+margen,
                                  (avatar.width+lado)//2-margen, (avatar.height+lado)//2-margen)).resize((44, 44), Image.LANCZOS)
            mascara = Image.new('L', (44, 44), 0); ImageDraw.Draw(mascara).ellipse((0, 0, 43, 43), fill=255)
            avatar.putalpha(mascara)
            self._avatar_ia = ctk.CTkImage(light_image=avatar, dark_image=avatar, size=(44, 44))
            avatar_mensaje = avatar.resize((26, 26), Image.LANCZOS)
            self._avatar_mensaje = ctk.CTkImage(
                light_image=avatar_mensaje, dark_image=avatar_mensaje, size=(26, 26))
        except Exception:
            self._avatar_ia = None
            self._avatar_mensaje = None
        self.avatar_ring = ctk.CTkFrame(cabecera, width=50, height=50, corner_radius=25,
                                        fg_color='#eef6ff', border_width=2, border_color='#168fbd')
        self.avatar_ring.place(x=14, y=9)
        ctk.CTkLabel(self.avatar_ring, text='' if self._avatar_ia else 'J', image=self._avatar_ia,
                     width=44, height=44, corner_radius=22, fg_color='#eef6ff', text_color='#00c8ff',
                     font=ctk.CTkFont('Poppins', 13, 'bold')).place(relx=.5, rely=.5, anchor='center')
        titulo = ctk.CTkLabel(cabecera, text='JELOX', text_color='#20242a',
                              font=ctk.CTkFont('Poppins', 17, 'bold'))
        titulo.place(x=76, y=12)
        self.jelox_status_dot = ctk.CTkLabel(cabecera, text='', width=8, height=8,
                                             corner_radius=4, fg_color='#13b981')
        self.jelox_status_dot.place(x=77, y=43)
        estado = ctk.CTkLabel(cabecera, text='Asistente activo', text_color='#68707c',
                              font=ctk.CTkFont('Poppins', 9))
        estado.place(x=91, y=38)

        def limpiar_chat():
            for widget in self.chat_burbujas.winfo_children():
                widget.destroy()
            self._chat_items.clear()
            self.historial.clear(); self._mensaje('JELOX', 'Conversación nueva. ¿En qué te ayudo?')

        def alternar_tamano():
            self._jelox_expanded = not self._jelox_expanded
            if self._jelox_expanded:
                w, h = 560, 720
                nx = raiz.winfo_rootx() + max(8, raiz.winfo_width() - w - 18)
                ny = raiz.winfo_rooty() + max(70, raiz.winfo_height() - h - 20)
                nx = max(8, min(nx, raiz.winfo_screenwidth() - w - 8))
                ny = max(8, min(ny, raiz.winfo_screenheight() - h - 8))
                self.ventana.geometry(f'{w}x{h}+{nx}+{ny}')
                self.ventana.after(25, self._redondear_ventana_chat)
                expandir.configure(text='↙')
            else:
                self.ventana.geometry(self._jelox_compact_geometry)
                self.ventana.after(25, self._redondear_ventana_chat)
                expandir.configure(text='↗')

        opciones = ctk.CTkButton(cabecera, text='•••', command=limpiar_chat, width=32, height=32,
                                 corner_radius=16, fg_color='transparent', hover_color='#edf0f3',
                                 text_color='#59606b', font=ctk.CTkFont('Poppins', 11, 'bold'))
        opciones.place(relx=1, x=-148, y=17, anchor='ne')
        minimizar = ctk.CTkButton(cabecera, text='—', command=self.ventana.withdraw, width=32, height=32,
                                  corner_radius=16, fg_color='transparent', hover_color='#edf0f3',
                                  text_color='#59606b', font=ctk.CTkFont('Arial', 15, 'bold'))
        minimizar.place(relx=1, x=-108, y=17, anchor='ne')
        expandir = ctk.CTkButton(cabecera, text='↗', command=alternar_tamano, width=32, height=32,
                                 corner_radius=16, fg_color='transparent', hover_color='#edf0f3',
                                 text_color='#59606b', font=ctk.CTkFont('Poppins', 15, 'bold'))
        expandir.place(relx=1, x=-68, y=17, anchor='ne')
        cerrar = ctk.CTkButton(cabecera, text='×', command=self.ventana.destroy, width=32, height=32,
                               corner_radius=16, fg_color='transparent', hover_color='#fee8e9',
                               text_color='#343941', font=ctk.CTkFont('Poppins', 18))
        cerrar.place(relx=1, x=-28, y=17, anchor='ne')
        if hasattr(self.app, '_agregar_tooltip'):
            self.app._agregar_tooltip(opciones, 'Nueva conversación')
            self.app._agregar_tooltip(minimizar, 'Minimizar JELOX')
            self.app._agregar_tooltip(expandir, 'Expandir o contraer')
            self.app._agregar_tooltip(cerrar, 'Cerrar JELOX')

        arrastre = {'x': 0, 'y': 0, 'wx': 0, 'wy': 0}
        def iniciar_arrastre(event):
            arrastre.update(x=event.x_root, y=event.y_root, wx=self.ventana.winfo_x(), wy=self.ventana.winfo_y())
        def mover(event):
            self.ventana.geometry(f'+{arrastre["wx"] + event.x_root-arrastre["x"]}+{arrastre["wy"] + event.y_root-arrastre["y"]}')
        for widget in (cabecera, titulo, estado):
            widget.bind('<ButtonPress-1>', iniciar_arrastre, add='+')
            widget.bind('<B1-Motion>', mover, add='+')

        buscador_box = ctk.CTkFrame(exterior, height=48, fg_color='#ffffff', corner_radius=0)
        buscador_box.pack(fill='x', padx=14); buscador_box.pack_propagate(False)
        self.buscar_chat_var = ctk.StringVar()
        buscar_pill = ctk.CTkFrame(buscador_box, height=36, corner_radius=18, fg_color='#f0f2f5')
        buscar_pill.pack(fill='x', pady=6); buscar_pill.pack_propagate(False)
        ctk.CTkLabel(buscar_pill, text='⌕', width=28, text_color='#68707c',
                     font=ctk.CTkFont('Arial', 18)).pack(side='left', padx=(7, 0))
        buscar = ctk.CTkEntry(buscar_pill, textvariable=self.buscar_chat_var,
                              placeholder_text='Buscar en JELOX', height=32, corner_radius=0,
                              border_width=0, fg_color='transparent', text_color='#20242a',
                              placeholder_text_color='#68707c', font=ctk.CTkFont('Poppins', 10))
        buscar.pack(side='left', fill='x', expand=True, padx=(0, 12), pady=2)

        pestanas = ctk.CTkFrame(exterior, height=42, fg_color='#ffffff', corner_radius=0)
        pestanas.pack(fill='x', padx=14); pestanas.pack_propagate(False)
        ctk.CTkButton(pestanas, text='Chat', width=64, height=32, corner_radius=16,
                      fg_color='#e7f1ff', hover_color='#dceaff', text_color='#0866ff',
                      font=ctk.CTkFont('Poppins', 10, 'bold')).pack(side='left')
        ctk.CTkButton(pestanas, text='Acciones', command=lambda: self._mensaje('Sistema', 'Acciones rápidas: resumen, stock, clientes, ventas y apertura de módulos.'),
                      width=80, height=32, corner_radius=16, fg_color='transparent', hover_color='#f0f2f5',
                      text_color='#20242a', font=ctk.CTkFont('Poppins', 10, 'bold')).pack(side='left', padx=4)
        ctk.CTkButton(pestanas, text='Leer nota', command=self.seleccionar_nota_venta,
                      width=86, height=32, corner_radius=16, fg_color='transparent', hover_color='#f0f2f5',
                      text_color='#20242a', font=ctk.CTkFont('Poppins', 10, 'bold')).pack(side='left')

        self.banner_jelox = ctk.CTkFrame(exterior, height=66, fg_color='#f4f7fb', corner_radius=10)
        self.banner_jelox.pack(fill='x', padx=14, pady=(4, 8)); self.banner_jelox.pack_propagate(False)
        ctk.CTkLabel(self.banner_jelox, text='!', width=25, height=25, corner_radius=13,
                     fg_color='#1683ff', text_color='white', font=ctk.CTkFont('Poppins', 12, 'bold')).place(x=12, y=12)
        ctk.CTkLabel(self.banner_jelox, text='JELOX está listo', text_color='#20242a',
                     font=ctk.CTkFont('Poppins', 10, 'bold')).place(x=47, y=9)
        ctk.CTkLabel(self.banner_jelox, text='Pregunta, consulta el negocio o lee una nota.', text_color='#505762',
                     font=ctk.CTkFont('Poppins', 8)).place(x=47, y=32)
        ctk.CTkButton(self.banner_jelox, text='×', command=self.banner_jelox.pack_forget,
                      width=28, height=28, corner_radius=14, fg_color='#e4e8ed', hover_color='#d8dde3',
                      text_color='#20242a', font=ctk.CTkFont('Poppins', 14)).place(relx=1, x=-12, y=12, anchor='ne')

        self._chat_items = []
        self.chat_burbujas = ctk.CTkScrollableFrame(
            exterior, corner_radius=10, border_width=0, fg_color='#ffffff',
            scrollbar_button_color='#d9dde3', scrollbar_button_hover_color='#c8cdd4')
        self.chat_burbujas.pack(fill='both', expand=True, padx=14, pady=(0, 7))
        self.chat = self.chat_burbujas

        def buscar_en_chat(_event=None):
            consulta = self.buscar_chat_var.get().strip()
            if not consulta:
                return
            consulta = consulta.casefold()
            encontrado = None
            for item in self._chat_items:
                item['burbuja'].configure(border_width=0)
                if encontrado is None and consulta in item['texto'].casefold():
                    encontrado = item
            if encontrado:
                encontrado['burbuja'].configure(border_width=2, border_color='#f0b84f')
                self.chat_burbujas.update_idletasks()
                alto = max(1, self.chat_burbujas.winfo_height())
                posicion = max(0.0, min(1.0, encontrado['fila'].winfo_y() / alto))
                self.chat_burbujas._parent_canvas.yview_moveto(posicion)
        buscar.bind('<Return>', buscar_en_chat)

        sugerencias = ctk.CTkFrame(exterior, fg_color='#ffffff', corner_radius=0)
        sugerencias.pack(fill='x', padx=14)
        for columna, texto in enumerate(('Resumen de hoy', 'Poco stock', 'Buscar cliente')):
            comando = {'Poco stock':'Productos con poco stock', 'Buscar cliente':'Buscar un cliente'}.get(texto, texto)
            sugerencias.grid_columnconfigure(columna, weight=1, uniform='acciones_jelox')
            ctk.CTkButton(
                sugerencias, text=texto, command=lambda t=comando: self.enviar(t),
                height=30, corner_radius=15, fg_color='#f0f2f5', hover_color='#e4e7eb',
                text_color='#505762', font=ctk.CTkFont('Poppins', 9)
            ).grid(row=0, column=columna, sticky='ew', padx=(0 if columna == 0 else 3, 0), pady=3)

        entrada_box = ctk.CTkFrame(exterior, fg_color='#ffffff', corner_radius=0, height=62)
        entrada_box.pack(fill='x', padx=14, pady=(4, 12)); entrada_box.pack_propagate(False)
        self.entrada = ctk.CTkEntry(entrada_box, placeholder_text='Escribe un mensaje...', height=42,
                                    corner_radius=21, border_width=1, border_color='#d9dde3',
                                    fg_color='#f7f8fa', font=ctk.CTkFont('Poppins', 10))
        self.entrada.pack(side='left', fill='x', expand=True, pady=8)
        self.entrada.bind('<Return>', lambda _e: self.enviar())
        self.boton = ctk.CTkButton(entrada_box, text='➤', command=self.enviar, width=42, height=42,
                                   corner_radius=21, fg_color='#0866ff', hover_color='#0758d7',
                                   font=ctk.CTkFont('Poppins', 15, 'bold'))
        self.boton.pack(side='right', padx=(7, 0), pady=8)
        self._texto_boton_reposo = '➤'

        self._mensaje('JELOX', f'Hola, {self.usuario}. Soy JELOX. ¿Qué necesitas?')
        self.ventana.deiconify(); self.ventana.lift(); self.entrada.focus()
        self.ventana.after(40, self._redondear_ventana_chat)
        self._animar_avatar_jelox()
        threading.Thread(target=self._precalentar_modelo, daemon=True).start()

    def _redondear_ventana_chat(self):
        """Recorta la ventana nativa en Windows sin perforar widgets claros."""
        try:
            import ctypes
            if not self.ventana or not self.ventana.winfo_exists():
                return
            self.ventana.update_idletasks()
            hwnd_widget = self.ventana.winfo_id()
            hwnd = ctypes.windll.user32.GetAncestor(hwnd_widget, 2) or hwnd_widget
            ancho, alto = self.ventana.winfo_width(), self.ventana.winfo_height()
            region = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, ancho + 1, alto + 1, 38, 38)
            ctypes.windll.user32.SetWindowRgn(hwnd, region, True)
        except Exception:
            pass

    def _animar_avatar_jelox(self, paso=0):
        if not self.ventana or not self.ventana.winfo_exists() or not hasattr(self, 'avatar_ring'):
            return
        colores = ('#0d5f88','#008fc4','#00c8ff','#78ecff','#00c8ff','#008fc4')
        self.avatar_ring.configure(border_color=colores[(paso // 2) % len(colores)])
        self.jelox_status_dot.configure(fg_color='#00e6a8' if (paso // 5) % 2 == 0 else '#13725e')
        self._avatar_anim_after = self.ventana.after(100, lambda: self._animar_avatar_jelox(paso + 1))

    def enviar(self, texto=None):
        texto = (texto if texto is not None else self.entrada.get()).strip()
        if not texto or self.boton.cget('state') == 'disabled':
            return
        self.entrada.delete(0, 'end')
        self._mensaje('Tu', texto)
        self.boton.configure(state='disabled', text='...' if self._texto_boton_reposo != 'Enviar' else 'Pensando...')
        threading.Thread(target=self._procesar, args=(texto,), daemon=True).start()

    def _procesar(self, texto):
        inventario_actualizado = False
        try:
            directa = self._respuesta_rapida(texto)
            if directa is not None:
                self.historial.extend([
                    {'role': 'user', 'content': texto},
                    {'role': 'assistant', 'content': directa},
                ])
                self.ventana.after(0, lambda c=directa: self._entregar_respuesta(c, False))
                return
            local = self._asegurar_ollama()
            clave = os.getenv('OPENAI_API_KEY', '').strip()
            if not local and not clave:
                raise RuntimeError('La IA local aun esta terminando de descargar su modelo. Intenta nuevamente en unos minutos.')
            mensajes = [{'role': 'system', 'content': self._instrucciones()}] + self.historial[-16:]
            mensajes.append({'role': 'user', 'content': texto})
            for _ in range(5):
                if local:
                    mensaje = self._llamar_ollama(mensajes, local).get('message', {})
                else:
                    respuesta = self._llamar_openai(clave, mensajes)
                    if not respuesta.ok:
                        raise RuntimeError(self._error_api(respuesta))
                    mensaje = respuesta.json()['choices'][0]['message']
                mensajes.append(mensaje)
                llamadas = mensaje.get('tool_calls') or []
                if not llamadas:
                    contenido = self._limpiar_respuesta(mensaje.get('content') or 'Listo.')
                    self.historial.extend([{'role': 'user', 'content': texto}, {'role': 'assistant', 'content': contenido}])
                    self.ventana.after(
                        0, lambda c=contenido, i=inventario_actualizado: self._entregar_respuesta(c, i))
                    return
                for llamada in llamadas:
                    nombre = llamada['function']['name']
                    argumentos = llamada['function'].get('arguments') or {}
                    if isinstance(argumentos, dict):
                        args = argumentos
                    else:
                        try: args = json.loads(argumentos)
                        except json.JSONDecodeError: args = {}
                    resultado = self._ejecutar(nombre, args)
                    if nombre == 'ajustar_stock' and resultado.get('ok'):
                        inventario_actualizado = True
                    herramienta = {'role': 'tool', 'content': json.dumps(resultado, ensure_ascii=False)}
                    if local:
                        herramienta['tool_name'] = nombre
                    else:
                        herramienta['tool_call_id'] = llamada['id']
                    mensajes.append(herramienta)
            raise RuntimeError('La solicitud necesito demasiados pasos. Intenta dividirla en dos instrucciones.')
        except Exception as exc:
            if self.ventana and self.ventana.winfo_exists():
                self.ventana.after(0, lambda e=str(exc): self._mensaje('Error', e))
        finally:
            if self.ventana and self.ventana.winfo_exists():
                self.ventana.after(0, lambda: self.boton.configure(
                    state='normal', text=getattr(self, '_texto_boton_reposo', 'Enviar')))

    def _precalentar_modelo(self):
        """Carga el modelo en segundo plano para reducir la espera de la primera pregunta."""
        modelo = self._asegurar_ollama()
        if not modelo:
            return
        try:
            requests.post(
                'http://127.0.0.1:11434/api/generate',
                json={'model': modelo, 'prompt': '', 'stream': False, 'keep_alive': '30m'},
                timeout=90,
            )
        except requests.RequestException:
            pass

    @staticmethod
    def _normalizar(texto):
        limpio = unicodedata.normalize('NFKD', str(texto or ''))
        return ''.join(c for c in limpio if not unicodedata.combining(c)).lower().strip()

    def _respuesta_rapida(self, texto):
        """Resuelve consultas frecuentes sin esperar al modelo generativo."""
        limpio = self._normalizar(texto)
        if not limpio:
            return None

        if ('resumen' in limpio or 'ventas de hoy' in limpio or 'vendi hoy' in limpio or
                'venta del dia' in limpio):
            dato = self._resumen()
            return (
                f"Resumen de hoy:\n"
                f"• Ventas registradas: {dato['ventas_hoy']}\n"
                f"• Importe vendido: ${dato['importe_hoy']:,.2f}\n"
                f"• Clientes: {dato['clientes']}\n"
                f"• Productos activos: {dato['productos_activos']}\n"
                f"• Productos con poco stock: {dato['productos_stock_bajo']}"
            )

        if ('poco stock' in limpio or 'stock bajo' in limpio or 'productos bajos' in limpio):
            with sqlite3.connect('database.db') as c:
                filas = c.execute(
                    "SELECT COALESCE(codigo,''),articulo,COALESCE(stock,0),COALESCE(precio,0) "
                    "FROM articulos WHERE lower(COALESCE(estado,'activo'))='activo' AND COALESCE(stock,0)<=5 "
                    "ORDER BY stock,articulo LIMIT 20"
                ).fetchall()
            if not filas:
                return 'El inventario está saludable: no hay productos con stock bajo.'
            detalle = '\n'.join(f"• {nombre} ({codigo or 'sin código'}): {stock} disponibles · ${precio:,.2f}" for codigo,nombre,stock,precio in filas)
            return f'Productos con poco stock ({len(filas)}):\n{detalle}'

        modulos = {
            'inicio': 'inicio', 'ventas': 'ventas', 'inventario': 'inventario',
            'clientes': 'clientes', 'pedidos': 'pedidos', 'proveedores': 'proveedores',
            'compras': 'compras', 'prestamos': 'prestamos', 'nominas': 'nominas',
            'abonos': 'abonos', 'configuracion': 'configuracion',
        }
        if any(verbo in limpio for verbo in ('abre ', 'abrir ', 've a ', 'muestra el modulo')):
            for palabra, modulo in modulos.items():
                if palabra in limpio:
                    resultado = self._abrir_modulo(modulo)
                    return f"Abrí el módulo de {palabra}." if resultado.get('ok') else resultado.get('error', 'No pude abrirlo.')

        if 'cliente' in limpio and any(v in limpio for v in ('buscar', 'busca', 'encuentra', 'consulta')):
            termino = re.split(r'cliente(?:s)?', texto, maxsplit=1, flags=re.I)[-1]
            termino = re.sub(r'^[\s:,-]*(llamado|nombre|que se llama|por)?\s*', '', termino, flags=re.I).strip(' .?')
            dato = self._buscar_clientes(termino, 12)
            filas = dato.get('clientes', [])
            if not filas:
                return f'No encontré clientes que coincidan con “{termino}”.' if termino else 'No hay clientes registrados.'
            detalle = '\n'.join(f"• {f['nombre']} · Tel. {f['telefono'] or 'sin teléfono'} · ID {f['identificacion'] or 'sin ID'}" for f in filas)
            return f'Clientes encontrados ({len(filas)}):\n{detalle}'

        if 'producto' in limpio and any(v in limpio for v in ('buscar', 'busca', 'encuentra', 'consulta')):
            termino = re.split(r'producto(?:s)?', texto, maxsplit=1, flags=re.I)[-1].strip(' :,-.?')
            dato = self._buscar_productos(termino, 12)
            filas = dato.get('productos', [])
            if not filas:
                return f'No encontré productos que coincidan con “{termino}”.'
            detalle = '\n'.join(f"• {f['articulo']} ({f['codigo']}): stock {f['stock']} · ${float(f['precio']):,.2f}" for f in filas)
            return f'Productos encontrados ({len(filas)}):\n{detalle}'

        return None

    def _solicitar_clave(self, texto_pendiente=None):
        clave = simpledialog.askstring('Activar inteligencia artificial',
            'Ingresa tu clave de API de OpenAI. Se conservara solo durante esta ejecucion:',
            show='*', parent=self.ventana)
        if clave:
            os.environ['OPENAI_API_KEY'] = clave.strip()
            self._mensaje('Sistema', 'La IA quedo activada. Estoy procesando tu solicitud...')
            if texto_pendiente:
                threading.Thread(target=self._procesar, args=(texto_pendiente,), daemon=True).start()
        else:
            self._mensaje('Sistema', 'Para usar la IA necesitas una clave de API de OpenAI.')

    def seleccionar_nota_venta(self):
        ruta = filedialog.askopenfilename(parent=self.ventana, title='Seleccionar foto de la nota de venta',
            filetypes=[('Imagenes', '*.jpg *.jpeg *.png *.webp'), ('Todos los archivos', '*.*')])
        if not ruta:
            return
        self._mensaje('Sistema', 'Estoy leyendo la nota para capturarla en Ventas. No modificare Inventario.')
        self.boton.configure(state='disabled', text='...' if self._texto_boton_reposo != 'Enviar' else 'Leyendo...')
        threading.Thread(target=self._analizar_nota, args=(ruta,), daemon=True).start()

    def _modelo_instalado(self, nombre):
        try:
            modelos = requests.get('http://127.0.0.1:11434/api/tags', timeout=3).json().get('models', [])
            return any(m.get('name') == nombre for m in modelos)
        except Exception:
            return False

    def _analizar_nota(self, ruta):
        try:
            esquema = {'type':'object','properties':{
                'folio':{'type':'string'},'cliente':{'type':'string'},'fecha':{'type':'string'},
                'direccion':{'type':'string'},'telefono':{'type':'string'},'vendedor':{'type':'string'},
                'tipo_pago':{'type':'string'},'abono':{'type':'number'},'total':{'type':'number'},
                'productos':{'type':'array','items':{'type':'object','properties':{
                    'codigo':{'type':'string'},'nombre':{'type':'string'},'cantidad':{'type':'number'},
                    'precio_unitario':{'type':'number'},'subtotal':{'type':'number'}},
                    'required':['nombre','cantidad','precio_unitario','subtotal']}}},
                'required':['folio','cliente','fecha','direccion','telefono','vendedor','tipo_pago','abono','total','productos']}
            prompt_vision = '''Lee esta nota fisica de venta, incluso si esta escrita a mano. Devuelve solamente los datos del formato JSON solicitado.
            Extrae: numero de nota como folio, fecha, cliente, direccion, telefono, nombre escrito en la parte superior como vendedor o persona que entrega, abono, total y todos los renglones.
            En cada renglon extrae descripcion como nombre, cantidad, precio unitario y subtotal. Deja codigo vacio.
            No inventes texto ni importes. Si un campo no es legible usa cadena vacia o 0. No relaciones los productos con ningun inventario.'''

            # Se obtiene primero un respaldo rapido. Si el modelo visual tarda o
            # el equipo esta ocupado, la revision nunca se abre vacia.
            texto_ocr, confianza_ocr = self._extraer_texto_ocr_con_confianza(ruta)

            # El modelo visual local lee directamente la fotografia y reconoce
            # escritura manual mucho mejor que el OCR tradicional.
            try:
                modelos = requests.get('http://127.0.0.1:11434/api/tags', timeout=4).json().get('models', [])
                nombres = [str(m.get('name', '')) for m in modelos]
                modelo_vision = next((n for n in nombres if 'qwen2.5vl' in n.lower()), None)
            except Exception:
                modelo_vision = None
            if modelo_vision:
                try:
                    imagen_b64 = self._preparar_imagen_nota(ruta)
                    respuesta_vision = requests.post('http://127.0.0.1:11434/api/chat', json={
                        'model': modelo_vision, 'stream': False, 'format': esquema,
                        'messages': [{'role': 'user', 'content': prompt_vision, 'images': [imagen_b64]}],
                        'think': False, 'keep_alive': '30m',
                        'options': {'temperature': 0.0, 'num_predict': 300, 'num_ctx': 2048}
                    }, timeout=45)
                except requests.RequestException:
                    respuesta_vision = None
                    if os.name == 'nt':
                        try:
                            subprocess.run(['taskkill','/F','/IM','llama-server.exe'],
                                           capture_output=True, timeout=8,
                                           creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                        except Exception:
                            pass
                if respuesta_vision is not None and respuesta_vision.ok:
                    contenido = respuesta_vision.json().get('message', {}).get('content', '')
                    datos = self._cargar_json_modelo(contenido)
                    datos['_confianza_ocr'] = 95
                    self.ventana.after(0, lambda d=datos,r=ruta: self._mostrar_revision_nota(d,r))
                    return

            prompt_base = '''Convierte el texto leido de una nota fisica de venta en datos estructurados.
            Extrae folio, cliente, fecha, direccion, telefono, vendedor, abono, total y renglones.
            No relaciones productos con Inventario y no inventes cantidades ni precios.'''
            datos_directos = self._datos_basicos_ocr(texto_ocr)
            if confianza_ocr >= 70 and datos_directos.get('productos'):
                datos_directos['_confianza_ocr'] = confianza_ocr
                self.ventana.after(0, lambda d=datos_directos,r=ruta: self._mostrar_revision_nota(d,r))
                return
            modelo_texto = self._asegurar_ollama() or 'qwen3:0.6b'
            if len(texto_ocr.strip()) < 24 or confianza_ocr < 52:
                datos = self._datos_basicos_ocr(texto_ocr)
                datos['_confianza_ocr'] = confianza_ocr
                self.ventana.after(0, lambda d=datos,r=ruta: self._mostrar_revision_nota(d,r))
                return
            respuesta = requests.post('http://127.0.0.1:11434/api/chat', json={
                'model':modelo_texto,'stream':False,'format':esquema,
                'messages':[{'role':'user','content':f'{prompt_base}\n\nTEXTO LEIDO DE LA NOTA:\n{texto_ocr}'}],
                'think':False,'keep_alive':'30m',
                'options':{'temperature':0.1,'num_predict':420,'num_ctx':3072}}, timeout=90)
            if not respuesta.ok:
                raise RuntimeError(respuesta.text[:300])
            contenido = respuesta.json().get('message',{}).get('content','')
            try:
                datos = self._cargar_json_modelo(contenido)
            except RuntimeError:
                datos = self._datos_basicos_ocr(texto_ocr)
            if False and not datos.get('productos'):
                raise RuntimeError('No pude detectar productos en la nota. Prueba con una foto mas clara y tomada de frente.')
            datos['_confianza_ocr'] = confianza_ocr
            self.ventana.after(0, lambda d=datos,r=ruta: self._mostrar_revision_nota(d,r))
        except Exception as exc:
            datos = self._datos_basicos_ocr(locals().get('texto_ocr', ''))
            datos['_confianza_ocr'] = locals().get('confianza_ocr', 0)
            if self.ventana and self.ventana.winfo_exists():
                self.ventana.after(0, lambda e=str(exc): self._mensaje('Sistema', f'La lectura automática fue parcial: {e}. Abro la revisión para que completes los datos.'))
                self.ventana.after(0, lambda d=datos,r=ruta: self._mostrar_revision_nota(d,r))
        finally:
            if self.ventana and self.ventana.winfo_exists():
                self.ventana.after(0, lambda: self.boton.configure(
                    state='normal', text=getattr(self, '_texto_boton_reposo', 'Enviar')))

    def _extraer_texto_ocr(self, ruta):
        return self._extraer_texto_ocr_con_confianza(ruta)[0]

    def _extraer_texto_ocr_con_confianza(self, ruta):
        ejecutable = os.path.join(os.getenv('LOCALAPPDATA',''), 'Programs', 'Tesseract-OCR', 'tesseract.exe')
        if not os.path.isfile(ejecutable):
            return '', 0.0
        temporal = os.path.join(tempfile.gettempdir(), f'nota_ocr_{uuid.uuid4().hex}.png')
        try:
            imagen = ImageOps.exif_transpose(Image.open(ruta)).convert('L')
            if imagen.width < 1400:
                factor = 1400 / max(1, imagen.width)
                imagen = imagen.resize((1400, int(imagen.height * factor)), Image.LANCZOS)
            imagen = ImageOps.autocontrast(imagen)
            imagen = ImageEnhance.Contrast(imagen).enhance(1.45).filter(ImageFilter.SHARPEN)
            imagen.save(temporal, 'PNG')
            proceso = subprocess.run([ejecutable, temporal, 'stdout', '-l', 'spa+eng', '--psm', '6', 'tsv'],
                                     capture_output=True, timeout=90, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            salida = proceso.stdout.decode('utf-8', errors='replace').splitlines()
            palabras, confianzas = [], []
            for linea in salida[1:]:
                partes = linea.split('\t', 11)
                if len(partes) < 12:
                    continue
                palabra = partes[11].strip()
                try:
                    confianza = float(partes[10])
                except ValueError:
                    continue
                if palabra:
                    palabras.append(palabra)
                    if confianza >= 0:
                        confianzas.append(confianza)
            promedio = sum(confianzas) / len(confianzas) if confianzas else 0.0
            if promedio < 60:
                # Segunda lectura para recibos con iluminación irregular o texto disperso.
                binaria = imagen.point(lambda pixel: 255 if pixel > 158 else 0)
                binaria.save(temporal, 'PNG')
                segundo = subprocess.run([ejecutable, temporal, 'stdout', '-l', 'spa+eng', '--psm', '11', 'tsv'],
                                         capture_output=True, timeout=90, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                palabras_2, confianzas_2 = [], []
                for linea in segundo.stdout.decode('utf-8', errors='replace').splitlines()[1:]:
                    partes = linea.split('\t', 11)
                    if len(partes) < 12 or not partes[11].strip():
                        continue
                    try:
                        confianza = float(partes[10])
                    except ValueError:
                        continue
                    palabras_2.append(partes[11].strip())
                    if confianza >= 0:
                        confianzas_2.append(confianza)
                promedio_2 = sum(confianzas_2) / len(confianzas_2) if confianzas_2 else 0.0
                if promedio_2 > promedio and len(palabras_2) >= 3:
                    palabras, promedio = palabras_2, promedio_2
            return ' '.join(palabras).strip(), promedio
        finally:
            try:
                if os.path.exists(temporal): os.remove(temporal)
            except OSError:
                pass

    @staticmethod
    def _preparar_imagen_nota(ruta):
        imagen = ImageOps.exif_transpose(Image.open(ruta)).convert('RGB')
        # 640 px reduce mucho el tiempo del modelo visual en equipos sin GPU.
        limite = 640
        if max(imagen.size) > limite:
            factor = limite / max(imagen.size)
            imagen = imagen.resize((max(1, int(imagen.width * factor)), max(1, int(imagen.height * factor))), Image.Resampling.LANCZOS)
        imagen = ImageOps.autocontrast(imagen, cutoff=1)
        imagen = ImageEnhance.Sharpness(imagen).enhance(1.25)
        salida = BytesIO()
        imagen.save(salida, format='JPEG', quality=88, optimize=True)
        return base64.b64encode(salida.getvalue()).decode('ascii')

    @staticmethod
    def _cargar_json_modelo(contenido):
        texto = (contenido or '').strip()
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            coincidencia = re.search(r'\{.*\}', texto, flags=re.S)
            if not coincidencia:
                raise RuntimeError('El lector no devolvió datos estructurados. Intenta con una foto más clara.')
            try:
                return json.loads(coincidencia.group(0))
            except json.JSONDecodeError as exc:
                raise RuntimeError('No pude interpretar los datos detectados en la nota.') from exc

    def _datos_basicos_ocr(self, texto):
        texto = str(texto or '')
        def buscar(patron, default=''):
            coincidencia = re.search(patron, texto, flags=re.I)
            return coincidencia.group(1).strip(' :-') if coincidencia else default
        fecha = buscar(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b')
        folio = buscar(r'\bfolio\b\s*(?:n[o°.]*)?\s*[:#-]?\s*([A-Z0-9-]{2,})')
        if not folio:
            folio = buscar(r'\b(?:nota|ticket)\b\s*(?:no|num|numero|n[°.]|#)\s*[:#-]?\s*([A-Z0-9-]{2,})')
        cliente = buscar(r'cliente\s*[:#-]?\s*(.+?)(?=\s+fecha\b|\s+folio\b|\s+total\b|$)', 'Cliente General')
        direccion = buscar(r'direcci[oó]n\s*[:#-]?\s*(.+?)(?=\s+tel[eé]fono\b|\s+cant\b|\s+descripci[oó]n\b|$)')
        telefono = buscar(r'tel[eé]fono\s*[:#-]?\s*([\d +()-]{6,})')
        total_txt = buscar(r'\btotal\b\s*[:$ ]+([\d,.]+)')
        abono_txt = buscar(r'\babono\b\s*[:$ ]+([\d,.]+)')
        pago = buscar(r'(?:tipo\s+de\s+)?pago\s*[:#-]?\s*([A-Za-záéíóúÁÉÍÓÚ]+)', 'Contado')
        try:
            total = float(total_txt.replace(',', '')) if total_txt else 0.0
        except ValueError:
            total = 0.0
        try:
            abono = float(abono_txt.replace(',', '')) if abono_txt else 0.0
        except ValueError:
            abono = 0.0
        productos = []
        try:
            with sqlite3.connect('database.db') as c:
                catalogo = c.execute("SELECT COALESCE(codigo,''),articulo,COALESCE(precio,0) FROM articulos WHERE lower(COALESCE(estado,'activo'))='activo' ORDER BY length(codigo) DESC").fetchall()
            for codigo, nombre, precio_catalogo in catalogo:
                if not codigo or not nombre:
                    continue
                nombre_patron = r'\s+'.join(re.escape(parte) for parte in str(nombre).split())
                patron = rf'(?<!\w){re.escape(str(codigo))}\s+{nombre_patron}\s+([\d.,]+)\s+\$?([\d.,]+)\s+\$?([\d.,]+)'
                coincidencia = re.search(patron, texto, flags=re.I)
                if not coincidencia:
                    continue
                try:
                    cantidad = float(coincidencia.group(1).replace(',', ''))
                    precio = float(coincidencia.group(2).replace(',', ''))
                    subtotal = float(coincidencia.group(3).replace(',', ''))
                except ValueError:
                    continue
                productos.append({'codigo': str(codigo), 'nombre': nombre, 'cantidad': cantidad,
                                  'precio_unitario': precio or float(precio_catalogo), 'subtotal': subtotal})
        except sqlite3.Error:
            pass
        if not total and productos:
            total = sum(float(p['subtotal']) for p in productos)
        return {'folio': folio, 'cliente': cliente, 'fecha': fecha, 'direccion': direccion,
                'telefono': telefono, 'vendedor': '', 'tipo_pago': pago,
                'abono': abono, 'total': total, 'productos': productos}

    def _mostrar_revision_nota(self, datos, ruta):
        revision = ctk.CTkToplevel(self.ventana)
        revision.title('Revisar nota antes de capturar en Ventas')
        revision.geometry('940x690'); revision.minsize(820,620)
        revision.configure(fg_color='#f5f6f8'); revision.transient(self.ventana); revision.grab_set()
        ctk.CTkLabel(revision,text='Revisa la venta detectada',font=ctk.CTkFont('Poppins',18,'bold'),text_color='#20242a').pack(anchor='w',padx=20,pady=(16,2))
        confianza = float(datos.get('_confianza_ocr', 0) or 0)
        ayuda = ('Verifica los datos detectados antes de registrar.' if datos.get('productos') else
                 'No reconocí todos los renglones. Usa Agregar para completarlos; la imagen no se registrará hasta confirmar.')
        ctk.CTkLabel(revision,text=f'{ayuda} · Lectura OCR: {confianza:.0f}%',
                     font=ctk.CTkFont('Poppins',9),text_color='#68707c').pack(anchor='w',padx=20)

        campos=ctk.CTkFrame(revision,fg_color='white',corner_radius=12,border_width=1,border_color='#e3e6ea')
        campos.pack(fill='x',padx=20,pady=12); campos.grid_columnconfigure((0,1,2,3),weight=1)
        entradas={}
        datos_campos=(
            ('folio','Folio',datos.get('folio','')),('fecha','Fecha',datos.get('fecha','')),
            ('vendedor','Vendedor / entrega',datos.get('vendedor','')),('abono','Abono',datos.get('abono',0)),
            ('cliente','Cliente',datos.get('cliente','Cliente General')),('direccion','Direccion',datos.get('direccion','')),
            ('telefono','Telefono',datos.get('telefono','')),('tipo_pago','Pago',datos.get('tipo_pago','Contado')),
        )
        for i,(clave,titulo,valor) in enumerate(datos_campos):
            fila=(i//4)*2; columna=i%4
            ctk.CTkLabel(campos,text=titulo,font=ctk.CTkFont('Poppins',9,'bold'),text_color='#505762').grid(row=fila,column=columna,sticky='w',padx=10,pady=(10,2))
            e=ctk.CTkEntry(campos,height=32,border_color='#d9dde3');e.grid(row=fila+1,column=columna,sticky='ew',padx=10,pady=(0,8));e.insert(0,str(valor or ''));entradas[clave]=e

        tabla_frame=ctk.CTkFrame(revision,fg_color='white',corner_radius=12,border_width=1,border_color='#e3e6ea')
        tabla_frame.pack(fill='both',expand=True,padx=20,pady=(0,10))
        columnas=('Producto','Cantidad','Precio','Subtotal')
        tabla=ttk.Treeview(tabla_frame,columns=columnas,show='headings',height=11)
        for col,w in zip(columnas,(420,100,130,140)):
            tabla.heading(col,text=col);tabla.column(col,width=w,anchor='w',stretch=(col=='Producto'))
        tabla.pack(fill='both',expand=True,padx=12,pady=12)
        items=[]
        for p in datos.get('productos',[]):
            nombre=str(p.get('nombre') or p.get('descripcion') or '').strip()
            cantidad=float(p.get('cantidad',0) or 0); precio=float(p.get('precio_unitario',0) or 0)
            subtotal=float(p.get('subtotal',0) or 0)
            if precio <= 0 and subtotal > 0 and cantidad > 0: precio=subtotal/cantidad
            if subtotal <= 0: subtotal=cantidad*precio
            if nombre: items.append({'nombre':nombre,'cantidad':cantidad,'precio':precio,'subtotal':subtotal})
        def recargar():
            tabla.delete(*tabla.get_children())
            for i,p in enumerate(items):
                tabla.insert('', 'end', iid=str(i), values=(p['nombre'],f"{p['cantidad']:g}",f"${p['precio']:.2f}",f"${p['subtotal']:.2f}"))
            total=sum(p['subtotal'] for p in items); total_lbl.configure(text=f'Total detectado: ${total:,.2f}')
        def editar():
            sel=tabla.selection()
            if not sel:return
            i=int(sel[0]);p=items[i]
            nombre=simpledialog.askstring('Corregir renglon','Descripcion escrita en la nota:',initialvalue=p['nombre'],parent=revision)
            if not nombre:return
            cantidad=simpledialog.askfloat('Cantidad','Cantidad vendida:',initialvalue=p['cantidad'],minvalue=0.001,parent=revision)
            if cantidad is None:return
            precio=simpledialog.askfloat('Precio','Precio unitario:',initialvalue=p['precio'],minvalue=0,parent=revision)
            if precio is None:return
            items[i].update(nombre=nombre.strip(),cantidad=cantidad,precio=precio,subtotal=cantidad*precio);recargar()
        def eliminar():
            sel=tabla.selection()
            if sel:items.pop(int(sel[0]));recargar()
        def agregar():
            nombre=simpledialog.askstring('Agregar renglon','Descripcion escrita en la nota:',parent=revision)
            if not nombre:return
            cantidad=simpledialog.askfloat('Cantidad','Cantidad vendida:',minvalue=0.001,parent=revision)
            if cantidad is None:return
            precio=simpledialog.askfloat('Precio','Precio unitario:',minvalue=0,parent=revision)
            if precio is None:return
            items.append({'nombre':nombre.strip(),'cantidad':cantidad,'precio':precio,'subtotal':cantidad*precio});recargar()
        acciones=ctk.CTkFrame(revision,fg_color='transparent');acciones.pack(fill='x',padx=20,pady=(0,16))
        ctk.CTkButton(acciones,text='Editar renglon',command=editar,width=120,height=34,fg_color='#343941').pack(side='left')
        ctk.CTkButton(acciones,text='Quitar',command=eliminar,width=80,height=34,fg_color='#ffffff',border_width=1,border_color='#d9dde3',text_color='#505762').pack(side='left',padx=6)
        ctk.CTkButton(acciones,text='Agregar',command=agregar,width=82,height=34,fg_color='#ffffff',border_width=1,border_color='#d9dde3',text_color='#505762').pack(side='left')
        total_lbl=ctk.CTkLabel(acciones,text='',font=ctk.CTkFont('Poppins',12,'bold'),text_color=COLOR_VINO);total_lbl.pack(side='left',padx=18)
        ctk.CTkButton(acciones,text='Capturar en Ventas',command=lambda:self._capturar_nota_en_ventas(datos,ruta,entradas,items,revision),width=160,height=38,fg_color=COLOR_VINO,hover_color=COLOR_VINO_OSCURO).pack(side='right')
        ctk.CTkButton(acciones,text='Cancelar',command=revision.destroy,width=82,height=38,fg_color='#e9ebef',text_color='#505762').pack(side='right',padx=7)
        tabla.bind('<Double-1>',lambda _e:editar());recargar()

    def _capturar_nota_en_ventas(self, datos, ruta, entradas, items, revision):
        if not items or any(not p.get('nombre') or p.get('cantidad',0) <= 0 for p in items):
            messagebox.showwarning('Revisa los renglones','Completa la descripcion y cantidad de cada renglon.',parent=revision)
            return
        def numero(clave):
            try:
                return float(str(entradas[clave].get()).replace('$','').replace(',','').strip() or 0)
            except (ValueError, KeyError):
                return 0.0
        captura = {
            'folio': entradas['folio'].get().strip(),
            'fecha': entradas['fecha'].get().strip(),
            'cliente': entradas['cliente'].get().strip() or 'Cliente General',
            'direccion': entradas['direccion'].get().strip(),
            'telefono': entradas['telefono'].get().strip(),
            'vendedor': entradas['vendedor'].get().strip(),
            'tipo_pago': entradas['tipo_pago'].get().strip() or 'Contado',
            'abono': numero('abono'),
            'total': sum(float(p.get('subtotal',0) or 0) for p in items),
            'productos': [dict(nombre=p['nombre'], cantidad=p['cantidad'],
                               precio_unitario=p['precio'], subtotal=p['subtotal']) for p in items],
        }
        try:
            carpeta=os.path.abspath(os.path.join('media','notas_venta'));os.makedirs(carpeta,exist_ok=True)
            ext=os.path.splitext(ruta)[1].lower() or '.jpg'
            destino=os.path.join(carpeta,f'nota_{uuid.uuid4().hex}{ext}')
            shutil.copy2(ruta,destino)
            self.app.capturar_nota_en_ventas(captura,destino)
            self._auditar('capturar_nota_en_ventas',{'folio':captura['folio'],'total':captura['total'],'imagen':destino},True)
            revision.destroy()
            self._mensaje('JELOX',f'Nota capturada en Ventas. Revisa el folio {captura["folio"] or "Sin folio"} y procesa el pago cuando este correcta.')
            if self.ventana and self.ventana.winfo_exists():
                self.ventana.withdraw()
        except Exception as exc:
            messagebox.showerror('No se pudo capturar en Ventas',str(exc),parent=revision)

    def _registrar_nota(self, datos, ruta, entradas, items, revision):
        invalidos=[p for p in items if not p['valido'] or p['cantidad']<=0 or p['cantidad']>p['stock']]
        if not items or invalidos:
            messagebox.showwarning('Revisa los productos','Corrige los renglones marcados como Revisar o Sin stock.',parent=revision);return
        folio=entradas['folio'].get().strip();cliente=entradas['cliente'].get().strip() or 'Cliente General'
        fecha=entradas['fecha'].get().strip() or datetime.now().strftime('%d/%m/%Y')
        tipo='Credito' if 'credit' in entradas['tipo_pago'].get().strip().lower() else 'Contado'
        total=sum(p['subtotal'] for p in items)
        if not messagebox.askyesno('Confirmar registro',f'¿Registrar la venta del folio {folio or "Sin folio"} por ${total:,.2f}?\n\nSe descontara el inventario.',parent=revision):return
        try:
            carpeta=os.path.abspath(os.path.join('media','notas_venta'));os.makedirs(carpeta,exist_ok=True)
            ext=os.path.splitext(ruta)[1].lower() or '.jpg';destino=os.path.join(carpeta,f'nota_{uuid.uuid4().hex}{ext}');shutil.copy2(ruta,destino)
            ahora=datetime.now();hora=ahora.strftime('%H:%M:%S');subtotal=total;iva=0.0
            with sqlite3.connect('database.db') as c:
                if folio and c.execute('SELECT 1 FROM ventas WHERE folio=?',(folio,)).fetchone():raise ValueError('Ya existe una venta con ese folio.')
                costo=sum(c.execute('SELECT costo FROM articulos WHERE codigo=?',(p['codigo'],)).fetchone()[0]*p['cantidad'] for p in items)
                monto_recibido=0 if tipo=='Credito' else total;saldo=total if tipo=='Credito' else 0;estado='Credito' if saldo else 'Pagado'
                cur=c.execute('''INSERT INTO ventas(numero_factura,factura,cliente,articulo,precio,cantidad,total,fecha,hora,costo,subtotal,iva,monto_recibido,cambio,folio,tipo_pago,saldo,estado_pago)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(None,None,cliente,'Venta Multiple',subtotal,1,total,fecha,hora,costo,subtotal,iva,monto_recibido,0,folio,tipo,saldo,estado))
                venta_id=cur.lastrowid
                for p in items:
                    c.execute('INSERT INTO detalle_ventas(venta_id,producto,precio_unitario,cantidad,subtotal) VALUES(?,?,?,?,?)',(venta_id,p['nombre'],p['precio'],p['cantidad'],p['subtotal']))
                    c.execute('UPDATE articulos SET stock=stock-? WHERE codigo=?',(p['cantidad'],p['codigo']))
                c.execute('''CREATE TABLE IF NOT EXISTS notas_venta_ia(id INTEGER PRIMARY KEY AUTOINCREMENT,venta_id INTEGER,ruta_imagen TEXT,usuario TEXT,fecha_registro TEXT)''')
                c.execute('INSERT INTO notas_venta_ia(venta_id,ruta_imagen,usuario,fecha_registro) VALUES(?,?,?,?)',(venta_id,destino,self.usuario,ahora.isoformat(timespec='seconds')))
            self._auditar('registrar_nota_venta',{'venta_id':venta_id,'folio':folio,'total':total,'imagen':destino},True)
            revision.destroy();self._mensaje('JELOX',f'Venta registrada correctamente. Folio: {folio or "Sin folio"}. Total: ${total:,.2f}.');self.app.refrescar_modulos()
        except Exception as exc:
            messagebox.showerror('No se pudo registrar',str(exc),parent=revision)

    def _llamar_openai(self, clave, mensajes):
        """Usa un modelo economico y prueba una alternativa compatible si la cuenta no lo tiene."""
        configurado = os.getenv('CARNES_LUEVANOS_AI_MODEL', '').strip()
        modelos = [m for m in (configurado, 'gpt-4o-mini', 'gpt-4.1-mini') if m]
        ultima = None
        for modelo in dict.fromkeys(modelos):
            ultima = requests.post('https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {clave}', 'Content-Type': 'application/json'},
                json={'model': modelo, 'messages': mensajes, 'tools': self._herramientas(),
                      'tool_choice': 'auto', 'temperature': 0.2}, timeout=90)
            if ultima.ok:
                return ultima
            if ultima.status_code not in (400, 404):
                return ultima
            try:
                detalle = ultima.json().get('error', {}).get('message', '').lower()
                if 'model' not in detalle:
                    return ultima
            except Exception:
                return ultima
        return ultima

    def _modelo_local_disponible(self):
        try:
            datos = requests.get('http://127.0.0.1:11434/api/tags', timeout=2).json()
            nombres = [m.get('name', '') for m in datos.get('models', [])]
            preferido = os.getenv('CARNES_LUEVANOS_LOCAL_MODEL', 'qwen3:0.6b')
            if preferido in nombres:
                return preferido
            return nombres[0] if nombres else None
        except Exception:
            return None

    def _asegurar_ollama(self):
        modelo = self._modelo_local_disponible()
        if modelo:
            return modelo
        ejecutable = shutil.which('ollama')
        if not ejecutable:
            candidato = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Programs', 'Ollama', 'ollama.exe')
            ejecutable = candidato if os.path.isfile(candidato) else None
        if not ejecutable:
            return None
        try:
            subprocess.Popen(
                [ejecutable, 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
            for _ in range(20):
                time.sleep(.5)
                modelo = self._modelo_local_disponible()
                if modelo:
                    return modelo
        except OSError:
            return None
        return None

    def _llamar_ollama(self, mensajes, modelo):
        respuesta = requests.post(
            'http://127.0.0.1:11434/api/chat',
            headers={'Content-Type': 'application/json'},
            json={
                'model': modelo, 'messages': mensajes, 'stream': False,
                'think': False, 'keep_alive': '30m',
                'options': {'temperature': 0.2, 'num_predict': 420, 'num_ctx': 4096},
            },
            timeout=120,
        )
        if not respuesta.ok:
            try:
                detalle = respuesta.json().get('error') or respuesta.text[:300]
            except Exception:
                detalle = respuesta.text[:300]
            raise RuntimeError(f'Ollama no pudo responder: {detalle}')
        return respuesta.json()

    def _instrucciones(self):
        return f'''Eres JELOX, el robot y asistente operativo inteligente del sistema Carnes Luévanos. Preséntate como JELOX cuando sea apropiado y responde siempre en español claro.
Usuario actual: {self.usuario}. Puedes responder preguntas generales y usar herramientas para consultar u operar el sistema.
Nunca inventes datos del negocio. Usa las herramientas para datos internos. Antes de una accion que modifica datos,
explica brevemente que hiciste o si el usuario la rechazo. No solicites ni reveles contraseñas, hashes o claves API.
Para operaciones no disponibles, abre el modulo correspondiente y explica al usuario el paso que falta.'''

    def _herramientas(self):
        def tool(nombre, descripcion, propiedades=None, requeridos=None):
            return {'type': 'function', 'function': {'name': nombre, 'description': descripcion,
                'parameters': {'type': 'object', 'properties': propiedades or {}, 'required': requeridos or [], 'additionalProperties': False}}}
        return [
            tool('resumen_negocio', 'Obtiene resumen actual de ventas, inventario, clientes y compras.'),
            tool('buscar_productos', 'Busca productos por nombre o codigo.', {'texto': {'type':'string'}, 'limite': {'type':'integer','minimum':1,'maximum':30}}, ['texto']),
            tool('buscar_clientes', 'Busca clientes por nombre, telefono, identificacion o correo.', {'texto': {'type':'string'}, 'limite': {'type':'integer','minimum':1,'maximum':30}}, ['texto']),
            tool('consultar_ventas', 'Consulta ventas recientes y opcionalmente filtra cliente o folio.', {'texto': {'type':'string'}, 'limite': {'type':'integer','minimum':1,'maximum':30}}),
            tool('abrir_modulo', 'Abre un modulo del sistema.', {'modulo': {'type':'string','enum':['inicio','ventas','inventario','clientes','pedidos','proveedores','compras','prestamos','nominas','abonos','configuracion']}}, ['modulo']),
            tool('crear_cliente', 'Crea un cliente. Requiere confirmacion visible.', {'nombre':{'type':'string'},'telefono':{'type':'string'},'identificacion':{'type':'string'},'direccion':{'type':'string'},'correo':{'type':'string'}}, ['nombre']),
            tool('ajustar_stock', 'Cambia existencias de un producto a una cantidad final. Requiere confirmacion visible.', {'codigo':{'type':'string'},'nuevo_stock':{'type':'integer','minimum':0},'motivo':{'type':'string'}}, ['codigo','nuevo_stock','motivo']),
        ]

    def _ejecutar(self, nombre, args):
        try:
            if nombre == 'resumen_negocio': return self._resumen()
            if nombre == 'buscar_productos': return self._buscar_productos(args.get('texto',''), args.get('limite',10))
            if nombre == 'buscar_clientes': return self._buscar_clientes(args.get('texto',''), args.get('limite',10))
            if nombre == 'consultar_ventas': return self._ventas(args.get('texto',''), args.get('limite',10))
            if nombre == 'abrir_modulo': return self._abrir_modulo(args['modulo'])
            if nombre == 'crear_cliente': return self._crear_cliente(args)
            if nombre == 'ajustar_stock': return self._ajustar_stock(args)
            return {'ok': False, 'error': 'Herramienta desconocida'}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def _resumen(self):
        hoy = datetime.now()
        fechas = (hoy.strftime('%d/%m/%Y'), hoy.strftime('%Y-%m-%d'))
        with sqlite3.connect('database.db') as c:
            total = c.execute("SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha IN (?,?)", fechas).fetchone()[0]
            ventas = c.execute("SELECT COUNT(*) FROM ventas WHERE fecha IN (?,?)", fechas).fetchone()[0]
            clientes = c.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
            productos = c.execute("SELECT COUNT(*),COALESCE(SUM(stock),0) FROM articulos WHERE lower(estado)='activo'").fetchone()
            bajo = c.execute("SELECT COUNT(*) FROM articulos WHERE lower(estado)='activo' AND stock<=5").fetchone()[0]
        return {'ok':True,'ventas_hoy':ventas,'importe_hoy':round(float(total),2),'clientes':clientes,'productos_activos':productos[0],'unidades_stock':productos[1],'productos_stock_bajo':bajo}

    def _buscar_productos(self, texto, limite):
        patron=f'%{texto}%'
        with sqlite3.connect('database.db') as c:
            filas=c.execute('SELECT codigo,articulo,precio,costo,stock,estado FROM articulos WHERE articulo LIKE ? OR codigo LIKE ? ORDER BY articulo LIMIT ?', (patron,patron,int(limite))).fetchall()
        return {'ok':True,'productos':[dict(zip(('codigo','articulo','precio','costo','stock','estado'),f)) for f in filas]}

    def _buscar_clientes(self, texto, limite):
        patron=f'%{texto}%'
        with sqlite3.connect('database.db') as c:
            filas=c.execute('SELECT id,nombre,cedula,celular,direccion,correo FROM clientes WHERE nombre LIKE ? OR CAST(cedula AS TEXT) LIKE ? OR CAST(celular AS TEXT) LIKE ? OR correo LIKE ? ORDER BY nombre LIMIT ?', (patron,patron,patron,patron,int(limite))).fetchall()
        return {'ok':True,'clientes':[dict(zip(('id','nombre','identificacion','telefono','direccion','correo'),f)) for f in filas]}

    def _ventas(self, texto, limite):
        patron=f'%{texto}%'
        with sqlite3.connect('database.db') as c:
            cols={r[1] for r in c.execute('PRAGMA table_info(ventas)')}
            folio='folio' if 'folio' in cols else ('factura' if 'factura' in cols else 'id')
            filas=c.execute(f'SELECT rowid,{folio},cliente,articulo,cantidad,total,fecha,hora FROM ventas WHERE cliente LIKE ? OR CAST({folio} AS TEXT) LIKE ? ORDER BY rowid DESC LIMIT ?', (patron,patron,int(limite))).fetchall()
        return {'ok':True,'ventas':[dict(zip(('id','folio','cliente','articulo','cantidad','total','fecha','hora'),f)) for f in filas]}

    def _abrir_modulo(self, modulo):
        mapa={'inicio':'Inicio','ventas':'Ventas','inventario':'Inventario','clientes':'Clientes','pedidos':'Pedidos','proveedores':'Proveedor','compras':'Compras','prestamos':'Prestamos','nominas':'Nominas','abonos':'Abonos','configuracion':'Configuracion'}
        metodo=getattr(self.app,mapa[modulo],None)
        if not callable(metodo): return {'ok':False,'error':'Modulo no disponible'}
        self.app.after(0, metodo)
        return {'ok':True,'modulo':modulo}

    def _confirmar(self, titulo, detalle):
        evento=threading.Event(); resultado={'si':False}
        def preguntar():
            resultado['si']=messagebox.askyesno(titulo, detalle, parent=self.ventana, icon='warning'); evento.set()
        self.ventana.after(0,preguntar); evento.wait(120)
        return resultado['si']

    def _crear_cliente(self, a):
        detalle=f"Se creara el cliente:\n\nNombre: {a['nombre']}\nTelefono: {a.get('telefono','')}\nIdentificacion: {a.get('identificacion','')}"
        if not self._confirmar('Confirmar nuevo cliente',detalle): return {'ok':False,'cancelado':True}
        with sqlite3.connect('database.db') as c:
            cur=c.execute('INSERT INTO clientes(nombre,cedula,celular,direccion,correo) VALUES(?,?,?,?,?)',(a['nombre'],a.get('identificacion',''),a.get('telefono',''),a.get('direccion',''),a.get('correo','')))
            uid=cur.lastrowid
        self._auditar('crear_cliente',a,True); self.app.after(0,self.app.refrescar_modulos)
        return {'ok':True,'cliente_id':uid}

    def _ajustar_stock(self, a):
        with sqlite3.connect('database.db') as c:
            fila=c.execute('SELECT articulo,stock FROM articulos WHERE codigo=?',(a['codigo'],)).fetchone()
        if not fila: return {'ok':False,'error':'Producto no encontrado'}
        detalle=f"Producto: {fila[0]}\nStock actual: {fila[1]}\nNuevo stock: {a['nuevo_stock']}\nMotivo: {a['motivo']}"
        if not self._confirmar('Confirmar ajuste de inventario',detalle): return {'ok':False,'cancelado':True}
        with sqlite3.connect('database.db') as c: c.execute('UPDATE articulos SET stock=? WHERE codigo=?',(a['nuevo_stock'],a['codigo']))
        self._auditar('ajustar_stock',a,True); self.app.after(0,self.app.refrescar_modulos)
        return {'ok':True,'producto':fila[0],'stock_anterior':fila[1],'stock_nuevo':a['nuevo_stock']}

    def _crear_tabla_auditoria(self):
        with sqlite3.connect('database.db') as c:
            c.execute('''CREATE TABLE IF NOT EXISTS auditoria_ia(id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,accion TEXT,argumentos TEXT,exito INTEGER,fecha TEXT)''')

    def _auditar(self, accion, argumentos, exito):
        with sqlite3.connect('database.db') as c:
            c.execute('INSERT INTO auditoria_ia(usuario,accion,argumentos,exito,fecha) VALUES(?,?,?,?,?)',
                      (self.usuario,accion,json.dumps(argumentos,ensure_ascii=False),int(exito),datetime.now().isoformat(timespec='seconds')))

    def _mensaje(self, autor, texto):
        if not hasattr(self, 'chat_burbujas'):
            self.chat.configure(state='normal')
            self.chat.insert('end', f'{autor}\n')
            self.chat.insert('end', f'{texto}\n\n')
            self.chat.configure(state='disabled'); self.chat.see('end')
            return

        texto = str(texto or '')
        es_usuario = autor.casefold() in ('tu', 'tú', 'usuario')
        es_jelox = autor.casefold() == 'jelox'
        fila = ctk.CTkFrame(self.chat_burbujas, fg_color='transparent', corner_radius=0)
        fila.pack(fill='x', padx=2, pady=4)

        columna = ctk.CTkFrame(fila, fg_color='transparent', corner_radius=0)
        columna.pack(side='right' if es_usuario else 'left', anchor='e' if es_usuario else 'w')

        if es_jelox:
            avatar = ctk.CTkLabel(
                fila, text='' if self._avatar_mensaje else 'J', image=self._avatar_mensaje,
                width=26, height=26, corner_radius=13, fg_color='transparent',
                text_color='#00c8ff', font=ctk.CTkFont('Poppins', 8, 'bold'))
            avatar.pack(side='left', anchor='n', padx=(0, 7), pady=(3, 0))
            columna.pack_forget()
            columna.pack(side='left', anchor='w')

        if es_usuario:
            fondo, color_texto = '#1769ff', '#ffffff'
        elif es_jelox:
            fondo, color_texto = '#eef0f2', '#20242a'
        else:
            fondo, color_texto = '#fff7e6', '#665122'

        burbuja = ctk.CTkFrame(columna, fg_color=fondo, corner_radius=17, border_width=0)
        burbuja.pack(anchor='e' if es_usuario else 'w')
        ctk.CTkLabel(
            burbuja, text=texto, wraplength=250, justify='left', anchor='w',
            text_color=color_texto, font=ctk.CTkFont('Poppins', 11)
        ).pack(padx=12, pady=8)

        hora = datetime.now().strftime('%H:%M')
        pie = f'Enviado · {hora}' if es_usuario else hora
        ctk.CTkLabel(
            columna, text=pie, text_color='#8a9099',
            font=ctk.CTkFont('Poppins', 8)
        ).pack(anchor='e' if es_usuario else 'w', padx=5, pady=(1, 0))

        self._chat_items.append({'texto': texto, 'burbuja': burbuja, 'fila': fila})

        def ir_al_final():
            try:
                self.chat_burbujas._parent_canvas.yview_moveto(1.0)
            except Exception:
                pass
        self.ventana.after(25, ir_al_final)

    def _entregar_respuesta(self, texto, inventario_actualizado=False):
        self._mensaje('JELOX', texto)
        if hasattr(self.app, 'notificar_respuesta_jelox'):
            self.app.notificar_respuesta_jelox(texto, inventario_actualizado=inventario_actualizado)

    @staticmethod
    def _error_api(respuesta):
        try: return respuesta.json().get('error',{}).get('message') or f'Error de OpenAI ({respuesta.status_code})'
        except Exception: return f'Error de OpenAI ({respuesta.status_code})'

    @staticmethod
    def _limpiar_respuesta(texto):
        texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.I | re.S)
        return texto.strip() or 'Listo.'
