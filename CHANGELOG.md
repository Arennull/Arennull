# `// CHANGELOG_TX_LOG`

> Bitácora de revisiones del perfil. Docs mínimas. Stay chrome.
> Log of profile README revisions. Minimal docs by design.

## REV 4.0 — 2026-07-10

- `NEW` Rediseño completo a estética **monocroma** (sin neón, sin glitch).
- `ADD` `scripts/` — toolkit que genera el perfil: retrato ASCII/Braille que se
  escribe solo (`make_ascii_svg.py`, `prep_photo.py`), panel de info
  (`make_info_card.py`) y heatmap de contribuciones (`fetch_contributions.py`,
  `render_heatmap_svg.py`) con reveal celda a celda. SVG puro, sin JS.
- `ADD` `.github/workflows/update-profile-art.yml` — re-scrapea contribuciones y
  re-renderiza el heatmap a diario, sin auth.
- `DEL` workflows `snake.yml` + `metrics.yml`; assets neón movidos a `assets/archive/`.

## REV 3.1 — 2026-05-19

- `ADD` `assets/banner-v3.svg` — banner animado con glitch RGB-split, parallax de skyline y typewriter.
- `ADD` `assets/boot-sequence.svg` — widget BIOS_ARENNULL sustituyendo el bloque `STATUS online`.
- `ADD` `assets/marquee.svg` — tira de mantras en loop bajo el banner.
- `ADD` `.github/workflows/metrics.yml` — auto-genera `assets/metrics.svg` cada lunes vía `lowlighter/metrics`.
- `ADD` Card WakaTime (lenguajes top de la semana) en `// GITHUB_TELEMETRY`.
- `ADD` `CHANGELOG.md` (este archivo).

## REV 3.0 — 2026-05-19

- `UPD` `assets/status-panel.svg` — scanline animada, LEDs pulsantes desfasados, barra de actividad y nuevo panel `SEC_SANDBOX`.
- `UPD` `assets/neon-divider.svg` — partículas viajando por las trazas con `animateMotion`.
- `ADD` `assets/loadout.svg` — 4 slots (`LANG / SHIP / INTEL / EDGE`) con el stack actual.
- `ADD` `assets/now-running.svg` — terminal `ps -ef` con los labs activos.
- `UPD` `README.md` — telemetría con 4 cards + fila de trofeos + tabla de labs + Node.js / GitHub Actions en stack.

## REV 2.1 — baseline

- Versión publicada previa: banner JPG, `status-panel` y `neon-divider` estáticos, snake action diaria.
