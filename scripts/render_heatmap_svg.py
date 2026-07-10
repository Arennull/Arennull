#!/usr/bin/env python3
"""
render_heatmap_svg.py — contributions.json -> contrib-heatmap.svg.

A GitHub-style 53x7 grid of rounded cells that reveal cell-by-cell in a
diagonal wave, MONOCHROME (a single 5-shade grayscale ramp with a Less->More
legend), plus real streak stats. Uses inline-CSS @keyframes (no JS) so it
animates inside a GitHub README <img>. STATIC=1 renders the final frame.

Usage:
    python scripts/render_heatmap_svg.py [contributions.json] [contrib-heatmap.svg]
    STATIC=1 python scripts/render_heatmap_svg.py ...
"""
import json
import os
import sys
from datetime import date

# ============================= CONFIG (edit me) =============================
CELL       = 12
GAP        = 3
RADIUS     = 2
# Less -> More, one grayscale hue (index = data-level 0..4)
SHADES     = ["#17171b", "#38383f", "#5f5f68", "#9b9ba4", "#ececef"]
FG         = "#e8e8ea"
MUTED      = "#8a8a92"
BG         = "#0b0b0e"
FONT       = "ui-monospace,'Cascadia Mono','Fira Code',Consolas,monospace"
PAD        = 18
WAVE_DELAY = 0.014        # seconds per diagonal step
CELL_DUR   = 0.35         # seconds a single cell takes to pop in
FONT_SIZE  = 13
# ===========================================================================

STATIC = os.environ.get("STATIC") == "1"


def sunday_index(iso: str) -> int:
    # python weekday(): Mon=0..Sun=6  ->  Sun=0..Sat=6 (GitHub rows)
    return (date.fromisoformat(iso).weekday() + 1) % 7


def layout(days):
    cells, col = [], 0
    for i, d in enumerate(days):
        wd = sunday_index(d["date"])
        if i > 0 and wd == 0:
            col += 1
        cells.append((col, wd, d["level"]))
    weeks = (col + 1) if days else 1
    return cells, weeks


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(data) -> str:
    days = data.get("days", [])
    cells, weeks = layout(days)

    grid_w = weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = grid_w + 2 * PAD
    footer_h = 40
    height = grid_h + 2 * PAD + footer_h

    cur = data.get("current_streak", {}).get("length", 0)
    lon = data.get("longest_streak", {}).get("length", 0)
    tot = data.get("total", 0)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Contribution heatmap">',
        "  <style>",
        f"    text{{font-family:{FONT};font-size:{FONT_SIZE}px}}",
    ]
    if STATIC:
        out.append("    .c{}")
    else:
        out.append(
            "    .c{opacity:0;transform-box:fill-box;transform-origin:center;"
            f"animation:pop {CELL_DUR}s ease-out forwards}}"
        )
        out.append(
            "    @keyframes pop{from{opacity:0;transform:scale(.4)}"
            "to{opacity:1;transform:scale(1)}}"
        )
    out += [
        "  </style>",
        f'  <rect width="{width}" height="{height}" fill="{BG}"/>',
        f'  <g transform="translate({PAD},{PAD})">',
    ]

    for (col, row, level) in cells:
        x = col * (CELL + GAP)
        y = row * (CELL + GAP)
        fill = SHADES[max(0, min(level, len(SHADES) - 1))]
        style = "" if STATIC else f' style="animation-delay:{(col + row) * WAVE_DELAY:.3f}s"'
        out.append(
            f'    <rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{fill}"{style}/>'
        )
    out.append("  </g>")

    # footer: streak stats (left) + Less->More legend (right)
    fy = PAD + grid_h + 26
    stats = f"current {cur}d · longest {lon}d · total {tot}"
    out.append(f'  <text x="{PAD}" y="{fy}" fill="{FG}">{esc(stats)}</text>')

    sw = CELL - 2
    legend_w = 5 * (sw + 4) + 4
    lx = width - PAD - legend_w - 74
    out.append(f'  <text x="{lx}" y="{fy}" fill="{MUTED}" text-anchor="end">Less</text>')
    for i, shade in enumerate(SHADES):
        x = lx + 6 + i * (sw + 4)
        out.append(
            f'  <rect x="{x}" y="{fy - sw + 2}" width="{sw}" height="{sw}" '
            f'rx="{RADIUS}" fill="{shade}"/>'
        )
    mx = lx + 6 + 5 * (sw + 4) + 4
    out.append(f'  <text x="{mx}" y="{fy}" fill="{MUTED}">More</text>')

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "contributions.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    if not os.path.exists(src):
        sys.exit(f"input not found: {src} (run fetch_contributions.py first)")
    with open(src) as fh:
        data = json.load(fh)
    with open(dst, "w") as fh:
        fh.write(build(data))
    print(f"[heatmap] wrote {dst}  ({'static' if STATIC else 'animated'})")


if __name__ == "__main__":
    main()
