from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html
from dash_iconify import DashIconify
from helpers.ag_grid import SET_FILTER_PARAMS, is_set_filter_candidate
from games.xenosaga.item_effects import (
    get_episode1_item_effect,
    get_episode2_item_effect,
    get_episode3_item_effect,
)
from pandas.api.types import is_numeric_dtype

EPISODE1_DROP_EFFECT_FIELDS = {
    "Normal Drop": "Normal Drop Effect",
    "Rare Drop": "Rare Drop Effect",
}
EPISODE2_DROP_EFFECT_FIELDS = {
    "Item": "Item Effect",
    "Rare Item": "Rare Item Effect",
}
EPISODE3_DROP_EFFECT_FIELDS = {
    "Normal Drop": "Normal Drop Effect",
    "Rare Drop": "Rare Drop Effect",
    "Stealable Item": "Stealable Item Effect",
}
EPISODE_DROP_EFFECT_FIELDS = {
    "ep1": EPISODE1_DROP_EFFECT_FIELDS,
    "ep2": EPISODE2_DROP_EFFECT_FIELDS,
    "ep3": EPISODE3_DROP_EFFECT_FIELDS,
}
ALL_DROP_EFFECT_FIELDS = {
    **EPISODE1_DROP_EFFECT_FIELDS,
    **EPISODE2_DROP_EFFECT_FIELDS,
    **EPISODE3_DROP_EFFECT_FIELDS,
}
NUMERIC_FILTER_FIELDS = {
    "Beam",
    "Aura",
    "Thunder",
    "Fire",
    "Ice",
    "Pierce",
    "Slash",
    "Hit",
    "Slow",
    "Blind",
    "Heavy",
    "Weak",
    "EthPD",
    "EthDD",
    "Junk",
    "ResDw",
    "Lost",
    "Curse",
}


def load_episode_rows(connection: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """Load and normalize rows for a single episode table.

    Args:
        connection: An open SQLite connection to the bundled enemy database.
        table_name: The table name for the selected Xenosaga episode.

    Returns:
        A DataFrame sorted by enemy name, with helper columns such as ``uuid``
        removed when present.
    """

    frame = pd.read_sql_query(f'SELECT * FROM "{table_name}"', connection)
    if "uuid" in frame.columns:
        frame = frame.drop(columns=["uuid"])
    frame = frame.sort_values(by=["Name"], na_position="last")
    return frame


def get_item_effect_for_episode(episode_tab: str, item_name: Any) -> str | None:
    """Return a display description for a drop item based on the episode."""

    if episode_tab == "ep1":
        return get_episode1_item_effect(item_name)
    if episode_tab == "ep2":
        return get_episode2_item_effect(item_name)
    if episode_tab == "ep3":
        return get_episode3_item_effect(item_name)
    return None


def enrich_episode_drop_columns(frame: pd.DataFrame, episode_tab: str) -> pd.DataFrame:
    """Attach hidden item-effect fields used by the UI."""

    enriched_frame = frame.copy()
    for field, effect_field in EPISODE_DROP_EFFECT_FIELDS.get(episode_tab, {}).items():
        if field not in enriched_frame.columns:
            continue
        enriched_frame[effect_field] = enriched_frame[field].map(
            lambda value: get_item_effect_for_episode(episode_tab, value)
        )
    return enriched_frame


def build_episode1_item_detail(label: str, item_name: Any, effect: Any) -> html.Div:
    """Render an inline item drop row with a hover/focus tooltip."""

    item_label = str(item_name).strip() if item_name is not None else "N/A"
    if item_label == "":
        item_label = "N/A"

    formatted_item = format_value(item_label)
    tooltip_target_id = re.sub(r"[^a-z0-9]+", "-", f"{label}-{formatted_item}".lower()).strip("-")
    tooltip_target_id = f"xenosaga-item-detail-{tooltip_target_id or 'unknown'}"

    detail_children: list[Any] = [
        html.B(f"{label}: "),
        html.Span(
            formatted_item,
            id=tooltip_target_id,
            className="xenosaga-item-tooltip-target",
            tabIndex=0,
        ),
    ]
    if effect:
        detail_children.extend(
            [
                html.Span(
                    DashIconify(
                        icon="material-symbols:info-outline-rounded",
                        width=14,
                        height=14,
                    ),
                    className="xenosaga-item-tooltip-indicator",
                    **{"aria-hidden": "true"},
                ),
                dbc.Tooltip(
                    str(effect),
                    target=tooltip_target_id,
                    placement="top",
                    className="xenosaga-item-tooltip",
                    trigger="hover focus",
                ),
            ]
        )

    return html.Div(detail_children, className="xenosaga-item-detail-inline")


def build_column_defs(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Build ag-grid column definitions with numeric-aware behavior.

    Args:
        frame: The DataFrame used to infer column names and numeric handling.

    Returns:
        A list of ag-grid column definitions with numeric columns configured for
        sorting and formatting.
    """

    # Determine if a column is numeric using dtype first, then sampled values
    def is_numeric_col(column_name: str) -> bool:
        """Estimate whether a mixed-content column should behave numerically.

        Args:
            column_name: The DataFrame column name to inspect.

        Returns:
            ``True`` when the column values should use numeric filtering and
            formatting in ag-grid, otherwise ``False``.
        """

        if column_name in NUMERIC_FILTER_FIELDS or is_numeric_dtype(frame[column_name].dtype):
            return True

        non_na_values = frame[column_name].dropna()
        if non_na_values.empty:
            return False

        sample_values = non_na_values.sample(min(100, len(non_na_values)), random_state=0).tolist()
        try:
            for value in sample_values:
                first_part = str(value).split("-")[0].strip().replace(",", "")
                float(first_part)
            return True
        except (TypeError, ValueError):
            return False

    boolean_columns = get_boolean_like_columns(frame)

    text_filter_fields = {"Name"}
    column_defs: list[dict[str, Any]] = []
    for field in frame.columns:
        if field in boolean_columns:
            col_def = {
                "field": field,
                "cellDataType": "boolean",
                "filter": "agSetColumnFilter",
                "filterParams": SET_FILTER_PARAMS,
            }
            if field == "Name":
                col_def["pinned"] = "left"
            column_defs.append(col_def)
            continue

        numeric_col = is_numeric_col(field)
        set_filter_col = (
            not numeric_col
            and is_set_filter_candidate(
                frame[field],
                field,
                excluded_fields=text_filter_fields,
            )
        )
        filter_type = (
            "agNumberColumnFilter"
            if numeric_col
            else "agSetColumnFilter" if set_filter_col else "agTextColumnFilter"
        )
        col_def: dict[str, Any] = {
            "field": field,
            "filter": filter_type,
        }
        if set_filter_col:
            col_def["filterParams"] = SET_FILTER_PARAMS
        if numeric_col:
            field_name = json.dumps(field)
            col_def["valueGetter"] = {"function": f"extractRangeStart(params, {field_name})"}
            col_def["valueFormatter"] = {"function": "formatNumberWithCommas(params)"}
        if field == "Name":
            col_def["pinned"] = "left"
        column_defs.append(col_def)
    return column_defs


def style_episode_drop_columns(column_defs: list[dict[str, Any]], episode_tab: str) -> list[dict[str, Any]]:
    """Make item drop columns compact, with hover affordances."""

    styled_column_defs: list[dict[str, Any]] = []
    drop_effect_fields = EPISODE_DROP_EFFECT_FIELDS.get(episode_tab, {})
    for col_def in column_defs:
        field = col_def.get("field")
        effect_field = drop_effect_fields.get(field)
        if not effect_field:
            styled_column_defs.append(col_def)
            continue

        styled_column_defs.append(
            {
                **col_def,
                "minWidth": 170,
                "tooltipValueGetter": {
                    "function": f"getLinkedFieldValue(params, {json.dumps(effect_field)})"
                },
                "cellStyle": {
                    "function": f"getItemDropCellStyle(params, {json.dumps(effect_field)})"
                },
            }
        )

    return styled_column_defs


def get_boolean_like_columns(frame: pd.DataFrame) -> set[str]:
    """Return columns whose non-empty values are textual booleans."""

    boolean_columns: set[str] = set()
    boolean_tokens = {"yes", "no", "true", "false"}

    for field in frame.columns:
        non_na_values = frame[field].dropna()
        if non_na_values.empty:
            continue

        normalized_values = {
            str(value).strip().lower() for value in non_na_values if str(value).strip() != ""
        }
        if normalized_values and normalized_values <= boolean_tokens:
            boolean_columns.add(field)

    return boolean_columns


def normalize_grid_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert textual booleans to real bools and replace missing values with ``None``."""

    normalized_frame = frame.copy()
    boolean_columns = get_boolean_like_columns(normalized_frame)
    boolean_map = {"yes": True, "true": True, "no": False, "false": False}

    for field in boolean_columns:
        normalized_frame[field] = normalized_frame[field].map(
            lambda value: boolean_map.get(str(value).strip().lower()) if pd.notnull(value) else None
        )

    return normalized_frame.astype(object).where(pd.notnull(normalized_frame), None)


def format_value(value: Any) -> str:
    """Format a cell value for modal or grid display.

    Args:
        value: The raw value retrieved from a table row.

    Returns:
        A user-facing string with empty values converted to ``N/A`` and numeric
        values formatted with thousands separators.
    """

    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str) and value == "":
        return "N/A"
    if not isinstance(value, str) and pd.isna(value):
        return "N/A"
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return f"{int(numeric_value):,}"
        return f"{numeric_value:,}"
    except (ValueError, TypeError):
        return str(value)


def apply_element_style(text: str) -> list[Any]:
    """Apply lightweight color styling to known comma-separated tokens.

    Args:
        text: A comma-separated string of element or status names.

    Returns:
        A list of Dash text fragments with known tokens wrapped in styled spans.
    """

    color_styles: dict[str, str] = {
        "Lightning": "yellow",
        "Fire": "red",
        "Ice": "lightblue",
        "Beam": "pink",
        "Yes": "green",
        "No": "red",
        "Cannot": "red",
    }
    parts: list[str] = text.split(", ")
    spans: list[Any] = []
    for i, part in enumerate(parts):
        color = color_styles.get(part)
        if color:
            spans.append(html.Span(part, style={"color": color}))
        else:
            spans.append(html.Span(part))
        if i < len(parts) - 1:
            spans.append(", ")
    return spans
