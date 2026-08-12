"""Interactive HTML BOM export.

Real interactive-board iBOM rendering (clickable footprint outlines on a
rendered PCB) is provided by the third-party InteractiveHtmlBom plugin
(https://github.com/openscopeproject/InteractiveHtmlBom, MIT licensed).
We don't vendor its source into LionCircuits — it's a sizeable multi-file
Python + JS project and bundling it reliably isn't practical here — but
once it's installed (via KiCad's Plugin and Content Manager, or pip, or
a manual copy) we invoke it directly and use its real pictorial output.
If it isn't installed, we fall back to a clean, dependency-free HTML
table (sortable, with a DNP/placed checkbox per row) built from the same
BOM data LionCircuits already generated — not a full board render, but
genuinely useful and it never leaves the user with nothing.

Invocation uses InteractiveHtmlBom's documented, supported entry point —
its `generate_interactive_bom.py` CLI script (or the `generate_interactive_bom`
console command if it was installed via pip) — rather than importing its
internal modules. That CLI contract (`--dest-dir`, `--no-browser`, a
board-file argument) is what the project's own docs/wiki describe as the
stable way to drive it programmatically; its internal Python API isn't
meant to be called as a library and has no stable signature across
versions, which is why the previous version of this function (guessing
at `generate_bom`/`main` on an imported module) never actually worked.
"""

import glob
import html
import json
import os
import shutil
import subprocess
import sys


def export_ibom(board, out_dir, bom_rows, board_path, filename="ibom.html"):
    """Try InteractiveHtmlBom first; fall back to a static HTML table.

    Returns (path_to_html_file, used_real_ibom: bool).
    """
    real_path = _try_real_ibom(board_path, out_dir)
    if real_path:
        return real_path, True

    path = os.path.join(out_dir, filename)
    _write_fallback_html(bom_rows, path)
    return path, False


def _candidate_plugin_root_patterns():
    """Glob patterns for where KiCad's PCM (or a manual install) puts
    third-party plugins, across OS and KiCad version. `*` stands in for
    the version folder (8.0, 9.0, ...) since we don't know it up front.
    """
    home = os.path.expanduser("~")
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        return [
            os.path.join(home, "Documents", "KiCad", "*", "3rdparty", "plugins"),
            os.path.join(appdata, "kicad", "*", "3rdparty", "plugins"),
            os.path.join(appdata, "kicad", "*", "scripting", "plugins"),
        ]
    if sys.platform == "darwin":
        return [
            os.path.join(home, "Documents", "KiCad", "*", "3rdparty", "plugins"),
            os.path.join(home, "Library", "Application Support", "kicad", "*", "3rdparty", "plugins"),
            os.path.join(home, "Library", "Preferences", "kicad", "*", "scripting", "plugins"),
        ]
    return [
        os.path.join(home, "Documents", "KiCad", "*", "3rdparty", "plugins"),
        os.path.join(home, ".local", "share", "kicad", "*", "3rdparty", "plugins"),
        os.path.join(home, ".config", "kicad", "*", "scripting", "plugins"),
    ]


def _find_generate_script():
    """Locate a manually-copied or PCM-installed generate_interactive_bom.py
    under any of KiCad's known third-party plugin directories."""
    for pattern in _candidate_plugin_root_patterns():
        for root in glob.glob(pattern):
            for match in glob.glob(os.path.join(root, "**", "generate_interactive_bom.py"),
                                    recursive=True):
                return match
    return None


def _try_real_ibom(board_path, out_dir):
    """Invoke InteractiveHtmlBom's CLI entry point if we can find it.

    Preference order: a pip-installed `generate_interactive_bom` console
    script on PATH, then a `generate_interactive_bom.py` found under
    KiCad's plugin directories, run with the same Python that's running
    this plugin (sys.executable — inside pcbnew's scripting environment
    that's KiCad's own bundled Python, which is what the tool needs).

    Returns the path to the generated HTML file, or None if the tool
    isn't available or the run failed for any reason — callers fall back
    to the static table in either case, so this never raises.
    """
    if not board_path or not os.path.isfile(board_path):
        return None  # unsaved board — nothing on disk for the CLI to read

    exe = shutil.which("generate_interactive_bom")
    if exe:
        cmd = [exe]
    else:
        script = _find_generate_script()
        if not script:
            return None
        cmd = [sys.executable, script]

    os.makedirs(out_dir, exist_ok=True)
    before = set(os.listdir(out_dir))
    try:
        subprocess.run(
            cmd + ["--no-browser", "--dest-dir", out_dir, board_path],
            check=True, capture_output=True, timeout=120,
        )
    except Exception:
        return None

    after = set(os.listdir(out_dir))
    new_html = sorted(f for f in (after - before) if f.lower().endswith(".html"))
    if new_html:
        return os.path.join(out_dir, new_html[0])

    # Re-running with the same board name overwrites its own previous
    # output, so the "new files" diff can come up empty on a second run —
    # fall back to whatever ibom-looking html is already sitting there.
    existing = sorted(f for f in after if f.lower().endswith(".html") and "ibom" in f.lower())
    if existing:
        return os.path.join(out_dir, existing[0])
    return None


def _write_fallback_html(bom_rows, path):
    """A small self-contained HTML BOM table: sortable columns, a search
    box, and a per-row 'placed' checkbox for hand-assembly checklists.
    """
    rows_json = json.dumps(bom_rows)
    columns = ["References", "Qty", "Value", "Footprint", "MPN",
               "Manufacturer", "LCSC", "Supplier", "Description"]
    header_html = "".join(f"<th onclick=\"sortBy('{c}')\">{html.escape(c)}</th>" for c in columns)

    doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>LionCircuits BOM</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; color: #1a1a1a; }}
  h1 {{ font-size: 20px; }}
  input#search {{ padding: 8px 10px; width: 320px; margin-bottom: 12px; font-size: 14px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
  th {{ background: #f4f4f4; cursor: pointer; user-select: none; position: sticky; top: 0; }}
  tr:nth-child(even) {{ background: #fafafa; }}
  tr.placed {{ opacity: 0.45; text-decoration: line-through; }}
  .note {{ color: #666; font-size: 12px; margin-bottom: 16px; }}
</style>
</head>
<body>
<h1>LionCircuits BOM</h1>
<p class="note">Generated from PCB footprint fields. For a full interactive board view
with clickable placement highlighting, install the
<a href="https://github.com/openscopeproject/InteractiveHtmlBom" target="_blank">InteractiveHtmlBom</a>
KiCad plugin and re-run LionCircuits.</p>
<input id="search" placeholder="Filter by reference, value, MPN...">
<table id="bomTable">
<thead><tr>{header_html}<th>Placed</th></tr></thead>
<tbody></tbody>
</table>
<script>
const rows = {rows_json};
const columns = {json.dumps(columns)};
let sortCol = null, sortAsc = true;

function render(filter) {{
  const tbody = document.querySelector('#bomTable tbody');
  tbody.innerHTML = '';
  const f = (filter || '').toLowerCase();
  rows.filter(r => JSON.stringify(r).toLowerCase().includes(f)).forEach((r, i) => {{
    const tr = document.createElement('tr');
    tr.id = 'row-' + i;
    columns.forEach(c => {{
      const td = document.createElement('td');
      td.textContent = r[c] || '';
      tr.appendChild(td);
    }});
    const cb = document.createElement('td');
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.onchange = () => tr.classList.toggle('placed', input.checked);
    cb.appendChild(input);
    tr.appendChild(cb);
    tbody.appendChild(tr);
  }});
}}

function sortBy(col) {{
  if (sortCol === col) sortAsc = !sortAsc; else {{ sortCol = col; sortAsc = true; }}
  rows.sort((a, b) => {{
    const av = (a[col] || '').toString();
    const bv = (b[col] || '').toString();
    return sortAsc ? av.localeCompare(bv, undefined, {{numeric: true}})
                   : bv.localeCompare(av, undefined, {{numeric: true}});
  }});
  render(document.getElementById('search').value);
}}

document.getElementById('search').addEventListener('input', e => render(e.target.value));
render('');
</script>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
