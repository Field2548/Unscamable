import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as e:
    raise SystemExit("Pillow not installed. Run: python -m pip install pillow") from e


SIZES = [16, 32, 48, 128]
BG = (0, 0, 0, 0)


def load_base_image(icons_dir: Path) -> Image.Image | None:
    # Prefer a 128px base to downscale cleanly
    candidates = [
        icons_dir / "logo-home128.png",
        icons_dir / "logo1024.png",
        icons_dir / "logo512.png",
        icons_dir / "logo256.png",
        icons_dir / "logo128.png",
        icons_dir / "logo.png",
    ]
    for p in candidates:
        if p.exists():
            try:
                return Image.open(p).convert("RGBA")
            except Exception:
                continue
    # As a fallback, try existing icon128.png if present (user's previous icon)
    fallback = icons_dir / "icon128.png"
    if fallback.exists():
        return Image.open(fallback).convert("RGBA")
    return None


def center_square(im: Image.Image) -> Image.Image:
    w, h = im.size
    if w == h:
        return im
    # Crop to center square
    if w > h:
        left = (w - h) // 2
        box = (left, 0, left + h, h)
    else:
        top = (h - w) // 2
        box = (0, top, w, top + w)
    return im.crop(box)


def circular_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def create_icon_from_base(base: Image.Image, size: int) -> Image.Image:
    # Prepare square crop, then resize
    sq = center_square(base)
    if sq.size != (size, size):
        sq = sq.resize((size, size), Image.LANCZOS)

    # Apply circular alpha mask
    mask = circular_mask(size)
    out = Image.new("RGBA", (size, size), BG)
    out.paste(sq, (0, 0), mask)
    return out


def main():
    root = Path(__file__).resolve().parents[1]
    icons_dir = root / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    base = load_base_image(icons_dir)
    if base is None:
        raise SystemExit("No base logo found in icons/. Place something like logo-home128.png or logo*.png.")

    for s in SIZES:
        img = create_icon_from_base(base, s)
        out = icons_dir / f"icon{s}.png"
        img.save(out, format="PNG")
        print(f"Wrote {out}")

    # Also circularize existing logo files in-place if present
    candidates = [
        "logo-home16.png", "logo-home32.png", "logo-home48.png", "logo-home128.png",
        "logo-ext16.png", "logo-ext32.png",
    ]
    for name in candidates:
        p = icons_dir / name
        if not p.exists():
            continue
        try:
            im = Image.open(p).convert("RGBA")
            size = min(im.size)
            # For non-square, center-crop first then resize back to original dimensions to keep DPI
            sq = center_square(im)
            if sq.size != (size, size):
                sq = sq.resize((size, size), Image.LANCZOS)
            mask = circular_mask(size)
            circ = Image.new("RGBA", (size, size), BG)
            circ.paste(sq, (0, 0), mask)
            # Resize back to original file size if it differed
            if circ.size != im.size:
                circ = circ.resize(im.size, Image.LANCZOS)
            circ.save(p, format="PNG")
            print(f"Circularized {p}")
        except Exception as e:
            print(f"Skip {p}: {e}")


if __name__ == "__main__":
    main()
