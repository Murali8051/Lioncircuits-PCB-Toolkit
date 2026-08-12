"""IPC-D-356 bare-board test netlist export.

Unlike the fab-package naming conventions elsewhere in this plugin, this
one is a real, documented pcbnew API (added to the SWIG Python bindings
in KiCad's kicad/code!89 merge request, available from KiCad 6 onward):

    writer = pcbnew.IPC356D_WRITER(board)
    writer.Write(path)

Same as GUI's File > Fabrication Outputs > IPC-D-356 Netlist File.
"""

import os

import pcbnew


def export_ipc_netlist(board, out_dir, filename="netlist.ipc"):
    """Write an IPC-D-356 netlist file. Returns the path written.

    Raises a clear RuntimeError (caught by process.py like every other
    export step, so it surfaces as a message rather than crashing) if
    this KiCad version's pcbnew module doesn't expose IPC356D_WRITER —
    it was only added in KiCad 6.
    """
    if not hasattr(pcbnew, "IPC356D_WRITER"):
        raise RuntimeError(
            "This KiCad version doesn't support IPC-D-356 export "
            "(pcbnew.IPC356D_WRITER is unavailable — needs KiCad 6 or newer)."
        )

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    writer = pcbnew.IPC356D_WRITER(board)
    writer.Write(path)
    return path
