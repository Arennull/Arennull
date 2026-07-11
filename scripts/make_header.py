#!/usr/bin/env python3
"""
make_header.py — render header.svg, the designed banner atop the profile.

A terminal-window card with a big display name, a tagline that types itself in,
a blinking cursor, and an accent underline that draws in. Pure SVG + SMIL (no JS)
so it animates inside a GitHub README <img>. STATIC=1 renders the final frame.

Usage:
    python scripts/make_header.py [header.svg]
    STATIC=1 python scripts/make_header.py ...
"""
import os
import sys

# ============================= CONFIG (edit me) =============================
W        = 880
H        = 172
NAME     = "ALEJANDRO"
TAGLINE  = "AI Builder · Full-Stack Dev · DAM Student"
LABEL    = "ALEJANDRO.NODE // ~/profile"
FG       = "#f2f2f4"      # ink
MUTED    = "#8a8a92"      # secondary
LINE     = "#26262c"      # borders
BG       = "#0b0b0e"
ACCENT   = "#7ee7c7"      # single restrained accent (mint/teal)
FONT     = "ui-monospace,'Cascadia Mono','Fira Code',Consolas,monospace"
NAME_SIZE = 56
PAD      = 28
# ===========================================================================

STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    cx = W / 2
    name_y = 92
    tag_y = 138
    # underline geometry (centered under the name)
    ul_w = 150
    ul_y = name_y + 20
    ul_x1, ul_x2 = cx - ul_w / 2, cx + ul_w / 2
    # tagline width (monospace advance ~0.60em + 1px letter-spacing)
    tag_w = int(len(TAGLINE) * (16 * 0.60 + 1))
    inner = W - 2 * PAD

    draw = "" if STATIC else (
        f'<animate attributeName="stroke-dashoffset" from="{ul_w}" to="0" '
        f'begin="0.2s" dur="0.9s" fill="freeze"/>'
    )
    # full-width left-to-right wipe — never clips the text on any viewer font
    reveal = "" if STATIC else (
        f'<animate attributeName="width" from="0" to="{inner}" begin="1.0s" '
        f'dur="1.1s" fill="freeze"/>'
    )
    tag_clip_w = inner if STATIC else 0
    cursor_x = int(cx + tag_w / 2 + 6)
    cursor = "" if STATIC else (
        f'<rect x="{cursor_x}" y="{tag_y - 12}" width="8" height="15" '
        f'fill="{ACCENT}" opacity="0"><set attributeName="opacity" to="1" begin="2.0s"/>'
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.4;0.5;0.9;1" '
        f'dur="1.05s" begin="2.1s" repeatCount="indefinite"/></rect>'
    )

    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="{esc(NAME)} — {esc(TAGLINE)}">',
        "  <defs>",
        '    <filter id="hglow" x="-20%" y="-40%" width="140%" height="180%">'
        '<feGaussianBlur stdDeviation="0.6"/></filter>',
        "  </defs>",
        "  <style>",
        f"    text{{font-family:{FONT}}}",
        "  </style>",
        f'  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" '
        f'fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>',
        # window chrome
        f'  <circle cx="{PAD}" cy="{PAD}" r="4.5" fill="{ACCENT}"/>',
        f'  <circle cx="{PAD+17}" cy="{PAD}" r="4.5" fill="{MUTED}"/>',
        f'  <circle cx="{PAD+34}" cy="{PAD}" r="4.5" fill="{LINE}"/>',
        f'  <text x="{W-PAD}" y="{PAD+5}" text-anchor="end" fill="{MUTED}" '
        f'font-size="12" letter-spacing="1.5">{esc(LABEL)}</text>',
        # name
        f'  <text x="{cx}" y="{name_y}" text-anchor="middle" fill="{FG}" '
        f'font-size="{NAME_SIZE}" font-weight="700" letter-spacing="10" '
        f'filter="url(#hglow)">{esc(NAME)}</text>',
        # accent underline (draws in)
        f'  <line x1="{ul_x1}" y1="{ul_y}" x2="{ul_x2}" y2="{ul_y}" stroke="{ACCENT}" '
        f'stroke-width="2.5" stroke-linecap="round" stroke-dasharray="{ul_w}" '
        f'stroke-dashoffset="{0 if STATIC else ul_w}">{draw}</line>',
        # tagline (types in), clipped
        f'  <clipPath id="tagclip"><rect x="{PAD}" y="{tag_y-16}" '
        f'width="{tag_clip_w}" height="22">{reveal}</rect></clipPath>',
        f'  <text x="{cx}" y="{tag_y}" text-anchor="middle" fill="{MUTED}" '
        f'font-size="16" letter-spacing="1" clip-path="url(#tagclip)">{esc(TAGLINE)}</text>',
        f'  {cursor}',
        "</svg>",
    ])


def main() -> None:
    dst = sys.argv[1] if len(sys.argv) > 1 else "header.svg"
    with open(dst, "w") as fh:
        fh.write(build())
    print(f"[header] wrote {dst}  ({W}x{H}, {'static' if STATIC else 'animated'})")


if __name__ == "__main__":
    main()
