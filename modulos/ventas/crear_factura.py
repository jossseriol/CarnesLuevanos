import datetime
import hashlib
import os
import sqlite3
import sys
import textwrap
import uuid
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageFont

from modulos.ventas.obtener_numero_factura import obtener_numero_factura_actual


W, H = 1275, 1650
SCALE = W / 612


def _pt(value):
    return int(round(value * SCALE))


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def obtener_configuracion(clave, default=""):
    try:
        with sqlite3.connect("database.db") as conn:
            row = conn.execute(
                "SELECT valor FROM configuracion_sistema WHERE clave = ?",
                (clave,),
            ).fetchone()
        return row[0] if row and row[0] is not None else default
    except sqlite3.Error:
        return default


def _money(value):
    try:
        return f"$ {float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "$ 0.00"


def _font(name="regular", size=10):
    fonts = {
        "regular": "media/fonts/poppinsregular.ttf",
        "medium": "media/fonts/poppinsmedium.ttf",
        "bold": "media/fonts/Poppins-SemiBold.ttf",
    }
    path = resource_path(fonts.get(name, fonts["regular"]))
    try:
        return ImageFont.truetype(path, _pt(size))
    except Exception:
        return ImageFont.load_default()


FONT = _font("regular", 8)
BOLD = _font("bold", 8)
TITLE = _font("bold", 13)
BIG = _font("bold", 16)
SMALL = _font("regular", 7)
SMALL_BOLD = _font("bold", 7)


def _draw_text(draw, xy, text, font=FONT, fill="black", width=None, line_gap=2):
    x, y = xy
    text = str(text or "")
    if width is None:
        draw.text((x, y), text, font=font, fill=fill)
        return y + font.size + line_gap

    avg = max(5, font.size * 0.45)
    chars = max(8, int(width / avg))
    lines = textwrap.wrap(text, width=chars) or [""]
    for line in lines:
        while draw.textlength(line, font=font) > width and len(line) > 3:
            line = line[:-4] + "..."
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def _draw_pair(draw, label_x, value_x, y, label, value, width=180):
    _draw_text(draw, (label_x, y), label, BOLD)
    return _draw_text(draw, (value_x, y), value, FONT, width=width)


def _center_text(draw, box, text, font=SMALL, fill="black"):
    x1, y1, x2, y2 = box
    text = str(text or "")
    max_width = max(8, x2 - x1 - _pt(4))
    while draw.textlength(text, font=font) > max_width and len(text) > 3:
        text = text[:-4] + "..."
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2), text, font=font, fill=fill)


def _draw_logo(img, x, y, size):
    logo_path = resource_path("media/icons/logo_luevanos.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            px = x + (size - logo.width) // 2
            py = y + (size - logo.height) // 2
            img.alpha_composite(logo, (px, py))
            return
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    draw.ellipse((x, y, x + size, y + size), outline="black", width=3)
    _center_text(draw, (x, y + size // 3, x + size, y + size // 2), "CARNES", BIG)
    _center_text(draw, (x, y + size // 2, x + size, y + size * 2 // 3), "LUEVANOS", TITLE)


def _draw_control_code(draw, x, y, size, data):
    digest = hashlib.sha256(str(data).encode("utf-8")).digest()
    cells = 29
    cell = size // cells
    draw.rectangle((x, y, x + size, y + size), fill="white", outline="black", width=1)
    for finder_x, finder_y in ((0, 0), (cells - 7, 0), (0, cells - 7)):
        rx = x + finder_x * cell
        ry = y + finder_y * cell
        draw.rectangle((rx, ry, rx + cell * 7, ry + cell * 7), outline="black", width=cell)
        draw.rectangle((rx + cell * 2, ry + cell * 2, rx + cell * 5, ry + cell * 5), fill="black")
    bit = 0
    for row in range(cells):
        for col in range(cells):
            in_finder = (row < 7 and col < 7) or (row < 7 and col >= cells - 7) or (row >= cells - 7 and col < 7)
            if in_finder:
                continue
            byte = digest[bit % len(digest)]
            if (byte >> (bit % 8)) & 1:
                draw.rectangle((x + col * cell, y + row * cell, x + (col + 1) * cell, y + (row + 1) * cell), fill="black")
            bit += 1


def _safe_float(value, default=0.0):
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return float(default)


def generar_factura(total_venta, cliente, productos=None, datos_venta=None, abrir=True):
    """Crea una factura visual en PDF con datos reales de la venta."""
    productos = list(productos or [])
    datos_venta = dict(datos_venta or {})
    numero_factura = datos_venta.get("numero_factura") or obtener_numero_factura_actual()
    folio = datos_venta.get("folio") or f"V-{int(numero_factura):06d}"
    fecha = datos_venta.get("fecha") or datetime.datetime.now().strftime("%d/%m/%Y")
    hora = datos_venta.get("hora") or datetime.datetime.now().strftime("%H:%M:%S")
    subtotal = _safe_float(datos_venta.get("subtotal"), sum(_safe_float(p.get("total")) for p in productos))
    iva = _safe_float(datos_venta.get("iva"), max(_safe_float(total_venta) - subtotal, 0))
    total = _safe_float(datos_venta.get("total"), _safe_float(total_venta, subtotal + iva))
    monto_recibido = _safe_float(datos_venta.get("monto_recibido"), total)
    cambio = _safe_float(datos_venta.get("cambio"), 0)
    saldo = _safe_float(datos_venta.get("saldo"), 0)
    tipo_pago = datos_venta.get("tipo_pago", "Contado")

    empresa_nombre = obtener_configuracion("nombre_empresa", "Carnes Luevanos")
    empresa_direccion = obtener_configuracion("direccion_empresa", "Gomez Palacio, Durango")
    empresa_telefono = obtener_configuracion("telefono_empresa", "+52(87) 1503-4671")
    empresa_rfc = obtener_configuracion("rif_empresa", "J-00000000-0")
    iva_porcentaje = str(obtener_configuracion("iva_porcentaje", "0")).replace(",", ".")
    try:
        iva_porcentaje_num = float(iva_porcentaje)
    except ValueError:
        iva_porcentaje_num = 0.0

    factura_dir = os.path.abspath("facturas")
    os.makedirs(factura_dir, exist_ok=True)
    safe_folio = "".join(ch for ch in str(folio) if ch.isalnum() or ch in ("-", "_")) or str(numero_factura)
    pdf_path = os.path.join(factura_dir, f"Factura_{safe_folio}.pdf")

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((1, 1, W - 2, H - 2), outline="black", width=2)

    _draw_logo(img, _pt(24), _pt(18), _pt(128))
    y0 = _pt(58)
    left_label, left_value = _pt(170), _pt(252)
    right_label, right_value = _pt(392), _pt(502)
    receptor = cliente or "Cliente General"
    folio_fiscal = str(datos_venta.get("folio_fiscal") or uuid.uuid4()).upper()
    certificado = datos_venta.get("certificado", "00001000000000000000")
    cp_emisor = datos_venta.get("cp_emisor", "27403")

    _draw_pair(draw, left_label, left_value, y0, "RFC emisor:", empresa_rfc)
    _draw_pair(draw, left_label, left_value, y0 + _pt(18), "Nombre emisor:", empresa_nombre, _pt(160))
    _draw_pair(draw, left_label, left_value, y0 + _pt(38), "RFC receptor:", datos_venta.get("rfc_receptor", ""))
    _draw_pair(draw, left_label, left_value, y0 + _pt(58), "Nombre receptor:", receptor, _pt(160))
    _draw_pair(draw, left_label, left_value, y0 + _pt(82), "Codigo postal del receptor:", datos_venta.get("cp_receptor", ""))
    _draw_pair(draw, left_label, left_value, y0 + _pt(114), "Regimen fiscal receptor:", datos_venta.get("regimen_receptor", ""))
    _draw_pair(draw, left_label, left_value, y0 + _pt(146), "Uso CFDI:", datos_venta.get("uso_cfdi", ""))

    _draw_pair(draw, right_label, right_value, y0, "Folio fiscal:", folio_fiscal, _pt(110))
    _draw_pair(draw, right_label, right_value, y0 + _pt(22), "No. de serie del CSD:", certificado, _pt(105))
    _draw_pair(draw, right_label, right_value, y0 + _pt(48), "CP y emision:", f"{cp_emisor} {fecha} {hora}", _pt(90))
    _draw_pair(draw, right_label, right_value, y0 + _pt(86), "Efecto de comprobante:", "Ingreso")
    _draw_pair(draw, right_label, right_value, y0 + _pt(112), "Regimen fiscal:", datos_venta.get("regimen_emisor", "Personas Fisicas con Actividades Empresariales"), _pt(96))
    _draw_pair(draw, right_label, right_value, y0 + _pt(150), "Exportacion:", "No aplica")

    draw.text((_pt(24), _pt(218)), "Conceptos", font=BIG, fill="black")
    x0, y = _pt(18), _pt(270)
    widths = [_pt(v) for v in (62, 62, 58, 58, 56, 66, 80, 70, 70)]
    headers = [
        "Clave del producto y/o servicio", "No. Identificacion", "Cantidad",
        "Clave de unidad", "Unidad", "Valor unitario", "Importe", "Descuento",
        "Objeto impuesto",
    ]
    row_h = _pt(28)
    x = x0
    for w, header in zip(widths, headers):
        draw.rectangle((x, y, x + w, y + row_h), fill="#d9d9d9", outline="black", width=1)
        _center_text(draw, (x + 2, y + 2, x + w - 2, y + row_h - 2), header, SMALL_BOLD)
        x += w

    y += row_h
    for index in range(2):
        item = productos[index] if index < len(productos) else {}
        cantidad = item.get("cantidad", "")
        precio = item.get("precio", item.get("precio_unitario", ""))
        importe = item.get("total", item.get("subtotal", ""))
        codigo = item.get("codigo", "") or item.get("clave", "")
        row = [
            "50111500" if item else "", codigo,
            f"{_safe_float(cantidad):g}" if cantidad != "" else "",
            "KGM" if item else "", "Kilo" if item else "",
            _money(precio) if item else "", _money(importe) if item else "",
            "$ 0.00" if item else "", "02" if item else "",
        ]
        x = x0
        for w, value in zip(widths, row):
            draw.rectangle((x, y, x + w, y + row_h), fill="white", outline="black", width=1)
            _center_text(draw, (x + 2, y + 2, x + w - 2, y + row_h - 2), value, SMALL)
            x += w
        y += row_h

    desc_h = _pt(46)
    draw.rectangle((x0, y, x0 + _pt(120), y + desc_h), fill="#d9d9d9", outline="black", width=1)
    _center_text(draw, (x0, y, x0 + _pt(120), y + desc_h), "Descripcion", SMALL_BOLD)
    draw.rectangle((x0 + _pt(120), y, x0 + _pt(360), y + desc_h), fill="white", outline="black", width=1)
    descripcion = "; ".join(str(p.get("nombre", p.get("producto", ""))) for p in productos[:5]) or "Venta de mostrador"
    _draw_text(draw, (x0 + _pt(125), y + _pt(8)), descripcion, SMALL, width=_pt(228), line_gap=1)

    tax_x, tax_w = x0 + _pt(360), sum(widths) - _pt(360)
    draw.rectangle((tax_x, y, tax_x + tax_w, y + desc_h), fill="white", outline="black", width=1)
    tax_headers = ["Impuesto", "Tipo", "Base", "Tipo Factor", "Tasa o Cuota", "Importe"]
    tax_values = ["IVA", "Traslado", _money(subtotal), "Tasa", f"{iva_porcentaje_num:.2f}%", _money(iva)]
    tw = tax_w // len(tax_headers)
    for i, header in enumerate(tax_headers):
        _center_text(draw, (tax_x + i * tw, y + _pt(4), tax_x + (i + 1) * tw, y + _pt(22)), header, SMALL_BOLD)
        _center_text(draw, (tax_x + i * tw, y + _pt(24), tax_x + (i + 1) * tw, y + desc_h), tax_values[i], SMALL)

    y += desc_h
    draw.rectangle((x0, y, x0 + _pt(120), y + _pt(24)), fill="#d9d9d9", outline="black", width=1)
    draw.rectangle((x0 + _pt(120), y, x0 + _pt(240), y + _pt(24)), fill="#d9d9d9", outline="black", width=1)
    _center_text(draw, (x0, y, x0 + _pt(120), y + _pt(24)), "Numero de pedimento", SMALL_BOLD)
    _center_text(draw, (x0 + _pt(120), y, x0 + _pt(240), y + _pt(24)), "Numero de cuenta predial", SMALL_BOLD)

    info_y = y + _pt(54)
    _draw_pair(draw, _pt(24), _pt(128), info_y, "Moneda:", "Peso Mexicano")
    _draw_pair(draw, _pt(24), _pt(128), info_y + _pt(24), "Forma de pago:", tipo_pago)
    _draw_pair(draw, _pt(24), _pt(128), info_y + _pt(48), "Metodo de pago:", "Pago en una sola exhibicion")
    if datos_venta.get("direccion_cliente"):
        _draw_pair(draw, _pt(24), _pt(128), info_y + _pt(72), "Direccion:", datos_venta.get("direccion_cliente"), _pt(220))
    if datos_venta.get("telefono_cliente"):
        _draw_pair(draw, _pt(24), _pt(128), info_y + _pt(96), "Telefono:", datos_venta.get("telefono_cliente"))
    if datos_venta.get("vendedor"):
        _draw_pair(draw, _pt(24), _pt(128), info_y + _pt(120), "Vendedor:", datos_venta.get("vendedor"))

    tx, vx = _pt(330), _pt(510)
    _draw_pair(draw, tx, vx, info_y, "Subtotal", _money(subtotal), _pt(80))
    _draw_pair(draw, tx, vx, info_y + _pt(24), f"Impuestos trasladados   IVA   {iva_porcentaje_num:.2f}%", _money(iva), _pt(80))
    _draw_pair(draw, tx, vx, info_y + _pt(48), "Total", _money(total), _pt(80))
    _draw_pair(draw, tx, vx, info_y + _pt(72), "Monto recibido", _money(monto_recibido), _pt(80))
    _draw_pair(draw, tx, vx, info_y + _pt(96), "Cambio", _money(cambio), _pt(80))
    if saldo > 0:
        _draw_pair(draw, tx, vx, info_y + _pt(120), "Saldo pendiente", _money(saldo), _pt(80))

    seal_y = _pt(606)
    sello = f"{folio_fiscal}|{empresa_rfc}|{receptor}|{folio}|{fecha} {hora}|{total:.2f}"
    sello_1 = hashlib.sha256(sello.encode("utf-8")).hexdigest().upper()
    sello_2 = hashlib.sha512(sello.encode("utf-8")).hexdigest().upper()
    _draw_text(draw, (_pt(24), seal_y), "Sello digital del comprobante:", BOLD)
    _draw_text(draw, (_pt(24), seal_y + _pt(18)), (sello_1 + "||" + sello_2)[:150] + "...", SMALL, width=_pt(560), line_gap=2)
    _draw_text(draw, (_pt(24), seal_y + _pt(44)), "Sello digital administrativo:", BOLD)
    _draw_text(draw, (_pt(24), seal_y + _pt(62)), (sello_2 + "||" + sello_1)[:150] + "...", SMALL, width=_pt(560), line_gap=2)

    qr_data = f"Folio={folio}&Cliente={receptor}&Total={total:.2f}&Fecha={fecha}"
    _draw_control_code(draw, _pt(28), _pt(684), _pt(74), qr_data)
    _draw_text(draw, (_pt(122), _pt(684)), "Cadena original del comprobante:", BOLD)
    _draw_text(draw, (_pt(122), _pt(706)), f"||{folio_fiscal}|{fecha} {hora}|{empresa_rfc}|{receptor}|{total:.2f}||", SMALL, width=_pt(455), line_gap=2)
    _draw_pair(draw, _pt(122), _pt(260), _pt(736), "RFC proveedor:", empresa_rfc, _pt(100))
    _draw_pair(draw, _pt(122), _pt(260), _pt(758), "Serie certificado:", certificado, _pt(100))
    _draw_pair(draw, _pt(390), _pt(505), _pt(736), "Certificacion:", f"{fecha} {hora}", _pt(88))

    footer = "Este documento es una representacion impresa de una venta"
    fw = draw.textlength(footer, font=BOLD)
    draw.text(((W - fw) / 2, _pt(778)), footer, font=BOLD, fill="black")
    draw.text((_pt(535), _pt(778)), "Pagina 1 de 1", font=FONT, fill="black")

    rgb = img.convert("RGB")
    rgb.save(pdf_path, "PDF", resolution=150.0)

    if abrir:
        try:
            os.startfile(pdf_path)
        except Exception:
            pass
        messagebox.showinfo("Factura generada", f"Se genero el PDF en:\n{pdf_path}")
    return pdf_path
