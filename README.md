# LionCircuits — Fabrication Export (KiCad plugin)

A KiCad PCB Editor action plugin. Click one toolbar button, get:

- **Gerbers** (RS-274X) + **Excellon drill files** — matches LionCircuits' fab-ready naming
  standard (`TOP.GTL`, `BOTTOM.GBL`, `TOPMASK.GTS`, `BOTTOMMASK.GBS`, `TOPSILK.GTO`,
  `BOTTOMSILK.GBO`, `TOPPASTE.GTP`, `OUTLINE.GKO`, `DRILL.DRL`/`NPTH.DRL`/`SLOT.DRL`,
  `DRLMAP.GBR`/`DRLDRAW.GBR`)
- **BOM for assembly** (CSV) — per-reference traceable, grouped by value/footprint/fields,
  with headers matching LionCircuits' assembly-BOM upload field names (Item Number,
  Designator, Unit Quantity, Description, Manufacturer Part Number, Footprint, Value)
- **BOM for components** (XLSX) — a supplier quote-request sheet (Project/Currency/
  Number of Boards, MPN/Description/Required Qty/Order Qty/Unit Price/Total Price/Alternates,
  Subtotal/GST/Total), currency selectable (INR/USD)
- **Component position / CPL file** (CSV)
- **IPC-D-356 netlist** — bare-board electrical test data
- **Interactive BOM** (HTML) — uses [InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom)
  if it's installed, otherwise falls back to a sortable/searchable HTML table built from the same BOM data
- Optional **zip** of the Gerbers + drill folder, ready to upload to a fab house

## Install

### Via KiCad's Plugin and Content Manager (recommended)

Search "LionCircuits" in **Tools → Plugin and Content Manager** and click Install.
(Once this package is listed in KiCad's official repository — see `metadata.json` for status.)

### Manual install

1. Copy the `plugins/lioncircuits` folder into your KiCad plugins directory:
   - Windows: `%APPDATA%\kicad\<version>\scripting\plugins\`
   - macOS: `~/Documents/KiCad/<version>/scripting/plugins/`
   - Linux: `~/.local/share/kicad/<version>/scripting/plugins/`
2. In KiCad's **PCB Editor**, go to **Tools → External Plugins → Refresh Plugins**
   (or restart the PCB Editor).
3. A new toolbar button "LionCircuits — Fabrication Export" appears. Click it.

## Usage

Click the toolbar button, pick which outputs you want, a currency and board count for the
components BOM, and an output folder, then hit **Generate**. Everything lands in
`<project>/lioncircuits_output/` by default (configurable in the dialog).

## Notes on the interactive BOM

Rendering a fully interactive, click-to-highlight PCB view (the thing InteractiveHtmlBom is famous
for) means re-drawing footprint outlines, silkscreen, and board outline as an SVG/HTML board — a
project in its own right. Rather than half-reimplementing that, LionCircuits invokes
InteractiveHtmlBom's own CLI if it's installed (via PATH or KiCad's plugin directories), and
otherwise falls back to a clean, dependency-free HTML BOM table with sorting, search, and a
per-row "placed" checkbox. If you want the full board-view experience every time, install
InteractiveHtmlBom alongside LionCircuits (via the PCM, searching "InteractiveHtmlBom").

## Files

```
metadata.json               # KiCad Plugin & Content Manager packaging metadata
resources/icon.png           # 64x64 PCM package icon
plugins/lioncircuits/
  __init__.py                  # registers the plugin with pcbnew
  plugin_action.py              # ActionPlugin: toolbar entry point, dialog, summary
  dialog.py                      # wx dialog: choose outputs, currency/board count, destination folder
  process.py                     # orchestrates the exporters below
  resources/icon.png              # 24x24 toolbar icon
  exporters/
    gerbers.py                     # Gerber + Excellon drill export (pcbnew PLOT_CONTROLLER / EXCELLON_WRITER)
    bom.py                          # BOM for assembly (CSV) + BOM for components (XLSX/CSV)
    position.py                     # Component position / CPL file
    ibom.py                          # Interactive BOM (delegates to InteractiveHtmlBom, or fallback HTML)
    netlist.py                        # IPC-D-356 netlist export
    archive.py                         # Zips gerbers+drill for fab upload
```

## Requirements

- KiCad 7, 8, or 9 (uses the `pcbnew` Python API and `wx` for the dialog, both bundled with KiCad)
- Optional: `openpyxl`, for the styled XLSX components BOM (falls back to CSV if not installed)
- Optional: [InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom) plugin, for
  the full interactive board-view BOM instead of the fallback table

## License

MIT — see `LICENSE`.
