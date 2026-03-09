from __future__ import annotations
from dash import register_page
from games.expedition33.calculator import callbacks as _callbacks
from games.expedition33.calculator.ui.page import layout

register_page(
    __name__,
    path="/exp33/calculator",
    name="Skill Damage Calculator",
    title="Expedition 33 Skill Damage Calculator",
    layout=layout,
)
