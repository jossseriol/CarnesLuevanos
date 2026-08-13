import qrcode
import sys
import os


def resource_path(relative_path):
 
    try:
  
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def generar_qr_producto(producto):
    """Genera un codigo QR con la informacion de un producto y lo guarda en media/qr."""
    if not producto:
        raise ValueError("Se necesita la informacion del producto para generar el QR.")

    # Crea la información del producto en formato de cadena
    info_producto = f"""
    Nombre: {producto.get('nombre') or producto.get('articulo', '')}
    Precio: {producto.get('precio', '')}
    Descripcion: {producto.get('descripcion', '')}
    """

    # Crea el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(info_producto)
    qr.make(fit=True)

    # Define la ruta a la carpeta media/qr
    ruta_qr = os.path.join("media", "qr")

    # Asegúrate de que la carpeta media/qr existe. Si no, créala.
    os.makedirs(ruta_qr, exist_ok=True)

    # Define el nombre del archivo
    nombre = str(producto.get('nombre') or producto.get('articulo') or 'producto').strip().replace(os.sep, '_')
    nombre_archivo = f"qr_{nombre}.png"

    # Define la ruta completa al archivo
    ruta_completa = os.path.join(ruta_qr, nombre_archivo)

    # Guarda el código QR en el archivo PNG
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(ruta_completa)

    print(f"Codigo QR guardado en: {ruta_completa}")

