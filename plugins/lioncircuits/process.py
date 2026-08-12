"""Ties the individual exporters together into one export run."""

import csv
import os

from .exporters import archive, bom, gerbers, ibom, netlist, position


def run_export(board, board_path, options):
    """Run the selected exports. `options` is the dict from LionCircuitsDialog.

    Returns a dict summary: {"messages": [...], "errors": [...], "files": [...]}.
    """
    out_dir = options["out_dir"]
    os.makedirs(out_dir, exist_ok=True)

    messages = []
    errors = []
    files = []

    bom_path = None
    if options.get("gerbers"):
        try:
            gerber_dir = os.path.join(out_dir, "gerbers")
            written = gerbers.export_gerbers(board, gerber_dir)
            gerbers.export_drill(board, gerber_dir)
            messages.append(f"Gerbers + drill files: {len(written)} layer(s) -> {gerber_dir}")
            files.append(gerber_dir)

            if options.get("zip"):
                zip_path = os.path.join(out_dir, "gerbers.zip")
                archive.zip_directory(
                    gerber_dir, zip_path,
                    extensions={".gbr", ".gbrjob", ".drl", ".gbl", ".gtl", ".gto",
                                ".gbo", ".gts", ".gbs", ".gko", ".gtp", ".gbp", ".txt"},
                )
                messages.append(f"Zipped fab package -> {zip_path}")
                files.append(zip_path)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the dialog
            errors.append(f"Gerbers/drill export failed: {exc}")

    if options.get("bom"):
        try:
            bom_path = bom.export_bom(board, out_dir)
            messages.append(f"BOM for assembly -> {bom_path}")
            files.append(bom_path)
        except Exception as exc:
            errors.append(f"BOM for assembly export failed: {exc}")

    if options.get("bom_quote"):
        try:
            project_name = os.path.splitext(os.path.basename(board_path))[0] if board_path else "Untitled"
            quote_path = bom.export_bom_quote(
                board, out_dir,
                project_name=project_name,
                currency=options.get("currency", "INR"),
                number_of_boards=options.get("number_of_boards", 1),
            )
            messages.append(f"BOM for components -> {quote_path}")
            files.append(quote_path)
        except Exception as exc:
            errors.append(f"BOM for components export failed: {exc}")

    if options.get("position"):
        try:
            pos_path = position.export_position(board, out_dir)
            messages.append(f"Position file -> {pos_path}")
            files.append(pos_path)
        except Exception as exc:
            errors.append(f"Position file export failed: {exc}")

    if options.get("ibom"):
        try:
            bom_rows = _read_bom_rows(bom_path) if bom_path else []
            ibom_path, used_real = ibom.export_ibom(board, out_dir, bom_rows, board_path)
            label = "Interactive BOM" if used_real else "Interactive BOM (fallback table)"
            messages.append(f"{label} -> {ibom_path}")
            files.append(ibom_path)
        except Exception as exc:
            errors.append(f"Interactive BOM export failed: {exc}")

    if options.get("ipc_netlist"):
        try:
            netlist_path = netlist.export_ipc_netlist(board, out_dir)
            messages.append(f"IPC-D-356 netlist -> {netlist_path}")
            files.append(netlist_path)
        except Exception as exc:
            errors.append(f"IPC-D-356 netlist export failed: {exc}")

    return {"messages": messages, "errors": errors, "files": files}


def _read_bom_rows(bom_path):
    with open(bom_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
