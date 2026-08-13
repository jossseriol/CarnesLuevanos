from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
source = Image.open(ROOT / "public" / "jelox.png").convert("RGBA")

# La marca X ocupa el centro del arte original. Se recorta antes de retirar
# el fondo para conservar sus facetas y su resplandor azul originales.
crop = source.crop((260, 210, 760, 700))
shape = Image.new("L", crop.size, 0)
draw = ImageDraw.Draw(shape)
pieces = (
    ((92, 126), (183, 128), (231, 183), (187, 238)),
    ((334, 51), (438, 51), (379, 153), (279, 153)),
    ((238, 169), (358, 169), (250, 312), (134, 316)),
    ((134, 326), (225, 328), (145, 404), (55, 404)),
    ((289, 251), (326, 286), (278, 287)),
    ((284, 302), (337, 288), (408, 374), (308, 374)),
)
for polygon in pieces:
    draw.polygon(polygon, fill=255)

glow = shape.filter(ImageFilter.GaussianBlur(13))
alpha = ImageChops.lighter(shape, glow.point(lambda value: round(value * 0.7)))
crop.putalpha(alpha)

bounds = crop.getbbox()
if bounds:
    crop = crop.crop(bounds)

crop = ImageEnhance.Color(crop).enhance(1.18)
crop.save(ROOT / "public" / "jelox-x.png", "PNG", optimize=True)
