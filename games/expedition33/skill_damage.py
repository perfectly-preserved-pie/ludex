from __future__ import annotations
from dash import Input, Output, callback, dcc, html, register_page
from games.expedition33.helpers import build_tab_payloads
from pathlib import Path
import dash_ag_grid as dag
import dash_bootstrap_components as dbc

TAB_CONFIG = [
    {"tab_id": "maelle", "label": "Maelle"},
    {"tab_id": "lune", "label": "Lune"},
    {"tab_id": "monoco", "label": "Monoco"},
    {"tab_id": "sciel", "label": "Sciel"},
    {"tab_id": "verso", "label": "Verso"},
    {"tab_id": "gustave", "label": "Gustave"},
]

CSV_DIR = Path(__file__).resolve().parents[2] / "assets" / "expedition33" / "clair_skill_damage"

# Dark theme for ag-grid
# https://www.dash-mantine-components.com/dash-ag-grid#dash-ag-grid-%E2%89%A5-v33
ag_grid_theme = {
    "function": (
        "themeQuartz.withParams({"
        "accentColor: 'var(--mantine-primary-color-filled)', "
        "backgroundColor: 'var(--mantine-color-body)', "
        "foregroundColor: 'var(--mantine-color-text)', "
        "fontFamily: 'var(--mantine-font-family)', "
        "headerFontWeight: 600"
        "})"
    )
}

tab_payloads = build_tab_payloads(TAB_CONFIG, CSV_DIR)
default_tab = TAB_CONFIG[0]["tab_id"]

grid = dag.AgGrid(
    id="exp33-skill-damage-grid",
    rowData=tab_payloads[default_tab]["rowData"],
    columnDefs=tab_payloads[default_tab]["columnDefs"],
    defaultColDef={"filter": True, "sortable": True, "resizable": True},
    style={"width": "100%", "height": "calc(100vh - 320px)"},
    dashGridOptions={
        "theme": ag_grid_theme,
        "pagination": True,
        "paginationPageSize": 50,
    },
)

layout = html.Div(
    [
        html.H1("Skill Damage"),
        dbc.Alert(
            html.Span(
                [
                    "Data courtesy of ",
                    html.A(
                        "JohnnyDamajer",
                        href="https://docs.google.com/spreadsheets/d/1hU299Jof7Ygtg1JmbITeBxFXh5iHtOIBPB1gVCRil6o/",
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                ]
            ),
            color="info",
            className="mt-2",
        ),
        dbc.Tabs(
            id="exp33-skill-damage-tabs",
            active_tab=default_tab,
            children=[dbc.Tab(label=tab["label"], tab_id=tab["tab_id"]) for tab in TAB_CONFIG],
            className="mb-3",
        ),
        grid,
    ]
)


@callback(
    Output("exp33-skill-damage-grid", "rowData"),
    Output("exp33-skill-damage-grid", "columnDefs"),
    Input("exp33-skill-damage-tabs", "active_tab"),
)
def update_grid_for_tab(active_tab: str) -> tuple[list[dict], list[dict]]:
    payload = tab_payloads.get(active_tab) or tab_payloads[default_tab]
    return payload["rowData"], payload["columnDefs"]


register_page(__name__, path="/skilldamage", name="Skill Damage", layout=layout)
