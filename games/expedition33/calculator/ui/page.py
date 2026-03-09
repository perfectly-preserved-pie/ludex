from __future__ import annotations

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html

from games.expedition33.calculator.core import HIDDEN_STYLE
from games.expedition33.calculator.ui.bonus_controls import bonus_controls
from games.expedition33.calculator.ui.character_controls import calculator_controls
from games.expedition33.calculator.ui.setup_fields import (
    attack_input,
    character_select,
    compare_skill_dropdown,
    enemy_affinity_select,
    pictos_select,
    save_import_store,
    save_upload,
    skill_dropdown,
    weapon_level_select,
    weapon_select,
)
from games.expedition33.helpers import build_title_card


def build_sources_alert() -> dbc.Alert:
    """Build the data-source attribution alert."""

    return dbc.Alert(
        html.Div(
            [
                html.Span(
                    [
                        "Skill data courtesy of ",
                        html.A(
                            "JohnnyDamajer",
                            href="https://docs.google.com/spreadsheets/d/1hU299Jof7Ygtg1JmbITeBxFXh5iHtOIBPB1gVCRil6o/",
                            target="_blank",
                            rel="noopener noreferrer",
                        ),
                    ]
                ),
                html.Span(
                    [
                        "Pictos, weapon, and damage scaling data courtesy of ",
                        html.A(
                            "ErikLeb and Blueye95",
                            href="https://docs.google.com/spreadsheets/d/1-d2ybbBy94JiVF6Mo_0-jmICTueH4oyN2q9_Va2gXbw/",
                            target="_blank",
                            rel="noopener noreferrer",
                        ),
                    ],
                    className="d-block mt-1",
                ),
            ]
        ),
        color="info",
        className="mt-2",
    )


def build_save_import_section() -> html.Div:
    """Build the imported-save setup block."""

    return html.Div(
        [
            dmc.Group(
                [
                    save_upload,
                    dmc.Text(
                        "Import a Clair Obscur: Expedition 33 `.sav` to prefill character, weapon, skill, and lumina selections.",
                        c="dimmed",
                        size="sm",
                    ),
                ],
                gap="sm",
                align="center",
            ),
            dbc.Alert(
                [
                    html.P(
                        [
                            "Save filename pattern: ",
                            html.Code("EXPEDITION_0_<save date>.sav"),
                        ],
                        className="mb-1",
                    ),
                    html.P(
                        [
                            "Linux: ",
                            html.Code(
                                "/steamuser/AppData/Local/Sandfall/Saved/SaveGames/<profile>/Backup/"
                            ),
                        ],
                        className="mb-1",
                    ),
                    html.P(
                        [
                            "Windows: ",
                            html.Code(
                                "C:\\Users\\<Your User Name>\\AppData\\Local\\Sandfall\\Saved\\SaveGames\\<some number>"
                            ),
                        ],
                        className="mb-1",
                    ),
                    html.P(
                        [
                            "Game Pass: ",
                            html.Code(
                                r"C:\Users\<Your User Name>\AppData\Local\Packages\KeplerInteractive.Expedition33_<some id>\SystemAppData\wgs\<numbered folders>"
                            ),
                        ],
                        className="mb-1",
                    ),
                    dmc.Text(
                        "If AppData is not visible in File Explorer, turn on hidden files.",
                        c="dimmed",
                        size="sm",
                    ),
                ],
                color="secondary",
                className="mt-2 mb-0 py-2",
            ),
            dbc.Alert(
                id="exp33-calculator-save-import-status",
                is_open=False,
                color="info",
                className="mt-2 mb-0",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Imported Build"),
                    dbc.CardBody(id="exp33-calculator-save-summary-body"),
                ],
                id="exp33-calculator-save-summary-card",
                className="mt-2",
                style=HIDDEN_STYLE,
            ),
        ]
    )


def build_setup_card() -> dbc.Card:
    """Build the calculator setup column."""

    return dbc.Card(
        [
            dbc.CardHeader("Setup"),
            dbc.CardBody(
                dmc.Stack(
                    [
                        build_save_import_section(),
                        character_select,
                        html.Div(
                            [
                                html.Label("Skill", className="form-label"),
                                skill_dropdown,
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Compare Against", className="form-label"),
                                compare_skill_dropdown,
                                html.Div(
                                    "Uses the same character, setup, weapon, Pictos, and enemy affinity.",
                                    className="form-text",
                                ),
                            ]
                        ),
                        attack_input,
                        enemy_affinity_select,
                        weapon_select,
                        weapon_level_select,
                        pictos_select,
                        bonus_controls,
                        calculator_controls,
                    ],
                    gap="md",
                )
            ),
        ]
    )


def build_results_column() -> dbc.Col:
    """Build the calculator results column."""

    return dbc.Col(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Comparison"),
                    dbc.CardBody(id="exp33-calculator-compare-overview-body"),
                ],
                id="exp33-calculator-compare-overview-card",
                className="mb-3 skill-compare-shell",
                style=HIDDEN_STYLE,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Result"),
                                    dbc.CardBody(id="exp33-calculator-result-body"),
                                ],
                                className="mb-3",
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader("Sheet Summary"),
                                    dbc.CardBody(id="exp33-calculator-summary-body"),
                                ]
                            ),
                        ],
                        id="exp33-calculator-primary-column",
                        lg=12,
                        className="mb-4",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Compare Result"),
                                    dbc.CardBody(id="exp33-calculator-compare-result-body"),
                                ],
                                className="mb-3",
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader("Compare Sheet Summary"),
                                    dbc.CardBody(id="exp33-calculator-compare-summary-body"),
                                ]
                            ),
                        ],
                        id="exp33-calculator-compare-column",
                        lg=6,
                        className="mb-4",
                        style=HIDDEN_STYLE,
                    ),
                ],
                className="g-4",
            ),
        ],
        lg=7,
        className="mb-4",
    )


def build_layout() -> dbc.Container:
    """Build the full calculator page layout."""

    return dbc.Container(
        [
            save_import_store,
            build_title_card("Skill Damage Calculator"),
            build_sources_alert(),
            dcc.Markdown(
                "Choose a character, pick a skill, then adjust the relevant combat state. "
                "The result card shows the applied breakpoint or derived formula and estimates damage from your current Attack Power, weapon passives, and Pictos."
            ),
            dbc.Row(
                [
                    dbc.Col(build_setup_card(), lg=5, className="mb-4"),
                    build_results_column(),
                ],
                className="g-4",
            ),
        ],
        fluid=True,
    )


layout = build_layout()
