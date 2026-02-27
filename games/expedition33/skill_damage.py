from __future__ import annotations
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update, register_page
from dash.exceptions import PreventUpdate
from games.expedition33.helpers import build_tab_payloads, format_value
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

modal = dbc.Modal(
    [
        dbc.ModalHeader(id="exp33-skill-damage-modal-header"),
        dbc.ModalBody(id="exp33-skill-damage-modal-content"),
        dbc.ModalFooter(
            dbc.Button("Close", id="exp33-skill-damage-close", className="ms-auto", n_clicks=0)
        ),
    ],
    id="exp33-skill-damage-modal",
    is_open=False,
    scrollable=True,
)


def format_modal_value(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return format_value(value)


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
        dcc.Markdown("Click anywhere on a row to open a popup with all skill details."),
        dbc.Tabs(
            id="exp33-skill-damage-tabs",
            active_tab=default_tab,
            children=[dbc.Tab(label=tab["label"], tab_id=tab["tab_id"]) for tab in TAB_CONFIG],
            className="mb-3",
        ),
        grid,
        modal,
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


@callback(
    Output("exp33-skill-damage-modal", "is_open"),
    Output("exp33-skill-damage-modal-header", "children"),
    Output("exp33-skill-damage-modal-content", "children"),
    Input("exp33-skill-damage-grid", "cellClicked"),
    Input("exp33-skill-damage-close", "n_clicks"),
    State("exp33-skill-damage-modal", "is_open"),
    State("exp33-skill-damage-grid", "rowData"),
    prevent_initial_call=True,
)
def open_and_populate_modal(cell_clicked_data, _close_btn_clicks, _modal_open, grid_data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "exp33-skill-damage-close":
        return False, no_update, no_update

    if trigger_id != "exp33-skill-damage-grid" or not cell_clicked_data:
        raise PreventUpdate

    selected_row = cell_clicked_data.get("data")
    row_index = cell_clicked_data.get("rowIndex")
    if selected_row is None and isinstance(row_index, int) and grid_data and 0 <= row_index < len(grid_data):
        selected_row = grid_data[row_index]

    if not selected_row:
        raise PreventUpdate

    skill_name = format_modal_value(selected_row.get("Skill")) or "Skill Details"
    details = {k: v for k, v in selected_row.items() if k != "Skill"}

    content = [
        html.Div(
            [html.B(f"{key}: "), html.Span(format_modal_value(value))],
            style={"margin-bottom": "10px"},
        )
        for key, value in details.items()
    ]

    return True, html.H4(skill_name), html.Div(content, className="modal-content-wrapper")


register_page(__name__, path="/skilldamage", name="Skill Damage", layout=layout)
