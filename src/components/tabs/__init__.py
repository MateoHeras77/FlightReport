# Inicialización del módulo tabs
from .data_entry_tab import render_data_entry_tab
from .announcements_tab import render_announcements_tab
from .shift_trades_tab import render_shift_trades_tab
from .wheelchair_tab import render_wheelchair_tab
from .timeline_tab import render_timeline_tab

__all__ = [
    "render_data_entry_tab",
    "render_announcements_tab",
    "render_shift_trades_tab",
    "render_wheelchair_tab",
    "render_timeline_tab",
]