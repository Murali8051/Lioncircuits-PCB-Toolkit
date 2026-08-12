import os

import pcbnew
import wx

from .dialog import LionCircuitsDialog
from .process import run_export


class LionCircuitsPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "LionCircuits — Fabrication Export"
        self.category = "Fabrication"
        self.description = ("Generate Gerbers, drill files, BOM, position file, "
                             "and interactive BOM in one click.")
        self.show_toolbar_button = True
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        self.icon_file_name = icon_path if os.path.isfile(icon_path) else ""

    def Run(self):
        board = pcbnew.GetBoard()
        if board is None:
            wx.MessageBox("No board is open.", "LionCircuits", wx.OK | wx.ICON_WARNING)
            return

        board_path = board.GetFileName()
        project_dir = os.path.dirname(board_path) if board_path else os.getcwd()
        default_out_dir = os.path.join(project_dir, "lioncircuits_output")

        parent = wx.GetActiveWindow()
        dlg = LionCircuitsDialog(parent, default_out_dir)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        options = dlg.get_options()
        dlg.Destroy()

        if not any([options["gerbers"], options["bom"], options["bom_quote"],
                    options["position"], options["ibom"], options["ipc_netlist"]]):
            wx.MessageBox("Nothing selected to export.", "LionCircuits", wx.OK | wx.ICON_INFORMATION)
            return

        wx.BeginBusyCursor()
        try:
            summary = run_export(board, board_path, options)
        finally:
            wx.EndBusyCursor()

        self._show_summary(summary, options["out_dir"])

    def _show_summary(self, summary, out_dir):
        if summary["errors"]:
            lines = []
            if summary["messages"]:
                lines.append("Done:")
                lines.extend(f"  \u2022 {m}" for m in summary["messages"])
            lines.append("")
            lines.append("Errors:")
            lines.extend(f"  \u2022 {e}" for e in summary["errors"])
            text = "\n".join(lines)
            wx.MessageBox(text, "LionCircuits — Export complete", wx.OK | wx.ICON_WARNING)
            return

        text = "Done" if summary["messages"] else "Nothing was generated."
        wx.MessageBox(text, "LionCircuits — Export complete", wx.OK | wx.ICON_INFORMATION)
        self._open_folder(out_dir)

    @staticmethod
    def _open_folder(path):
        try:
            if os.name == "nt":
                os.startfile(path)  # noqa: S606 - user-triggered, opens their own output folder
            elif os.uname().sysname == "Darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception:
            pass  # opening the folder is a nicety, not essential
