from __future__ import annotations
from assets.xenosaga.load_sqlite_database import load_sqlite_database
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update, register_page
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
from games.xenosaga.helpers import apply_element_style, build_column_defs, format_value, load_episode_rows
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd

EPISODE_TABS = {
    "ep1": {"label": "Episode I", "table": "episode1"},
    "ep2": {"label": "Episode II", "table": "episode2"},
    "ep3": {"label": "Episode III", "table": "episode3"},
}


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
with load_sqlite_database() as conn:
    episode_frames = {tab_id: load_episode_rows(conn, cfg["table"]) for tab_id, cfg in EPISODE_TABS.items()}


episode_payloads = {}
for tab_id, frame in episode_frames.items():
    safe_frame = frame.astype(object).where(pd.notnull(frame), None)
    episode_payloads[tab_id] = {
        "rowData": safe_frame.to_dict("records"),
        "columnDefs": build_column_defs(frame),
    }

title_card = dbc.Card(
    [
        html.H3("Xenosaga Enemy Database", className="card-title"),
        html.I("Mystic powers, grant me a miracle! ✨", style={"margin-bottom": "10px"}),
        html.P(
            "This is a mobile-friendly searchable, sortable, and filterable table of all enemies in the Xenosaga series, organized by game.",
            style={"margin-bottom": "0px"},
        ),
        html.P(
            "Clicking on anywhere on a row will display the selected enemy's stats in a popup.",
            style={"margin-bottom": "0px"},
        ),
        html.I(
            children=[DashIconify(icon="octicon:mark-github-16")],
            style={
                "margin-right": "5px",
                "margin-left": "0px",
            },
        ),
        html.A("GitHub", href="https://github.com/perfectly-preserved-pie/expedition33/tree/main/pages/xenosaga", target="_blank"),
    ],
    body=True,
)


grid = dag.AgGrid(
    id="xenosaga-grid",
    rowData=episode_payloads["ep1"]["rowData"],
    columnDefs=episode_payloads["ep1"]["columnDefs"],
    defaultColDef={"filter": True, "sortable": True, "resizable": True},
    style={"width": "100%", "height": "calc(100vh - 330px)"},
    dashGridOptions={
        "theme": ag_grid_theme,
        "pagination": True,
        "paginationPageSize": 50,
    },
)

modal = dbc.Modal(
    [
        dbc.ModalHeader(id="xenosaga-modal-header"),
        dbc.ModalBody(id="xenosaga-modal-content"),
        dbc.ModalFooter(
            dbc.Button("Close", id="xenosaga-close", className="ml-auto", n_clicks=0)
        ),
    ],
    id="xenosaga-modal",
    is_open=False,
    scrollable=True,
)


layout = html.Div(
    [
        title_card,
        dcc.Markdown(
            "Select an episode tab and use the column filters to search, sort, and compare enemy stats."
        ),
        dbc.Tabs(
            id="xenosaga-tabs",
            active_tab="ep1",
            children=[dbc.Tab(label=cfg["label"], tab_id=tab_id) for tab_id, cfg in EPISODE_TABS.items()],
            className="mb-3",
        ),
        grid,
        modal,
    ]
)


@callback(
    Output("xenosaga-grid", "rowData"),
    Output("xenosaga-grid", "columnDefs"),
    Input("xenosaga-tabs", "active_tab"),
)
def update_grid_for_episode(active_tab: str) -> tuple[list[dict], list[dict]]:
    payload = episode_payloads.get(active_tab) or episode_payloads["ep1"]
    return payload["rowData"], payload["columnDefs"]


@callback(
    Output("xenosaga-modal", "is_open"),
    Output("xenosaga-modal-header", "children"),
    Output("xenosaga-modal-content", "children"),
    Input("xenosaga-grid", "cellClicked"),
    Input("xenosaga-close", "n_clicks"),
    State("xenosaga-modal", "is_open"),
    State("xenosaga-grid", "rowData"),
    prevent_initial_call=True,
)
def open_and_populate_modal(cell_clicked_data, close_btn_clicks, modal_open, grid_data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "xenosaga-close":
        return False, no_update, no_update

    if trigger_id != "xenosaga-grid" or not cell_clicked_data:
        raise PreventUpdate

    selected_row = cell_clicked_data.get("data")
    row_index = cell_clicked_data.get("rowIndex")
    if selected_row is None and isinstance(row_index, int) and grid_data and 0 <= row_index < len(grid_data):
        selected_row = grid_data[row_index]

    if not selected_row:
        raise PreventUpdate

    enemy_name = selected_row.get("Name", "Enemy Details")
    details = {k: v for k, v in selected_row.items() if k != "Name"}

    content = []
    for key, value in details.items():
        if isinstance(value, str):
            spans = apply_element_style(value)
            content.append(html.Div([html.B(f"{key}: "), *spans], style={"margin-bottom": "10px"}))
        else:
            content.append(
                html.Div(
                    [html.B(f"{key}: "), html.Span(format_value(value))],
                    style={"margin-bottom": "10px"},
                )
            )

    return True, html.H4(enemy_name), html.Div(content, className="modal-content-wrapper")


register_page(
    __name__,
    path="/xenosaga",
    name="Enemy Database",
    layout=layout,
)
