"""Adaptador de módulos heredados con coordenadas fijas al área disponible."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from modulos.utils.estilos_modernos import estilos


def hacer_adaptable(modulo, base_width=1400, base_height=760):
    """Escala widgets administrados con place sin alterar su lógica."""
    estado = {"capturado": False, "items": [], "after": None}

    def recorrer(widget):
        for child in widget.winfo_children():
            try:
                if isinstance(child, tk.LabelFrame):
                    child.configure(bg=estilos.COLORS["white"], fg=estilos.COLORS["primary2"],
                                    relief="flat", bd=0, highlightthickness=1,
                                    highlightbackground=estilos.COLORS["border"])
                elif isinstance(child, tk.Entry):
                    child.configure(relief="flat", bd=0, highlightthickness=1,
                                    highlightbackground=estilos.COLORS["border"],
                                    highlightcolor=estilos.COLORS["primary1"])
                if child.winfo_manager() == "place":
                    info = child.place_info()
                    valores = {}
                    for clave in ("x", "y", "width", "height"):
                        raw = info.get(clave, "")
                        if raw not in ("", None):
                            try:
                                valores[clave] = float(raw)
                            except (TypeError, ValueError):
                                pass
                    estado["items"].append((child, valores))
                recorrer(child)
            except tk.TclError:
                continue

    def capturar():
        if estado["capturado"] or not modulo.winfo_exists():
            return
        modulo.update_idletasks()
        recorrer(modulo)
        estado["capturado"] = True
        aplicar()

    def aplicar():
        if not estado["capturado"] or not modulo.winfo_exists():
            return
        ancho = max(720, modulo.winfo_width())
        alto = max(520, modulo.winfo_height())
        sx = min(1.0, max(0.62, ancho / float(base_width)))
        sy = min(1.0, max(0.68, alto / float(base_height)))
        for widget, original in estado["items"]:
            if not widget.winfo_exists():
                continue
            config = {}
            if "x" in original:
                config["x"] = round(original["x"] * sx)
            if "y" in original:
                config["y"] = round(original["y"] * sy)
            if original.get("width", 0) > 0:
                config["width"] = max(1, round(original["width"] * sx))
            if original.get("height", 0) > 0:
                config["height"] = max(1, round(original["height"] * sy))
            try:
                widget.place_configure(**config)
            except (tk.TclError, ValueError):
                pass

    def programar(_event=None):
        if estado["after"]:
            try:
                modulo.after_cancel(estado["after"])
            except tk.TclError:
                pass
        estado["after"] = modulo.after(60, capturar if not estado["capturado"] else aplicar)

    modulo.configure(bg=estilos.COLORS["bg_primary"])
    try:
        style = ttk.Style(modulo)
        style.configure("Treeview", font=("Poppins", 9), rowheight=26,
                        background=estilos.COLORS["white"], fieldbackground=estilos.COLORS["white"])
        style.configure("Treeview.Heading", font=("Poppins", 9, "bold"))
    except tk.TclError:
        pass
    modulo.bind("<Configure>", programar, add="+")
    modulo.after(120, capturar)
    return estado
