#!/usr/bin/env python3
"""
make_info_card.py — render info-card.svg, the monochrome panel beside the portrait.

Lists experience / stack / highlights (NOT GitHub stats — the heatmap covers
those). Keep H equal to the portrait's displayed height so the README table's
two columns line up. Uses inline-CSS keyframes (no JS) for a subtle line-by-line
fade-in; STATIC=1 renders the final frame.

Usage:
    python scripts/make_info_card.py [info-card.svg]
    STATIC=1 python scripts/make_info_card.py ...
"""
import os
import sys

# ============================= CONFIG (edit me) =============================
W          = 490
H          = 477  # set to match the portrait's displayed height
HOST       = "alejandro@arennull:~$"
TITLE      = "// OPERATOR"
ROWS = [
    ("ROLE",  "DAM student · building in public"),
    ("STACK", "TypeScript · Python · Node"),
    ("SHIP",  "Railway · Vercel · Cloudflare"),
    ("AI",    "OpenAI · Hugging Face · eval"),
    ("CODE",  "React · Prisma · clean refactors"),
    ("FOCUS", "AI · automation · data · APIs"),
    ("MODE",  "trace → ship → refactor → sandbox"),
]
FG         = "#e8e8ea"                  # ink
MUTED      = "#8a8a92"                  # labels / secondary
LINE       = "#26262c"                  # borders / dividers
ACCENT     = "#7ee7c7"                  # single accent (matches header/heatmap)
BG         = "#0b0b0e"
FONT       = "ui-monospace,'Cascadia Mono','Fira Code',Consolas,monospace"
TITLE_SIZE = 15
ROW_SIZE   = 15
LABEL_COL  = 92                         # px width reserved for the label column
PAD        = 26
ROW_STEP   = 0.10                       # seconds between each row fading in
# ===========================================================================

STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    header_y = PAD + TITLE_SIZE
    dot_y = PAD + 2
    # vertical layout for the rows region (starts below the header divider)
    top = header_y + 48
    bottom = H - PAD
    n = len(ROWS)
    step = (bottom - top) / n
    row_anim = "" if STATIC else "opacity:0;animation:fin .5s ease-out forwards;"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Info card">',
        "  <style>",
        f"    text{{font-family:{FONT}}}",
        f"    .lbl{{fill:{MUTED};font-size:{ROW_SIZE}px;letter-spacing:1px}}",
        f"    .val{{fill:{FG};font-size:{ROW_SIZE}px}}",
        (f"    .row{{{row_anim}}}" if not STATIC else "    .row{}"),
        "    @keyframes fin{to{opacity:1}}",
        "  </style>",
        f'  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
        f'fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>',
        # window dots (accent + monochrome, matches header/heatmap)
        f'  <circle cx="{PAD}" cy="{dot_y+6}" r="4" fill="{ACCENT}"/>',
        f'  <circle cx="{PAD+16}" cy="{dot_y+6}" r="4" fill="{MUTED}"/>',
        f'  <circle cx="{PAD+32}" cy="{dot_y+6}" r="4" fill="{LINE}"/>',
        # title + host prompt
        f'  <text x="{W-PAD}" y="{header_y}" text-anchor="end" class="lbl" '
        f'font-size="{TITLE_SIZE}">{esc(TITLE)}</text>',
        f'  <text x="{PAD}" y="{header_y+18}" class="val" '
        f'font-size="{TITLE_SIZE}" fill="{FG}">{esc(HOST)}</text>',
        f'  <line x1="{PAD}" y1="{header_y+30}" x2="{W-PAD}" y2="{header_y+30}" '
        f'stroke="{LINE}" stroke-width="1"/>',
    ]

    for i, (label, value) in enumerate(ROWS):
        cy = int(round(top + step * i + step / 2)) + ROW_SIZE // 3
        delay = "" if STATIC else f' style="animation-delay:{i*ROW_STEP:.2f}s"'
        out.append(f'  <g class="row"{delay}>')
        out.append(f'    <text x="{PAD}" y="{cy}" class="lbl">{esc(label)}</text>')
        out.append(
            f'    <text x="{PAD+LABEL_COL}" y="{cy}" class="val">{esc(value)}</text>'
        )
        out.append("  </g>")

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    dst = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    with open(dst, "w") as fh:
        fh.write(build())
    print(f"[info] wrote {dst}  ({W}x{H}, {'static' if STATIC else 'animated'})")


if __name__ == "__main__":
    main()
