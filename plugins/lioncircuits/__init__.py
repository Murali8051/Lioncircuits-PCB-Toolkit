"""
LionCircuits Fabrication Export — KiCad PCB Editor action plugin.

Registers a single toolbar/menu action that, when clicked, generates
a fabrication package for the currently open board:

  * Gerbers (all copper + technical layers, including inner layers)
  * Excellon drill files (+ drill map)
  * A BOM (grouped by value/footprint/fields, pulled from footprint fields)
  * A component position / pick-and-place (CPL) file
  * An interactive HTML BOM (iBOM), via the InteractiveHtmlBom plugin if
    it's installed, otherwise a clean self-contained fallback table.

Everything lands in <project>/lioncircuits_output/, and the Gerbers +
drill files are also zipped up ready to send to a fab house.
"""

from .plugin_action import LionCircuitsPlugin

LionCircuitsPlugin().register()
