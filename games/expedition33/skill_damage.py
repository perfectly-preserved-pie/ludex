from __future__ import annotations
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update, register_page
from dash.exceptions import PreventUpdate
from games.expedition33.helpers import build_tab_payloads, build_title_card, format_value
from pathlib import Path
from typing import Any
import dash_ag_grid as dag
import dash_bootstrap_components as dbc

TAB_CONFIG = [
    {"tab_id": "gustave", "label": "Gustave"},
    {"tab_id": "lune", "label": "Lune"},
    {"tab_id": "maelle", "label": "Maelle"},
    {"tab_id": "monoco", "label": "Monoco"},
    {"tab_id": "sciel", "label": "Sciel"},
    {"tab_id": "verso", "label": "Verso"},
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


def format_modal_value(value: Any) -> str:
    """Format a value for display inside the skill detail modal.

    Args:
        value: The raw row value selected from the grid.

    Returns:
        A user-facing string, with booleans rendered as ``Yes`` or ``No`` and
        all other values delegated to the shared formatter.
    """

    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return format_value(value)


layout = html.Div(
    [
        build_title_card("Skill Damage"),
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
    """Swap the skill grid payload when the active tab changes.

    Args:
        active_tab: The currently selected character tab id.

    Returns:
        A two-item tuple containing the row data and column definitions for the
        requested tab, or the default tab if the id is unknown.
    """

    payload = tab_payloads.get(active_tab) or tab_payloads[default_tab]
    return payload["rowData"], payload["columnDefs"]


@callback(
    Output("exp33-skill-damage-modal", "is_open"),
    Output("exp33-skill-damage-modal-header", "children"),
    Output("exp33-skill-damage-modal-content", "children"),
    Input("exp33-skill-damage-grid", "cellClicked"),
    Input("exp33-skill-damage-close", "n_clicks"),
    State("exp33-skill-damage-modal", "is_open"),
    State("exp33-skill-damage-grid", "virtualRowData"),
    prevent_initial_call=True,
)
def open_and_populate_modal(
    cell_clicked_data: dict[str, Any] | None,
    _close_btn_clicks: int | None,
    _modal_open: bool,
    virtual_row_data: list[dict[str, Any]] | None,
) -> tuple[bool, Any, Any]:
    """Open the skill detail modal for the clicked grid row.

    Args:
        cell_clicked_data: The Dash AG Grid click payload for the selected
            cell.
        _close_btn_clicks: The close button click count. It is unused beyond
            triggering the callback.
        _modal_open: The current modal state. It is unused because the callback
            always recomputes the next state.
        virtual_row_data: The currently visible grid rows, used as a fallback
            lookup when the click payload omits the row data.

    Returns:
        A tuple of ``(is_open, header_children, body_children)`` for the modal.
    """

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
    if (
        selected_row is None
        and isinstance(row_index, int)
        and virtual_row_data
        and 0 <= row_index < len(virtual_row_data)
    ):
        selected_row = virtual_row_data[row_index]

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


register_page(__name__, path="/skilldamage", name="Skill Damage", title="Skill Damage", layout=layout)
