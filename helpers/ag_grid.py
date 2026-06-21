from __future__ import annotations

from typing import Any

AUTO_SIZE_COLUMNS = "autoSize"
SET_FILTER_PARAMS = {"buttons": ["reset", "apply"], "closeOnApply": True}


def is_set_filter_candidate(
    values: Any,
    field: str,
    *,
    excluded_fields: set[str] | None = None,
    max_unique_values: int = 40,
    max_unique_ratio: float = 0.6,
    max_average_value_length: int = 40,
) -> bool:
    """Return whether a text-like column should use AG Grid's set filter."""

    if excluded_fields and field in excluded_fields:
        return False

    non_empty_values = [
        str(value).strip()
        for value in values.dropna().tolist()
        if str(value).strip() != ""
    ]
    if not non_empty_values:
        return False

    unique_values = set(non_empty_values)
    unique_count = len(unique_values)
    unique_ratio = unique_count / len(non_empty_values)
    average_value_length = sum(len(value) for value in unique_values) / unique_count

    return (
        unique_count <= max_unique_values
        and unique_ratio <= max_unique_ratio
        and average_value_length <= max_average_value_length
    )


def default_grid_column_config() -> dict[str, Any]:
    """Return shared Dash AG Grid column defaults."""

    return {
        "defaultColDef": {"filter": True, "sortable": True, "resizable": True},
        "columnSize": AUTO_SIZE_COLUMNS,
        "columnSizeOptions": {"skipHeader": False},
    }


def default_dash_grid_options(**options: Any) -> dict[str, Any]:
    """Return shared Dash AG Grid options merged with page-specific options."""

    return {
        "suppressColumnVirtualisation": True,
        **options,
    }
