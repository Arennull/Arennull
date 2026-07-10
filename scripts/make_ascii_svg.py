#!/usr/bin/env python3
"""
make_ascii_svg.py — turn source-prepped.png into avi-ascii.svg.

A clean MONOCHROME ASCII portrait that "types itself in like a terminal":
the canvas is blank at t=0 and each row is revealed left-to-right in a
staggered cascade, with a caret riding the reveal edge. Uses SMIL only (no
JavaScript), so it animates inside a GitHub README <img>.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [avi-ascii.svg]
    STATIC=1 python scripts/make_ascii_svg.py ...   # render the final frame only

Install deps once:  pip install -r requirements-local.txt
"""
import os
import sys

import numpy as np
from PIL import Image

# ============================= CONFIG (edit me) =============================
COLS        = 92            # portrait width in characters (raise for more detail)
CONTRAST    = 1.18          # >1 pushes darks darker / lights lighter
GAMMA       = 0.90          # <1 brightens midtones so the face isn't muddy
WHITE_FLOOR = 0.06          # luminance <= this renders BLANK (clears dark background)
RAMP        = " .:-=+*oO#@" # dark pixel -> light pixel (last char = brightest)
FONT_SIZE   = 12            # px; also the line height
CHAR_ASPECT = 0.60          # monospace advance / line-height (for undistorted aspect)
FG          = "#e8e8ea"     # single ink color (monochrome)
BG          = "#0b0b0e"     # backdrop
PAD         = 18            # px padding around the art
PER_ROW     = 0.055         # seconds between each row starting to type
ROW_DUR     = 0.75          # seconds a single row takes to reveal
BRAILLE_DOT = 3            # px per Braille dot when input is Braille art
# ===========================================================================

STATIC = os.environ.get("STATIC") == "1"


def load_gray(path: str) -> np.ndarray:
    img = Image.open(path).convert("L")
    return np.asarray(img, dtype=np.float32)


def load_art_txt(path: str):
    """Use a ready-made ASCII/Braille art file verbatim (skip the photo pipeline).

    Braille blanks (U+2800) are real glyphs, not spaces, so only trailing blank
    padding is trimmed; internal alignment is preserved.
    """
    with open(path, encoding="utf-8") as fh:
        raw = [ln.rstrip("\n").rstrip("⠀ ") for ln in fh]
    # drop leading/trailing empty rows
    while raw and not raw[0].strip("⠀ "):
        raw.pop(0)
    while raw and not raw[-1].strip("⠀ "):
        raw.pop()
    return raw


def to_ascii_rows(gray: np.ndarray):
    h, w = gray.shape
    rows = max(1, int(round(COLS * (h / w) * CHAR_ASPECT)))
    small = np.asarray(
        Image.fromarray(gray.astype(np.uint8)).resize((COLS, rows), Image.LANCZOS),
        dtype=np.float32,
    ) / 255.0

    # tone curve
    small = np.power(np.clip(small, 0, 1), GAMMA)
    small = np.clip((small - 0.5) * CONTRAST + 0.5, 0, 1)

    n = len(RAMP) - 1
    lines = []
    for r in range(rows):
        chars = []
        for c in range(COLS):
            l = small[r, c]
            if l <= WHITE_FLOOR:
                chars.append(" ")
            else:
                chars.append(RAMP[int(round(l * n))])
        lines.append("".join(chars).rstrip())
    return lines


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- Braille art -> crisp dot-matrix (font-independent) --------------------
# Unicode Braille bit -> (dot_col, dot_row) within a 2x4 cell.
_BRAILLE_DOTS = {
    0x01: (0, 0), 0x02: (0, 1), 0x04: (0, 2), 0x40: (0, 3),
    0x08: (1, 0), 0x10: (1, 1), 0x20: (1, 2), 0x80: (1, 3),
}


def is_braille(lines) -> bool:
    total = filled = 0
    for ln in lines:
        for ch in ln:
            if ch.strip():
                total += 1
                if 0x2800 <= ord(ch) <= 0x28FF:
                    filled += 1
    return total > 0 and filled / total > 0.6


def _runs(row_bits):
    """Yield (start, length) runs of True in a boolean list."""
    x = 0
    n = len(row_bits)
    while x < n:
        if row_bits[x]:
            s = x
            while x < n and row_bits[x]:
                x += 1
            yield s, x - s
        else:
            x += 1


def build_braille_svg(lines) -> str:
    d = BRAILLE_DOT
    max_len = max((len(l) for l in lines), default=0)
    wdots = max_len * 2
    width = 2 * PAD + wdots * d
    height = 2 * PAD + len(lines) * 4 * d + 4 * d  # +band for cursor

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="ASCII portrait">',
        f'  <rect width="{width}" height="{height}" fill="{BG}"/>',
        "  <defs>",
    ]

    # per-text-line reveal windows (typing cascade)
    for i in range(len(lines)):
        y = PAD + i * 4 * d
        full_w = width - 2 * PAD
        start_w = full_w if STATIC else 0
        rect = f'      <rect x="{PAD}" y="{y}" width="{start_w}" height="{4 * d}">'
        if not STATIC:
            rect += (f'<animate attributeName="width" from="0" to="{full_w}" '
                     f'begin="{i * PER_ROW:.3f}s" dur="{ROW_DUR:.3f}s" fill="freeze"/>')
        out.append(f'    <clipPath id="clip{i}">')
        out.append(rect + "</rect>")
        out.append("    </clipPath>")
    out.append("  </defs>")

    # emit each line's set dots as run-length-merged rects, clipped by its window
    for i, line in enumerate(lines):
        # 4 dot-rows x wdots grid for this text line
        grid = [[False] * wdots for _ in range(4)]
        for c, ch in enumerate(line):
            o = ord(ch)
            if not (0x2800 <= o <= 0x28FF):
                continue
            bits = o - 0x2800
            for bit, (dc, dr) in _BRAILLE_DOTS.items():
                if bits & bit:
                    grid[dr][2 * c + dc] = True
        rects = []
        for dr in range(4):
            y = PAD + (i * 4 + dr) * d
            for start, length in _runs(grid[dr]):
                rects.append(
                    f'<rect x="{PAD + start * d}" y="{y}" '
                    f'width="{length * d}" height="{d}"/>'
                )
        if rects:
            out.append(f'  <g fill="{FG}" clip-path="url(#clip{i})">{"".join(rects)}</g>')

    # resting blinking cursor
    total = (len(lines) * PER_ROW) + ROW_DUR
    cy = PAD + len(lines) * 4 * d
    op = "1" if STATIC else "0"
    show = "" if STATIC else f'<set attributeName="opacity" to="1" begin="{total:.3f}s"/>'
    blink = "" if STATIC else (
        f'<animate attributeName="opacity" values="1;1;0;0;1" '
        f'keyTimes="0;0.4;0.5;0.9;1" dur="1.1s" begin="{total:.3f}s" '
        f'repeatCount="indefinite"/>'
    )
    out.append(
        f'  <rect x="{PAD}" y="{cy}" width="{2 * d}" height="{4 * d}" '
        f'fill="{FG}" opacity="{op}">{show}{blink}</rect>'
    )
    out.append("</svg>")
    return "\n".join(out)


def build_svg(lines) -> str:
    char_w = FONT_SIZE * CHAR_ASPECT
    max_len = max((len(l) for l in lines), default=0)
    width = int(round(2 * PAD + max_len * char_w))
    height = int(round(2 * PAD + len(lines) * FONT_SIZE))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="ASCII portrait">',
        "  <style>",
        "    text{font-family:ui-monospace,'DejaVu Sans Mono','Cascadia Mono',"
        "'Fira Code',Consolas,'Segoe UI Symbol',monospace;"
        f"white-space:pre;fill:{FG};font-size:{FONT_SIZE}px}}",
        f"    .caret{{fill:{FG}}}",
        "  </style>",
        f'  <rect width="{width}" height="{height}" fill="{BG}"/>',
        "  <defs>",
    ]

    # per-row clip paths (the reveal windows)
    for i, line in enumerate(lines):
        y = PAD + i * FONT_SIZE
        full_w = max(1, int(round(len(line) * char_w))) if line else 1
        start_w = full_w if STATIC else 0
        out.append(f'    <clipPath id="clip{i}">')
        rect = (f'      <rect x="{PAD}" y="{y}" width="{start_w}" '
                f'height="{FONT_SIZE + 2}">')
        if not STATIC and line:
            rect += (f'<animate attributeName="width" from="0" to="{full_w}" '
                     f'begin="{i * PER_ROW:.3f}s" dur="{ROW_DUR:.3f}s" '
                     f'calcMode="linear" fill="freeze"/>')
        out.append(rect + "</rect>")
        out.append("    </clipPath>")
    out.append("  </defs>")

    # rows of text, each clipped by its reveal window
    baseline = PAD + FONT_SIZE - 2
    for i, line in enumerate(lines):
        y = baseline + i * FONT_SIZE
        content = esc(line) if line else ""
        out.append(
            f'  <text x="{PAD}" y="{y}" clip-path="url(#clip{i})" '
            f'xml:space="preserve">{content}</text>'
        )

    # caret that rides each row's reveal edge (animated build only)
    if not STATIC:
        for i, line in enumerate(lines):
            if not line:
                continue
            y = PAD + i * FONT_SIZE
            end_x = PAD + int(round(len(line) * char_w))
            begin = i * PER_ROW
            out.append(
                f'  <rect class="caret" x="{PAD}" y="{y}" '
                f'width="{max(2, int(char_w))}" height="{FONT_SIZE}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{begin:.3f}s"/>'
                f'<animate attributeName="x" from="{PAD}" to="{end_x}" '
                f'begin="{begin:.3f}s" dur="{ROW_DUR:.3f}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/>'
                f'</rect>'
            )

    # resting blinking cursor once typing is done
    total = (len(lines) * PER_ROW) + ROW_DUR
    cy = PAD + len(lines) * FONT_SIZE
    cx = PAD
    blink = "" if STATIC else (
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.4;0.5;0.9;1" '
        f'dur="1.1s" begin="{total:.3f}s" repeatCount="indefinite"/>'
    )
    cursor_op = "1" if STATIC else "0"
    show = "" if STATIC else f'<set attributeName="opacity" to="1" begin="{total:.3f}s"/>'
    out.append(
        f'  <rect class="caret" x="{cx}" y="{cy}" width="{max(2, int(char_w))}" '
        f'height="{FONT_SIZE}" opacity="{cursor_op}">{show}{blink}</rect>'
    )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    dst = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"
    if not os.path.exists(src):
        sys.exit(f"input not found: {src} (run prep_photo.py first, or pass a .txt art file)")
    if src.lower().endswith(".txt"):
        lines = load_art_txt(src)          # ready-made ASCII/Braille art
        svg = build_braille_svg(lines) if is_braille(lines) else build_svg(lines)
    else:
        lines = to_ascii_rows(load_gray(src))  # generate from a prepped photo
        svg = build_svg(lines)
    with open(dst, "w") as fh:
        fh.write(svg)
    mode = "static" if STATIC else "animated"
    print(f"[ascii] wrote {dst}  ({len(lines)} rows x {COLS} cols, {mode})")


if __name__ == "__main__":
    main()
