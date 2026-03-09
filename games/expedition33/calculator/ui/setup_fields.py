from __future__ import annotations

from dash import dcc, html
import dash_mantine_components as dmc

from games.expedition33.calculator.core import (
    CALCULATOR_DATA,
    CHARACTER_META,
    DEFAULT_CHARACTER,
    DEFAULT_SKILLS,
    HIDDEN_STYLE,
    skill_options_for,
)
from games.expedition33.calculator.pictos import PICTO_OPTIONS
from games.expedition33.calculator.weapons import WEAPON_LEVEL_OPTIONS, weapon_options_for


character_select = dmc.Select(
    id="exp33-calculator-character",
    label="Character",
    value=DEFAULT_CHARACTER,
    data=[{"label": meta["label"], "value": key} for key, meta in CHARACTER_META.items()],
    clearable=False,
    allowDeselect=False,
)

skill_dropdown = dcc.Dropdown(
    id="exp33-calculator-skill",
    options=skill_options_for(DEFAULT_CHARACTER),
    value=DEFAULT_SKILLS[DEFAULT_CHARACTER],
    clearable=False,
)

compare_skill_dropdown = dcc.Dropdown(
    id="exp33-calculator-compare-skill",
    options=skill_options_for(DEFAULT_CHARACTER),
    value=None,
    clearable=True,
    placeholder="Optional second skill for comparison",
)

save_upload = dcc.Upload(
    id="exp33-calculator-save-upload",
    children=dmc.Button("Import .sav", variant="light"),
    accept=".sav,.SAV",
    multiple=False,
)

save_import_store = dcc.Store(id="exp33-calculator-save-import-store")

attack_input = dmc.NumberInput(
    id="exp33-calculator-attack",
    label="Attack Power",
    value=CALCULATOR_DATA[DEFAULT_CHARACTER]["default_attack"],
    min=1,
    step=1,
)

enemy_affinity_select = dmc.Select(
    id="exp33-calculator-enemy-affinity",
    label="Enemy affinity",
    value="neutral",
    data=[
        {"label": "Neutral", "value": "neutral"},
        {"label": "Weakness", "value": "weak"},
        {"label": "Resistance", "value": "resist"},
    ],
    clearable=False,
    allowDeselect=False,
    description="Only affects elemental skills. Weakness = 1.5x, Resistance = 0.5x.",
)

pictos_select = dmc.MultiSelect(
    id="exp33-calculator-pictos",
    label="Pictos/Lumina",
    data=PICTO_OPTIONS,
    value=[],
    searchable=True,
    clearable=True,
    placeholder="Select supported damage Pictos/Lumina",
    description="Only directly calculable damage Pictos/Lumina from the sheet are listed here.",
)

weapon_select = dmc.Select(
    id="exp33-calculator-weapon",
    label="Weapon",
    data=weapon_options_for(DEFAULT_CHARACTER),
    value=None,
    searchable=True,
    clearable=True,
    placeholder="Select a supported damage-modifying weapon",
    description="Only weapon passives with direct damage effects the calculator can model are listed here.",
)

weapon_level_select = html.Div(
    dmc.Select(
        id="exp33-calculator-weapon-level",
        label="Weapon level",
        value="20",
        data=WEAPON_LEVEL_OPTIONS,
        clearable=False,
    ),
    id="exp33-calculator-control-weapon-level",
    style=HIDDEN_STYLE,
)
