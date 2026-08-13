from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SOURCE = PUBLIC / "logo-luevanos.png"
NAVY = (7, 17, 27, 255)


def make_icon(filename: str, size: int, logo_ratio: float) -> None:
    source = Image.open(SOURCE).convert("RGBA")
    target_logo_size = round(size * logo_ratio)
    source = source.resize((target_logo_size, target_logo_size), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (size, size), NAVY)
    x = (size - source.width) // 2
    y = (size - source.height) // 2
    mask = Image.new("L", (target_logo_size, target_logo_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, target_logo_size - 1, target_logo_size - 1), fill=255)
    canvas.paste(source, (x, y), mask)
    ring_width = max(3, round(size * 0.018))
    inset = max(1, ring_width // 2)
    ImageDraw.Draw(canvas).ellipse(
        (x - inset, y - inset, x + target_logo_size + inset, y + target_logo_size + inset),
        outline=(231, 161, 42, 255),
        width=ring_width,
    )
    canvas.convert("RGB").save(PUBLIC / filename, "PNG", optimize=True)


make_icon("apple-touch-icon.png", 180, 0.84)
make_icon("icon-192.png", 192, 0.84)
make_icon("icon-512.png", 512, 0.84)
make_icon("icon-maskable-512.png", 512, 0.68)
