import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from modulos.utils.estilos_modernos import estilos


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class RendimientoModerno(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre, bg=estilos.COLORS['bg_primary'])
        self.entries = {}
        self.resultados = {}
        self.widgets()

    def widgets(self):
        self.crear_header()
        self.crear_formulario()
        self.crear_metricas()
        self.crear_detalle()

    def crear_header(self):
        header = tk.Frame(self, bg=estilos.COLORS['bg_primary'])
        header.place(x=20, y=15, width=1360, height=70)

        tk.Label(
            header,
            text="Modulo de Rendimiento",
            font=('Poppins', 24, 'bold'),
            bg=estilos.COLORS['bg_primary'],
            fg=estilos.COLORS['primary2']
        ).place(x=0, y=0)

        tk.Label(
            header,
            text="Calcula costo en pie, rendimiento en canal, gastos, subproductos y costo neto por kg.",
            font=('Poppins', 11),
            bg=estilos.COLORS['bg_primary'],
            fg=estilos.COLORS['dark_gray']
        ).place(x=3, y=42)

    def crear_formulario(self):
        self.form_frame = ctk.CTkFrame(
            self,
            width=360,
            height=620,
            corner_radius=18,
            fg_color=estilos.COLORS['white'],
            border_width=1,
            border_color=estilos.COLORS['border']
        )
        self.form_frame.place(x=20, y=100)

        ctk.CTkLabel(
            self.form_frame,
            text="Datos del procesamiento",
            font=ctk.CTkFont(family="Poppins", size=20, weight="bold"),
            fg_color='transparent',
            bg_color=estilos.COLORS['white'],
            text_color=estilos.COLORS['primary2']
        ).place(x=22, y=18)

        self.crear_seccion("Datos principales", 62)
        self.entries["producto"] = self.crear_campo("producto", "Nombre del producto", 22, 92, width=316)
        self.entries["kg_pie"] = self.crear_campo("kg_pie", "Kg en pie", 22, 150)
        self.entries["precio_pie"] = self.crear_campo("precio_pie", "$ kg en pie", 190, 150)

        self.crear_seccion("Procesamiento", 216)
        self.entries["kg_canal"] = self.crear_campo("kg_canal", "Kg canal", 22, 246)

        self.crear_seccion("Gastos", 216, x=190)
        self.entries["maquila"] = self.crear_campo("maquila", "Maquila", 190, 246)
        self.entries["flete"] = self.crear_campo("flete", "Flete", 190, 304)

        self.crear_seccion("Subproductos", 362)
        self.entries["precio_viscera"] = self.crear_campo("precio_viscera", "$ viscera kg", 22, 392)
        self.entries["kg_piel"] = self.crear_campo("kg_piel", "Kg piel", 190, 392)
        self.entries["precio_piel"] = self.crear_campo("precio_piel", "$ piel kg", 22, 450)

        ctk.CTkButton(
            self.form_frame,
            text="Calcular",
            command=self.calcular,
            width=148,
            height=42,
            corner_radius=12,
            fg_color=estilos.COLORS['primary2'],
            hover_color=estilos.COLORS['secondary1'],
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold")
        ).place(x=22, y=548)

        ctk.CTkButton(
            self.form_frame,
            text="Limpiar",
            command=self.limpiar,
            width=148,
            height=42,
            corner_radius=12,
            fg_color=estilos.COLORS['dark_gray'],
            hover_color=estilos.COLORS['gray'],
            font=ctk.CTkFont(family="Poppins", size=12, weight="bold")
        ).place(x=188, y=548)

    def crear_seccion(self, titulo, y, x=22):
        ctk.CTkLabel(
            self.form_frame,
            text=titulo,
            font=ctk.CTkFont(family="Poppins", size=13, weight="bold"),
            fg_color='transparent',
            bg_color=estilos.COLORS['white'],
            text_color=estilos.COLORS['primary2']
        ).place(x=x, y=y)

    def crear_campo(self, key, etiqueta, x, y, width=148):
        ctk.CTkLabel(
            self.form_frame,
            text=etiqueta,
            font=ctk.CTkFont(family="Poppins", size=10, weight="bold"),
            fg_color='transparent',
            bg_color=estilos.COLORS['white'],
            text_color=estilos.COLORS['dark_gray']
        ).place(x=x, y=y)

        placeholders = {
            "producto": "Ej. canal, lote, producto",
            "kg_pie": "Kg",
            "precio_pie": "$",
            "kg_canal": "Kg",
            "maquila": "$",
            "flete": "$",
            "precio_viscera": "$",
            "kg_piel": "Kg",
            "precio_piel": "$",
        }
        return self.crear_entry(placeholders.get(key, ""), x, y + 20, width)

    def crear_entry(self, placeholder, x, y, width=148):
        entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text=placeholder,
            width=width,
            height=34,
            corner_radius=10,
            border_color=estilos.COLORS['border'],
            fg_color=estilos.COLORS['white'],
            text_color=estilos.COLORS['dark'],
            placeholder_text_color=estilos.COLORS['gray'],
            font=ctk.CTkFont(family="Poppins", size=12)
        )
        entry.place(x=x, y=y)
        return entry

    def crear_metricas(self):
        self.metric_frame = tk.Frame(self, bg=estilos.COLORS['bg_primary'])
        self.metric_frame.place(x=405, y=100, width=955, height=210)

        cards = [
            ("Total pie", "total_pie", estilos.COLORS['primary2'], 0, 0),
            ("Rendimiento", "rendimiento", estilos.COLORS['secondary1'], 320, 0),
            ("$ canal", "precio_canal", estilos.COLORS['info2'], 640, 0),
            ("Tot c/gastos", "total_con_gastos", estilos.COLORS['accent1'], 0, 110),
            ("Sub prod", "subproductos", estilos.COLORS['warning'], 320, 110),
            ("$ neto canal", "neto_canal", estilos.COLORS['success'], 640, 110),
        ]

        for titulo, key, color, x, y in cards:
            card = ctk.CTkFrame(self.metric_frame, width=292, height=88, corner_radius=16, fg_color=color)
            card.place(x=x, y=y)
            tk.Label(card, text=titulo, bg=color, fg=estilos.COLORS['white'], font=('Poppins', 11, 'bold')).place(x=18, y=12)
            label = tk.Label(card, text="$ 0.00", bg=color, fg=estilos.COLORS['white'], font=('Poppins', 20, 'bold'))
            label.place(x=18, y=40)
            self.resultados[key] = label

    def crear_detalle(self):
        self.detalle_frame = ctk.CTkFrame(
            self,
            width=955,
            height=390,
            corner_radius=18,
            fg_color=estilos.COLORS['white'],
            border_width=1,
            border_color=estilos.COLORS['border']
        )
        self.detalle_frame.place(x=405, y=330)

        ctk.CTkLabel(
            self.detalle_frame,
            text="Resumen del calculo",
            font=ctk.CTkFont(family="Poppins", size=20, weight="bold"),
            fg_color='transparent',
            bg_color=estilos.COLORS['white'],
            text_color=estilos.COLORS['primary2']
        ).place(x=22, y=18)

        self.detalle_text = tk.Text(
            self.detalle_frame,
            bg=estilos.COLORS['white'],
            fg=estilos.COLORS['dark'],
            font=('Consolas', 11),
            relief='flat',
            bd=0,
            height=17,
            wrap='word'
        )
        self.detalle_text.place(x=22, y=58, width=910, height=300)
        self.detalle_text.configure(state='disabled')

    def obtener_numero(self, key):
        valor = self.entries[key].get().strip().replace(",", "")
        if not valor:
            return 0.0
        return float(valor)

    def calcular(self):
        try:
            producto = self.entries["producto"].get().strip() or "Producto"
            kg_pie = self.obtener_numero("kg_pie")
            precio_pie = self.obtener_numero("precio_pie")
            kg_canal = self.obtener_numero("kg_canal")
            maquila = self.obtener_numero("maquila")
            flete = self.obtener_numero("flete")
            precio_viscera = self.obtener_numero("precio_viscera")
            kg_piel = self.obtener_numero("kg_piel")
            precio_piel = self.obtener_numero("precio_piel")

            if kg_pie <= 0 or kg_canal <= 0:
                messagebox.showwarning("Datos incompletos", "Kg en pie y kg canal deben ser mayores a cero.")
                return

            total_pie = kg_pie * precio_pie
            rendimiento = (kg_canal / kg_pie) * 100
            total_gastos = maquila + flete
            total_con_gastos = total_pie + total_gastos
            precio_canal = total_con_gastos / kg_canal
            viscera = kg_canal * precio_viscera
            piel = kg_piel * precio_piel
            subproductos = viscera + piel
            total_menos_subproductos = total_con_gastos - subproductos
            neto_canal = total_menos_subproductos / kg_canal

            self.resultados["total_pie"].configure(text=self.formato_moneda(total_pie))
            self.resultados["rendimiento"].configure(text=f"{rendimiento:,.2f}%")
            self.resultados["precio_canal"].configure(text=self.formato_moneda(precio_canal))
            self.resultados["total_con_gastos"].configure(text=self.formato_moneda(total_con_gastos))
            self.resultados["subproductos"].configure(text=self.formato_moneda(subproductos))
            self.resultados["neto_canal"].configure(text=self.formato_moneda(neto_canal))

            detalle = (
                f"Datos principales\n"
                f"- Nombre del producto: {producto}.\n"
                f"- Kg en pie: {kg_pie:,.2f} kg.\n"
                f"- Precio: {self.formato_moneda(precio_pie)} por kg en pie.\n"
                f"- Tot pie: {kg_pie:,.2f} kg x {self.formato_moneda(precio_pie)} = {self.formato_moneda(total_pie)}.\n\n"
                f"Procesamiento y rendimiento\n"
                f"- Kg canal: {kg_canal:,.2f} kg.\n"
                f"- Rendimiento: {rendimiento:,.2f}%.\n"
                f"- $ canal: {self.formato_moneda(total_con_gastos)} / {kg_canal:,.2f} kg = {self.formato_moneda(precio_canal)}.\n\n"
                f"Gastos adicionales\n"
                f"- Maquila: {self.formato_moneda(maquila)}.\n"
                f"- Flete: {self.formato_moneda(flete)}.\n"
                f"- Total gastos: {self.formato_moneda(total_gastos)}.\n\n"
                f"Ingresos y resultados\n"
                f"- Tot c/gastos: {self.formato_moneda(total_pie)} + {self.formato_moneda(total_gastos)} = {self.formato_moneda(total_con_gastos)}.\n"
                f"- Viscera: {kg_canal:,.2f} kg x {self.formato_moneda(precio_viscera)} = {self.formato_moneda(viscera)}.\n"
                f"- Piel: {kg_piel:,.2f} kg x {self.formato_moneda(precio_piel)} = {self.formato_moneda(piel)}.\n"
                f"- Total subproductos: {self.formato_moneda(subproductos)}.\n"
                f"- Tot - sub/p: {self.formato_moneda(total_con_gastos)} - {self.formato_moneda(subproductos)} = {self.formato_moneda(total_menos_subproductos)}.\n"
                f"- $ neto canal: {self.formato_moneda(total_menos_subproductos)} / {kg_canal:,.2f} kg = {self.formato_moneda(neto_canal)}."
            )
            self.actualizar_detalle(detalle)
        except ValueError:
            messagebox.showerror("Error", "Revisa que los campos numericos tengan valores validos.")

    def actualizar_detalle(self, texto):
        self.detalle_text.configure(state='normal')
        self.detalle_text.delete("1.0", tk.END)
        self.detalle_text.insert("1.0", texto)
        self.detalle_text.configure(state='disabled')

    def limpiar(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.actualizar_detalle("")
        for key, label in self.resultados.items():
            label.configure(text="0.00%" if key == "rendimiento" else "$ 0.00")

    @staticmethod
    def formato_moneda(valor):
        return f"$ {valor:,.2f}"



