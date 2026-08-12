"""Small wx dialog: choose which outputs to generate and the destination
folder, then run. Kept intentionally simple — this is a utility dialog,
not the main event."""

import os
import wx


class LionCircuitsDialog(wx.Dialog):
    def __init__(self, parent, default_out_dir):
        super().__init__(parent, title="LionCircuits — Fabrication Export",
                          size=(440, 456),
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Generate fabrication files")
        title_font = title.GetFont()
        title_font.SetPointSize(title_font.GetPointSize() + 2)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        sizer.Add(title, 0, wx.ALL, 12)

        self.cb_gerbers = wx.CheckBox(panel, label="Gerbers + drill files")
        self.cb_bom = wx.CheckBox(panel, label="BOM for assembly")
        self.cb_bom_quote = wx.CheckBox(panel, label="BOM for components")
        self.cb_position = wx.CheckBox(panel, label="Component position file (CPL)")
        self.cb_ibom = wx.CheckBox(panel, label="Interactive BOM (HTML)")
        self.cb_ipc_netlist = wx.CheckBox(panel, label="IPC-D-356 netlist")
        for cb in (self.cb_gerbers, self.cb_bom, self.cb_bom_quote, self.cb_position,
                   self.cb_ibom, self.cb_ipc_netlist):
            cb.SetValue(True)
            sizer.Add(cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # --- Quote BOM details (Project / Currency / Number of Boards) ---
        quote_row = wx.BoxSizer(wx.HORIZONTAL)
        quote_row.Add(wx.StaticText(panel, label="Currency:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.currency_ctrl = wx.Choice(panel, choices=["INR", "USD"])
        self.currency_ctrl.SetSelection(0)
        quote_row.Add(self.currency_ctrl, 0, wx.RIGHT, 16)
        quote_row.Add(wx.StaticText(panel, label="Number of boards:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.num_boards_ctrl = wx.SpinCtrl(panel, min=1, max=100000, initial=1, size=(80, -1))
        # wx.SpinCtrl on Windows doesn't commit a typed-in value until the
        # control loses focus or Enter is pressed — clicking Generate right
        # after typing a number (without Tab/Enter first) would silently
        # read back the old value via GetValue(). Track it live on every
        # keystroke/spin instead of reading cold at Generate time.
        self._number_of_boards = 1
        self.num_boards_ctrl.Bind(wx.EVT_TEXT, self._on_num_boards_change)
        self.num_boards_ctrl.Bind(wx.EVT_SPINCTRL, self._on_num_boards_change)
        quote_row.Add(self.num_boards_ctrl, 0)
        sizer.Add(quote_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)

        # --- Output folder picker ---
        out_label = wx.StaticText(panel, label="Output folder:")
        sizer.Add(out_label, 0, wx.LEFT | wx.TOP, 12)

        out_row = wx.BoxSizer(wx.HORIZONTAL)
        self.out_dir_ctrl = wx.TextCtrl(panel, value=default_out_dir)
        browse_btn = wx.Button(panel, label="Browse...")
        browse_btn.Bind(wx.EVT_BUTTON, self._on_browse)
        out_row.Add(self.out_dir_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        out_row.Add(browse_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(out_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)

        self.cb_zip = wx.CheckBox(panel, label="Zip Gerbers + drill files for fab upload")
        self.cb_zip.SetValue(True)
        sizer.Add(self.cb_zip, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 12)

        sizer.AddStretchSpacer(1)
        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        # --- Buttons: right-aligned Generate / Cancel ---
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        generate_btn = wx.Button(panel, wx.ID_OK, "Generate")
        generate_btn.SetDefault()
        btn_row.AddStretchSpacer(1)
        btn_row.Add(cancel_btn, 0, wx.RIGHT, 8)
        btn_row.Add(generate_btn, 0)
        sizer.Add(btn_row, 0, wx.EXPAND | wx.ALL, 12)

        panel.SetSizer(sizer)

        # Attach the panel to the dialog itself so it actually fills the
        # window instead of collapsing to its minimum content size.
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(outer)

        self.SetMinSize((420, 436))
        self.Layout()
        self.Fit()

    def _on_browse(self, event):
        dlg = wx.DirDialog(self, "Choose output folder", self.out_dir_ctrl.GetValue())
        if dlg.ShowModal() == wx.ID_OK:
            self.out_dir_ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

    def _on_num_boards_change(self, event):
        try:
            value = self.num_boards_ctrl.GetValue()
            if value:
                self._number_of_boards = value
        except (ValueError, TypeError):
            pass  # mid-edit / temporarily invalid text — keep the last good value
        event.Skip()

    def get_options(self):
        # Belt-and-braces: also read GetValue() directly, in case focus
        # already left the control (normal case) — but prefer the
        # live-tracked value, which is the one that's actually reliable
        # right after typing.
        try:
            cold_value = self.num_boards_ctrl.GetValue()
        except (ValueError, TypeError):
            cold_value = None
        number_of_boards = self._number_of_boards or cold_value or 1

        return {
            "gerbers": self.cb_gerbers.GetValue(),
            "bom": self.cb_bom.GetValue(),
            "bom_quote": self.cb_bom_quote.GetValue(),
            "position": self.cb_position.GetValue(),
            "ibom": self.cb_ibom.GetValue(),
            "ipc_netlist": self.cb_ipc_netlist.GetValue(),
            "zip": self.cb_zip.GetValue(),
            "out_dir": self.out_dir_ctrl.GetValue() or os.getcwd(),
            "currency": self.currency_ctrl.GetStringSelection() or "INR",
            "number_of_boards": number_of_boards,
        }
