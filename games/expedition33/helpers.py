from __future__ import annotations
from pandas.api.types import is_numeric_dtype
from pathlib import Path
from typing import Any
import pandas as pd

def clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.dropna(axis=1, how="all")

    # Keep non-empty columns even when the source header is blank.
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
    frame = frame.dropna(how="all")
    return frame


def build_column_defs(frame: pd.DataFrame) -> list[dict[str, Any]]:
    column_defs: list[dict[str, Any]] = []
    for column in frame.columns:
        numeric_col = is_numeric_dtype(frame[column])
        col_def = {
            "field": column,
            "headerName": column,
            "filter": "agNumberColumnFilter" if numeric_col else "agTextColumnFilter",
        }
        if numeric_col:
            # Display commas without changing the underlying numeric value used for sorting/filtering.
            col_def["valueFormatter"] = {"function": "formatNumberWithCommas(params)"}
        column_defs.append(col_def)
    return column_defs


def format_value(value: Any) -> str:
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
