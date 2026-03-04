from __future__ import annotations
from dash import html
from dash_iconify import DashIconify
from pandas.api.types import is_numeric_dtype
from pathlib import Path
from typing import Any
import dash_bootstrap_components as dbc
import pandas as pd


def build_title_card(title: str, subtitle: str = "For those who come after.") -> dbc.Card:
    """Build the shared Expedition 33 title card.

    Args:
        title: The main page title.
        subtitle: The italic subtitle shown below the title.

    Returns:
        A Bootstrap card using the same structure as the Xenosaga title card.
    """

    return dbc.Card(
        [
            html.H3(title, className="card-title"),
            html.I(subtitle, style={"marginBottom": "10px"}),
            html.Br(),
            html.Div(
                [
                    html.Span(
                        [
                            DashIconify(icon="octicon:mark-github-16"),
                            html.A(
                                "GitHub",
                                href="https://github.com/perfectly-preserved-pie/ludex/tree/main/games/expedition33/calculator",
                                target="_blank",
                            ),
                        ],
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "gap": "5px",
                        },
                    ),
                    html.Span(
                        [
                            DashIconify(icon="streamline-color:send-email"),
                            html.A(
                                "hey@ludex.games",
                                href="mailto:hey@ludex.games",
                                target="_blank",
                            ),
                        ],
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "gap": "5px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "columnGap": "15px",
                    "rowGap": "8px",
                    "flexWrap": "wrap",
                },
            ),
        ],
        body=True,
    )

def clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize a raw spreadsheet export before displaying it.

    Args:
        frame: The source DataFrame loaded from a CSV sheet.

    Returns:
        A cleaned DataFrame with unnamed columns normalized, junk columns
        removed, and fully empty rows dropped.
    """

    frame = frame.dropna(axis=1, how="all")

    # Keep non-empty columns even when the source header is blank
    renamed_columns: dict[str, str] = {}
    used_names: set[str] = set()
    extra_index = 1
    for column in frame.columns:
        name = str(column).strip()
        if not name or name.startswith("Unnamed:"):
            name = f"Extra {extra_index}"
            extra_index += 1

        while name in used_names:
            name = f"{name}_{extra_index}"
            extra_index += 1

        renamed_columns[column] = name
        used_names.add(name)

    frame = frame.rename(columns=renamed_columns)

    # Remove junk columns 
    extra_cols = [
        c
        for c in frame.columns
        if str(c).startswith("Extra") or str(c).startswith("Test") or str(c) == "Base Attack" or str(c) == "T2" or str(c) == "T3"
    ]
    if extra_cols:
        frame = frame.drop(columns=extra_cols)

    frame = frame.dropna(how="all")
    return frame


def build_column_defs(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Build ag-grid column definitions for an Expedition 33 table.

    Args:
        frame: The cleaned DataFrame used to infer column names and filter
            types.

    Returns:
        A list of ag-grid column definition dictionaries.
    """

    column_defs: list[dict[str, Any]] = []
    for column in frame.columns:
        numeric_col = is_numeric_dtype(frame[column])
        col_def: dict[str, Any] = {
            "field": column,
            "headerName": column,
            "filter": "agNumberColumnFilter" if numeric_col else "agTextColumnFilter",
        }

        # custom comparator for the "Game Description" column to sort by difficulty rank instead of alphabetically
        if column == "Game Description":
            col_def["comparator"] = {"function": "gameDescriptionComparator"}

        column_defs.append(col_def)
    return column_defs


def format_value(value: Any) -> str:
    """Format a table or modal value for display.

    Args:
        value: The raw value pulled from a DataFrame record.

    Returns:
        A user-facing string with empty values replaced by ``-`` and numeric
        values formatted with thousands separators.
    """

    if value is None:
        return "-"
    if isinstance(value, str) and value == "":
        return "-"
    if not isinstance(value, str) and pd.isna(value):
        return "-"
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return f"{int(numeric_value):,}"
        return f"{numeric_value:,}"
    except (ValueError, TypeError):
        return str(value)


def build_tab_payloads(tab_config: list[dict[str, str]], csv_dir: Path) -> dict[str, dict[str, Any]]:
    """Load row and column payloads for each tabbed CSV view.

    Args:
        tab_config: The tab metadata describing which CSV file backs each tab.
        csv_dir: The directory containing the per-tab CSV files.

    Returns:
        A mapping of tab ids to ag-grid payload dictionaries containing
        ``rowData`` and ``columnDefs``.
    """

    payloads: dict[str, dict[str, Any]] = {}
    for tab in tab_config:
        tab_id = tab["tab_id"]
        csv_path = csv_dir / f"{tab_id}.csv"
        frame = clean_frame(pd.read_csv(csv_path))
        safe_frame = frame.astype(object).where(pd.notnull(frame), None)
        payloads[tab_id] = {
            "rowData": safe_frame.to_dict("records"),
            "columnDefs": build_column_defs(frame),
        }
    return payloads
