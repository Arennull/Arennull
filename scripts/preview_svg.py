#!/usr/bin/env python3
"""
preview_svg.py — rasterize an SVG to a throwaway PNG with headless Chromium.

Local dev helper only (never committed output). Lets you eyeball an artifact
before it ships. Animated SVGs are captured after WAIT_MS so you see the
settled/late frame; render the source with STATIC=1 to capture the final frame
deterministically.

Usage:
    python scripts/preview_svg.py <in.svg> <out.png> [css_width_px]
"""
import os
import sys

from playwright.sync_api import sync_playwright

# ============================= CONFIG (edit me) =============================
WAIT_MS   = 4500          # let animations play before the screenshot
BG        = "#0b0b0e"     # page backdrop behind the SVG
DENSITY   = 2             # device scale factor (crisper preview)
DEFAULT_W = 0             # 0 = use the SVG's own width; else force this CSS width
# ===========================================================================

# Prefer the environment's pre-installed Chromium.
_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
]
EXECUTABLE = next((p for p in _CANDIDATES if os.path.exists(p)), None)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: python scripts/preview_svg.py <in.svg> <out.png> [css_width_px]")
    svg_path = os.path.abspath(sys.argv[1])
    out_path = os.path.abspath(sys.argv[2])
    force_w = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_W

    with open(svg_path) as fh:
        svg = fh.read()

    width_css = f"width:{force_w}px;height:auto;" if force_w else ""
    html = (
        f'<!doctype html><meta charset="utf-8">'
        f'<body style="margin:0;background:{BG};display:inline-block">'
        f'<div style="display:inline-block;{width_css}">{svg}</div>'
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EXECUTABLE,
            args=["--no-sandbox", "--force-color-profile=srgb"],
        )
        page = browser.new_page(device_scale_factor=DENSITY)
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(WAIT_MS)
        el = page.query_selector("div")
        el.screenshot(path=out_path)
        browser.close()
    print(f"[preview] wrote {out_path}")


if __name__ == "__main__":
    main()
