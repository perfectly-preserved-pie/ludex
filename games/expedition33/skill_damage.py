from __future__ import annotations
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update, register_page
from dash.exceptions import PreventUpdate
from games.expedition33.helpers import build_tab_payloads, build_title_card, format_value
import math
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
MULTIPLIER_COLUMNS = (
    "Damage Multi",
    "Dmg Con1",
    "Con Max Dmg",
    "Dmg Max",
    "All Crit Dmg",
    "DmMax",
    "ConDmg",
    "ConTwilight",
    "TwilightDmg",
    "SRankMAX",
)
DETAIL_FIELD_PRIORITY = (
    "Damage Multi",
    "Condition 1",
    "Dmg Con1",
    "Condition",
    "ConDmg",
    "ConTwilight",
    "TwilightDmg",
    "Con Max Dmg",
    "Dmg Max",
    "All Crit Dmg",
    "DmMax",
    "SRankMAX",
    "Cost",
    "Skill Points Cost",
    "Game Description",
    "Attack Type",
    "Target",
    "AOE",
    "Element",
    "Damage Element",
    "Stance",
    "Mask",
    "Lunar",
    "Foretell",
    "Base Scaling",
    "Hit Count",
    "Conditional Scaling",
    "Grade Bonus",
    "Creates Stains",
    "Consume Stains",
    "Required Stains",
    "Wheel Steps",
    "Lune Mode",
    "Maelle Mode",
    "Monoco Mode",
    "Verso Mode",
    "Base Turns",
    "Max Turns",
    "Notes",
)

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
    style={"width": "100%", "height": "65vh", "minHeight": "420px"},
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


def normalize_tab_id(active_tab: str | None) -> str:
    """Resolve the requested tab id to a loaded payload key."""

    return active_tab if active_tab in tab_payloads else default_tab


def raw_skill_name(row: dict[str, Any]) -> str:
    """Read the unformatted skill name from a sheet row."""

    value = row.get("Skill")
    return str(value).strip() if value is not None else ""


tab_skill_rows = {
    tab_id: {
        raw_skill_name(row): row
        for row in payload["rowData"]
        if raw_skill_name(row)
    }
    for tab_id, payload in tab_payloads.items()
}
tab_skill_options = {
    tab_id: [{"label": skill_name, "value": skill_name} for skill_name in rows]
    for tab_id, rows in tab_skill_rows.items()
}


def default_compare_values(active_tab: str | None) -> tuple[str | None, str | None]:
    """Pick the default compare selections for a tab."""

    options = tab_skill_options.get(normalize_tab_id(active_tab), [])
    if not options:
        return None, None

    left_value = options[0]["value"]
    right_value = options[1]["value"] if len(options) > 1 else options[0]["value"]
    return left_value, right_value


def parse_compare_number(value: Any) -> float | None:
    """Parse a numeric sheet cell used by the comparison summary."""

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return None if isinstance(value, float) and math.isnan(value) else float(value)

    if value is None:
        return None

    text = str(value).strip().replace(",", "").replace("%", "").replace("?", "")
    if not text or text == "-":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def format_numeric_metric(value: float | None, suffix: str = "") -> str:
    """Format a numeric comparison metric with an optional suffix."""

    if value is None:
        return "-"
    return f"{format_value(value)}{suffix}"


def display_value_present(value: Any) -> bool:
    """Return whether a row value should be shown in comparison output."""

    return format_modal_value(value) != "-"


def first_present_value(row: dict[str, Any], *keys: str) -> str:
    """Return the first displayable value from a row across candidate keys."""

    for key in keys:
        value = format_modal_value(row.get(key))
        if value != "-":
            return value
    return "-"


def build_metric_tile(label: str, value: str, hint: str) -> html.Div:
    """Build a single compact metric tile for the comparison cards."""

    return html.Div(
        [
            html.Div(label, className="skill-compare-metric-label"),
            html.Div(value, className="skill-compare-metric-value"),
            html.Div(hint, className="skill-compare-metric-hint"),
        ],
        className="skill-compare-metric-tile",
    )


def extract_compare_metrics(row: dict[str, Any]) -> dict[str, Any]:
    """Derive the main comparison metrics for a skill row."""

    base_multiplier = parse_compare_number(row.get("Damage Multi"))
    best_multiplier = base_multiplier
    best_source = "Damage Multi" if base_multiplier is not None else None

    for column in MULTIPLIER_COLUMNS[1:]:
        candidate = parse_compare_number(row.get(column))
        if candidate is not None and (best_multiplier is None or candidate > best_multiplier):
            best_multiplier = candidate
            best_source = column

    cost = parse_compare_number(row.get("Cost"))
    base_per_ap = None
    best_per_ap = None
    if cost not in (None, 0):
        if base_multiplier is not None:
            base_per_ap = round(base_multiplier / cost, 2)
        if best_multiplier is not None:
            best_per_ap = round(best_multiplier / cost, 2)

    return {
        "base_multiplier": base_multiplier,
        "best_multiplier": best_multiplier,
        "best_source": best_source,
        "cost": cost,
        "base_per_ap": base_per_ap,
        "best_per_ap": best_per_ap,
    }


def build_compare_summary_card(slot_label: str, row: dict[str, Any], accent_class: str) -> dbc.Card:
    """Build one side of the skill comparison summary."""

    metrics = extract_compare_metrics(row)
    difficulty = first_present_value(row, "Game Description")
    target = first_present_value(row, "Target")
    element = first_present_value(row, "Damage Element", "Element")
    condition = first_present_value(row, "Condition 1", "Condition")
    meta = " | ".join(value for value in (difficulty, target, element) if value != "-") or "Sheet entry"

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(slot_label, className="skill-compare-slot-label"),
                html.H4(format_modal_value(row.get("Skill")), className="mb-1"),
                html.P(meta, className="skill-compare-meta mb-3"),
                html.Div(
                    [
                        build_metric_tile(
                            "Base Multiplier",
                            format_numeric_metric(metrics["base_multiplier"], "x"),
                            "Unconditional sheet value",
                        ),
                        build_metric_tile(
                            "Best Listed",
                            format_numeric_metric(metrics["best_multiplier"], "x"),
                            f"From {metrics['best_source']}" if metrics["best_source"] else "No listed multiplier",
                        ),
                        build_metric_tile(
                            "AP Cost",
                            format_numeric_metric(metrics["cost"]),
                            "Lower cost wins",
                        ),
                        build_metric_tile(
                            "Best / AP",
                            format_numeric_metric(metrics["best_per_ap"], "x"),
                            "Highest listed multiplier per AP",
                        ),
                    ],
                    className="skill-compare-metrics",
                ),
                html.Div(
                    [
                        html.Div("Condition", className="skill-compare-detail-label"),
                        html.Div(
                            condition if condition != "-" else "No extra damage condition listed.",
                            className="skill-compare-detail-value",
                        ),
                    ],
                    className="skill-compare-detail-block",
                ),
            ]
        ),
        className=f"h-100 skill-compare-card {accent_class}",
    )


def build_advantage_item(
    label: str,
    left_value: float | None,
    right_value: float | None,
    suffix: str = "",
    higher_is_better: bool = True,
) -> html.Div:
    """Describe which side leads for a single numeric metric."""

    if left_value is None or right_value is None:
        detail = "Not comparable"
    elif math.isclose(left_value, right_value):
        detail = "Tie"
    else:
        left_wins = left_value > right_value if higher_is_better else left_value < right_value
        winner = "Skill A" if left_wins else "Skill B"
        detail = f"{winner} by {format_numeric_metric(abs(left_value - right_value), suffix)}"

    return html.Div(
        [
            html.Div(label, className="skill-compare-advantage-label"),
            html.Div(detail, className="skill-compare-advantage-value"),
        ],
        className="skill-compare-advantage-item",
    )


def comparison_fields(left_row: dict[str, Any], right_row: dict[str, Any]) -> list[str]:
    """Resolve the ordered list of fields shown in the detailed comparison table."""

    keys = {
        key
        for key in {*left_row.keys(), *right_row.keys()}
        if key != "Skill" and (display_value_present(left_row.get(key)) or display_value_present(right_row.get(key)))
    }
    ordered_keys = [key for key in DETAIL_FIELD_PRIORITY if key in keys]
    remaining_keys = sorted(keys.difference(ordered_keys))
    return ordered_keys + remaining_keys


def build_compare_table(left_row: dict[str, Any], right_row: dict[str, Any]) -> dbc.Table:
    """Build the full side-by-side field comparison table."""

    rows = []
    for field in comparison_fields(left_row, right_row):
        left_value = format_modal_value(left_row.get(field))
        right_value = format_modal_value(right_row.get(field))
        rows.append(
            html.Tr(
                [
                    html.Th(field, scope="row"),
                    html.Td(html.Div(left_value, className="skill-compare-cell-text")),
                    html.Td(html.Div(right_value, className="skill-compare-cell-text")),
                ],
                className="skill-compare-different-row" if left_value != right_value else None,
            )
        )

    return dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Field"),
                        html.Th("Skill A"),
                        html.Th("Skill B"),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
        bordered=False,
        hover=True,
        responsive=True,
        className="skill-compare-table mb-0",
    )


def build_compare_content(active_tab: str | None, left_skill: str | None, right_skill: str | None) -> Any:
    """Render the skill comparison panel for the selected tab and skills."""

    tab_id = normalize_tab_id(active_tab)
    row_lookup = tab_skill_rows.get(tab_id, {})
    left_row = row_lookup.get(left_skill or "")
    right_row = row_lookup.get(right_skill or "")

    if not left_row or not right_row:
        return dbc.Alert(
            "Select two skills in the current character tab to compare them.",
            color="secondary",
            className="mb-0",
        )

    left_metrics = extract_compare_metrics(left_row)
    right_metrics = extract_compare_metrics(right_row)

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        build_compare_summary_card("Skill A", left_row, "skill-compare-card-a"),
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Comparison", className="skill-compare-slot-label"),
                                    html.H4("Where each skill leads", className="mb-3"),
                                    html.Div(
                                        [
                                            build_advantage_item(
                                                "Base multiplier",
                                                left_metrics["base_multiplier"],
                                                right_metrics["base_multiplier"],
                                                suffix="x",
                                            ),
                                            build_advantage_item(
                                                "Best listed multiplier",
                                                left_metrics["best_multiplier"],
                                                right_metrics["best_multiplier"],
                                                suffix="x",
                                            ),
                                            build_advantage_item(
                                                "AP cost",
                                                left_metrics["cost"],
                                                right_metrics["cost"],
                                                higher_is_better=False,
                                            ),
                                            build_advantage_item(
                                                "Best multiplier per AP",
                                                left_metrics["best_per_ap"],
                                                right_metrics["best_per_ap"],
                                                suffix="x",
                                            ),
                                        ],
                                        className="skill-compare-advantage-list",
                                    ),
                                ]
                            ),
                            className="h-100 skill-compare-card skill-compare-card-delta",
                        ),
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        build_compare_summary_card("Skill B", right_row, "skill-compare-card-b"),
                        lg=4,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Detailed Comparison", className="skill-compare-slot-label"),
                        html.H4("All listed fields", className="mb-3"),
                        build_compare_table(left_row, right_row),
                    ]
                ),
                className="skill-compare-card",
            ),
        ]
    )


default_compare_left, default_compare_right = default_compare_values(default_tab)


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
        dcc.Markdown(
            "Click anywhere on a row to open a popup with all skill details. "
            "Use the compare panel to compare two skills within the active character tab."
        ),
        dbc.Tabs(
            id="exp33-skill-damage-tabs",
            active_tab=default_tab,
            children=[dbc.Tab(label=tab["label"], tab_id=tab["tab_id"]) for tab in TAB_CONFIG],
            className="mb-3",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div("Skill Comparison", className="skill-compare-slot-label"),
                    html.H4("Compare two skills", className="mb-2"),
                    html.P(
                        "Selections follow the current character tab, so you can quickly compare options without leaving the grid.",
                        className="mb-3 skill-compare-meta",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Skill A", html_for="exp33-skill-damage-compare-left"),
                                    dcc.Dropdown(
                                        id="exp33-skill-damage-compare-left",
                                        options=tab_skill_options[default_tab],
                                        value=default_compare_left,
                                        clearable=False,
                                        searchable=True,
                                    ),
                                ],
                                md=6,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Skill B", html_for="exp33-skill-damage-compare-right"),
                                    dcc.Dropdown(
                                        id="exp33-skill-damage-compare-right",
                                        options=tab_skill_options[default_tab],
                                        value=default_compare_right,
                                        clearable=False,
                                        searchable=True,
                                    ),
                                ],
                                md=6,
                                className="mb-3",
                            ),
                        ],
                        className="g-3",
                    ),
                    html.Div(
                        build_compare_content(default_tab, default_compare_left, default_compare_right),
                        id="exp33-skill-damage-compare-content",
                    ),
                ]
            ),
            className="mb-3 skill-compare-shell",
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
    Output("exp33-skill-damage-compare-left", "options"),
    Output("exp33-skill-damage-compare-left", "value"),
    Output("exp33-skill-damage-compare-right", "options"),
    Output("exp33-skill-damage-compare-right", "value"),
    Input("exp33-skill-damage-tabs", "active_tab"),
)
def update_compare_dropdowns(active_tab: str) -> tuple[list[dict[str, str]], str | None, list[dict[str, str]], str | None]:
    """Refresh compare dropdown options when the character tab changes."""

    tab_id = normalize_tab_id(active_tab)
    options = tab_skill_options.get(tab_id, [])
    left_value, right_value = default_compare_values(tab_id)
    return options, left_value, options, right_value


@callback(
    Output("exp33-skill-damage-compare-content", "children"),
    Input("exp33-skill-damage-tabs", "active_tab"),
    Input("exp33-skill-damage-compare-left", "value"),
    Input("exp33-skill-damage-compare-right", "value"),
)
def update_compare_content(active_tab: str, left_skill: str | None, right_skill: str | None) -> Any:
    """Render the skill comparison view for the selected dropdown values."""

    return build_compare_content(active_tab, left_skill, right_skill)


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


register_page(
    __name__,
    path="/exp33/skilldamage",
    name="Skill Damage",
    title="Skill Damage",
    layout=layout,
)
