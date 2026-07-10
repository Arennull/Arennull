#!/usr/bin/env python3
"""
prep_photo.py — one-time local image prep for the ASCII portrait.

Removes the background (rembg / u2net) and boosts local contrast (CLAHE) so a
face reads as legible tones instead of a dark blob, then writes a clean
grayscale PNG that make_ascii_svg.py turns into the terminal portrait.

Usage:
    python scripts/prep_photo.py <input photo> source-prepped.png

Notes:
    * rembg downloads its model on first run. If that download is blocked
      (offline / proxied network), this script logs a notice and continues
      with CLAHE only — you still get a usable portrait, just without the
      cut-out. Set SKIP_BG=True below (or env SKIP_BG=1) to force that path.
    * Install deps once:  pip install -r requirements-local.txt
"""
import os
import sys

import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    sys.exit("opencv-python is required: pip install -r requirements-local.txt")

# ============================= CONFIG (edit me) =============================
OUT_SIZE   = (720, 720)     # working resolution before ASCII downsampling
BG_COLOR   = (11, 11, 14)   # solid background the cut-out is composited onto (R,G,B)
CLIP_LIMIT = 2.6            # CLAHE contrast strength — raise if the face is flat/dark
TILE_GRID  = (8, 8)         # CLAHE local region grid — smaller = more local contrast
GAMMA      = 1.0            # >1 darkens midtones, <1 brightens them
SKIP_BG    = False          # True -> skip rembg entirely (CLAHE only)
# ===========================================================================

SKIP_BG = SKIP_BG or os.environ.get("SKIP_BG") == "1"


def load_rgb(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def remove_background(img: Image.Image) -> Image.Image:
    """Return an RGB image with the subject composited on BG_COLOR.

    Falls back to the original image if rembg is unavailable or its model
    cannot be fetched.
    """
    if SKIP_BG:
        print("[prep] SKIP_BG set — skipping background removal.")
        return img
    try:
        from rembg import remove
        cut = remove(img)  # RGBA with alpha
        cut = cut.convert("RGBA")
        bg = Image.new("RGBA", cut.size, BG_COLOR + (255,))
        return Image.alpha_composite(bg, cut).convert("RGB")
    except Exception as exc:  # noqa: BLE001 - any failure -> graceful fallback
        print(f"[prep] background removal unavailable ({exc}); using CLAHE only.")
        return img


def to_clahe_gray(img: Image.Image) -> np.ndarray:
    gray = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=TILE_GRID)
    out = clahe.apply(gray)
    if GAMMA != 1.0:
        norm = (out / 255.0) ** GAMMA
        out = np.clip(norm * 255.0, 0, 255).astype(np.uint8)
    return out


def fit_letterbox(gray: np.ndarray, size) -> Image.Image:
    """Contain-fit onto a BG_COLOR canvas so the aspect ratio is preserved."""
    g = Image.fromarray(gray).convert("L")
    g.thumbnail(size, Image.LANCZOS)
    bg_lum = int(round(0.299 * BG_COLOR[0] + 0.587 * BG_COLOR[1] + 0.114 * BG_COLOR[2]))
    canvas = Image.new("L", size, bg_lum)
    canvas.paste(g, ((size[0] - g.width) // 2, (size[1] - g.height) // 2))
    return canvas


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python scripts/prep_photo.py <input photo> source-prepped.png")
    src, dst = sys.argv[1], sys.argv[2]
    if not os.path.exists(src):
        sys.exit(f"input not found: {src}")

    img = load_rgb(src)
    img = remove_background(img)
    gray = to_clahe_gray(img)
    out = fit_letterbox(gray, OUT_SIZE)
    out.save(dst)
    print(f"[prep] wrote {dst}  ({out.width}x{out.height}, grayscale)")


if __name__ == "__main__":
    main()
