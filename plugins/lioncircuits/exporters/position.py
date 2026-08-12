"""Component position / pick-and-place (CPL) file export."""

import csv
import os
import pcbnew


def export_position(board, out_dir, filename="positions.csv"):
    """Write a CSV placement file (Ref, Val, Package, PosX, PosY, Rot, Side)
    for every footprint that isn't excluded from position files.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)

    rows = []
    for fp in board.GetFootprints():
        attrs = fp.GetAttributes()
        try:
            excluded = bool(attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        except AttributeError:
            excluded = False
        if excluded:
            continue

        pos = fp.GetPosition()
        rows.append({
            "Ref": fp.GetReference(),
            "Val": fp.GetValue(),
            "Package": str(fp.GetFPID().GetLibItemName()),
            "PosX(mm)": round(pcbnew.ToMM(pos.x), 4),
            "PosY(mm)": round(-pcbnew.ToMM(pos.y), 4),  # KiCad Y is flipped vs. most CAM tools
            "Rotation": round(fp.GetOrientationDegrees(), 2),
            "Side": "bottom" if fp.IsFlipped() else "top",
        })

    rows.sort(key=lambda r: _natural_key(r["Ref"]))

    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Ref", "Val", "Package", "PosX(mm)", "PosY(mm)", "Rotation", "Side"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return path


def _natural_key(ref):
    """Sort references like R1, R2, R10 in human order instead of R1, R10, R2."""
    import re
    parts = re.split(r"(\d+)", ref)
    return [int(p) if p.isdigit() else p for p in parts]
